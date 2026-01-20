"""
Pydantic schemas for Django Ninja API
"""
from ninja import Schema
from typing import Optional
from datetime import datetime


# Base schemas can be defined here
class BaseSchema(Schema):
    """Base schema with common fields"""
    pass


class ErrorSchema(Schema):
    """Error response schema"""
    error: str
    detail: Optional[str] = None

