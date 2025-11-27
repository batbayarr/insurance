-- PostgreSQL Depreciation Calculation Function
-- Calculates depreciation expenses for a given period
-- Uses report_assetcard_balance to check asset quantities
-- Updates ast_depreciation_expense table

DROP FUNCTION IF EXISTS public.calculate_depreciation(SMALLINT);
DROP FUNCTION IF EXISTS public.calculate_depreciation(SMALLINT, INTEGER);

CREATE OR REPLACE FUNCTION public.calculate_depreciation(p_period_id SMALLINT, p_user_id INTEGER)
RETURNS TABLE (
    assetaccountid INTEGER,
    assetaccountcode VARCHAR(20),
    assetcardid INTEGER,
    assetcardcode VARCHAR(5),
    assetcardname VARCHAR(50),
    debitaccountid INTEGER,
    debitaccountcode VARCHAR(20),
    creditaccountid INTEGER,
    creditaccountcode VARCHAR(20),
    accountid INTEGER,
    periodid SMALLINT,
    periodname VARCHAR(17),
    expenseday SMALLINT,
    dailyexpense NUMERIC(24,6),
    expenseamount NUMERIC(24,6),
    documentno VARCHAR(50)
) AS $$
DECLARE
    v_begin_date DATE;
    v_end_date DATE;
    v_expense_days SMALLINT;
