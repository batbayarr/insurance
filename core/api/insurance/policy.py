"""
Policy API endpoints using Django Ninja
"""
from ninja import Router
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import AnonymousUser
from core.models import (
    Ref_Policy_Template,
    Ref_Template_Product,
    Ref_Template_Product_Item,
    Ref_Template_Product_Item_Risk
)
from .schemas import (
    PolicyTemplateSchema,
    PolicyTemplateCreateSchema,
    PolicyTemplateUpdateSchema,
    PolicyTemplateDetailIntegratedSchema,
    SuccessResponse,
    ErrorResponse
)

router = Router(tags=["Policy"])


def check_auth(request):
    """Helper to check if user is authenticated"""
    # Django Ninja with django_auth calls the auth function and sets request.auth
    # The django_auth function in auth.py returns request.user if authenticated
    # Check request.auth first (set by Django Ninja), then fallback to request.user
    user = getattr(request, 'auth', None)
    if user is None:
        # Fallback: check request.user directly (Django session auth)
        user = getattr(request, 'user', None)
    
    # If still no user, check if user is authenticated via Django's is_authenticated
    if user is None or isinstance(user, AnonymousUser) or not getattr(user, 'is_authenticated', False):
        from ninja.errors import HttpError
        raise HttpError(401, "Authentication required")
    return user


@router.get("/templates", response=List[PolicyTemplateSchema])
def list_policy_templates(request):
    """
    List all policy templates
    """
    check_auth(request)
    templates = Ref_Policy_Template.objects.all().order_by('PolicyTemplateName')
    return list(templates)


@router.get("/templates/integrated", response=List[PolicyTemplateDetailIntegratedSchema])
def list_policy_templates_integrated(request):
    """
    Get all policy templates in an integrated format.
    Returns one row per template-product-item-risk combination using the new template structure:
    - ins_ref_template (Ref_Policy_Template)
    - ins_ref_template_product (Ref_Template_Product)
    - ins_ref_template_product_item (Ref_Template_Product_Item)
    - ins_ref_template_product_item_risk (Ref_Template_Product_Item_Risk)
    """
    # Explicitly check authentication - django_auth might not raise 401 automatically
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        from ninja.errors import HttpError
        raise HttpError(401, "Authentication required")
    
    try:
        # Query all template product item risks with all related data
        template_risks = Ref_Template_Product_Item_Risk.objects.select_related(
            'TemplateProductItemId__TemplateProductId__TemplateId',
            'TemplateProductItemId__TemplateProductId__ProductId__ProductTypeId__ProductGroupId',
            'TemplateProductItemId__TemplateProductId__ProductId__ProductTypeId',
            'TemplateProductItemId__TemplateProductId__ProductId',
            'TemplateProductItemId__ItemId__ItemTypeId',
            'TemplateProductItemId__ItemId',
            'RiskId__RiskTypeId',
            'RiskId'
        ).filter(
            TemplateProductItemId__TemplateProductId__TemplateId__IsDelete=False
        ).order_by(
            'TemplateProductItemId__TemplateProductId__TemplateId__PolicyTemplateName',
            'TemplateProductItemId__TemplateProductId__ProductId__ProductName',
            'TemplateProductItemId__ItemId__ItemName',
            'RiskId__RiskName'
        )
        
        # Build integrated data structure (one row per template-product-item-risk combination)
        integrated_data = []
        templates_with_details = set()
        
        for risk in template_risks:
            try:
                template = risk.TemplateProductItemId.TemplateProductId.TemplateId
                template_id = template.PolicyTemplateId
                templates_with_details.add(template_id)
                
                product = risk.TemplateProductItemId.TemplateProductId.ProductId
                product_type = getattr(product, 'ProductTypeId', None)
                product_group = getattr(product_type, 'ProductGroupId', None) if product_type else None
                
                item = risk.TemplateProductItemId.ItemId
                item_type = getattr(item, 'ItemTypeId', None)
                
                risk_obj = risk.RiskId
                risk_type = getattr(risk_obj, 'RiskTypeId', None)
                
                row_data = {
                    'PolicyTemplateId': int(template_id),
                    'PolicyTemplateName': str(template.PolicyTemplateName) if template.PolicyTemplateName else '',
                    'ProductGroupName': str(product_group.ProductGroupName) if product_group and product_group.ProductGroupName else None,
                    'ProductTypeName': str(product_type.ProductTypeName) if product_type and product_type.ProductTypeName else None,
                    'ProductName': str(product.ProductName) if product and product.ProductName else None,
                    'RiskTypeName': str(risk_type.RiskTypeName) if risk_type and risk_type.RiskTypeName else None,
                    'RiskName': str(risk_obj.RiskName) if risk_obj and risk_obj.RiskName else None,
                    'ItemTypeName': str(item_type.ItemTypeName) if item_type and item_type.ItemTypeName else None,
                    'ItemName': str(item.ItemName) if item and item.ItemName else None,
                    'CommPercent': float(risk.CommPercent) if risk.CommPercent is not None else None,
                }
            except AttributeError as attr_error:
                # Skip this row if any related object is missing
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Missing related object for template risk {risk.TemplateProductItemRiskId}: {str(attr_error)}')
                continue
            
            # Create schema instance to ensure proper validation
            try:
                schema_instance = PolicyTemplateDetailIntegratedSchema(**row_data)
                integrated_data.append(schema_instance)
            except Exception as schema_error:
                # If validation fails, log and skip this row
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Schema validation error for template risk {risk.TemplateProductItemRiskId}: {str(schema_error)}')
                logger.warning(f'Row data: {row_data}')
                continue
        
        # Also include templates that have no products/items/risks (templates without any details)
        
        # Get all templates and add those without details
        all_templates = Ref_Policy_Template.objects.filter(
            IsDelete=False
        ).order_by('PolicyTemplateName')
        
        for template in all_templates:
            if template.PolicyTemplateId not in templates_with_details:
                # Template without details - return only template information
                row_data = {
                    'PolicyTemplateId': int(template.PolicyTemplateId),
                    'PolicyTemplateName': str(template.PolicyTemplateName) if template.PolicyTemplateName else '',
                    'ProductGroupName': None,
                    'ProductTypeName': None,
                    'ProductName': None,
                    'RiskTypeName': None,
                    'RiskName': None,
                    'ItemTypeName': None,
                    'ItemName': None,
                    'CommPercent': None,
                }
                # Create schema instance to ensure proper validation
                try:
                    schema_instance = PolicyTemplateDetailIntegratedSchema(**row_data)
                    integrated_data.append(schema_instance)
                except Exception as schema_error:
                    # If validation fails, log and skip this row
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f'Schema validation error for template {template.PolicyTemplateId}: {str(schema_error)}')
                    logger.warning(f'Row data: {row_data}')
                    continue
        
        # Return empty list if no data (Django Ninja handles this fine)
        if not integrated_data:
            return []
        
        # Return the list of schema instances
        # Django Ninja will serialize them automatically
        return integrated_data
    except HttpError:
        # Re-raise HTTP errors as-is
        raise
    except Exception as e:
        # Log the error and return a proper error response
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in list_policy_templates_integrated: {str(e)}', exc_info=True)
        from ninja.errors import HttpError
        # Return 500 for server errors, not 422
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.get("/templates/{template_id}", response=PolicyTemplateSchema)
def get_policy_template(request, template_id: int):
    """
    Get a specific policy template by ID
    """
    check_auth(request)
    template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id)
    return template


