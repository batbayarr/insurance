-- FUNCTION: public.report_inventory_balance_warehouse(date, date, SMALLINT, INTEGER)
-- Calculates inventory balance filtered by warehouse and account
-- Based on calculate_inventory_balance but adds warehouse and account filtering

DROP FUNCTION IF EXISTS public.report_inventory_balance_warehouse(date, date, SMALLINT, INTEGER);

CREATE OR REPLACE FUNCTION public.report_inventory_balance_warehouse(
	begindate date,
	enddate date,
	p_warehouse_id SMALLINT DEFAULT NULL,
	p_account_id INTEGER DEFAULT NULL)
    RETURNS TABLE(
        accountid integer, 
        accountcode character varying, 
        accountname character varying, 
        inventoryid integer, 
        inventorycode character varying, 
        inventoryname character varying, 
        measurementid smallint, 
        measurementname character varying,
        warehouseid smallint,
        warehousecode character varying,
        warehousename character varying,
        beginningquantity numeric, 
        beginningcost numeric, 
        inquantity numeric, 
        incost numeric, 
        outquantity numeric, 
        outcost numeric, 
        endingquantity numeric, 
        endingcost numeric
    ) 
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
            ibb."WarehouseId",
            ri."MeasurementId",
            SUM(ibb."Quantity") AS starting_quantity,
            SUM(ibb."Quantity" * ibb."UnitCost") AS starting_cost
        FROM inv_beginning_balance ibb
        INNER JOIN ref_inventory ri ON ibb."InventoryId" = ri."InventoryId"
        WHERE ibb."IsDelete" = false
            AND (p_warehouse_id IS NULL OR ibb."WarehouseId" = p_warehouse_id)
            AND (p_account_id IS NULL OR ibb."AccountId" = p_account_id)
        GROUP BY ibb."AccountId", ibb."InventoryId", ibb."WarehouseId", ri."MeasurementId"
    ),

    -- 2) Income before begindate (DocumentTypeId IN (5, 9)) increases stock
    income_before_begin AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            id."WarehouseId",
            SUM(idi."Quantity") AS in_quantity_before,
            SUM(idi."Quantity" * idi."UnitCost") AS in_cost_before
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (5, 9)
            AND id."DocumentDate" < begindate
            AND id."IsDelete" = false
            AND (p_warehouse_id IS NULL OR id."WarehouseId" = p_warehouse_id)
            AND (p_account_id IS NULL OR id."AccountId" = p_account_id)
        GROUP BY id."AccountId", idi."InventoryId", id."WarehouseId"
    ),

    -- 3) Expense before begindate (DocumentTypeId IN (6, 7, 8)) decreases stock
    expense_before_begin AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            id."WarehouseId",
            SUM(idi."Quantity") AS out_quantity_before,
            SUM(idi."Quantity" * idi."UnitCost") AS out_cost_before
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (6, 7, 8)
            AND id."DocumentDate" < begindate
            AND id."IsDelete" = false
            AND (p_warehouse_id IS NULL OR id."WarehouseId" = p_warehouse_id)
            AND (p_account_id IS NULL OR id."AccountId" = p_account_id)
        GROUP BY id."AccountId", idi."InventoryId", id."WarehouseId"
    ),

    -- 4) Income during period [begindate, enddate]
    income_period AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            id."WarehouseId",
            SUM(idi."Quantity") AS in_quantity,
            SUM(idi."Quantity" * idi."UnitCost") AS in_cost
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (5, 9)
            AND id."DocumentDate" >= begindate
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
            AND (p_warehouse_id IS NULL OR id."WarehouseId" = p_warehouse_id)
            AND (p_account_id IS NULL OR id."AccountId" = p_account_id)
        GROUP BY id."AccountId", idi."InventoryId", id."WarehouseId"
    ),

    -- 5) Expense during period [begindate, enddate]
    expense_period AS (
        SELECT 
            id."AccountId",
            idi."InventoryId",
            id."WarehouseId",
            SUM(idi."Quantity") AS out_quantity,
            SUM(idi."Quantity" * idi."UnitCost") AS out_cost
        FROM inv_document id
        INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
        WHERE id."DocumentTypeId" IN (6, 7, 8)
            AND id."DocumentDate" >= begindate
            AND id."DocumentDate" <= enddate
            AND id."IsDelete" = false
            AND (p_warehouse_id IS NULL OR id."WarehouseId" = p_warehouse_id)
            AND (p_account_id IS NULL OR id."AccountId" = p_account_id)
        GROUP BY id."AccountId", idi."InventoryId", id."WarehouseId"
    ),

    -- 6) All AccountId + InventoryId + WarehouseId + MeasurementId combinations encountered
    account_inventory_combinations AS (
        SELECT DISTINCT "AccountId", "InventoryId", "WarehouseId", "MeasurementId" FROM starting_balances
        UNION
        SELECT DISTINCT ib."AccountId", ib."InventoryId", ib."WarehouseId", ri."MeasurementId"
        FROM income_before_begin ib
        INNER JOIN ref_inventory ri ON ib."InventoryId" = ri."InventoryId"
        UNION
        SELECT DISTINCT eb."AccountId", eb."InventoryId", eb."WarehouseId", ri."MeasurementId"
        FROM expense_before_begin eb
        INNER JOIN ref_inventory ri ON eb."InventoryId" = ri."InventoryId"
        UNION
        SELECT DISTINCT ip."AccountId", ip."InventoryId", ip."WarehouseId", ri."MeasurementId"
        FROM income_period ip
        INNER JOIN ref_inventory ri ON ip."InventoryId" = ri."InventoryId"
        UNION
        SELECT DISTINCT ep."AccountId", ep."InventoryId", ep."WarehouseId", ri."MeasurementId"
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
        COALESCE(rw."WarehouseId", 0)::SMALLINT AS warehouseid,
        COALESCE(rw."WarehouseCode", '') AS warehousecode,
        COALESCE(rw."WarehouseName", '') AS warehousename,

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
    LEFT JOIN ref_warehouse rw ON aic."WarehouseId" = rw."WarehouseId"
    LEFT JOIN starting_balances sb ON aic."AccountId" = sb."AccountId"
        AND aic."InventoryId" = sb."InventoryId"
        AND (aic."WarehouseId" = sb."WarehouseId" OR (aic."WarehouseId" IS NULL AND sb."WarehouseId" IS NULL))
    LEFT JOIN income_before_begin ibb ON aic."AccountId" = ibb."AccountId"
        AND aic."InventoryId" = ibb."InventoryId"
        AND (aic."WarehouseId" = ibb."WarehouseId" OR (aic."WarehouseId" IS NULL AND ibb."WarehouseId" IS NULL))
    LEFT JOIN expense_before_begin ebb ON aic."AccountId" = ebb."AccountId"
        AND aic."InventoryId" = ebb."InventoryId"
        AND (aic."WarehouseId" = ebb."WarehouseId" OR (aic."WarehouseId" IS NULL AND ebb."WarehouseId" IS NULL))
    LEFT JOIN income_period ip ON aic."AccountId" = ip."AccountId"
        AND aic."InventoryId" = ip."InventoryId"
        AND (aic."WarehouseId" = ip."WarehouseId" OR (aic."WarehouseId" IS NULL AND ip."WarehouseId" IS NULL))
    LEFT JOIN expense_period ep ON aic."AccountId" = ep."AccountId"
        AND aic."InventoryId" = ep."InventoryId"
        AND (aic."WarehouseId" = ep."WarehouseId" OR (aic."WarehouseId" IS NULL AND ep."WarehouseId" IS NULL))
    WHERE ra."IsDelete" = false
        AND (p_account_id IS NULL OR ra."AccountId" = p_account_id)
    ORDER BY ra."AccountCode", ri."InventoryCode", COALESCE(rw."WarehouseCode", '');

END;
$BODY$;

ALTER FUNCTION public.report_inventory_balance_warehouse(date, date, SMALLINT, INTEGER)
    OWNER TO postgres;

-- Comment on function
COMMENT ON FUNCTION report_inventory_balance_warehouse(date, date, SMALLINT, INTEGER) IS 
'Calculates inventory balance for a given date range, optionally filtered by warehouse and account.
Parameters: begindate (start date), enddate (end date), p_warehouse_id (optional warehouse ID, NULL for all warehouses), p_account_id (optional account ID, NULL for all accounts).
Returns inventory balances grouped by AccountId, InventoryId, WarehouseId, and MeasurementId.
When p_warehouse_id is NULL, returns balances for all warehouses.
When p_warehouse_id is provided, filters all calculations to that specific warehouse.
When p_account_id is NULL, returns balances for all accounts.
When p_account_id is provided, filters all calculations to that specific account.';

