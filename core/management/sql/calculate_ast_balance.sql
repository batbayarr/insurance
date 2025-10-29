-- PostgreSQL Asset Balance Function (As Of Date)
-- Calculates asset balances by AccountId + AssetCardId as of a given date
-- Includes beginning balances, cumulative income/expense up to the date, and depreciation expense

DROP FUNCTION IF EXISTS public.calculate_ast_balance(date);

CREATE OR REPLACE FUNCTION public.calculate_ast_balance(
    asofdate DATE
)
RETURNS TABLE (
    accountid INTEGER,
    accountcode VARCHAR(20),
    accountname VARCHAR(200),
    assetid INTEGER,
    assetcode VARCHAR(5),
    assetname VARCHAR(50),
    assetcardid INTEGER,
    assetcardcode VARCHAR(5),
    assetcardname VARCHAR(50),
    cumulateddepreciation NUMERIC(24,6),
    depreciationexpense NUMERIC(24,6),
    beginningquantity NUMERIC(24,6),
    beginningcost NUMERIC(24,6),
    inquantity NUMERIC(24,6),
    incost NUMERIC(24,6),
    outquantity NUMERIC(24,6),
    outcost NUMERIC(24,6),
    endingquantity NUMERIC(24,6),
    endingcost NUMERIC(24,6)
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- 1) Starting Balance from ast_beginning_balance (per AccountId + AssetCardId)
    starting_balances AS (
        SELECT 
            abb."AccountId",
            abb."AssetCardId",
            rac."AssetId",
            SUM(abb."Quantity") AS starting_quantity,
            SUM(abb."Quantity" * abb."UnitCost") AS starting_cost,
            SUM(COALESCE(abb."CumulatedDepreciation", 0)) AS cumulated_depreciation
        FROM ast_beginning_balance abb
        INNER JOIN ref_asset_card rac ON abb."AssetCardId" = rac."AssetCardId"
        WHERE abb."IsDelete" = false
        GROUP BY abb."AccountId", abb."AssetCardId", rac."AssetId"
    ),

    -- 2) Income (DocumentTypeId = 10) up to and including asofdate
    income_transactions AS (
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            SUM(adi."Quantity") AS in_quantity,
            SUM(adi."Quantity" * adi."UnitCost") AS in_cost
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 10
            AND ad."DocumentDate" <= asofdate
            AND ad."IsDelete" = false
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),

    -- 3) Expense (DocumentTypeId = 11) up to and including asofdate
    expense_transactions AS (
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            SUM(adi."Quantity") AS out_quantity,
            SUM(adi."Quantity" * adi."UnitCost") AS out_cost
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 11
            AND ad."DocumentDate" <= asofdate
            AND ad."IsDelete" = false
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),

    -- 4) Depreciation expense up to and including asofdate
    depreciation_expenses AS (
        SELECT 
            ade."AssetCardId",
            SUM(ade."ExpenseAmount") AS depreciation_expense
        FROM ast_depreciation_expense ade
        WHERE (ade."DepreciationDate" <= asofdate)
            OR (ade."DepreciationDate" IS NULL AND ade."CreatedDate" <= asofdate)
        GROUP BY ade."AssetCardId"
    ),

    -- 5) Collect all AccountId + AssetCardId combos from all sources
    account_asset_combinations AS (
        SELECT DISTINCT "AccountId", "AssetCardId", "AssetId" FROM starting_balances
        UNION
        SELECT DISTINCT it."AccountId", it."AssetCardId", rac."AssetId"
        FROM income_transactions it
        INNER JOIN ref_asset_card rac ON it."AssetCardId" = rac."AssetCardId"
        UNION
        SELECT DISTINCT et."AccountId", et."AssetCardId", rac."AssetId"
        FROM expense_transactions et
        INNER JOIN ref_asset_card rac ON et."AssetCardId" = rac."AssetCardId"
    )

    SELECT 
        ra."AccountId",
        ra."AccountCode",
        ra."AccountName",
        ras."AssetId",
        ras."AssetCode",
        ras."AssetName",
        rac."AssetCardId",
        rac."AssetCardCode",
        rac."AssetCardName",

        -- Cumulated Depreciation from starting balances
        COALESCE(sb.cumulated_depreciation, 0)::NUMERIC(24,6) AS CumulatedDepreciation,

        -- Depreciation Expense up to asofdate
        COALESCE(de.depreciation_expense, 0)::NUMERIC(24,6) AS DepreciationExpense,

        -- Beginning balances from starting table
        COALESCE(sb.starting_quantity, 0)::NUMERIC(24,6) AS BeginningQuantity,
        COALESCE(sb.starting_cost, 0)::NUMERIC(24,6) AS BeginningCost,

        -- Income/Expense to date
        COALESCE(it.in_quantity, 0)::NUMERIC(24,6) AS InQuantity,
        COALESCE(it.in_cost, 0)::NUMERIC(24,6) AS InCost,
        COALESCE(et.out_quantity, 0)::NUMERIC(24,6) AS OutQuantity,
        COALESCE(et.out_cost, 0)::NUMERIC(24,6) AS OutCost,

        -- Ending = Beginning + In - Out
        (COALESCE(sb.starting_quantity, 0) + 
        COALESCE(it.in_quantity, 0) - 
        COALESCE(et.out_quantity, 0))::NUMERIC(24,6) AS EndingQuantity,

        (COALESCE(sb.starting_cost, 0) + 
        COALESCE(it.in_cost, 0) - 
        COALESCE(et.out_cost, 0))::NUMERIC(24,6) AS EndingCost

    FROM account_asset_combinations aac
    INNER JOIN ref_account ra ON aac."AccountId" = ra."AccountId"
    INNER JOIN ref_asset_card rac ON aac."AssetCardId" = rac."AssetCardId"
    INNER JOIN ref_asset ras ON aac."AssetId" = ras."AssetId"
    LEFT JOIN starting_balances sb ON aac."AccountId" = sb."AccountId" 
        AND aac."AssetCardId" = sb."AssetCardId"
    LEFT JOIN income_transactions it ON aac."AccountId" = it."AccountId" 
        AND aac."AssetCardId" = it."AssetCardId"
    LEFT JOIN expense_transactions et ON aac."AccountId" = et."AccountId" 
        AND aac."AssetCardId" = et."AssetCardId"
    LEFT JOIN depreciation_expenses de ON aac."AssetCardId" = de."AssetCardId"
    WHERE ra."IsDelete" = false
    ORDER BY ra."AccountCode", ras."AssetCode", rac."AssetCardCode";
END;
$$ LANGUAGE plpgsql;