BEGIN
    -- Get period dates
    SELECT "BeginDate", "EndDate" 
    INTO v_begin_date, v_end_date
    FROM ref_period 
    WHERE "PeriodId" = p_period_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Period ID % not found', p_period_id;
    END IF;
    
    -- Delete existing unposted records for this period
    -- Preserves records already linked to documents (posted transactions)
    DELETE FROM ast_depreciation_expense 
    WHERE "PeriodId" = p_period_id 
        AND "DocumentId" IS NULL;
    
    
    -- Insert new depreciation records
    -- Only for assets with positive ending quantity and daily expense > 0
    -- Calculates actual usage days based on receipt date and disposal date
    WITH asset_receipts AS (
        -- First receipt date for each asset card (up to period end)
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            MIN(ad."DocumentDate") AS first_receipt_date
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 10
            AND ad."IsDelete" = false
            AND ad."DocumentDate" <= v_end_date
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),
    asset_disposals AS (
        -- First disposal date within the period (if any)
        SELECT 
            ad."AccountId",
            adi."AssetCardId",
            MIN(ad."DocumentDate") AS first_disposal_date
        FROM ast_document ad
        INNER JOIN ast_document_item adi ON ad."DocumentId" = adi."DocumentId"
        WHERE ad."DocumentTypeId" = 11
            AND ad."IsDelete" = false
            AND ad."DocumentDate" BETWEEN v_begin_date AND v_end_date
        GROUP BY ad."AccountId", adi."AssetCardId"
    ),
    asset_usage_periods AS (
        -- Calculate actual usage period for each asset
        SELECT 
            bal.accountid,
            bal.assetcardid,
            bal.endingquantity,
            rac."DailyExpense",
            rada."ExpenseAccountId",
            rada."DepreciationAccountId",
            rada."AssetAccountId",
            -- Start date: MAX of receipt date or period begin
            -- If asset was received before period, use period begin
            -- If asset was received during period, use receipt date
            GREATEST(
                COALESCE(ar.first_receipt_date, v_begin_date),
                v_begin_date
            ) AS usage_start_date,
            -- End date: MIN of disposal date (if exists within period) or period end
            -- If disposed within period, use disposal date
            -- Otherwise, use period end
            LEAST(
                COALESCE(ad.first_disposal_date, v_end_date),
                v_end_date
            ) AS usage_end_date
        FROM report_assetcard_balance(v_end_date) bal
        INNER JOIN ref_asset_card rac ON bal.assetcardid = rac."AssetCardId"
        INNER JOIN ref_asset_depreciation_account rada 
            ON bal.accountid = rada."AssetAccountId"
            AND rada."IsDelete" = false
        LEFT JOIN asset_receipts ar 
            ON bal.accountid = ar."AccountId"
            AND bal.assetcardid = ar."AssetCardId"
        LEFT JOIN asset_disposals ad 
            ON bal.accountid = ad."AccountId"
            AND bal.assetcardid = ad."AssetCardId"
        WHERE bal.endingquantity > 0
            AND rac."DailyExpense" > 0
            -- Only calculate if asset was received before or during the period
            AND COALESCE(ar.first_receipt_date, v_begin_date) <= v_end_date
    )
    INSERT INTO ast_depreciation_expense (
        "AssetCardId", 
        "PeriodId", 
        "ExpenseDay", 
        "DepreciationDate",
        "ExpenseAmount", 
        "DebitAccountId", 
        "CreditAccountId",
        "AccountId",
        "CreatedBy", 
        "CreatedDate", 
        "ModifiedBy", 
        "ModifiedDate"
    )
    SELECT 
        aup.assetcardid,
        p_period_id,
        (aup.usage_end_date - aup.usage_start_date + 1)::SMALLINT AS expense_days,
        aup.usage_end_date AS depreciation_date,
        ((aup.usage_end_date - aup.usage_start_date + 1)::NUMERIC(24,6) * aup."DailyExpense")::NUMERIC(24,6) AS expense_amount,
        aup."ExpenseAccountId", -- Debit: Expense Account
        aup."DepreciationAccountId", -- Credit: Accumulated Depreciation
        aup."AssetAccountId", -- Asset Account
        p_user_id, -- CreatedBy (session user ID)
        CURRENT_DATE,
        p_user_id, -- ModifiedBy (session user ID)
        CURRENT_DATE
    FROM asset_usage_periods aup
    WHERE aup.usage_start_date <= aup.usage_end_date; -- Ensure valid date range
    
    -- Check for existing depreciation cash documents and delete them if they exist
    -- Delete from cash_document_detail first (due to foreign key constraint)
    DELETE FROM cash_document_detail 
    WHERE "DocumentId" IN (
        SELECT cd."DocumentId" 
        FROM cash_document cd 
        WHERE cd."DocumentTypeId" = 13 
            AND cd."DocumentDate" BETWEEN v_begin_date AND v_end_date
    );
    
    -- Delete from cash_document
    DELETE FROM cash_document 
    WHERE "DocumentTypeId" = 13 
        AND "DocumentDate" BETWEEN v_begin_date AND v_end_date;
    
    -- Create cash documents for depreciation expenses
    -- Group depreciation expenses and insert into cash_document with corresponding details
    WITH grouped_expenses AS (
        SELECT 
            ade."AccountId",
            ade."DebitAccountId",
            ade."CreditAccountId",
            ade."DepreciationDate",
            ade."PeriodId",
            SUM(ade."ExpenseAmount") AS total_expense,
            ade."DocumentId" AS original_doc_id
        FROM ast_depreciation_expense ade
        WHERE ade."PeriodId" = p_period_id
            AND ade."DocumentId" IS NULL
        GROUP BY 
            ade."AccountId",
            ade."DebitAccountId",
            ade."CreditAccountId",
            ade."DepreciationDate",
            ade."PeriodId",
            ade."DocumentId"
    ),
    inserted_documents AS (
        INSERT INTO cash_document (
            "DocumentNo",
            "DocumentTypeId",
            "DocumentDate",
            "Description",
            "IsLock",
            "IsDelete",
            "ModifiedBy",
            "ModifiedDate",
            "CreatedBy",
            "CreatedDate",
            "ClientId",
            "ClientBankId",
            "CurrencyId",
            "CurrencyAmount",
            "CurrencyExchange",
            "CurrencyMNT",
            "IsVat",
            "VatAccountId",
            "IsPosted",
            "AccountId",
            "PaidClientId"
        )
        SELECT 
            COALESCE(
                ge.original_doc_id::VARCHAR,
                'ЭЛ ' || TO_CHAR(ge."DepreciationDate", 'YY-MM-DD')
            ) AS document_no,
            13, -- DocumentTypeId
            ge."DepreciationDate",
            ra."AccountCode" || ' Элэгдэд ' || rp."PeriodName" AS description,
            false, -- IsLock
            false, -- IsDelete
            p_user_id, -- ModifiedBy
            CURRENT_DATE, -- ModifiedDate
            p_user_id, -- CreatedBy
            CURRENT_DATE, -- CreatedDate
            1, -- ClientId
            NULL, -- ClientBankId
            1, -- CurrencyId
            ge.total_expense, -- CurrencyAmount
            1, -- CurrencyExchange
            ge.total_expense, -- CurrencyMNT
            false, -- IsVat
            NULL, -- VatAccountId
            false, -- IsPosted
            ge."AccountId",
            NULL -- PaidClientId
        FROM grouped_expenses ge
        INNER JOIN ref_account ra ON ge."AccountId" = ra."AccountId"
        INNER JOIN ref_period rp ON ge."PeriodId" = rp."PeriodId"
        RETURNING "DocumentId", "AccountId"
    )
    -- Insert detail records for both debit and credit entries
    INSERT INTO cash_document_detail (
        "DocumentId",
        "AccountId",
        "ClientId",
        "CurrencyId",
        "CurrencyExchange",
        "CurrencyAmount",
        "IsDebit",
        "DebitAmount",
        "CreditAmount",
        "ContractId",
        "CashFlowId"
    )
    -- Debit entries
    SELECT 
        id."DocumentId",
        ge."DebitAccountId" AS "AccountId",
        1, -- ClientId
        1, -- CurrencyId
        1::NUMERIC(10,4), -- CurrencyExchange
        ge.total_expense, -- CurrencyAmount
        true, -- IsDebit
        ge.total_expense, -- DebitAmount
        0::NUMERIC(24,6), -- CreditAmount
        NULL::INTEGER, -- ContractId
        NULL::SMALLINT -- CashFlowId
    FROM inserted_documents id
    INNER JOIN grouped_expenses ge 
        ON id."AccountId" = ge."AccountId"
    UNION ALL
    -- Credit entries
    SELECT 
        id."DocumentId",
        ge."CreditAccountId" AS "AccountId",
        1, -- ClientId
        1, -- CurrencyId
        1::NUMERIC(10,4), -- CurrencyExchange
        ge.total_expense, -- CurrencyAmount
        false, -- IsDebit
        0::NUMERIC(24,6), -- DebitAmount
        ge.total_expense, -- CreditAmount
        NULL::INTEGER, -- ContractId
        NULL::SMALLINT -- CashFlowId
    FROM inserted_documents id
    INNER JOIN grouped_expenses ge 
        ON id."AccountId" = ge."AccountId";
    
    -- Return results with full details including account codes and period name
    RETURN QUERY
    SELECT 
        rada."AssetAccountId",
        ra_asset."AccountCode" AS assetaccountcode,
        ade."AssetCardId",
        rac."AssetCardCode",
        rac."AssetCardName",
        ade."DebitAccountId",
        ra_debit."AccountCode" AS debitaccountcode,
        ade."CreditAccountId",
        ra_credit."AccountCode" AS creditaccountcode,
        ade."AccountId",
        ade."PeriodId"::SMALLINT,
        rp."PeriodName",
        ade."ExpenseDay"::SMALLINT,
        rac."DailyExpense"::NUMERIC(24,6),
        ade."ExpenseAmount"::NUMERIC(24,6),
        COALESCE(ad."DocumentNo", NULL)::VARCHAR(50) AS documentno
    FROM ast_depreciation_expense ade
    INNER JOIN ref_asset_card rac ON ade."AssetCardId" = rac."AssetCardId"
    INNER JOIN ref_period rp ON ade."PeriodId" = rp."PeriodId"
    INNER JOIN ref_account ra_debit ON ade."DebitAccountId" = ra_debit."AccountId"
    INNER JOIN ref_account ra_credit ON ade."CreditAccountId" = ra_credit."AccountId"
    INNER JOIN ref_asset_depreciation_account rada 
        ON rada."ExpenseAccountId" = ade."DebitAccountId"
        AND rada."DepreciationAccountId" = ade."CreditAccountId"
        AND rada."IsDelete" = false
    INNER JOIN ref_account ra_asset ON rada."AssetAccountId" = ra_asset."AccountId"
    LEFT JOIN ast_document ad ON ade."DocumentId" = ad."DocumentId"
    WHERE ade."PeriodId" = p_period_id
    ORDER BY rada."AssetAccountId", ade."AssetCardId";
END;
$$ LANGUAGE plpgsql;

-- Comment on function
COMMENT ON FUNCTION calculate_depreciation(SMALLINT, INTEGER) IS 
'Calculates and updates depreciation expenses for a given accounting period based on actual usage days.
Only processes assets with positive ending quantity and daily expense > 0.
Calculates depreciation from receipt date (or period begin if received earlier) to period end (or disposal date if disposed within period).
If asset is disposed within period resulting in ending quantity = 0, no depreciation is calculated.
If asset is received mid-period, depreciation is calculated from receipt date to period end.
Deletes unposted records (DocumentId IS NULL) for the period before inserting new calculations.
Automatically creates cash_document and cash_document_detail entries for the depreciation expenses.
Parameters: p_period_id (accounting period), p_user_id (session user for audit fields, required).
Returns detailed results including account codes, period information, and document numbers.';

