-- Test script for trial balance function
-- Run this to test the function step by step

-- 1. First, check if the function exists
SELECT routine_name, routine_type 
FROM information_schema.routines 
WHERE routine_name = 'calculate_trial_balance';

-- 2. Test with a simple date range
SELECT * FROM calculate_trial_balance('2025-01-01', '2025-12-31') LIMIT 5;

-- 3. Check if we have data in the beginning balance tables
SELECT 'cash_beginning_balance' as table_name, COUNT(*) as record_count 
FROM cash_beginning_balance 
WHERE "IsDelete" = false
UNION ALL
SELECT 'inv_beginning_balance' as table_name, COUNT(*) as record_count 
FROM inv_beginning_balance 
WHERE "IsDelete" = false
UNION ALL
SELECT 'ast_beginning_balance' as table_name, COUNT(*) as record_count 
FROM ast_beginning_balance 
WHERE "IsDelete" = false;

-- 4. Check if we have accounts
SELECT COUNT(*) as account_count FROM ref_account WHERE "IsDelete" = false;

-- 5. Check if we have account types
SELECT "AccountTypeId", "AccountTypeName", "IsActive" 
FROM ref_account_type 
ORDER BY "AccountTypeId";

-- 6. Test a simple query to see if the basic structure works
SELECT 
    ra."AccountId",
    ra."AccountCode", 
    ra."AccountName",
    rat."AccountTypeName",
    rat."IsActive"
FROM ref_account ra
INNER JOIN ref_account_type rat ON ra."AccountTypeId" = rat."AccountTypeId"
WHERE ra."IsDelete" = false
ORDER BY ra."AccountCode"
LIMIT 10;
