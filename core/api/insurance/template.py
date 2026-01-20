"""
Template Tree API endpoints using Django Ninja
Manages CRUD operations for Template → Product → Item → Risk hierarchy
"""
from ninja import Router
from typing import List, Optional
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import AnonymousUser
from django.db.models import Prefetch
from core.models import (
    Ref_Policy_Template,
    Ref_Template_Product,
    Ref_Template_Product_Item,
    Ref_Template_Product_Item_Risk
)
from .schemas import (
    TemplateSchema,
    TemplateCreateSchema,
    TemplateUpdateSchema,
    TemplateProductSchema,
    TemplateProductCreateSchema,
    TemplateProductUpdateSchema,
    TemplateProductItemSchema,
    TemplateProductItemCreateSchema,
    TemplateProductItemUpdateSchema,
    TemplateProductItemRiskSchema,
    TemplateProductItemRiskCreateSchema,
    TemplateProductItemRiskUpdateSchema,
    TemplateTreeSchema,
    TemplateProductTreeSchema,
    TemplateProductItemTreeSchema,
    CombinedDetailSchema,
    SuccessResponse,
    ErrorResponse
)

router = Router(tags=["Template Tree"])


def check_auth(request):
    """Helper to check if user is authenticated"""
    user = getattr(request, 'auth', None)
    if user is None:
        user = getattr(request, 'user', None)
    
    if user is None or isinstance(user, AnonymousUser) or not getattr(user, 'is_authenticated', False):
        from ninja.errors import HttpError
        raise HttpError(401, "Authentication required")
    return user


# ==================== TEMPLATE ENDPOINTS ====================

@router.get("/templates", response=List[TemplateSchema])
def list_templates(request):
    """List all templates"""
    try:
        check_auth(request)
        templates = Ref_Policy_Template.objects.filter(IsDelete=False).order_by('PolicyTemplateName')
        # Convert QuerySet to list for proper serialization
        return [template for template in templates]
    except Exception as e:
        import traceback
        from .schemas import ErrorResponse
        error_trace = traceback.format_exc()
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Error in list_templates: {str(e)}\n{error_trace}')
        # Return error response
        from ninja.errors import HttpError
        raise HttpError(500, f"Internal server error: {str(e)}")


@router.get("/templates/{template_id}", response=TemplateSchema)
def get_template(request, template_id: int):
    """Get a specific template by ID"""
    check_auth(request)
    template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id, IsDelete=False)
    return template


@router.post("/templates", response={200: TemplateSchema, 400: ErrorResponse})
def create_template(request, payload: TemplateCreateSchema):
    """Create a new template"""
    check_auth(request)
    try:
        template = Ref_Policy_Template.objects.create(
            PolicyTemplateName=payload.PolicyTemplateName,
            Description=payload.Description,
            IsActive=payload.IsActive,
            FilePath=payload.FilePath,
            CreatedBy=check_auth(request),
            ModifiedBy=check_auth(request)
        )
        return 200, template
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.put("/templates/{template_id}", response={200: TemplateSchema, 400: ErrorResponse})
def update_template(request, template_id: int, payload: TemplateUpdateSchema):
    """Update an existing template"""
    check_auth(request)
    try:
        template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id, IsDelete=False)
        
        if payload.PolicyTemplateName is not None:
            template.PolicyTemplateName = payload.PolicyTemplateName
        if payload.Description is not None:
            template.Description = payload.Description
        if payload.IsActive is not None:
            template.IsActive = payload.IsActive
        if payload.FilePath is not None:
            template.FilePath = payload.FilePath
        
        template.ModifiedBy = check_auth(request)
        template.save()
        
        return 200, template
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.delete("/templates/{template_id}", response={200: SuccessResponse, 400: ErrorResponse})
def delete_template(request, template_id: int):
    """Delete a template (soft delete)"""
    check_auth(request)
    try:
        template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id, IsDelete=False)
        template.IsDelete = True
        template.ModifiedBy = check_auth(request)
        template.save()
        return 200, SuccessResponse(message="Template deleted successfully")
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


