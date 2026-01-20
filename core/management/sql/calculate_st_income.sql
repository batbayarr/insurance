CREATE OR REPLACE FUNCTION public.calculate_st_income(
    begindate date,
    enddate date
)
RETURNS TABLE(
    "StIncomeId" smallint,
    "StIncome" character varying,
    "StIncomeName" character varying,
    "EndBalance" numeric,
    "Order" smallint
)
LANGUAGE plpgsql
VOLATILE
AS $BODY$
BEGIN
    -- 1. Reset EndBalance
    UPDATE st_income si
    SET "EndBalance" = 0;

    -- 2. Calculate balances from cash documents
    WITH
    account_type_totals AS (
        SELECT
            ra."AccountTypeId",
            COALESCE(SUM(cdd."DebitAmount"), 0) AS total_debit,
            COALESCE(SUM(cdd."CreditAmount"), 0) AS total_credit
        FROM cash_document_detail cdd
        INNER JOIN cash_document cd
            ON cdd."DocumentId" = cd."DocumentId"
        INNER JOIN ref_account ra
            ON cdd."AccountId" = ra."AccountId"
        WHERE cd."DocumentTypeId" = 14
          AND cd."DocumentDate" >= begindate
          AND cd."DocumentDate" <= enddate
          AND cd."IsDelete" = false
          AND ra."AccountTypeId" <> 102
          AND ra."IsDelete" = false
        GROUP BY ra."AccountTypeId"
    ),
    income_totals AS (
        SELECT
            rat."StIncomeId",
            SUM(att.total_debit + att.total_credit) AS end_balance
        FROM account_type_totals att
        INNER JOIN ref_account_type rat
            ON att."AccountTypeId" = rat."AccountTypeId"
        WHERE rat."StIncomeId" IS NOT NULL
        GROUP BY rat."StIncomeId"
    )
    UPDATE st_income si
    SET "EndBalance" = COALESCE(it.end_balance, 0)
    FROM income_totals it
    WHERE si."StIncomeId" = it."StIncomeId";

    -- 3. Calculated rows

    -- StIncomeId = 3
    UPDATE st_income si
    SET "EndBalance" =
        COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" IN (1)), 0)
      - COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" IN (2)), 0)
    WHERE si."StIncomeId" = 3;

    -- StIncomeId = 18
    UPDATE st_income si
    SET "EndBalance" =
        COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" IN (3,4,5,6,7,8,13,14)), 0)
      - COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" IN (9,10,11,12,15,16,17)), 0)
    WHERE si."StIncomeId" = 18;

    -- StIncomeId = 20
    UPDATE st_income si
    SET "EndBalance" =
        COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" = 18), 0)
      - COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" = 19), 0)
    WHERE si."StIncomeId" = 20;

    -- StIncomeId = 22
    UPDATE st_income si
    SET "EndBalance" =
        COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" = 18), 0)
      - COALESCE(
            (SELECT SUM(si2."EndBalance")
             FROM st_income si2
             WHERE si2."StIncomeId" = 19), 0)
    WHERE si."StIncomeId" = 22;

    -- 4. Return result
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
$BODY$;

ALTER FUNCTION public.calculate_st_income(date, date)
OWNER TO postgres;