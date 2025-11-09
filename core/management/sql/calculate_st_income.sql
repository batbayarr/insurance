-- PostgreSQL St_Income Calculation Function
-- This function calculates and updates EndBalance in st_income table
-- Parameters: begindate DATE, enddate DATE
-- Groups accounts by StIncomeId and updates st_income table
-- Only processes cash_document where DocumentTypeId = 14 (closing entries)
-- Filters out AccountTypeId = 102

-- Drop the function if it exists
DROP FUNCTION IF EXISTS public.calculate_st_income(date, date);

CREATE OR REPLACE FUNCTION public.calculate_st_income(
    begindate DATE,
    enddate DATE
)
RETURNS TABLE (
    "StIncomeId" SMALLINT,
    "StIncome" VARCHAR(30),
    "StIncomeName" VARCHAR(150),
    "EndBalance" NUMERIC(24,6),
    "Order" SMALLINT
) AS $$
BEGIN
    -- First, reset all EndBalance to 0
    UPDATE st_income SET "EndBalance" = 0;
    
    -- Update st_income table with calculated balances
    WITH 
    -- 1. Calculate sum of DebitAmount and CreditAmount by AccountTypeId
    -- From cash_document_detail where DocumentTypeId = 14 and date range
    -- Filter AccountTypeId <> 102
    account_type_totals AS (
        SELECT 
            ra."AccountTypeId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS total_debit,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS total_credit
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        INNER JOIN ref_account ra ON cdd."AccountId" = ra."AccountId"
        WHERE cd."DocumentTypeId" = 14
            AND cd."DocumentDate" >= begindate
            AND cd."DocumentDate" <= enddate
            AND cd."IsDelete" = false
            AND ra."AccountTypeId" <> 102
            AND ra."IsDelete" = false
        GROUP BY ra."AccountTypeId"
    ),
    
    -- 2. Join with ref_account_type to get StIncomeId
    -- Calculate EndBalance = sum(DebitAmount) + sum(CreditAmount)
    income_totals AS (
        SELECT 
            rat."StIncomeId",
            COALESCE(SUM(att.total_debit + att.total_credit), 0) AS end_balance
        FROM account_type_totals att
        INNER JOIN ref_account_type rat ON att."AccountTypeId" = rat."AccountTypeId"
        WHERE rat."StIncomeId" IS NOT NULL
        GROUP BY rat."StIncomeId"
    )
    
    -- Update st_income table with calculated EndBalance
    UPDATE st_income si
    SET 
        "EndBalance" = COALESCE(it.end_balance, 0)
    FROM income_totals it
    WHERE si."StIncomeId" = it."StIncomeId";
    
    -- Return all st_income records ordered by Order and StIncome
    RETURN QUERY
    SELECT 
        si."StIncomeId",
        si."StIncome",
        si."StIncomeName",
        si."EndBalance",
        si."Order"
    FROM st_income si
    ORDER BY si."Order", si."StIncome";
    
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT calculate_st_income('2025-01-01', '2025-12-31');