# ==================== TREE STRUCTURE ENDPOINT ====================
# This must come BEFORE parameterized routes to avoid routing conflicts

@router.get("/templates/tree", response=List[TemplateTreeSchema])
def get_template_tree(request):
    """Get complete template tree structure with all nested relationships"""
    check_auth(request)
    
    # Optimized query with all prefetches
    templates = Ref_Policy_Template.objects.filter(
        IsDelete=False
    ).prefetch_related(
        Prefetch(
            'template_products',
            queryset=Ref_Template_Product.objects.select_related('ProductId').prefetch_related(
                Prefetch(
                    'template_product_items',
                    queryset=Ref_Template_Product_Item.objects.select_related('ItemId').prefetch_related(
                        Prefetch(
                            'template_product_item_risks',
                            queryset=Ref_Template_Product_Item_Risk.objects.select_related('RiskId')
                        )
                    )
                )
            )
        )
    ).order_by('PolicyTemplateName')
    
    result = []
    for template in templates:
        products_data = []
        for tp in template.template_products.all():
            items_data = []
            for tpi in tp.template_product_items.all():
                risks_data = []
                for tpir in tpi.template_product_item_risks.all():
                    comm_percent = float(tpir.CommPercent) if tpir.CommPercent is not None else None
                    risks_data.append({
                        'TemplateProductItemRiskId': tpir.TemplateProductItemRiskId,
                        'TemplateProductItemId': tpir.TemplateProductItemId.TemplateProductItemId,
                        'RiskId': tpir.RiskId.RiskId,
                        'CommPercent': comm_percent,
                        'RiskName': tpir.RiskId.RiskName,
                        'RiskCode': tpir.RiskId.RiskCode
                    })
                
                items_data.append({
                    'TemplateProductItemId': tpi.TemplateProductItemId,
                    'TemplateProductId': tpi.TemplateProductId.TemplateProductId,
                    'ItemId': tpi.ItemId.ItemId,
                    'ItemName': tpi.ItemId.ItemName,
                    'ItemCode': tpi.ItemId.ItemCode,
                    'risks': risks_data
                })
            
            products_data.append({
                'TemplateProductId': tp.TemplateProductId,
                'TemplateId': tp.TemplateId.PolicyTemplateId,
                'ProductId': tp.ProductId.ProductId,
                'ProductName': tp.ProductId.ProductName,
                'ProductCode': tp.ProductId.ProductCode,
                'items': items_data
            })
        
        result.append({
            'PolicyTemplateId': template.PolicyTemplateId,
            'PolicyTemplateName': template.PolicyTemplateName,
            'Description': template.Description,
            'IsActive': template.IsActive,
            'products': products_data
        })
    
    return result


# ==================== COMBINED DETAIL ENDPOINT ====================