@router.post("/templates", response={200: PolicyTemplateSchema, 400: ErrorResponse})
def create_policy_template(request, payload: PolicyTemplateCreateSchema):
    """
    Create a new policy template
    """
    check_auth(request)
    try:
        template = Ref_Policy_Template.objects.create(
            PolicyTemplateName=payload.PolicyTemplateName,
            PolicyTemplateCode=payload.PolicyTemplateCode,
            IsActive=payload.IsActive,
            CreatedBy=check_auth(request),
            ModifiedBy=check_auth(request)
        )
        return 200, template
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.put("/templates/{template_id}", response={200: PolicyTemplateSchema, 400: ErrorResponse})
def update_policy_template(request, template_id: int, payload: PolicyTemplateUpdateSchema):
    """
    Update an existing policy template
    """
    check_auth(request)
    try:
        template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id)
        
        if payload.PolicyTemplateName is not None:
            template.PolicyTemplateName = payload.PolicyTemplateName
        if payload.PolicyTemplateCode is not None:
            template.PolicyTemplateCode = payload.PolicyTemplateCode
        if payload.IsActive is not None:
            template.IsActive = payload.IsActive
        
        template.ModifiedBy = check_auth(request)
        template.save()
        
        return 200, template
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.delete("/templates/{template_id}", response={200: SuccessResponse, 400: ErrorResponse})
def delete_policy_template(request, template_id: int):
    """
    Delete a policy template
    """
    check_auth(request)
    try:
        template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id)
        template.delete()
        return 200, SuccessResponse(message="Policy template deleted successfully")
    except Exception as e:
        return 400, ErrorResponse(error=str(e))

