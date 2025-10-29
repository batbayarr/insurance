-- FUNCTION: public.calculate_inventory_balance(date, date)

-- DROP FUNCTION IF EXISTS public.calculate_inventory_balance(date, date);

CREATE OR REPLACE FUNCTION public.calculate_inventory_balance(
	begindate date,
	enddate date)
    RETURNS TABLE(accountid integer, accountcode character varying, accountname character varying, inventoryid integer, inventorycode character varying, inventoryname character varying, measurementid smallint, measurementname character varying, beginningquantity numeric, beginningcost numeric, inquantity numeric, incost numeric, outquantity numeric, outcost numeric, endingquantity numeric, endingcost numeric) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
BEGIN
    RETURN QUERY
    WITH 
    -- 1) Starting balances from inv_beginning_balance (system initial balances)
    starting_balances AS (
        SELECT 
            ibb."AccountId",
            ibb."InventoryId",
            ri."MeasurementId",
            SUM(ibb."Quantity") AS starting_quantity,
            SUM(ibb."Quantity" * ibb."UnitCost") AS starting_cost
        FROM inv_beginning_balance ibb
        INNER JOIN ref_inventory ri ON ibb."InventoryId" = ri."InventoryId"
        WHERE ibb."IsDelete" = false
        GROUP BY ibb."AccountId", ibb."InventoryId", ri."MeasurementId"
    ),

    -- 2) Income before begindate (DocumentTypeId IN (5, 9)) increases stock
    income_before_begin AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            SUM(idi."Quantity") AS in_quantity_before,
            SUM(idi."Quantity" * idi."UnitCost") AS in_cost_before
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (5, 9)
            AND id."DocumentDate" < begindate
            AND id."IsDelete" = false
        GROUP BY id."AccountId", idi."InventoryId"
    ),

    -- 3) Expense before begindate (DocumentTypeId IN (6, 7, 8)) decreases stock
    expense_before_begin AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            SUM(idi."Quantity") AS out_quantity_before,
            SUM(idi."Quantity" * idi."UnitCost") AS out_cost_before
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (6, 7, 8)
            AND id."DocumentDate" < begindate
            AND id."IsDelete" = false
        GROUP BY id."AccountId", idi."InventoryId"
    ),

    -- 4) Income during period [begindate, enddate]
    income_period AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            SUM(idi."Quantity") AS in_quantity,
            SUM(idi."Quantity" * idi."UnitCost") AS in_cost
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (5, 9)
            AND id."DocumentDate" >= begindate
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
        GROUP BY id."AccountId", idi."InventoryId"
    ),

    -- 5) Expense during period [begindate, enddate]
    expense_period AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            SUM(idi."Quantity") AS out_quantity,
            SUM(idi."Quantity" * idi."UnitCost") AS out_cost
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (6, 7, 8)
            AND id."DocumentDate" >= begindate
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
        GROUP BY id."AccountId", idi."InventoryId"
    ),

    -- 6) All AccountId + InventoryId + MeasurementId combinations encountered
    account_inventory_combinations AS (
        SELECT DISTINCT "AccountId", "InventoryId", "MeasurementId" FROM starting_balances
        UNION
        SELECT DISTINCT ib."AccountId", ib."InventoryId", ri."MeasurementId"
        FROM income_before_begin ib
        INNER JOIN ref_inventory ri ON ib."InventoryId" = ri."InventoryId"
        UNION
        SELECT DISTINCT eb."AccountId", eb."InventoryId", ri."MeasurementId"
        FROM expense_before_begin eb
        INNER JOIN ref_inventory ri ON eb."InventoryId" = ri."InventoryId"
        UNION
        SELECT DISTINCT ip."AccountId", ip."InventoryId", ri."MeasurementId"
        FROM income_period ip
        INNER JOIN ref_inventory ri ON ip."InventoryId" = ri."InventoryId"
        UNION
        SELECT DISTINCT ep."AccountId", ep."InventoryId", ri."MeasurementId"
        FROM expense_period ep
        INNER JOIN ref_inventory ri ON ep."InventoryId" = ri."InventoryId"
    )

    SELECT 
        ra."AccountId",
        ra."AccountCode",
        ra."AccountName",
        ri."InventoryId",
        ri."InventoryCode",
        ri."InventoryName",
        rm."MeasurementId",
        rm."MeasurementName",

        -- Beginning balance as of begindate
        COALESCE(sb.starting_quantity, 0) +
        COALESCE(ibb.in_quantity_before, 0) -
        COALESCE(ebb.out_quantity_before, 0) AS BeginningQuantity,

        COALESCE(sb.starting_cost, 0) +
        COALESCE(ibb.in_cost_before, 0) -
        COALESCE(ebb.out_cost_before, 0) AS BeginningCost,

        -- Period movements
        COALESCE(ip.in_quantity, 0) AS InQuantity,
        COALESCE(ip.in_cost, 0) AS InCost,
        COALESCE(ep.out_quantity, 0) AS OutQuantity,
        COALESCE(ep.out_cost, 0) AS OutCost,

        -- Ending balance as of enddate
        COALESCE(sb.starting_quantity, 0) +
        COALESCE(ibb.in_quantity_before, 0) -
        COALESCE(ebb.out_quantity_before, 0) +
        COALESCE(ip.in_quantity, 0) -
        COALESCE(ep.out_quantity, 0) AS EndingQuantity,

        COALESCE(sb.starting_cost, 0) +
        COALESCE(ibb.in_cost_before, 0) -
        COALESCE(ebb.out_cost_before, 0) +
        COALESCE(ip.in_cost, 0) -
        COALESCE(ep.out_cost, 0) AS EndingCost

    FROM account_inventory_combinations aic
    INNER JOIN ref_account ra ON aic."AccountId" = ra."AccountId"
    INNER JOIN ref_inventory ri ON aic."InventoryId" = ri."InventoryId"
    INNER JOIN ref_measurement rm ON aic."MeasurementId" = rm."MeasurementId"
    LEFT JOIN starting_balances sb ON aic."AccountId" = sb."AccountId"
        AND aic."InventoryId" = sb."InventoryId"
    LEFT JOIN income_before_begin ibb ON aic."AccountId" = ibb."AccountId"
        AND aic."InventoryId" = ibb."InventoryId"
    LEFT JOIN expense_before_begin ebb ON aic."AccountId" = ebb."AccountId"
        AND aic."InventoryId" = ebb."InventoryId"
    LEFT JOIN income_period ip ON aic."AccountId" = ip."AccountId"
        AND aic."InventoryId" = ip."InventoryId"
    LEFT JOIN expense_period ep ON aic."AccountId" = ep."AccountId"
        AND aic."InventoryId" = ep."InventoryId"
    WHERE ra."IsDelete" = false
    ORDER BY ra."AccountCode", ri."InventoryCode";

END;
$BODY$;

ALTER FUNCTION public.calculate_inventory_balance(date, date)
    OWNER TO postgres;
