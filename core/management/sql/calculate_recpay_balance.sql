-- PostgreSQL Receivable/Payable Balance Function
-- This function calculates receivable and payable account balances by AccountId + ClientId combination
-- for a given date range
-- Parameters: begindate DATE, enddate DATE
-- Returns: Balance data for receivable and payable accounts grouped by AccountId and ClientId

-- Drop the function if it exists
DROP FUNCTION IF EXISTS public.calculate_recpay_balance(date, date);

CREATE OR REPLACE FUNCTION public.calculate_recpay_balance(
    begindate DATE,
    enddate DATE
)
RETURNS TABLE (
    accountid INTEGER,
    accountcode VARCHAR(20),
    accountname VARCHAR(200),
    accounttype VARCHAR(100),
    accounttypeid SMALLINT,
    clientid INTEGER,
    clientcode VARCHAR(5),
    clientname VARCHAR(100),
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
    -- 1. Starting Balance (from cash_beginning_balance table filtered by AccountId and ClientId)
    starting_balances AS (
        SELECT 
            "AccountId",
            "ClientId",
            SUM("CurrencyAmount" * "CurrencyExchange") AS starting_balance
        FROM cash_beginning_balance 
        WHERE "IsDelete" = false
        GROUP BY "AccountId", "ClientId"
    ),
    
    -- 2. Transactions Before Begin Date (grouped by AccountId and ClientId)
    transactions_before_begin AS (
        SELECT 
            cdd."AccountId",
            cdd."ClientId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS debit_before,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS credit_before
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" < begindate 
            AND cd."IsDelete" = false
        GROUP BY cdd."AccountId", cdd."ClientId"
        
        UNION ALL
        
        SELECT 
            idd."AccountId",
            idd."ClientId",
            COALESCE(SUM(idd."DebitAmount"), 0) AS debit_before,
            COALESCE(SUM(idd."CreditAmount"), 0) AS credit_before
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        WHERE id."DocumentDate" < begindate 
            AND id."IsDelete" = false
        GROUP BY idd."AccountId", idd."ClientId"
        
        UNION ALL
        
        SELECT 
            add."AccountId",
            add."ClientId",
            COALESCE(SUM(add."DebitAmount"), 0) AS debit_before,
            COALESCE(SUM(add."CreditAmount"), 0) AS credit_before
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        WHERE ad."DocumentDate" < begindate 
            AND ad."IsDelete" = false
        GROUP BY add."AccountId", add."ClientId"
    ),
    
    -- Aggregate transactions before begin date
    aggregated_before_begin AS (
        SELECT 
            "AccountId",
            "ClientId",
            SUM(debit_before) AS total_debit_before,
            SUM(credit_before) AS total_credit_before
        FROM transactions_before_begin
        GROUP BY "AccountId", "ClientId"
    ),
    
    -- 3. Period Transactions (between begindate and enddate, grouped by AccountId and ClientId)
    period_transactions AS (
        SELECT 
            cdd."AccountId",
            cdd."ClientId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS period_debit,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS period_credit
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" >= begindate 
            AND cd."DocumentDate" <= enddate
            AND cd."IsDelete" = false
        GROUP BY cdd."AccountId", cdd."ClientId"
        
        UNION ALL
        
        SELECT 
            idd."AccountId",
            idd."ClientId",
            COALESCE(SUM(idd."DebitAmount"), 0) AS period_debit,
            COALESCE(SUM(idd."CreditAmount"), 0) AS period_credit
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        WHERE id."DocumentDate" >= begindate 
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
        GROUP BY idd."AccountId", idd."ClientId"
        
        UNION ALL
        
        SELECT 
            add."AccountId",
            add."ClientId",
            COALESCE(SUM(add."DebitAmount"), 0) AS period_debit,
            COALESCE(SUM(add."CreditAmount"), 0) AS period_credit
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        WHERE ad."DocumentDate" >= begindate 
            AND ad."DocumentDate" <= enddate
            AND ad."IsDelete" = false
        GROUP BY add."AccountId", add."ClientId"
    ),
    
    -- Aggregate period transactions
    aggregated_period AS (
        SELECT 
            "AccountId",
            "ClientId",
            SUM(period_debit) AS total_period_debit,
            SUM(period_credit) AS total_period_credit
        FROM period_transactions
        GROUP BY "AccountId", "ClientId"
    ),
    
    -- 4. Get all unique AccountId + ClientId combinations from all sources
    account_client_combinations AS (
        SELECT DISTINCT "AccountId", "ClientId" FROM starting_balances
        UNION
        SELECT DISTINCT "AccountId", "ClientId" FROM aggregated_before_begin
        UNION
        SELECT DISTINCT "AccountId", "ClientId" FROM aggregated_period
    )
    
    -- Main query combining all data
    SELECT 
        ra."AccountId",
        ra."AccountCode",
        ra."AccountName",
        rat."AccountTypeName" AS AccountType,
        rat."AccountTypeId",
        acc."ClientId",
        rc."ClientCode",
        rc."ClientName",
        
        -- Beginning Balance (as of begindate)
        -- Receivable accounts: Show in Debit column
        CASE 
            WHEN rat."AccountTypeId" IN (3, 4, 5, 6) THEN 
                COALESCE(sb.starting_balance, 0) + 
                COALESCE(abb.total_debit_before, 0) - 
                COALESCE(abb.total_credit_before, 0)
            ELSE 0
        END AS BeginningBalanceDebit,
        
        -- Payable accounts: Show in Credit column
        CASE 
            WHEN rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 THEN 
                COALESCE(sb.starting_balance, 0) - 
                COALESCE(abb.total_debit_before, 0) + 
                COALESCE(abb.total_credit_before, 0)
            ELSE 0
        END AS BeginningBalanceCredit,
        
        -- Period transactions
        COALESCE(ap.total_period_debit, 0) AS DebitAmount,
        COALESCE(ap.total_period_credit, 0) AS CreditAmount,
        
        -- Ending Balance
        -- Receivable accounts: Show in Debit column
        CASE 
            WHEN rat."AccountTypeId" IN (3, 4, 5, 6) THEN 
                COALESCE(sb.starting_balance, 0) + 
                COALESCE(abb.total_debit_before, 0) - 
                COALESCE(abb.total_credit_before, 0) +
                COALESCE(ap.total_period_debit, 0) - 
                COALESCE(ap.total_period_credit, 0)
            ELSE 0
        END AS EndingBalanceDebit,
        
        -- Payable accounts: Show in Credit column
        CASE 
            WHEN rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 THEN 
                COALESCE(sb.starting_balance, 0) - 
                COALESCE(abb.total_debit_before, 0) + 
                COALESCE(abb.total_credit_before, 0) -
                COALESCE(ap.total_period_debit, 0) + 
                COALESCE(ap.total_period_credit, 0)
            ELSE 0
        END AS EndingBalanceCredit
        
    FROM ref_account ra
    INNER JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
    INNER JOIN account_client_combinations acc ON ra."AccountId" = acc."AccountId"
    LEFT JOIN ref_client rc ON acc."ClientId" = rc."ClientId"
    LEFT JOIN starting_balances sb ON ra."AccountId" = sb."AccountId" 
        AND acc."ClientId" = sb."ClientId"
    LEFT JOIN aggregated_before_begin abb ON ra."AccountId" = abb."AccountId" 
        AND acc."ClientId" = abb."ClientId"
    LEFT JOIN aggregated_period ap ON ra."AccountId" = ap."AccountId" 
        AND acc."ClientId" = ap."ClientId"
    WHERE ra."IsDelete" = false
        AND (
            (rat."AccountTypeId" IN (3, 4, 5, 6) AND rat."IsActive" = true)  -- Receivable
            OR 
            (rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 AND rat."IsActive" = false)  -- Payable
        )
    ORDER BY ra."AccountCode", rc."ClientCode" NULLS LAST;
    
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- Get all receivable and payable balances for a date range:
-- SELECT * FROM calculate_recpay_balance('2025-01-01', '2025-12-31');

-- Filter by specific client:
-- SELECT * FROM calculate_recpay_balance('2025-01-01', '2025-12-31') WHERE clientid = 123;

-- Filter by specific account:
-- SELECT * FROM calculate_recpay_balance('2025-01-01', '2025-12-31') WHERE accountid = 456;

-- Get only receivable accounts (AccountTypeId 3,4,5,6):
-- SELECT * FROM calculate_recpay_balance('2025-01-01', '2025-12-31') WHERE accounttypeid IN (3,4,5,6);

-- Get only payable accounts (AccountTypeId 42-58):
-- SELECT * FROM calculate_recpay_balance('2025-01-01', '2025-12-31') WHERE accounttypeid > 41 AND accounttypeid < 59;

-- Get total receivables by client:
-- SELECT clientid, clientname, SUM(endingbalance) as total_receivable
-- FROM calculate_recpay_balance('2025-01-01', '2025-12-31')
-- WHERE accounttypeid IN (3,4,5,6)
-- GROUP BY clientid, clientname
-- ORDER BY total_receivable DESC;

-- Get total payables by client:
-- SELECT clientid, clientname, SUM(endingbalance) as total_payable
-- FROM calculate_recpay_balance('2025-01-01', '2025-12-31')
-- WHERE accounttypeid > 41 AND accounttypeid < 59
-- GROUP BY clientid, clientname
-- ORDER BY total_payable DESC;

