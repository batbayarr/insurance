-- PostgreSQL St_Balance Calculation Function
-- This function calculates and updates BeginBalance and EndBalance in st_balance table
-- Parameters: begindate DATE, enddate DATE
-- Groups accounts by StBalanceId and updates st_balance table

-- Drop the function if it exists
DROP FUNCTION IF EXISTS public.calculate_st_balance(date, date);

CREATE OR REPLACE FUNCTION public.calculate_st_balance(
    begindate DATE,
    enddate DATE
)
RETURNS TABLE (
    "StbalanceId" SMALLINT,
    "StbalanceCode" VARCHAR(30),
    "StbalanceName" VARCHAR(150),
    "BeginBalance" NUMERIC(24,6),
    "EndBalance" NUMERIC(24,6),
    "Order" SMALLINT
) AS $$
BEGIN
    -- Update st_balance table with calculated balances
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
    ),
    
    -- Calculate account balances
    account_balances AS (
        SELECT 
            ra."AccountId",
            rat."StBalanceId",
            
            -- Beginning Balance (as of begindate)
            CASE 
                WHEN rat."IsActive" = true THEN 
                    -- Active accounts: StartingBalance + DebitBefore - CreditBefore
                    COALESCE(sb.starting_balance, 0) + 
                    COALESCE(abb.total_debit_before, 0) - 
                    COALESCE(abb.total_credit_before, 0)
                ELSE 
                    -- Passive accounts: StartingBalance - DebitBefore + CreditBefore
                    COALESCE(sb.starting_balance, 0) - 
                    COALESCE(abb.total_debit_before, 0) + 
                    COALESCE(abb.total_credit_before, 0)
            END AS begin_balance,
            
            -- Ending Balance
            CASE 
                WHEN rat."IsActive" = true THEN 
                    -- Active accounts: BeginningBalance + DebitAmount - CreditAmount
                    COALESCE(sb.starting_balance, 0) + 
                    COALESCE(abb.total_debit_before, 0) - 
                    COALESCE(abb.total_credit_before, 0) +
                    COALESCE(ap.total_period_debit, 0) - 
                    COALESCE(ap.total_period_credit, 0)
                ELSE 
                    -- Passive accounts: BeginningBalance - DebitAmount + CreditAmount
                    COALESCE(sb.starting_balance, 0) - 
                    COALESCE(abb.total_debit_before, 0) + 
                    COALESCE(abb.total_credit_before, 0) -
                    COALESCE(ap.total_period_debit, 0) + 
                    COALESCE(ap.total_period_credit, 0)
            END AS end_balance
            
        FROM ref_account ra
        INNER JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
        LEFT JOIN starting_balances sb ON ra."AccountId" = sb."AccountId"
        LEFT JOIN aggregated_before_begin abb ON ra."AccountId" = abb."AccountId"
        LEFT JOIN aggregated_period ap ON ra."AccountId" = ap."AccountId"
        WHERE ra."IsDelete" = false
            AND rat."StBalanceId" IS NOT NULL
    ),
    
    -- Group by StBalanceId and calculate totals
    grouped_balances AS (
        SELECT 
            "StBalanceId",
            SUM(begin_balance) AS total_begin_balance,
            SUM(end_balance) AS total_end_balance
        FROM account_balances
        GROUP BY "StBalanceId"
    )
    
    -- Update st_balance table with calculated values
    UPDATE st_balance sb
    SET 
        "BeginBalance" = COALESCE(gb.total_begin_balance, 0),
        "EndBalance" = COALESCE(gb.total_end_balance, 0)
    FROM grouped_balances gb
    WHERE sb."StbalanceId" = gb."StBalanceId";
    
    -- Return all st_balance records ordered by Order and StbalanceCode
    RETURN QUERY
    SELECT 
        sb."StbalanceId",
        sb."StbalanceCode",
        sb."StbalanceName",
        sb."BeginBalance",
        sb."EndBalance",
        sb."Order"
    FROM st_balance sb
    ORDER BY sb."Order", sb."StbalanceCode";
    
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT calculate_st_balance('2025-01-01', '2025-12-31');