@router.get("/templates/{template_id}/combined-details", response=List[CombinedDetailSchema])
def get_combined_details(request, template_id: int):
    """Get combined/flattened view of all template relationships"""
    check_auth(request)
    get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id, IsDelete=False)
    
    # Get all template products with their items and risks
    template_products = Ref_Template_Product.objects.filter(
        TemplateId=template_id
    ).select_related('ProductId').prefetch_related(
        Prefetch(
            'template_product_items',
            queryset=Ref_Template_Product_Item.objects.select_related('ItemId').prefetch_related(
                Prefetch(
                    'template_product_item_risks',
                    queryset=Ref_Template_Product_Item_Risk.objects.select_related('RiskId')
                )
            )
        )
    )
    
    result = []
    for tp in template_products:
        # If no items, add product-only row
        if not tp.template_product_items.exists():
            result.append(CombinedDetailSchema(
                TemplateProductId=tp.TemplateProductId,
                TemplateProductItemId=None,
                TemplateProductItemRiskId=None,
                ProductId=tp.ProductId.ProductId,
                ProductName=tp.ProductId.ProductName,
                ProductCode=tp.ProductId.ProductCode,
                ItemId=None,
                ItemName=None,
                ItemCode=None,
                RiskId=None,
                RiskName=None,
                RiskCode=None,
                CommPercent=None
            ))
        else:
            for tpi in tp.template_product_items.all():
                # If no risks, add product-item row
                if not tpi.template_product_item_risks.exists():
                    result.append(CombinedDetailSchema(
                        TemplateProductId=tp.TemplateProductId,
                        TemplateProductItemId=tpi.TemplateProductItemId,
                        TemplateProductItemRiskId=None,
                        ProductId=tp.ProductId.ProductId,
                        ProductName=tp.ProductId.ProductName,
                        ProductCode=tp.ProductId.ProductCode,
                        ItemId=tpi.ItemId.ItemId,
                        ItemName=tpi.ItemId.ItemName,
                        ItemCode=tpi.ItemId.ItemCode,
                        RiskId=None,
                        RiskName=None,
                        RiskCode=None,
                        CommPercent=None
                    ))
                else:
                    # Add product-item-risk rows
                    for tpir in tpi.template_product_item_risks.all():
                        comm_percent = float(tpir.CommPercent) if tpir.CommPercent is not None else None
                        result.append(CombinedDetailSchema(
                            TemplateProductId=tp.TemplateProductId,
                            TemplateProductItemId=tpi.TemplateProductItemId,
                            TemplateProductItemRiskId=tpir.TemplateProductItemRiskId,
                            ProductId=tp.ProductId.ProductId,
                            ProductName=tp.ProductId.ProductName,
                            ProductCode=tp.ProductId.ProductCode,
                            ItemId=tpi.ItemId.ItemId,
                            ItemName=tpi.ItemId.ItemName,
                            ItemCode=tpi.ItemId.ItemCode,
                            RiskId=tpir.RiskId.RiskId,
                            RiskName=tpir.RiskId.RiskName,
                            RiskCode=tpir.RiskId.RiskCode,
                            CommPercent=comm_percent
                        ))
    
    return result


# ==================== TEMPLATE PRODUCT ENDPOINTS ====================
# Note: Specific routes (like /templates/tree) must come before parameterized routes

@router.get("/templates/{template_id}/products", response=List[TemplateProductSchema])
def list_template_products(request, template_id: int):
    """List all products for a specific template"""
    check_auth(request)
    get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id, IsDelete=False)
    products = Ref_Template_Product.objects.filter(
        TemplateId=template_id
    ).select_related('ProductId').order_by('ProductId__ProductName')
    
    result = []
    for tp in products:
        product_name = tp.ProductId.ProductName if tp.ProductId.ProductName else None
        product_code = tp.ProductId.ProductCode if tp.ProductId.ProductCode else None
        result.append(TemplateProductSchema(
            TemplateProductId=tp.TemplateProductId,
            TemplateId=tp.TemplateId.PolicyTemplateId,
            ProductId=tp.ProductId.ProductId,
            ProductName=product_name,
            ProductCode=product_code
        ))
    return result


