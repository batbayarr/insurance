# Trial Balance Function Installation and Usage

## Installation

To install the trial balance function in your PostgreSQL database:

1. **Connect to your PostgreSQL database** using psql or your preferred database client
2. **Execute the SQL file**:
   ```sql
   \i core/management/sql/calculate_trial_balance.sql
   ```
   
   Or copy and paste the contents of `calculate_trial_balance.sql` directly into your database client.

## Function Usage

### Basic Usage
```sql
SELECT * FROM calculate_trial_balance('2025-02-01', '2025-03-31');
```

### Parameters
- `begindate` (DATE): The start date for the trial balance period
- `enddate` (DATE): The end date for the trial balance period

### Return Columns
- `AccountId`: Account identifier
- `AccountCode`: Account code
- `AccountName`: Account name
- `AccountType`: Account type name
- `BeginningBalanceDebit`: Beginning balance debit amount (as of begindate)
- `BeginningBalanceCredit`: Beginning balance credit amount (as of begindate)
- `DebitAmount`: Total debit transactions during the period
- `CreditAmount`: Total credit transactions during the period
- `EndingBalanceDebit`: Ending balance debit amount (as of enddate)
- `EndingBalanceCredit`: Ending balance credit amount (as of enddate)

## Function Logic

### Beginning Balance Calculation
1. **Starting Balance**: Sums initial balances from:
   - `cash_beginning_balance`: `CurrencyAmount * CurrencyExchange`
   - `inv_beginning_balance`: `Quantity * UnitCost`
   - `ast_beginning_balance`: `Quantity * UnitCost`

2. **Transactions Before Begin Date**: Calculates all transactions before the begindate to determine the beginning balance as of the begindate

3. **Account Type Logic**:
   - **Active accounts** (IsActive=true): Beginning balance goes to debit column
   - **Passive accounts** (IsActive=false): Beginning balance goes to credit column

### Period Transactions
- Sums all debit and credit transactions between begindate and enddate
- Includes transactions from all three document types: cash, inventory, and asset

### Ending Balance Calculation
- **Active accounts**: BeginningBalance + DebitAmount - CreditAmount
- **Passive accounts**: BeginningBalance - DebitAmount + CreditAmount

## Testing

### Test with Sample Data
```sql
-- Test with a specific date range
SELECT * FROM calculate_trial_balance('2025-01-01', '2025-12-31');

-- Test with a shorter period
SELECT * FROM calculate_trial_balance('2025-02-01', '2025-02-28');

-- Filter for specific accounts
SELECT * FROM calculate_trial_balance('2025-02-01', '2025-03-31') 
WHERE AccountCode LIKE '1%';  -- Asset accounts
```

### Verify Results
1. **Check beginning balances**: Ensure they match your expected starting balances plus transactions before the begindate
2. **Verify period transactions**: Compare with your transaction reports for the same period
3. **Validate ending balances**: Ensure they equal beginning balance plus/minus period transactions

## Notes

- The function excludes records where `IsDelete = true`
- All transactions are included regardless of `IsPosted` status
- Negative balances are handled according to account type (active accounts show negative as debit, passive accounts show negative as credit)
- The function returns all accounts, even those with zero balances
