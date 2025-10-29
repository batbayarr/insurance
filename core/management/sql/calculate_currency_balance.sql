-- PostgreSQL Currency Balance Function
-- This function calculates cash, receivable, and payable account balances by AccountId + ClientId + CurrencyId combination
-- for a given date range
-- Parameters: begindate DATE, enddate DATE
-- Returns: Balance data with separate currency and MNT amounts for cash, receivable, and payable accounts

-- Drop the function if it exists
DROP FUNCTION IF EXISTS public.calculate_currency_balance(date, date);

CREATE OR REPLACE FUNCTION public.calculate_currency_balance(
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
    currencyid SMALLINT,
    currencyname VARCHAR(50),
    beginningbalancecurdebit NUMERIC(24,6),
    beginningbalancemntdebit NUMERIC(24,6),
    beginningbalancecurcredit NUMERIC(24,6),
    beginningbalancemntcredit NUMERIC(24,6),
    debitcur NUMERIC(24,6),
    debitmnt NUMERIC(24,6),
    creditcur NUMERIC(24,6),
    creditmnt NUMERIC(24,6),
    endingbalancecurdebit NUMERIC(24,6),
    endingbalancemntdebit NUMERIC(24,6),
    endingbalancecurcredit NUMERIC(24,6),
    endingbalancemntcredit NUMERIC(24,6)
) AS $$
BEGIN
    RETURN QUERY
    WITH 
    -- 1. Starting Balance (from cash_beginning_balance table filtered by AccountId, ClientId, and CurrencyId)
    starting_balances AS (
        SELECT 
            "AccountId",
            "ClientId",
            "CurrencyId",
            SUM("CurrencyAmount") AS starting_balance_cur,
            SUM("CurrencyAmount" * "CurrencyExchange") AS starting_balance_mnt
        FROM cash_beginning_balance 
        WHERE "IsDelete" = false
        GROUP BY "AccountId", "ClientId", "CurrencyId"
    ),
    
    -- 2. Transactions Before Begin Date (grouped by AccountId, ClientId, and CurrencyId)
    transactions_before_begin AS (
        SELECT 
            cdd."AccountId",
            cdd."ClientId",
            cdd."CurrencyId",
            COALESCE(SUM(CASE WHEN cdd."IsDebit" = true THEN cdd."CurrencyAmount" ELSE 0 END), 0) AS debit_cur_before,
            COALESCE(SUM(cdd."DebitAmount"), 0) AS debit_mnt_before,
            COALESCE(SUM(CASE WHEN cdd."IsDebit" = false THEN cdd."CurrencyAmount" ELSE 0 END), 0) AS credit_cur_before,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS credit_mnt_before
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" < begindate 
            AND cd."IsDelete" = false
        GROUP BY cdd."AccountId", cdd."ClientId", cdd."CurrencyId"
        
        UNION ALL
        
        SELECT 
            idd."AccountId",
            idd."ClientId",
            idd."CurrencyId",
            COALESCE(SUM(CASE WHEN idd."IsDebit" = true THEN idd."CurrencyAmount" ELSE 0 END), 0) AS debit_cur_before,
            COALESCE(SUM(idd."DebitAmount"), 0) AS debit_mnt_before,
            COALESCE(SUM(CASE WHEN idd."IsDebit" = false THEN idd."CurrencyAmount" ELSE 0 END), 0) AS credit_cur_before,
            COALESCE(SUM(idd."CreditAmount"), 0) AS credit_mnt_before
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        WHERE id."DocumentDate" < begindate 
            AND id."IsDelete" = false
        GROUP BY idd."AccountId", idd."ClientId", idd."CurrencyId"
        
        UNION ALL
        
        SELECT 
            add."AccountId",
            add."ClientId",
            add."CurrencyId",
            COALESCE(SUM(CASE WHEN add."IsDebit" = true THEN add."CurrencyAmount" ELSE 0 END), 0) AS debit_cur_before,
            COALESCE(SUM(add."DebitAmount"), 0) AS debit_mnt_before,
            COALESCE(SUM(CASE WHEN add."IsDebit" = false THEN add."CurrencyAmount" ELSE 0 END), 0) AS credit_cur_before,
            COALESCE(SUM(add."CreditAmount"), 0) AS credit_mnt_before
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        WHERE ad."DocumentDate" < begindate 
            AND ad."IsDelete" = false
        GROUP BY add."AccountId", add."ClientId", add."CurrencyId"
    ),
    
    -- Aggregate transactions before begin date
    aggregated_before_begin AS (
        SELECT 
            "AccountId",
            "ClientId",
            "CurrencyId",
            SUM(debit_cur_before) AS total_debit_cur_before,
            SUM(debit_mnt_before) AS total_debit_mnt_before,
            SUM(credit_cur_before) AS total_credit_cur_before,
            SUM(credit_mnt_before) AS total_credit_mnt_before
        FROM transactions_before_begin
        GROUP BY "AccountId", "ClientId", "CurrencyId"
    ),
    
    -- 3. Period Transactions (between begindate and enddate, grouped by AccountId, ClientId, and CurrencyId)
    period_transactions AS (
        SELECT 
            cdd."AccountId",
            cdd."ClientId",
            cdd."CurrencyId",
            COALESCE(SUM(CASE WHEN cdd."IsDebit" = true THEN cdd."CurrencyAmount" ELSE 0 END), 0) AS period_debit_cur,
            COALESCE(SUM(cdd."DebitAmount"), 0) AS period_debit_mnt,
            COALESCE(SUM(CASE WHEN cdd."IsDebit" = false THEN cdd."CurrencyAmount" ELSE 0 END), 0) AS period_credit_cur,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS period_credit_mnt
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" >= begindate 
            AND cd."DocumentDate" <= enddate
            AND cd."IsDelete" = false
        GROUP BY cdd."AccountId", cdd."ClientId", cdd."CurrencyId"
        
        UNION ALL
        
        SELECT 
            idd."AccountId",
            idd."ClientId",
            idd."CurrencyId",
            COALESCE(SUM(CASE WHEN idd."IsDebit" = true THEN idd."CurrencyAmount" ELSE 0 END), 0) AS period_debit_cur,
            COALESCE(SUM(idd."DebitAmount"), 0) AS period_debit_mnt,
            COALESCE(SUM(CASE WHEN idd."IsDebit" = false THEN idd."CurrencyAmount" ELSE 0 END), 0) AS period_credit_cur,
            COALESCE(SUM(idd."CreditAmount"), 0) AS period_credit_mnt
        FROM inv_document_detail idd
        INNER JOIN inv_document id ON idd."DocumentId" = id."DocumentId"
        WHERE id."DocumentDate" >= begindate 
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
        GROUP BY idd."AccountId", idd."ClientId", idd."CurrencyId"
        
        UNION ALL
        
        SELECT 
            add."AccountId",
            add."ClientId",
            add."CurrencyId",
            COALESCE(SUM(CASE WHEN add."IsDebit" = true THEN add."CurrencyAmount" ELSE 0 END), 0) AS period_debit_cur,
            COALESCE(SUM(add."DebitAmount"), 0) AS period_debit_mnt,
            COALESCE(SUM(CASE WHEN add."IsDebit" = false THEN add."CurrencyAmount" ELSE 0 END), 0) AS period_credit_cur,
            COALESCE(SUM(add."CreditAmount"), 0) AS period_credit_mnt
        FROM ast_document_detail add
        INNER JOIN ast_document ad ON add."DocumentId" = ad."DocumentId"
        WHERE ad."DocumentDate" >= begindate 
            AND ad."DocumentDate" <= enddate
            AND ad."IsDelete" = false
        GROUP BY add."AccountId", add."ClientId", add."CurrencyId"
    ),
    
    -- Aggregate period transactions
    aggregated_period AS (
        SELECT 
            "AccountId",
            "ClientId",
            "CurrencyId",
            SUM(period_debit_cur) AS total_period_debit_cur,
            SUM(period_debit_mnt) AS total_period_debit_mnt,
            SUM(period_credit_cur) AS total_period_credit_cur,
            SUM(period_credit_mnt) AS total_period_credit_mnt
        FROM period_transactions
        GROUP BY "AccountId", "ClientId", "CurrencyId"
    ),
    
    -- 4. Get all unique AccountId + ClientId + CurrencyId combinations from all sources
    account_client_currency_combinations AS (
        SELECT DISTINCT "AccountId", "ClientId", "CurrencyId" FROM starting_balances
        UNION
        SELECT DISTINCT "AccountId", "ClientId", "CurrencyId" FROM aggregated_before_begin
        UNION
        SELECT DISTINCT "AccountId", "ClientId", "CurrencyId" FROM aggregated_period
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
        acc."CurrencyId",
        cur."Currency_name",
        
        -- Beginning Balance Currency (Debit) - Cash and Receivable only
        CASE 
            WHEN rat."AccountTypeId" IN (1, 2, 3, 4, 5, 6) THEN
                COALESCE(sb.starting_balance_cur, 0) + 
                COALESCE(abb.total_debit_cur_before, 0) - 
                COALESCE(abb.total_credit_cur_before, 0)
            ELSE 0
        END AS BeginningBalanceCurDebit,
        
        -- Beginning Balance MNT (Debit) - Cash and Receivable only
        CASE 
            WHEN rat."AccountTypeId" IN (1, 2, 3, 4, 5, 6) THEN
                COALESCE(sb.starting_balance_mnt, 0) + 
                COALESCE(abb.total_debit_mnt_before, 0) - 
                COALESCE(abb.total_credit_mnt_before, 0)
            ELSE 0
        END AS BeginningBalanceMntDebit,
        
        -- Beginning Balance Currency (Credit) - Payable only
        CASE 
            WHEN rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 THEN
                COALESCE(sb.starting_balance_cur, 0) - 
                COALESCE(abb.total_debit_cur_before, 0) + 
                COALESCE(abb.total_credit_cur_before, 0)
            ELSE 0
        END AS BeginningBalanceCurCredit,
        
        -- Beginning Balance MNT (Credit) - Payable only
        CASE 
            WHEN rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 THEN
                COALESCE(sb.starting_balance_mnt, 0) - 
                COALESCE(abb.total_debit_mnt_before, 0) + 
                COALESCE(abb.total_credit_mnt_before, 0)
            ELSE 0
        END AS BeginningBalanceMntCredit,
        
        -- Period Debit Currency
        COALESCE(ap.total_period_debit_cur, 0) AS DebitCur,
        
        -- Period Debit MNT
        COALESCE(ap.total_period_debit_mnt, 0) AS DebitMnt,
        
        -- Period Credit Currency
        COALESCE(ap.total_period_credit_cur, 0) AS CreditCur,
        
        -- Period Credit MNT
        COALESCE(ap.total_period_credit_mnt, 0) AS CreditMnt,
        
        -- Ending Balance Currency (Debit) - Cash and Receivable only
        CASE 
            WHEN rat."AccountTypeId" IN (1, 2, 3, 4, 5, 6) THEN
                COALESCE(sb.starting_balance_cur, 0) + 
                COALESCE(abb.total_debit_cur_before, 0) - 
                COALESCE(abb.total_credit_cur_before, 0) +
                COALESCE(ap.total_period_debit_cur, 0) - 
                COALESCE(ap.total_period_credit_cur, 0)
            ELSE 0
        END AS EndingBalanceCurDebit,
        
        -- Ending Balance MNT (Debit) - Cash and Receivable only
        CASE 
            WHEN rat."AccountTypeId" IN (1, 2, 3, 4, 5, 6) THEN
                COALESCE(sb.starting_balance_mnt, 0) + 
                COALESCE(abb.total_debit_mnt_before, 0) - 
                COALESCE(abb.total_credit_mnt_before, 0) +
                COALESCE(ap.total_period_debit_mnt, 0) - 
                COALESCE(ap.total_period_credit_mnt, 0)
            ELSE 0
        END AS EndingBalanceMntDebit,
        
        -- Ending Balance Currency (Credit) - Payable only
        CASE 
            WHEN rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 THEN
                COALESCE(sb.starting_balance_cur, 0) - 
                COALESCE(abb.total_debit_cur_before, 0) + 
                COALESCE(abb.total_credit_cur_before, 0) -
                COALESCE(ap.total_period_debit_cur, 0) + 
                COALESCE(ap.total_period_credit_cur, 0)
            ELSE 0
        END AS EndingBalanceCurCredit,
        
        -- Ending Balance MNT (Credit) - Payable only
        CASE 
            WHEN rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 THEN
                COALESCE(sb.starting_balance_mnt, 0) - 
                COALESCE(abb.total_debit_mnt_before, 0) + 
                COALESCE(abb.total_credit_mnt_before, 0) -
                COALESCE(ap.total_period_debit_mnt, 0) + 
                COALESCE(ap.total_period_credit_mnt, 0)
            ELSE 0
        END AS EndingBalanceMntCredit
        
    FROM ref_account ra
    INNER JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
    INNER JOIN account_client_currency_combinations acc ON ra."AccountId" = acc."AccountId"
    LEFT JOIN ref_client rc ON acc."ClientId" = rc."ClientId"
    LEFT JOIN ref_currency cur ON acc."CurrencyId" = cur."CurrencyId"
    LEFT JOIN starting_balances sb ON ra."AccountId" = sb."AccountId" 
        AND acc."ClientId" = sb."ClientId"
        AND acc."CurrencyId" = sb."CurrencyId"
    LEFT JOIN aggregated_before_begin abb ON ra."AccountId" = abb."AccountId" 
        AND acc."ClientId" = abb."ClientId"
        AND acc."CurrencyId" = abb."CurrencyId"
    LEFT JOIN aggregated_period ap ON ra."AccountId" = ap."AccountId" 
        AND acc."ClientId" = ap."ClientId"
        AND acc."CurrencyId" = ap."CurrencyId"
    WHERE ra."IsDelete" = false
        AND (
            (rat."AccountTypeId" IN (1, 2) AND rat."IsActive" = true)  -- Cash
            OR 
            (rat."AccountTypeId" IN (3, 4, 5, 6) AND rat."IsActive" = true)  -- Receivable
            OR 
            (rat."AccountTypeId" > 41 AND rat."AccountTypeId" < 59 AND rat."IsActive" = false)  -- Payable
        )
    ORDER BY ra."AccountCode", rc."ClientCode" NULLS LAST, acc."CurrencyId";
    
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- Get all currency balances for a date range:
-- SELECT * FROM calculate_currency_balance('2025-01-01', '2025-12-31');

-- Filter by specific currency:
-- SELECT * FROM calculate_currency_balance('2025-01-01', '2025-12-31') WHERE currencyid = 'USD';

-- Get totals by currency:
-- SELECT currencyid, currencyname, 
--        SUM(endingbalancecurdebit) + SUM(endingbalancecurcredit) as total_cur,
--        SUM(endingbalancemntdebit) + SUM(endingbalancemntcredit) as total_mnt
-- FROM calculate_currency_balance('2025-01-01', '2025-12-31')
-- GROUP BY currencyid, currencyname;

-- Cash accounts only:
-- SELECT * FROM calculate_currency_balance('2025-01-01', '2025-12-31')
-- WHERE accounttypeid IN (1, 2);

-- Receivable accounts only:
-- SELECT * FROM calculate_currency_balance('2025-01-01', '2025-12-31')
-- WHERE accounttypeid IN (3, 4, 5, 6);

-- Payable accounts only:
-- SELECT * FROM calculate_currency_balance('2025-01-01', '2025-12-31')
-- WHERE accounttypeid > 41 AND accounttypeid < 59;

-- Get balance by client and currency:
-- SELECT clientcode, clientname, currencyid,
--        SUM(endingbalancecurdebit) as total_debit_cur,
--        SUM(endingbalancecurcredit) as total_credit_cur,
--        SUM(endingbalancemntdebit) as total_debit_mnt,
--        SUM(endingbalancemntcredit) as total_credit_mnt
-- FROM calculate_currency_balance('2025-01-01', '2025-12-31')
-- GROUP BY clientcode, clientname, currencyid
-- ORDER BY clientcode, currencyid;