@router.post("/templates/{template_id}/products", response={200: TemplateProductSchema, 400: ErrorResponse})
def create_template_product(request, template_id: int, payload: TemplateProductCreateSchema):
    """Create a new template product"""
    check_auth(request)
    try:
        template = get_object_or_404(Ref_Policy_Template, PolicyTemplateId=template_id, IsDelete=False)
        from core.models import Ref_Product
        product = get_object_or_404(Ref_Product, ProductId=payload.ProductId)
        
        # Check if already exists
        if Ref_Template_Product.objects.filter(TemplateId=template, ProductId=product).exists():
            return 400, ErrorResponse(error="This product is already associated with this template")
        
        template_product = Ref_Template_Product.objects.create(
            TemplateId=template,
            ProductId=product
        )
        
        return 200, {
            'TemplateProductId': template_product.TemplateProductId,
            'TemplateId': template_product.TemplateId.PolicyTemplateId,
            'ProductId': template_product.ProductId.ProductId,
            'ProductName': template_product.ProductId.ProductName,
            'ProductCode': template_product.ProductId.ProductCode
        }
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.put("/products/{product_id}", response={200: TemplateProductSchema, 400: ErrorResponse})
def update_template_product(request, product_id: int, payload: TemplateProductUpdateSchema):
    """Update an existing template product"""
    check_auth(request)
    try:
        template_product = get_object_or_404(Ref_Template_Product, TemplateProductId=product_id)
        
        if payload.ProductId is not None:
            from core.models import Ref_Product
            product = get_object_or_404(Ref_Product, ProductId=payload.ProductId)
            template_product.ProductId = product
            template_product.save()
        
        return 200, {
            'TemplateProductId': template_product.TemplateProductId,
            'TemplateId': template_product.TemplateId.PolicyTemplateId,
            'ProductId': template_product.ProductId.ProductId,
            'ProductName': template_product.ProductId.ProductName,
            'ProductCode': template_product.ProductId.ProductCode
        }
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.delete("/products/{product_id}", response={200: SuccessResponse, 400: ErrorResponse})
def delete_template_product(request, product_id: int):
    """Delete a template product"""
    check_auth(request)
    try:
        template_product = get_object_or_404(Ref_Template_Product, TemplateProductId=product_id)
        template_product.delete()
        return 200, SuccessResponse(message="Template product deleted successfully")
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


# ==================== TEMPLATE PRODUCT ITEM ENDPOINTS ====================

@router.get("/products/{product_id}/items", response=List[TemplateProductItemSchema])
def list_template_product_items(request, product_id: int):
    """List all items for a specific template product"""
    check_auth(request)
    get_object_or_404(Ref_Template_Product, TemplateProductId=product_id)
    items = Ref_Template_Product_Item.objects.filter(
        TemplateProductId=product_id
    ).select_related('ItemId').order_by('ItemId__ItemName')
    
    result = []
    for tpi in items:
        result.append({
            'TemplateProductItemId': tpi.TemplateProductItemId,
            'TemplateProductId': tpi.TemplateProductId.TemplateProductId,
            'ItemId': tpi.ItemId.ItemId,
            'ItemName': tpi.ItemId.ItemName,
            'ItemCode': tpi.ItemId.ItemCode
        })
    return result


@router.post("/products/{product_id}/items", response={200: TemplateProductItemSchema, 400: ErrorResponse})
def create_template_product_item(request, product_id: int, payload: TemplateProductItemCreateSchema):
    """Create a new template product item"""
    check_auth(request)
    try:
        template_product = get_object_or_404(Ref_Template_Product, TemplateProductId=product_id)
        from core.models import Ref_Item
        item = get_object_or_404(Ref_Item, ItemId=payload.ItemId)
        
        # Check if already exists
        if Ref_Template_Product_Item.objects.filter(TemplateProductId=template_product, ItemId=item).exists():
            return 400, ErrorResponse(error="This item is already associated with this template product")
        
        template_product_item = Ref_Template_Product_Item.objects.create(
            TemplateProductId=template_product,
            ItemId=item
        )
        
        return 200, {
            'TemplateProductItemId': template_product_item.TemplateProductItemId,
            'TemplateProductId': template_product_item.TemplateProductId.TemplateProductId,
            'ItemId': template_product_item.ItemId.ItemId,
            'ItemName': template_product_item.ItemId.ItemName,
            'ItemCode': template_product_item.ItemId.ItemCode
        }
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.put("/items/{item_id}", response={200: TemplateProductItemSchema, 400: ErrorResponse})
def update_template_product_item(request, item_id: int, payload: TemplateProductItemUpdateSchema):
    """Update an existing template product item"""
    check_auth(request)
    try:
        template_product_item = get_object_or_404(Ref_Template_Product_Item, TemplateProductItemId=item_id)
        
        if payload.ItemId is not None:
            from core.models import Ref_Item
            item = get_object_or_404(Ref_Item, ItemId=payload.ItemId)
            template_product_item.ItemId = item
            template_product_item.save()
        
        return 200, {
            'TemplateProductItemId': template_product_item.TemplateProductItemId,
            'TemplateProductId': template_product_item.TemplateProductId.TemplateProductId,
            'ItemId': template_product_item.ItemId.ItemId,
            'ItemName': template_product_item.ItemId.ItemName,
            'ItemCode': template_product_item.ItemId.ItemCode
        }
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.delete("/items/{item_id}", response={200: SuccessResponse, 400: ErrorResponse})
def delete_template_product_item(request, item_id: int):
    """Delete a template product item"""
    check_auth(request)
    try:
        template_product_item = get_object_or_404(Ref_Template_Product_Item, TemplateProductItemId=item_id)
        template_product_item.delete()
        return 200, SuccessResponse(message="Template product item deleted successfully")
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


