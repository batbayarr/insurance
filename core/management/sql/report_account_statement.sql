-- PostgreSQL Account Statement Function
-- This function returns transaction details for a specific account within a date range
-- Parameters: AccountId INTEGER, beginDate DATE, EndDate DATE
-- Returns: DocumentDate, DocumentNo, DocumentId, DocumentTypeId, DocumentSource, ClientName, Description, CurrencyName, CurrencyExchange, CurrencyAmount, DebitAmount, CreditAmount, AccountCode

-- Drop the function if it exists
DROP FUNCTION IF EXISTS public.report_account_statement(INTEGER, DATE, DATE);

CREATE OR REPLACE FUNCTION public.report_account_statement(
    AccountId INTEGER,
    beginDate DATE,
    EndDate DATE
)
RETURNS TABLE (
    DocumentDate DATE,
    DocumentNo VARCHAR(50),
    DocumentId INTEGER,
    DocumentTypeId SMALLINT,
    DocumentSource VARCHAR(10),
    ClientName VARCHAR(200),
    Description TEXT,
    CurrencyName VARCHAR(50),
    CurrencyExchange NUMERIC(10,4),
    CurrencyAmount NUMERIC(24,6),
    DebitAmount NUMERIC(24,6),
    CreditAmount NUMERIC(24,6),
    AccountCode VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    -- Cash Document Details
    SELECT 
        cd."DocumentDate",
        cd."DocumentNo",
        cd."DocumentId",
        cd."DocumentTypeId",
        'cash'::VARCHAR(10) AS DocumentSource,
        COALESCE(c."ClientName", '') AS ClientName,
        COALESCE(cd."Description", '')::TEXT AS Description,
        COALESCE(cur."Currency_name", '') AS CurrencyName,
        COALESCE(cdd."CurrencyExchange", 1.0000) AS CurrencyExchange,
        COALESCE(cdd."CurrencyAmount", 0) AS CurrencyAmount,
        COALESCE(cdd."DebitAmount", 0) AS DebitAmount,
        COALESCE(cdd."CreditAmount", 0) AS CreditAmount,
        COALESCE(a."AccountCode", '') AS AccountCode
    FROM cash_document cd
    INNER JOIN cash_document_detail cdd ON cd."DocumentId" = cdd."DocumentId"
    LEFT JOIN ref_account a ON cdd."AccountId" = a."AccountId"
    LEFT JOIN ref_client c ON cdd."ClientId" = c."ClientId"
    LEFT JOIN ref_currency cur ON cdd."CurrencyId" = cur."CurrencyId"
    WHERE cd."DocumentId" IN (
        SELECT DISTINCT "DocumentId" 
        FROM cash_document_detail 
        WHERE "AccountId" = AccountId
    )
        AND cd."DocumentDate" >= beginDate
        AND cd."DocumentDate" <= EndDate
        AND cd."IsDelete" = false
    
    UNION ALL
    
    -- Inventory Document Details
    SELECT 
        id."DocumentDate",
        id."DocumentNo",
        id."DocumentId",
        id."DocumentTypeId",
        'inv'::VARCHAR(10) AS DocumentSource,
        COALESCE(c."ClientName", '') AS ClientName,
        COALESCE(id."Description", '')::TEXT AS Description,
        COALESCE(cur."Currency_name", '') AS CurrencyName,
        COALESCE(idd."CurrencyExchange", 1.0000) AS CurrencyExchange,
        COALESCE(idd."CurrencyAmount", 0) AS CurrencyAmount,
        COALESCE(idd."DebitAmount", 0) AS DebitAmount,
        COALESCE(idd."CreditAmount", 0) AS CreditAmount,
        COALESCE(a."AccountCode", '') AS AccountCode
    FROM inv_document id
    INNER JOIN inv_document_detail idd ON id."DocumentId" = idd."DocumentId"
    LEFT JOIN ref_account a ON idd."AccountId" = a."AccountId"
    LEFT JOIN ref_client c ON idd."ClientId" = c."ClientId"
    LEFT JOIN ref_currency cur ON idd."CurrencyId" = cur."CurrencyId"
    WHERE id."DocumentId" IN (
        SELECT DISTINCT "DocumentId" 
        FROM inv_document_detail 
        WHERE "AccountId" = AccountId
    )
        AND id."DocumentDate" >= beginDate
        AND id."DocumentDate" <= EndDate
        AND id."IsDelete" = false
    
    UNION ALL
    
    -- Asset Document Details
    SELECT 
        ad."DocumentDate",
        ad."DocumentNo",
        ad."DocumentId",
        ad."DocumentTypeId",
        'ast'::VARCHAR(10) AS DocumentSource,
        COALESCE(c."ClientName", '') AS ClientName,
        COALESCE(ad."Description", '')::TEXT AS Description,
        COALESCE(cur."Currency_name", '') AS CurrencyName,
        COALESCE(add."CurrencyExchange", 1.0000) AS CurrencyExchange,
        COALESCE(add."CurrencyAmount", 0) AS CurrencyAmount,
        COALESCE(add."DebitAmount", 0) AS DebitAmount,
        COALESCE(add."CreditAmount", 0) AS CreditAmount,
        COALESCE(a."AccountCode", '') AS AccountCode
    FROM ast_document ad
    INNER JOIN ast_document_detail add ON ad."DocumentId" = add."DocumentId"
    LEFT JOIN ref_account a ON add."AccountId" = a."AccountId"
    LEFT JOIN ref_client c ON add."ClientId" = c."ClientId"
    LEFT JOIN ref_currency cur ON add."CurrencyId" = cur."CurrencyId"
    WHERE ad."DocumentId" IN (
        SELECT DISTINCT "DocumentId" 
        FROM ast_document_detail 
        WHERE "AccountId" = AccountId
    )
        AND ad."DocumentDate" >= beginDate
        AND ad."DocumentDate" <= EndDate
        AND ad."IsDelete" = false
    
    ORDER BY "DocumentDate", "DocumentNo";
    
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT * FROM report_account_statement(1, '2025-01-01', '2025-12-31');


