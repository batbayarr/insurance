-- PostgreSQL Asset Balance Temp Function (As Of Date)
-- Calculates asset balances by AccountId + AssetCardId as of a given date
-- Includes beginning balances, income/disposal transactions, depreciation expenses, and predicted depreciation

DROP FUNCTION IF EXISTS public.calculate_ast_balance_temp(INTEGER, DATE);

CREATE OR REPLACE FUNCTION public.calculate_ast_balance_temp(
    p_account_id INTEGER,
    p_asofdate DATE
)
RETURNS TABLE (
    accountid INTEGER,
    accountcode VARCHAR(20),
    assetname VARCHAR(50),
    assetcardid INTEGER,
    assetcardname VARCHAR(50),
    unitcost NUMERIC(24,6),
    endingquantity NUMERIC(24,6),
    cumulateddepreciation NUMERIC(24,6),
    depreciationexpense NUMERIC(24,6),
    predicteddepreciation NUMERIC(24,6),
    totalexpense NUMERIC(24,6),
    netbookvalue NUMERIC(24,6),
    dailyexpense NUMERIC(24,6),
    usage_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- 1) Period Detection: Get current period dates
    period_bounds AS (
        SELECT 
            rp."BeginDate",
            rp."EndDate"
        FROM ref_period rp
        WHERE p_asofdate BETWEEN rp."BeginDate" AND rp."EndDate"
        ORDER BY rp."BeginDate" DESC
        LIMIT 1
    ),
    period_dates AS (
        SELECT 
            COALESCE((SELECT "BeginDate" FROM period_bounds), date_trunc('month', p_asofdate)::DATE) AS period_begin,
            p_asofdate AS period_end
    ),

    -- 2) Beginning Balance from ast_beginning_balance (per AccountId + AssetCardId)
    starting_balances AS (
        SELECT 
            abb."AccountId",
            abb."AssetCardId",
            rac."AssetId",
            SUM(abb."Quantity") AS beginning_quantity,
            SUM(abb."Quantity" * abb."UnitCost") AS beginning_cost,
            SUM(COALESCE(abb."CumulatedDepreciation", 0)) AS cumulated_depreciation,
            MAX(abb."UnitCost") AS unit_cost
        FROM ast_beginning_balance abb
        INNER JOIN ref_asset_card rac ON abb."AssetCardId" = rac."AssetCardId"
        WHERE abb."AccountId" = p_account_id
            AND abb."IsDelete" = false
        GROUP BY abb."AccountId", abb."AssetCardId", rac."AssetId"
    ),

    -- 3) Income (DocumentTypeId = 10) up to and including asofdate
    income_transactions AS (
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            SUM(adi."Quantity") AS in_quantity,
            SUM(adi."Quantity" * adi."UnitCost") AS in_cost
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 10
            AND ad."AccountId" = p_account_id
            AND ad."DocumentDate" <= p_asofdate
            AND ad."IsDelete" = false
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),

    -- 4) Disposal (DocumentTypeId = 11) up to and including asofdate
    disposal_transactions AS (
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            SUM(adi."Quantity") AS out_quantity,
            SUM(adi."Quantity" * adi."UnitCost") AS out_cost
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 11
            AND ad."AccountId" = p_account_id
            AND ad."DocumentDate" <= p_asofdate
            AND ad."IsDelete" = false
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),

    -- 5) Collect all AccountId + AssetCardId combinations
    account_asset_combinations AS (
        SELECT DISTINCT "AccountId", "AssetCardId", "AssetId" FROM starting_balances
        UNION
        SELECT DISTINCT it."AccountId", it."AssetCardId", rac."AssetId"
        FROM income_transactions it
        INNER JOIN ref_asset_card rac ON it."AssetCardId" = rac."AssetCardId"
        UNION
        SELECT DISTINCT dt."AccountId", dt."AssetCardId", rac."AssetId"
        FROM disposal_transactions dt
        INNER JOIN ref_asset_card rac ON dt."AssetCardId" = rac."AssetCardId"
    ),

    -- 6) Calculate Ending Quantity
    ending_quantities AS (
        SELECT 
            aac."AccountId",
            aac."AssetCardId",
            aac."AssetId",
            COALESCE(sb.beginning_quantity, 0) + COALESCE(it.in_quantity, 0) - COALESCE(dt.out_quantity, 0) AS ending_quantity,
            COALESCE(sb.beginning_cost, 0) + COALESCE(it.in_cost, 0) - COALESCE(dt.out_cost, 0) AS ending_cost,
            COALESCE(sb.cumulated_depreciation, 0) AS cumulated_depreciation,
            COALESCE(sb.unit_cost, rac."UnitCost", 0) AS unit_cost
        FROM account_asset_combinations aac
        LEFT JOIN starting_balances sb ON aac."AccountId" = sb."AccountId" 
            AND aac."AssetCardId" = sb."AssetCardId"
        LEFT JOIN income_transactions it ON aac."AccountId" = it."AccountId" 
            AND aac."AssetCardId" = it."AssetCardId"
        LEFT JOIN disposal_transactions dt ON aac."AccountId" = dt."AccountId" 
            AND aac."AssetCardId" = dt."AssetCardId"
        LEFT JOIN ref_asset_card rac ON aac."AssetCardId" = rac."AssetCardId"
        WHERE COALESCE(sb.beginning_quantity, 0) + COALESCE(it.in_quantity, 0) - COALESCE(dt.out_quantity, 0) > 0
    ),

    -- 7) Depreciation Expense from ast_depreciation_expense (before current period)
    depreciation_expenses AS (
        SELECT
            ade."AccountId",
            ade."AssetCardId",
            COALESCE(SUM(ade."ExpenseAmount"), 0)::NUMERIC(24,6) AS depreciation_expense
        FROM ast_depreciation_expense ade
        INNER JOIN ending_quantities eq ON ade."AccountId" = eq."AccountId"
            AND ade."AssetCardId" = eq."AssetCardId"
        CROSS JOIN period_dates pd
        WHERE ade."AccountId" = p_account_id
            AND ade."DepreciationDate" < pd.period_begin
        GROUP BY ade."AccountId", ade."AssetCardId"
    ),

    -- 8) First receipt date (DocumentDate from income documents)
    asset_receipts AS (
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            MIN(ad."DocumentDate") AS first_receipt_date
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 10
            AND ad."AccountId" = p_account_id
            AND ad."DocumentDate" <= p_asofdate
            AND ad."IsDelete" = false
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),

    -- 9) Predicted Depreciation for current period
    predicted_depreciation AS (
        SELECT
            eq."AccountId",
            eq."AssetCardId",
            CASE 
                WHEN sb."AssetCardId" IS NOT NULL THEN 
                    -- Asset exists in beginning balance: start from period_begin
                    (SELECT period_begin FROM period_dates)
                WHEN ar.first_receipt_date IS NOT NULL THEN
                    -- Asset received mid-period: start from MAX(period_begin, receipt_date)
                    GREATEST(
                        (SELECT period_begin FROM period_dates),
                        ar.first_receipt_date
                    )
                ELSE
                    -- Fallback to period_begin
                    (SELECT period_begin FROM period_dates)
            END AS start_date,
            (SELECT period_end FROM period_dates) AS end_date,
            rac."DailyExpense"
        FROM ending_quantities eq
        INNER JOIN ref_asset_card rac ON eq."AssetCardId" = rac."AssetCardId"
        LEFT JOIN starting_balances sb ON eq."AccountId" = sb."AccountId" 
            AND eq."AssetCardId" = sb."AssetCardId"
        LEFT JOIN asset_receipts ar ON eq."AccountId" = ar."AccountId"
            AND eq."AssetCardId" = ar."AssetCardId"
        WHERE eq.ending_quantity > 0
            AND rac."DailyExpense" > 0
    ),
    predicted_depreciation_calc AS (
        SELECT
            "AccountId",
            "AssetCardId",
            CASE 
                WHEN end_date >= start_date THEN
                    ((end_date - start_date + 1)::NUMERIC(24,6) * "DailyExpense")::NUMERIC(24,6)
                ELSE
                    0::NUMERIC(24,6)
            END AS predicted_depreciation,
            CASE 
                WHEN end_date >= start_date THEN
                    (end_date - start_date + 1)::INTEGER
                ELSE
                    0::INTEGER
            END AS usage_days
        FROM predicted_depreciation
    )

    -- 10) Final SELECT: Integrate all CTEs
    SELECT 
        ra."AccountId",
        ra."AccountCode",
        ras."AssetName",
        rac."AssetCardId",
        rac."AssetCardName",
        COALESCE(eq.unit_cost, rac."UnitCost", 0)::NUMERIC(24,6) AS UnitCost,
        eq.ending_quantity::NUMERIC(24,6) AS EndingQuantity,
        COALESCE(eq.cumulated_depreciation, 0)::NUMERIC(24,6) AS CumulatedDepreciation,
        COALESCE(de.depreciation_expense, 0)::NUMERIC(24,6) AS DepreciationExpense,
        COALESCE(pdc.predicted_depreciation, 0)::NUMERIC(24,6) AS Predicteddepreciation,
        (COALESCE(eq.cumulated_depreciation, 0) + 
         COALESCE(de.depreciation_expense, 0) + 
         COALESCE(pdc.predicted_depreciation, 0))::NUMERIC(24,6) AS TotalExpense,
        (COALESCE(eq.unit_cost, rac."UnitCost", 0) - 
         (COALESCE(eq.cumulated_depreciation, 0) + 
          COALESCE(de.depreciation_expense, 0) + 
          COALESCE(pdc.predicted_depreciation, 0)))::NUMERIC(24,6) AS NetBookValue,
        COALESCE(rac."DailyExpense", 0)::NUMERIC(24,6) AS DailyExpense,
        COALESCE(pdc.usage_days, 0)::INTEGER AS UsageDays
    FROM ending_quantities eq
    INNER JOIN ref_account ra ON eq."AccountId" = ra."AccountId"
    INNER JOIN ref_asset_card rac ON eq."AssetCardId" = rac."AssetCardId"
    INNER JOIN ref_asset ras ON eq."AssetId" = ras."AssetId"
    LEFT JOIN depreciation_expenses de ON eq."AccountId" = de."AccountId" 
        AND eq."AssetCardId" = de."AssetCardId"
    LEFT JOIN predicted_depreciation_calc pdc ON eq."AccountId" = pdc."AccountId" 
        AND eq."AssetCardId" = pdc."AssetCardId"
    WHERE ra."IsDelete" = false
        AND eq.ending_quantity > 0
    ORDER BY ra."AccountCode", rac."AssetCardCode";
END;
$$ LANGUAGE plpgsql;