# ==================== TEMPLATE PRODUCT ITEM RISK ENDPOINTS ====================

@router.get("/items/{item_id}/risks", response=List[TemplateProductItemRiskSchema])
def list_template_product_item_risks(request, item_id: int):
    """List all risks for a specific template product item"""
    check_auth(request)
    get_object_or_404(Ref_Template_Product_Item, TemplateProductItemId=item_id)
    risks = Ref_Template_Product_Item_Risk.objects.filter(
        TemplateProductItemId=item_id
    ).select_related('RiskId').order_by('RiskId__RiskName')
    
    result = []
    for tpir in risks:
        comm_percent = float(tpir.CommPercent) if tpir.CommPercent is not None else None
        result.append({
            'TemplateProductItemRiskId': tpir.TemplateProductItemRiskId,
            'TemplateProductItemId': tpir.TemplateProductItemId.TemplateProductItemId,
            'RiskId': tpir.RiskId.RiskId,
            'CommPercent': comm_percent,
            'RiskName': tpir.RiskId.RiskName,
            'RiskCode': tpir.RiskId.RiskCode
        })
    return result


@router.post("/items/{item_id}/risks", response={200: TemplateProductItemRiskSchema, 400: ErrorResponse})
def create_template_product_item_risk(request, item_id: int, payload: TemplateProductItemRiskCreateSchema):
    """Create a new template product item risk"""
    check_auth(request)
    try:
        template_product_item = get_object_or_404(Ref_Template_Product_Item, TemplateProductItemId=item_id)
        from core.models import Ref_Risk
        risk = get_object_or_404(Ref_Risk, RiskId=payload.RiskId)
        
        # Check if already exists
        if Ref_Template_Product_Item_Risk.objects.filter(TemplateProductItemId=template_product_item, RiskId=risk).exists():
            return 400, ErrorResponse(error="This risk is already associated with this template product item")
        
        from decimal import Decimal
        comm_percent = Decimal(str(payload.CommPercent)) if payload.CommPercent is not None else None
        
        template_product_item_risk = Ref_Template_Product_Item_Risk.objects.create(
            TemplateProductItemId=template_product_item,
            RiskId=risk,
            CommPercent=comm_percent
        )
        
        comm_percent_float = float(template_product_item_risk.CommPercent) if template_product_item_risk.CommPercent is not None else None
        return 200, {
            'TemplateProductItemRiskId': template_product_item_risk.TemplateProductItemRiskId,
            'TemplateProductItemId': template_product_item_risk.TemplateProductItemId.TemplateProductItemId,
            'RiskId': template_product_item_risk.RiskId.RiskId,
            'CommPercent': comm_percent_float,
            'RiskName': template_product_item_risk.RiskId.RiskName,
            'RiskCode': template_product_item_risk.RiskId.RiskCode
        }
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.put("/risks/{risk_id}", response={200: TemplateProductItemRiskSchema, 400: ErrorResponse})
def update_template_product_item_risk(request, risk_id: int, payload: TemplateProductItemRiskUpdateSchema):
    """Update an existing template product item risk"""
    check_auth(request)
    try:
        template_product_item_risk = get_object_or_404(Ref_Template_Product_Item_Risk, TemplateProductItemRiskId=risk_id)
        
        if payload.RiskId is not None:
            from core.models import Ref_Risk
            risk = get_object_or_404(Ref_Risk, RiskId=payload.RiskId)
            template_product_item_risk.RiskId = risk
        
        if payload.CommPercent is not None:
            from decimal import Decimal
            template_product_item_risk.CommPercent = Decimal(str(payload.CommPercent))
        
        template_product_item_risk.save()
        
        comm_percent_float = float(template_product_item_risk.CommPercent) if template_product_item_risk.CommPercent is not None else None
        return 200, {
            'TemplateProductItemRiskId': template_product_item_risk.TemplateProductItemRiskId,
            'TemplateProductItemId': template_product_item_risk.TemplateProductItemId.TemplateProductItemId,
            'RiskId': template_product_item_risk.RiskId.RiskId,
            'CommPercent': comm_percent_float,
            'RiskName': template_product_item_risk.RiskId.RiskName,
            'RiskCode': template_product_item_risk.RiskId.RiskCode
        }
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


