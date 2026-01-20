"""
Pydantic schemas for Insurance API
"""
from ninja import Schema
from typing import Optional, List
from datetime import datetime


# Policy Template Schemas
class PolicyTemplateSchema(Schema):
    """Policy Template schema"""
    PolicyTemplateId: int
    PolicyTemplateName: str
    PolicyTemplateCode: Optional[str] = None
    IsActive: bool
    CreatedDate: Optional[datetime] = None
    ModifiedDate: Optional[datetime] = None


class PolicyTemplateCreateSchema(Schema):
    """Schema for creating a policy template"""
    PolicyTemplateName: str
    PolicyTemplateCode: Optional[str] = None
    IsActive: bool = True


class PolicyTemplateUpdateSchema(Schema):
    """Schema for updating a policy template"""
    PolicyTemplateName: Optional[str] = None
    PolicyTemplateCode: Optional[str] = None
    IsActive: Optional[bool] = None


# Policy Schemas (when you implement actual policies)
class PolicySchema(Schema):
    """Policy schema"""
    PolicyId: int
    PolicyNumber: str
    PolicyName: str
    # Add other policy fields as needed


# Response schemas
class SuccessResponse(Schema):
    """Success response schema"""
    success: bool = True
    message: str


class ErrorResponse(Schema):
    """Error response schema"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# Integrated Policy Template Schema for modal display
class PolicyTemplateDetailIntegratedSchema(Schema):
    """Schema for integrated policy template detail row (one row per template-detail combination)"""
    PolicyTemplateId: int
    PolicyTemplateName: str
    ProductGroupName: Optional[str] = None
    ProductTypeName: Optional[str] = None
    ProductName: Optional[str] = None
    RiskTypeName: Optional[str] = None
    RiskName: Optional[str] = None
    ItemTypeName: Optional[str] = None
    ItemName: Optional[str] = None
    CommPercent: Optional[float] = None


# Template Tree Schemas
class TemplateSchema(Schema):
    """Template schema"""
    PolicyTemplateId: int
    PolicyTemplateName: str
    Description: Optional[str] = None
    IsActive: bool
    FilePath: Optional[str] = None
    IsDelete: bool
    CreatedDate: Optional[datetime] = None
    ModifiedDate: Optional[datetime] = None


class TemplateCreateSchema(Schema):
    """Schema for creating a template"""
    PolicyTemplateName: str
    Description: Optional[str] = None
    IsActive: bool = True
    FilePath: Optional[str] = None


class TemplateUpdateSchema(Schema):
    """Schema for updating a template"""
    PolicyTemplateName: Optional[str] = None
    Description: Optional[str] = None
    IsActive: Optional[bool] = None
    FilePath: Optional[str] = None


class TemplateProductSchema(Schema):
    """Template Product schema"""
    TemplateProductId: int
    TemplateId: int
    ProductId: int
    ProductName: Optional[str] = None  # For display
    ProductCode: Optional[str] = None  # For display


class TemplateProductCreateSchema(Schema):
    """Schema for creating a template product"""
    ProductId: int


class TemplateProductUpdateSchema(Schema):
    """Schema for updating a template product"""
    ProductId: Optional[int] = None


class TemplateProductItemSchema(Schema):
    """Template Product Item schema"""
    TemplateProductItemId: int
    TemplateProductId: int
    ItemId: int
    ItemName: Optional[str] = None  # For display
    ItemCode: Optional[str] = None  # For display


class TemplateProductItemCreateSchema(Schema):
    """Schema for creating a template product item"""
    ItemId: int


class TemplateProductItemUpdateSchema(Schema):
    """Schema for updating a template product item"""
    ItemId: Optional[int] = None


class TemplateProductItemRiskSchema(Schema):
    """Template Product Item Risk schema"""
    TemplateProductItemRiskId: int
    TemplateProductItemId: int
    RiskId: int
    CommPercent: Optional[float] = None
    RiskName: Optional[str] = None  # For display
    RiskCode: Optional[str] = None  # For display


class TemplateProductItemRiskCreateSchema(Schema):
    """Schema for creating a template product item risk"""
    RiskId: int
    CommPercent: Optional[float] = None


class TemplateProductItemRiskUpdateSchema(Schema):
    """Schema for updating a template product item risk"""
    RiskId: Optional[int] = None
    CommPercent: Optional[float] = None


class CombinedDetailSchema(Schema):
    """Schema for combined detail view showing flattened template relationships"""
    TemplateProductId: int
    TemplateProductItemId: Optional[int] = None
    TemplateProductItemRiskId: Optional[int] = None
    ProductId: int
    ProductName: Optional[str] = None
    ProductCode: Optional[str] = None
    ItemId: Optional[int] = None
    ItemName: Optional[str] = None
    ItemCode: Optional[str] = None
    RiskId: Optional[int] = None
    RiskName: Optional[str] = None
    RiskCode: Optional[str] = None
    CommPercent: Optional[float] = None


# Tree structure schema for hierarchical display
class TemplateTreeSchema(Schema):
    """Nested tree structure for template hierarchy"""
    PolicyTemplateId: int
    PolicyTemplateName: str
    Description: Optional[str] = None
    IsActive: bool
    products: Optional[List['TemplateProductTreeSchema']] = []


class TemplateProductTreeSchema(Schema):
    """Template Product with nested items"""
    TemplateProductId: int
    TemplateId: int
    ProductId: int
    ProductName: Optional[str] = None
    ProductCode: Optional[str] = None
    items: Optional[List['TemplateProductItemTreeSchema']] = []


class TemplateProductItemTreeSchema(Schema):
    """Template Product Item with nested risks"""
    TemplateProductItemId: int
    TemplateProductId: int
    ItemId: int
    ItemName: Optional[str] = None
    ItemCode: Optional[str] = None
    risks: Optional[List['TemplateProductItemRiskSchema']] = []


# Update forward references
TemplateTreeSchema.model_rebuild()
TemplateProductTreeSchema.model_rebuild()
TemplateProductItemTreeSchema.model_rebuild()