-- FUNCTION: public.calculate_st_balance(date, date)

-- DROP FUNCTION IF EXISTS public.calculate_st_balance(date, date);

CREATE OR REPLACE FUNCTION public.calculate_st_balance(
	begindate date,
	enddate date)
    RETURNS TABLE("StbalanceId" smallint, "StbalanceCode" character varying, "StbalanceName" character varying, "BeginBalance" numeric, "EndBalance" numeric, "Order" smallint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
BEGIN
    -------------------------------------------------------------------
    -- 1. Clear balances
    -------------------------------------------------------------------
    UPDATE public.st_balance
    SET "BeginBalance" = 0,
        "EndBalance" = 0;

    -------------------------------------------------------------------
    -- 2. Calculate balances by accounts
    -------------------------------------------------------------------
    WITH 
    starting_balances AS (
        SELECT 
            ra."AccountId",
            COALESCE(cash_bb.starting_balance, 0)
            + COALESCE(inv_bb.starting_balance, 0)
            + COALESCE(ast_bb.starting_balance, 0) AS starting_balance
        FROM ref_account ra
        LEFT JOIN (
            SELECT "AccountId", SUM("CurrencyAmount" * "CurrencyExchange") AS starting_balance
            FROM cash_beginning_balance 
            WHERE "IsDelete" = false
            GROUP BY "AccountId"
        ) cash_bb USING ("AccountId")
        LEFT JOIN (
            SELECT "AccountId", SUM("Quantity" * "UnitCost") AS starting_balance
            FROM inv_beginning_balance 
            WHERE "IsDelete" = false
            GROUP BY "AccountId"
        ) inv_bb USING ("AccountId")
        LEFT JOIN (
            SELECT "AccountId", SUM("UnitCost")-SUM("CumulatedDepreciation") AS starting_balance
            FROM ast_beginning_balance 
            WHERE "IsDelete" = false
            GROUP BY "AccountId"
        ) ast_bb USING ("AccountId")
    ),

    transactions_before AS (
        SELECT "AccountId",
               SUM("DebitAmount") AS debit_before,
               SUM("CreditAmount") AS credit_before
        FROM (
            SELECT cdd."AccountId", cdd."DebitAmount", cdd."CreditAmount"
            FROM cash_document_detail cdd
            JOIN cash_document cd ON cd."DocumentId" = cdd."DocumentId"
            WHERE cd."DocumentDate" < begindate AND cd."IsDelete" = false

            UNION ALL
            SELECT idd."AccountId", idd."DebitAmount", idd."CreditAmount"
            FROM inv_document_detail idd
            JOIN inv_document id ON id."DocumentId" = idd."DocumentId"
            WHERE id."DocumentDate" < begindate AND id."IsDelete" = false

            UNION ALL
            SELECT add."AccountId", add."DebitAmount", add."CreditAmount"
            FROM ast_document_detail add
            JOIN ast_document ad ON ad."DocumentId" = add."DocumentId"
            WHERE ad."DocumentDate" < begindate AND ad."IsDelete" = false
        ) t
        GROUP BY "AccountId"
    ),

    period_transactions AS (
        SELECT "AccountId",
               SUM("DebitAmount") AS period_debit,
               SUM("CreditAmount") AS period_credit
        FROM (
            SELECT cdd."AccountId", cdd."DebitAmount", cdd."CreditAmount"
            FROM cash_document_detail cdd
            JOIN cash_document cd ON cd."DocumentId" = cdd."DocumentId"
            WHERE cd."DocumentDate" >= begindate 
              AND cd."DocumentDate" <= enddate 
              AND cd."IsDelete" = false

            UNION ALL
            SELECT idd."AccountId", idd."DebitAmount", idd."CreditAmount"
            FROM inv_document_detail idd
            JOIN inv_document id ON id."DocumentId" = idd."DocumentId"
            WHERE id."DocumentDate" >= begindate 
              AND id."DocumentDate" <= enddate 
              AND id."IsDelete" = false

            UNION ALL
            SELECT add."AccountId", add."DebitAmount", add."CreditAmount"
            FROM ast_document_detail add
            JOIN ast_document ad ON ad."DocumentId" = add."DocumentId"
            WHERE ad."DocumentDate" >= begindate 
              AND ad."DocumentDate" <= enddate 
              AND ad."IsDelete" = false
        ) t
        GROUP BY "AccountId"
    ),

    account_balances AS (
        SELECT 
            ra."AccountId",
            rat."StBalanceId" AS stid,

            -- BEGIN BALANCE
            CASE WHEN rat."IsActive" = true THEN
                COALESCE(sb.starting_balance,0)
                + COALESCE(tb.debit_before,0)
                - COALESCE(tb.credit_before,0)
            ELSE
                COALESCE(sb.starting_balance,0)
                - COALESCE(tb.debit_before,0)
                + COALESCE(tb.credit_before,0)
            END AS beginbalance,

            -- END BALANCE
            CASE WHEN rat."IsActive" = true THEN
                COALESCE(sb.starting_balance,0)
                + COALESCE(tb.debit_before,0)
                - COALESCE(tb.credit_before,0)
                + COALESCE(pt.period_debit,0)
                - COALESCE(pt.period_credit,0)
            ELSE
                COALESCE(sb.starting_balance,0)
                - COALESCE(tb.debit_before,0)
                + COALESCE(tb.credit_before,0)
                - COALESCE(pt.period_debit,0)
                + COALESCE(pt.period_credit,0)
            END AS endbalance

        FROM ref_account ra
        JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
        LEFT JOIN starting_balances sb USING ("AccountId")
        LEFT JOIN transactions_before tb USING ("AccountId")
        LEFT JOIN period_transactions pt USING ("AccountId")
        WHERE ra."IsDelete" = false
          AND rat."StBalanceId" IS NOT NULL
    ),

    grouped_balances AS (
        SELECT 
            stid AS "StbalanceId",
            SUM(beginbalance) AS b,
            SUM(endbalance) AS e
        FROM account_balances
        GROUP BY stid
    )

    UPDATE st_balance sb
    SET "BeginBalance" = gb.b,
        "EndBalance" = gb.e
    FROM grouped_balances gb
    WHERE sb."StbalanceId" = gb."StbalanceId";

    -------------------------------------------------------------------
    -- 3. Manual grouped hierarchical balances (ALL FIXED)
    -------------------------------------------------------------------

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (3,4,5,6,7,8,9,10,11,12)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (3,4,5,6,7,8,9,10,11,12))
    WHERE sb."StbalanceId" = 13;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (15,16,17,18,19,20,21,22,23)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (15,16,17,18,19,20,21,22,23))
    WHERE sb."StbalanceId" = 24;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (13,24)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (13,24))
    WHERE sb."StbalanceId" = 25;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (29,30,31,32,33,34,35,36,37,38,39,40)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (29,30,31,32,33,34,35,36,37,38,39,40))
    WHERE sb."StbalanceId" = 41;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (43,44,45,46,47)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (43,44,45,46,47))
    WHERE sb."StbalanceId" = 48;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (41,48)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (41,48))
    WHERE sb."StbalanceId" = 49;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (51,52,53,54,55,56,57,58,59,60)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (51,52,53,54,55,56,57,58,59,60))
    WHERE sb."StbalanceId" = 61;

    UPDATE st_balance sb SET
        "BeginBalance" = (SELECT SUM(sb2."BeginBalance") FROM st_balance sb2 WHERE sb2."StbalanceId" IN (49,61)),
        "EndBalance"   = (SELECT SUM(sb2."EndBalance")   FROM st_balance sb2 WHERE sb2."StbalanceId" IN (49,61))
    WHERE sb."StbalanceId" = 62;

    -------------------------------------------------------------------
    -- 4. Return data
    -------------------------------------------------------------------
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
$BODY$;

ALTER FUNCTION public.calculate_st_balance(date, date)
    OWNER TO postgres;
