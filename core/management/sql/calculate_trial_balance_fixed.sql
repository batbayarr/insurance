-- PostgreSQL Trial Balance Function (Fixed Version)
-- This function calculates trial balance for a given date range
-- Parameters: begindate DATE, enddate DATE
-- Returns: Trial balance data with beginning balances, period transactions, and ending balances

-- Drop the function if it exists
DROP FUNCTION IF EXISTS public.calculate_trial_balance(date, date);

CREATE OR REPLACE FUNCTION public.calculate_trial_balance(
    begindate DATE,
    enddate DATE
)
RETURNS TABLE (
    accountid INTEGER,
    accountcode VARCHAR(20),
    accountname VARCHAR(200),
    accounttype VARCHAR(100),
    beginningbalancedebit NUMERIC(24,6),
    beginningbalancecredit NUMERIC(24,6),
    debitamount NUMERIC(24,6),
    creditamount NUMERIC(24,6),
    endingbalancedebit NUMERIC(24,6),
    endingbalancecredit NUMERIC(24,6)
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- 1. Starting Balance (from beginning balance tables)
    starting_balances AS (
        SELECT 
            ra."AccountId",
            COALESCE(cash_bb.starting_balance, 0) + 
            COALESCE(inv_bb.starting_balance, 0) + 
            COALESCE(ast_bb.starting_balance, 0) AS starting_balance
        FROM ref_account ra
        LEFT JOIN (
            SELECT 
                "AccountId",
                SUM("CurrencyAmount" * "CurrencyExchange") AS starting_balance
            FROM cash_beginning_balance 
            WHERE "IsDelete" = false
            GROUP BY "AccountId"
        ) cash_bb ON ra."AccountId" = cash_bb."AccountId"
        LEFT JOIN (
            SELECT 
                "AccountId",
                SUM("Quantity" * "UnitCost") AS starting_balance
            FROM inv_beginning_balance 
            WHERE "IsDelete" = false
            GROUP BY "AccountId"
        ) inv_bb ON ra."AccountId" = inv_bb."AccountId"
        LEFT JOIN (
            SELECT 
                "AccountId",
                SUM("Quantity" * "UnitCost") AS starting_balance
            FROM ast_beginning_balance 
            WHERE "IsDelete" = false
            GROUP BY "AccountId"
        ) ast_bb ON ra."AccountId" = ast_bb."AccountId"
    ),
    
    -- 2. Transactions Before Begin Date
    transactions_before_begin AS (
        SELECT 
            cdd."AccountId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS debit_before,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS credit_before
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" < begindate 
            AND cd."IsDelete" = false
        GROUP BY cdd."AccountId"
        
        UNION ALL
        
        SELECT 
            idd."AccountId",
            COALESCE(SUM(idd."DebitAmount"), 0) AS debit_before,
            COALESCE(SUM(idd."CreditAmount"), 0) AS credit_before
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        WHERE id."DocumentDate" < begindate 
            AND id."IsDelete" = false
        GROUP BY idd."AccountId"
        
        UNION ALL
        
        SELECT 
            add."AccountId",
            COALESCE(SUM(add."DebitAmount"), 0) AS debit_before,
            COALESCE(SUM(add."CreditAmount"), 0) AS credit_before
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        WHERE ad."DocumentDate" < begindate 
            AND ad."IsDelete" = false
        GROUP BY add."AccountId"
    ),
    
    -- Aggregate transactions before begin date
    aggregated_before_begin AS (
        SELECT 
            "AccountId",
            SUM(debit_before) AS total_debit_before,
            SUM(credit_before) AS total_credit_before
        FROM transactions_before_begin
        GROUP BY "AccountId"
    ),
    
    -- 3. Period Transactions (between begindate and enddate)
    period_transactions AS (
        SELECT 
            cdd."AccountId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS period_debit,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS period_credit
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" >= begindate 
            AND cd."DocumentDate" <= enddate
            AND cd."IsDelete" = false
        GROUP BY cdd."AccountId"
        
        UNION ALL
        
        SELECT 
            idd."AccountId",
            COALESCE(SUM(idd."DebitAmount"), 0) AS period_debit,
            COALESCE(SUM(idd."CreditAmount"), 0) AS period_credit
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        WHERE id."DocumentDate" >= begindate 
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
        GROUP BY idd."AccountId"
        
        UNION ALL
        
        SELECT 
            add."AccountId",
            COALESCE(SUM(add."DebitAmount"), 0) AS period_debit,
            COALESCE(SUM(add."CreditAmount"), 0) AS period_credit
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        WHERE ad."DocumentDate" >= begindate 
            AND ad."DocumentDate" <= enddate
            AND ad."IsDelete" = false
        GROUP BY add."AccountId"
    ),
    
    -- Aggregate period transactions
    aggregated_period AS (
        SELECT 
            "AccountId",
            SUM(period_debit) AS total_period_debit,
            SUM(period_credit) AS total_period_credit
        FROM period_transactions
        GROUP BY "AccountId"
    )
    
    -- Main query combining all data
    SELECT 
        ra."AccountId",
        ra."AccountCode",
        ra."AccountName",
        rat."AccountTypeName" AS AccountType,
        
        -- Beginning Balance (as of begindate)
        CASE 
            WHEN rat."IsActive" = true THEN 
                -- Active accounts: StartingBalance + DebitBefore - CreditBefore
                GREATEST(0, COALESCE(sb.starting_balance, 0) + 
                           COALESCE(abb.total_debit_before, 0) - 
                           COALESCE(abb.total_credit_before, 0))
            ELSE 0
        END AS BeginningBalanceDebit,
        
        CASE 
            WHEN rat."IsActive" = false THEN 
                -- Passive accounts: StartingBalance - DebitBefore + CreditBefore
                GREATEST(0, COALESCE(sb.starting_balance, 0) - 
                           COALESCE(abb.total_debit_before, 0) + 
                           COALESCE(abb.total_credit_before, 0))
            ELSE 0
        END AS BeginningBalanceCredit,
        
        -- Period transactions
        COALESCE(ap.total_period_debit, 0) AS DebitAmount,
        COALESCE(ap.total_period_credit, 0) AS CreditAmount,
        
        -- Ending Balance
        CASE 
            WHEN rat."IsActive" = true THEN 
                -- Active accounts: BeginningBalance + DebitAmount - CreditAmount
                -- Show positive balance in debit column, negative balance stays negative
                COALESCE(sb.starting_balance, 0) + 
                COALESCE(abb.total_debit_before, 0) - 
                COALESCE(abb.total_credit_before, 0) +
                COALESCE(ap.total_period_debit, 0) - 
                COALESCE(ap.total_period_credit, 0)
            ELSE 0
        END AS EndingBalanceDebit,
        
        CASE 
            WHEN rat."IsActive" = false THEN 
                -- Passive accounts: BeginningBalance - DebitAmount + CreditAmount
                -- Show positive balance in credit column, negative balance stays negative
                COALESCE(sb.starting_balance, 0) - 
                COALESCE(abb.total_debit_before, 0) + 
                COALESCE(abb.total_credit_before, 0) -
                COALESCE(ap.total_period_debit, 0) + 
                COALESCE(ap.total_period_credit, 0)
            ELSE 0
        END AS EndingBalanceCredit
        
    FROM ref_account ra
    INNER JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
    LEFT JOIN starting_balances sb ON ra."AccountId" = sb."AccountId"
    LEFT JOIN aggregated_before_begin abb ON ra."AccountId" = abb."AccountId"
    LEFT JOIN aggregated_period ap ON ra."AccountId" = ap."AccountId"
    WHERE ra."IsDelete" = false
    ORDER BY ra."AccountCode";
    
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM calculate_trial_balance('2025-01-01', '2025-12-31');