@router.delete("/risks/{risk_id}", response={200: SuccessResponse, 400: ErrorResponse})
def delete_template_product_item_risk(request, risk_id: int):
    """Delete a template product item risk"""
    check_auth(request)
    try:
        template_product_item_risk = get_object_or_404(Ref_Template_Product_Item_Risk, TemplateProductItemRiskId=risk_id)
        template_product_item_risk.delete()
        return 200, SuccessResponse(message="Template product item risk deleted successfully")
    except Exception as e:
        return 400, ErrorResponse(error=str(e))


# ==================== TREE STRUCTURE ENDPOINT ====================

@router.get("/templates/tree", response=List[TemplateTreeSchema])
def get_template_tree(request):
    """Get complete template tree structure with all nested relationships"""
    check_auth(request)
    
    # Optimized query with all prefetches
    templates = Ref_Policy_Template.objects.filter(
        IsDelete=False
    ).prefetch_related(
        Prefetch(
            'template_products',
            queryset=Ref_Template_Product.objects.select_related('ProductId').prefetch_related(
                Prefetch(
                    'template_product_items',
                    queryset=Ref_Template_Product_Item.objects.select_related('ItemId').prefetch_related(
                        Prefetch(
                            'template_product_item_risks',
                            queryset=Ref_Template_Product_Item_Risk.objects.select_related('RiskId')
                        )
                    )
                )
            )
        )
    ).order_by('PolicyTemplateName')
    
    result = []
    for template in templates:
        products_data = []
        for tp in template.template_products.all():
            items_data = []
            for tpi in tp.template_product_items.all():
                risks_data = []
                for tpir in tpi.template_product_item_risks.all():
                    comm_percent = float(tpir.CommPercent) if tpir.CommPercent is not None else None
                    risks_data.append({
                        'TemplateProductItemRiskId': tpir.TemplateProductItemRiskId,
                        'TemplateProductItemId': tpir.TemplateProductItemId.TemplateProductItemId,
                        'RiskId': tpir.RiskId.RiskId,
                        'CommPercent': comm_percent,
                        'RiskName': tpir.RiskId.RiskName,
                        'RiskCode': tpir.RiskId.RiskCode
                    })
                
                items_data.append({
                    'TemplateProductItemId': tpi.TemplateProductItemId,
                    'TemplateProductId': tpi.TemplateProductId.TemplateProductId,
                    'ItemId': tpi.ItemId.ItemId,
                    'ItemName': tpi.ItemId.ItemName,
                    'ItemCode': tpi.ItemId.ItemCode,
                    'risks': risks_data
                })
            
            products_data.append({
                'TemplateProductId': tp.TemplateProductId,
                'TemplateId': tp.TemplateId.PolicyTemplateId,
                'ProductId': tp.ProductId.ProductId,
                'ProductName': tp.ProductId.ProductName,
                'ProductCode': tp.ProductId.ProductCode,
                'items': items_data
            })
        
        result.append({
            'PolicyTemplateId': template.PolicyTemplateId,
            'PolicyTemplateName': template.PolicyTemplateName,
            'Description': template.Description,
            'IsActive': template.IsActive,
            'products': products_data
        })
    
    return result

