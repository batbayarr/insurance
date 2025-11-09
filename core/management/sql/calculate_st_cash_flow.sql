
-- FUNCTION: public.calculate_st_cash_flow(date, date)

-- DROP FUNCTION IF EXISTS public.calculate_st_cash_flow(date, date);

CREATE OR REPLACE FUNCTION public.calculate_st_cash_flow(
	begindate date,
	enddate date)
    RETURNS TABLE (
        "StCashFlowId" SMALLINT,
        "StCashFlowCode" VARCHAR(30),
        "StCashFlowName" VARCHAR(150),
        "EndBalance" NUMERIC(24,6),
        "Order" SMALLINT,
        "IsVisible" BOOLEAN
    )
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
DECLARE
    v_beginning_balance NUMERIC(24,6);
BEGIN
    -- Step 1: Calculate Beginning Balance from cash_beginning_balance
    -- Get sum(currencyExchange * currencyAmount) where AccountTypeId in (1, 2)
    SELECT COALESCE(SUM(cbb."CurrencyExchange" * cbb."CurrencyAmount"), 0)
    INTO v_beginning_balance
    FROM cash_beginning_balance cbb
    INNER JOIN ref_account ra ON cbb."AccountId" = ra."AccountId"
    INNER JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
    WHERE rat."AccountTypeId" IN (1, 2)
        AND cbb."IsDelete" = false;
    
    -- Step 2: Update StCashFlowId = 52 with Beginning Balance
    UPDATE st_cashflow scf
    SET "EndBalance" = v_beginning_balance
    WHERE scf."StCashFlowId" = 52;
    
    -- Step 3: Calculate and update EndBalance for each CashFlowId
    -- Select records from cash_document_detail joined with cash_document
    -- Group by CashFlowId and sum DebitAmount and CreditAmount
    WITH cash_flow_totals AS (
        SELECT 
            cdd."CashFlowId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS total_debit,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS total_credit
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd ON cdd."DocumentId" = cd."DocumentId"
        WHERE cd."DocumentDate" >= begindate
            AND cd."DocumentDate" <= enddate
            AND cd."IsDelete" = false
            AND cdd."CashFlowId" IS NOT NULL
        GROUP BY cdd."CashFlowId"
    )
    -- Update st_cashflow's EndBalance field with sum(DebitAmount) + sum(CreditAmount)
    UPDATE st_cashflow scf
    SET "EndBalance" = COALESCE(cft.total_debit, 0) + COALESCE(cft.total_credit, 0)
    FROM cash_flow_totals cft
    WHERE scf."StCashFlowId" = cft."CashFlowId";
    
    -- Return all st_cashflow records (visible items only) ordered by Order and StCashFlowCode
    RETURN QUERY
    SELECT 
        scf."StCashFlowId",
        scf."StCashFlowCode",
        scf."StCashFlowName",
        scf."EndBalance",
        scf."Order",
        scf."IsVisible"
    FROM st_cashflow scf
    WHERE scf."IsVisible" = true
    ORDER BY scf."Order", scf."StCashFlowCode";
    
END;
$BODY$;

ALTER FUNCTION public.calculate_st_cash_flow(date, date)
    OWNER TO postgres;
