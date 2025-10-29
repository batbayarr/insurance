"""
Context processor to make Ref_Constant values available globally in all templates.
"""
from decimal import Decimal
from .utils import get_database_description


def global_constants(request):
    """
    Load system constants from Ref_Constant table and make them available globally.
    Constants are loaded once at startup for optimal performance.
    
    Returns a dictionary with the following constants:
    - COMPANY_NAME: Company name (ConstantID=1)
    - VAT_RATE: VAT rate as decimal for calculations (ConstantID=2)
    - VAT_RATE_PERCENT: VAT rate as percentage string for display
    - DIRECTOR: Director name (ConstantID=3)
    - CHIEF_ACCOUNTANT: Chief Accountant name (ConstantID=4)
    - CASH_ACCOUNTANT: Cash Accountant name (ConstantID=5)
    - CASHIER: Cashier name (ConstantID=6)
    - CONSTANT_7: Hardcoded placeholder (ConstantID=7)
    - CONSTANT_8: Hardcoded placeholder (ConstantID=8)
    - VAT_ACCOUNT_RECEIVABLE: VAT Account Receivable ID (ConstantID=9)
    - VAT_ACCOUNT_PAYABLE: VAT Account Payable ID (ConstantID=10)
    - CONSTANT_11: Hardcoded placeholder (ConstantID=11)
    - CONSTANT_12: Hardcoded placeholder (ConstantID=12)
    - CONSTANT_13: Hardcoded placeholder (ConstantID=13)
    - CONSTANT_14: Hardcoded placeholder (ConstantID=14)
    """
    # Default fallback values
    constants = {
        'COMPANY_NAME': 'Silicon4 Accounting',
        'VAT_RATE': 0.10,  # Decimal for calculations
        'VAT_RATE_PERCENT': '10.00',  # String for display
        'DIRECTOR': '',
        'CHIEF_ACCOUNTANT': '',
        'CASH_ACCOUNTANT': '',
        'CASHIER': '',
        'CONSTANT_7': '',  # Placeholder for any additional constant
        'CONSTANT_8': '',  # Placeholder for any additional constant
        'VAT_ACCOUNT_RECEIVABLE': '8',  # Default VAT Receivable Account ID
        'VAT_ACCOUNT_PAYABLE': '9',     # Default VAT Payable Account ID
        'CONSTANT_11': '',  # Placeholder for any additional constant
        'CONSTANT_12': '',  # Placeholder for any additional constant
        'CONSTANT_13': '',  # Placeholder for any additional constant
        'CONSTANT_14': '',  # Placeholder for any additional constant
    }
    
    try:
        from .models import Ref_Constant
        
        # Fetch all constants we need (including hardcoded 7,8,11,12,13,14)
        constant_mapping = {
            1: 'COMPANY_NAME',
            2: 'VAT_RATE',
            3: 'DIRECTOR',
            4: 'CHIEF_ACCOUNTANT',
            5: 'CASH_ACCOUNTANT',
            6: 'CASHIER',
            7: 'CONSTANT_7',  # Hardcoded placeholder
            8: 'CONSTANT_8',  # Hardcoded placeholder
            9: 'VAT_ACCOUNT_RECEIVABLE',
            10: 'VAT_ACCOUNT_PAYABLE',
            11: 'CONSTANT_11',  # Hardcoded placeholder
            12: 'CONSTANT_12',  # Hardcoded placeholder
            13: 'CONSTANT_13',  # Hardcoded placeholder
            14: 'CONSTANT_14',  # Hardcoded placeholder
        }
        
        # Fetch constants from database
        ref_constants = Ref_Constant.objects.filter(
            ConstantID__in=constant_mapping.keys()
        ).values('ConstantID', 'ConstantName')
        
        # Map database values to constant names
        for ref_const in ref_constants:
            constant_id = ref_const['ConstantID']
            constant_value = ref_const['ConstantName']
            constant_key = constant_mapping[constant_id]
            
            # Special handling for VAT_RATE
            if constant_id == 2:
                try:
                    # Convert VAT percentage to decimal (10 -> 0.10)
                    vat_decimal = float(constant_value) / 100
                    constants['VAT_RATE'] = vat_decimal
                    constants['VAT_RATE_PERCENT'] = constant_value  # Keep original for display
                except (ValueError, TypeError):
                    pass  # Use default fallback
            else:
                constants[constant_key] = constant_value
        
        # Debug logging for VAT accounts
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"VAT_ACCOUNT_RECEIVABLE: {constants.get('VAT_ACCOUNT_RECEIVABLE', 'NOT SET')}")
        logger.info(f"VAT_ACCOUNT_PAYABLE: {constants.get('VAT_ACCOUNT_PAYABLE', 'NOT SET')}")
        
    except Exception as e:
        # Log error but don't crash - use default fallback values
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error loading global constants: {e}. Using default values.")
    
    # Add database description if user is authenticated
    if request.user.is_authenticated:
        try:
            company_code = request.session.get('company_code', '')
            selected_database = request.session.get('selected_database', 'silicon4')
            
            if company_code:
                database_description = get_database_description(company_code, selected_database)
                constants['DATABASE_DESCRIPTION'] = database_description
                constants['COMPANY_CODE'] = company_code
            else:
                constants['DATABASE_DESCRIPTION'] = selected_database
                constants['COMPANY_CODE'] = ''
        except Exception as e:
            # Fallback to database name if error occurs
            constants['DATABASE_DESCRIPTION'] = request.session.get('selected_database', 'silicon4')
            constants['COMPANY_CODE'] = ''
    
    return constants

