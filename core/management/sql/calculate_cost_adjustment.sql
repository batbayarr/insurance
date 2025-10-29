-- PostgreSQL Cost Adjustment Calculation Function
-- Calculates weighted average cost for inventory items and updates outbound transaction costs
-- Updates inv_document_item and inv_document_detail tables for DocumentTypeId IN (6, 7, 9)

DROP FUNCTION IF EXISTS public.calculate_cost_adjustment(SMALLINT);

CREATE OR REPLACE FUNCTION public.calculate_cost_adjustment(p_period_id SMALLINT)
RETURNS VOID AS $$
DECLARE
    v_begin_date DATE;
    v_end_date DATE;
BEGIN
    -- Get period dates
    SELECT "BeginDate", "EndDate" 
    INTO v_begin_date, v_end_date
    FROM ref_period 
    WHERE "PeriodId" = p_period_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Period ID % not found', p_period_id;
    END IF;
    
    -- Step 1: Calculate weighted average cost per inventory item
    -- Using UNION to combine beginning balance and purchase transactions
    WITH average_costs AS (
        SELECT 
            accountid,
            inventoryid,
            SUM(quantity) AS total_quantity,
            SUM(total_cost) AS total_cost,
            SUM(total_cost) / SUM(quantity) AS average_cost
        FROM (
            -- Beginning balance data
            SELECT 
                "AccountId" AS accountid,
                "InventoryId" AS inventoryid,
                "Quantity" AS quantity,
                "UnitCost" AS unit_cost,
                ("Quantity" * "UnitCost") AS total_cost
            FROM inv_beginning_balance
            WHERE "IsDelete" = false
            
            UNION ALL
            
            -- Purchase transactions (DocumentTypeId = 5)
            SELECT 
                id."AccountId" AS accountid,
                idi."InventoryId" AS inventoryid,
                idi."Quantity" AS quantity,
                idi."UnitCost" AS unit_cost,
                (idi."Quantity" * idi."UnitCost") AS total_cost
            FROM inv_document id
            INNER JOIN inv_document_item idi ON id."DocumentId" = idi."DocumentId"
            WHERE id."DocumentTypeId" = 5
                AND id."DocumentDate" <= v_end_date
                AND id."IsDelete" = false
        ) combined_data
        GROUP BY accountid, inventoryid
        HAVING SUM(quantity) > 0
    )
    -- Step 2: Update inv_document_item with new average costs
    UPDATE inv_document_item 
    SET "UnitCost" = ac.average_cost
    FROM inv_document id, average_costs ac
    WHERE inv_document_item."DocumentId" = id."DocumentId"
        AND id."AccountId" = ac.accountid 
        AND inv_document_item."InventoryId" = ac.inventoryid
        AND id."DocumentTypeId" IN (6, 7, 9)
        AND id."DocumentDate" <= v_end_date
        AND id."IsDelete" = false;
    
    -- Step 3: Calculate new document totals and update inv_document_detail
    WITH document_totals AS (
        SELECT 
            idi."DocumentId",
            SUM(idi."UnitCost" * idi."Quantity") AS document_total
        FROM inv_document_item idi
        INNER JOIN inv_document id ON idi."DocumentId" = id."DocumentId"
        WHERE id."DocumentTypeId" IN (6, 7, 9)
            AND id."DocumentDate" <= v_end_date
            AND id."IsDelete" = false
        GROUP BY idi."DocumentId"
    )
    UPDATE inv_document_detail 
    SET 
        "CurrencyAmount" = dt.document_total,
        "DebitAmount" = CASE 
            WHEN "IsDebit" = true THEN dt.document_total 
            ELSE "DebitAmount" 
        END,
        "CreditAmount" = CASE 
            WHEN "IsDebit" = false THEN dt.document_total 
            ELSE "CreditAmount" 
        END        
    FROM document_totals dt
    WHERE inv_document_detail."DocumentId" = dt."DocumentId";
    
END;
$$ LANGUAGE plpgsql;

-- Comment on function
COMMENT ON FUNCTION calculate_cost_adjustment(SMALLINT) IS 
'Calculates weighted average cost for inventory items based on beginning balance and purchase transactions.
Updates UnitCost in inv_document_item and DebitAmount/CreditAmount in inv_document_detail for outbound transactions (DocumentTypeId 6, 7, 9).
Performs updates only, no return values.';