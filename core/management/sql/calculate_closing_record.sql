-- PostgreSQL Closing Record Calculation Function
-- Calculates period-end closing entries for income and expense accounts
-- Creates two cash documents: one for income closing, one for expense closing

DROP FUNCTION IF EXISTS public.calculate_closing_record(SMALLINT, INTEGER);

CREATE OR REPLACE FUNCTION public.calculate_closing_record(p_period_id SMALLINT, p_user_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_closing_account_id INTEGER;
    v_begin_date DATE;
    v_end_date DATE;
    v_period_name VARCHAR(17);
    v_income_total NUMERIC(24,6);
    v_expense_total NUMERIC(24,6);
    v_income_doc_id INTEGER;
    v_expense_doc_id INTEGER;
BEGIN
    -- Get closing account ID from constants (ConstantID = 14)
    SELECT CAST("ConstantName" AS INTEGER)
    INTO v_closing_account_id
    FROM ref_constant
    WHERE "ConstantID" = 14;
    
    IF v_closing_account_id IS NULL THEN
        RAISE EXCEPTION 'Closing Account ID (ConstantID=14) not found in ref_constant table';
    END IF;
    
    -- Get period dates and name
    SELECT "BeginDate", "EndDate", "PeriodName"
    INTO v_begin_date, v_end_date, v_period_name
    FROM ref_period
    WHERE "PeriodId" = p_period_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Period ID % not found', p_period_id;
    END IF;
    
    -- Cleanup: Delete existing closing documents for this period
    DELETE FROM cash_document_detail
    WHERE "DocumentId" IN (
        SELECT "DocumentId"
        FROM cash_document
        WHERE "DocumentTypeId" = 14
            AND "DocumentDate" = v_end_date
    );
    
    DELETE FROM cash_document
    WHERE "DocumentTypeId" = 14
        AND "DocumentDate" <= v_end_date;
    
    -- Create temporary table for calculated amounts
    CREATE TEMP TABLE temp_calculated_amounts AS
    WITH unionized_accounts AS (
        -- Cash document details
        SELECT 
            cdd."AccountId",
            rea."AccountCode",
            rat."AccountTypeId",
            rat."AccountTypeName",
            rat."IsActive",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS debit,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS credit
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        INNER JOIN ref_account rea ON rea."AccountId" = cdd."AccountId"
        INNER JOIN ref_account_type rat ON rat."AccountTypeId" = rea."AccountTypeId"
        WHERE cd."DocumentDate" <= v_end_date
            AND cd."IsDelete" = false
            AND rat."AccountTypeId" BETWEEN 69 AND 101
        GROUP BY cdd."AccountId", rea."AccountCode", rat."AccountTypeId", rat."AccountTypeName", rat."IsActive"
        
        UNION ALL
        
        -- Inventory document details
        SELECT 
            idd."AccountId",
            rea."AccountCode",
            rat."AccountTypeId",
            rat."AccountTypeName",
            rat."IsActive",
            COALESCE(SUM(idd."DebitAmount"), 0) AS debit,
            COALESCE(SUM(idd."CreditAmount"), 0) AS credit
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        INNER JOIN ref_account rea ON rea."AccountId" = idd."AccountId"
        INNER JOIN ref_account_type rat ON rat."AccountTypeId" = rea."AccountTypeId"
        WHERE id."DocumentDate" <= v_end_date
            AND id."IsDelete" = false
            AND rat."AccountTypeId" BETWEEN 69 AND 101
        GROUP BY idd."AccountId", rea."AccountCode", rat."AccountTypeId", rat."AccountTypeName", rat."IsActive"
        
        UNION ALL
        
        -- Asset document details
        SELECT 
            add."AccountId",
            rea."AccountCode",
            rat."AccountTypeId",
            rat."AccountTypeName",
            rat."IsActive",
            COALESCE(SUM(add."DebitAmount"), 0) AS debit,
            COALESCE(SUM(add."CreditAmount"), 0) AS credit
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        INNER JOIN ref_account rea ON rea."AccountId" = add."AccountId"
        INNER JOIN ref_account_type rat ON rat."AccountTypeId" = rea."AccountTypeId"
        WHERE ad."DocumentDate" <= v_end_date
            AND ad."IsDelete" = false
            AND rat."AccountTypeId" BETWEEN 69 AND 101
        GROUP BY add."AccountId", rea."AccountCode", rat."AccountTypeId", rat."AccountTypeName", rat."IsActive"
    )
    SELECT 
        "AccountId",
        "AccountCode",
        "AccountTypeId",
        "AccountTypeName",
        "IsActive",
        SUM(debit) AS total_debit,
        SUM(credit) AS total_credit,
        CASE 
            WHEN "IsActive" = true THEN SUM(debit) - SUM(credit)
            ELSE SUM(credit) - SUM(debit)
        END AS amount
    FROM unionized_accounts
    GROUP BY "AccountId", "AccountCode", "AccountTypeId", "AccountTypeName", "IsActive"
    HAVING CASE 
        WHEN "IsActive" = true THEN SUM(debit) - SUM(credit)
        ELSE SUM(credit) - SUM(debit)
    END <> 0;
    
    -- Calculate totals for income and expense
    SELECT 
        COALESCE(SUM(CASE WHEN "IsActive" = false THEN amount ELSE 0 END), 0),
        COALESCE(SUM(CASE WHEN "IsActive" = true THEN amount ELSE 0 END), 0)
    INTO v_income_total, v_expense_total 
    FROM temp_calculated_amounts;
    
    -- Insert income closing document (Batch A)
    IF v_income_total > 0 THEN
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
        VALUES (
            'ХБ1-' || TO_CHAR(v_end_date, 'YYYY-MM-DD'),
            14,
            v_end_date,
            'Орлогын хаалт: ' || v_period_name,
            false,
            false,
            p_user_id,
            CURRENT_DATE,
            p_user_id,
            CURRENT_DATE,
            1,
            NULL,
            1,
            v_income_total,
            1,
            v_income_total,
            false,
            NULL,
            false,
            v_closing_account_id,
            NULL
        )
        RETURNING "DocumentId" INTO v_income_doc_id;
        
        -- Insert income closing details
        -- A.2.1: Closing account credit entry
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
        VALUES (
            v_income_doc_id,
            v_closing_account_id,
            1,
            1,
            1::NUMERIC(10,4),
            v_income_total,
            false,
            0::NUMERIC(24,6),
            v_income_total,
            NULL::INTEGER,
            NULL::SMALLINT
        );
        
        -- A.2.2: Income account debit entries
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
        SELECT 
            v_income_doc_id,
            ca."AccountId",
            1,
            1,
            1::NUMERIC(10,4),
            ca.amount,
            true,
            ca.amount,
            0::NUMERIC(24,6),
            NULL::INTEGER,
            NULL::SMALLINT
        FROM temp_calculated_amounts ca
        WHERE ca."IsActive" = false AND ca.amount > 0;
    END IF;
    
    -- Insert expense closing document (Batch B)
    IF v_expense_total > 0 THEN
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
        VALUES (
            'ХБ2-' || TO_CHAR(v_end_date, 'YYYY-MM-DD'),
            14,
            v_end_date,
            'Зардлын хаалт: ' || v_period_name,
            false,
            false,
            p_user_id,
            CURRENT_DATE,
            p_user_id,
            CURRENT_DATE,
            1,
            NULL,
            1,
            v_expense_total,
            1,
            v_expense_total,
            false,
            NULL,
            false,
            v_closing_account_id,
            NULL
        )
        RETURNING "DocumentId" INTO v_expense_doc_id;
        
        -- Insert expense closing details
        -- B.2.1: Closing account debit entry
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
        VALUES (
            v_expense_doc_id,
            v_closing_account_id,
            1,
            1,
            1::NUMERIC(10,4),
            v_expense_total,
            true,
            v_expense_total,
            0::NUMERIC(24,6),
            NULL::INTEGER,
            NULL::SMALLINT
        );
        
        -- B.2.2: Expense account credit entries
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
        SELECT 
            v_expense_doc_id,
            ca."AccountId",
            1,
            1,
            1::NUMERIC(10,4),
            ca.amount,
            false,
            0::NUMERIC(24,6),
            ca.amount,
            NULL::INTEGER,
            NULL::SMALLINT
        FROM temp_calculated_amounts ca
        WHERE ca."IsActive" = true AND ca.amount > 0;
    END IF;
    
    -- Clean up temporary table
    DROP TABLE IF EXISTS temp_calculated_amounts;
    
END;
$$ LANGUAGE plpgsql;

-- Comment on function
COMMENT ON FUNCTION calculate_closing_record(SMALLINT, INTEGER) IS 
'Calculates and creates period-end closing entries for income and expense accounts.
Creates two cash documents (DocumentTypeId=14): one for income closing (ХБ1), one for expense closing (ХБ2).
Aggregates accounts with AccountTypeId between 69 and 101 from cash, inventory, and asset documents.
Parameters: p_period_id (accounting period), p_user_id (session user for audit fields).
Automatically deletes existing closing entries for the period before creating new ones.';

