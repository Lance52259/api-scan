"""Data models for Huawei Cloud API responses"""

from typing import List, Optional, Any, Dict


class Product:
    """Product information model"""
    def __init__(self, **data):
        self.name = data.get('name', '')
        self.productshort = data.get('productshort', '')
        self.description = data.get('description')


class ProductGroup:
    """Product group model"""
    def __init__(self, **data):
        self.name = data.get('name', '')
        self.products = [Product(**p) if isinstance(p, dict) else p for p in data.get('products', [])]


class ProductsResponse:
    """Response model for products API"""
    def __init__(self, **data):
        self.groups = [ProductGroup(**g) if isinstance(g, dict) else g for g in data.get('groups', [])]

    @classmethod
    def model_validate(cls, data):
        """兼容Pydantic v1和v2的验证方法"""
        return cls(**data)


class ApiBasicInfo:
    """Basic API information model"""
    def __init__(self, **data):
        self.id = data.get('id', '')
        self.name = data.get('name', '')
        self.alias_name = data.get('alias_name', '')
        self.method = data.get('method', '')
        self.summary = data.get('summary', '')
        self.tags = data.get('tags', '')
        self.product_short = data.get('product_short', '')
        self.info_version = data.get('info_version', '')

    def model_dump(self):
        """兼容Pydantic v1和v2的序列化方法"""
        return {
            'id': self.id,
            'name': self.name,
            'alias_name': self.alias_name,
            'method': self.method,
            'summary': self.summary,
            'tags': self.tags,
            'product_short': self.product_short,
            'info_version': self.info_version
        }


class ApisResponse:
    """Response model for APIs listing"""
    def __init__(self, **data):
        self.count = data.get('count', 0)
        self.api_basic_infos = [ApiBasicInfo(**api) if isinstance(api, dict) else api
                               for api in data.get('api_basic_infos', [])]

    @classmethod
    def model_validate(cls, data):
        """兼容Pydantic v1和v2的验证方法"""
        return cls(**data)


class ApiDetailResponse:
    """Response model for API detail"""
    def __init__(self, **data):
        self.data = data.get('data', {})
