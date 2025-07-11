"""Huawei Cloud API client for fetching API documentation"""

import httpx
from typing import List, Optional, Dict, Any
import json
from .models import ProductsResponse, ApisResponse, ApiBasicInfo, Product


class HuaweiCloudApiClient:
    """Client for interacting with Huawei Cloud API Explorer"""

    def __init__(self):
        self.base_url = "https://console.huaweicloud.com/apiexplorer/new"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_products(self) -> ProductsResponse:
        """获取所有产品信息"""
        url = f"{self.base_url}/v5/products"
        response = await self.client.get(url)
        response.raise_for_status()
        return ProductsResponse.model_validate(response.json())

    async def find_product_short(self, target_product_name: str) -> Optional[str]:
        """根据产品名称查找产品简称"""
        products_response = await self.get_products()

        for group in products_response.groups:
            for product in group.products:
                if product.name == target_product_name:
                    return product.productshort

        return None

    async def get_apis_page(self, product_short: str, offset: int = 0, limit: int = 100) -> ApisResponse:
        """获取指定产品的API列表（分页）"""
        url = f"{self.base_url}/v3/apis"
        params = {
            "offset": offset,
            "limit": limit,
            "product_short": product_short
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return ApisResponse.model_validate(response.json())

    async def get_all_apis(self, product_short: str) -> List[ApiBasicInfo]:
        """获取指定产品的所有API信息"""
        all_apis = []
        offset = 0
        limit = 100

        while True:
            apis_response = await self.get_apis_page(product_short, offset, limit)
            all_apis.extend(apis_response.api_basic_infos)

            # 如果当前页的数量小于总数，继续获取下一页
            if offset + limit < apis_response.count:
                offset += limit
            else:
                break

        return all_apis

    async def find_api_by_summary(self, product_short: str, interface_name: str) -> Optional[ApiBasicInfo]:
        """根据接口名称查找API信息"""
        all_apis = await self.get_all_apis(product_short)

        for api in all_apis:
            if interface_name in api.summary:
                return api

        return None

    async def get_api_detail(self, product_short: str, api_name: str) -> Dict[str, Any]:
        """获取API详细信息"""
        url = f"{self.base_url}/v4/apis/detail"
        params = {
            "product_short": product_short,
            "name": api_name
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_api_info_by_user_input(self, target_product_name: str, interface_name: str) -> Dict[str, Any]:
        """根据用户输入获取完整的API信息"""
        # 步骤1：获取产品简称
        product_short = await self.find_product_short(target_product_name)
        if not product_short:
            raise ValueError(f"未找到产品: {target_product_name}")

        # 步骤2：查找匹配的API
        api_info = await self.find_api_by_summary(product_short, interface_name)
        if not api_info:
            raise ValueError(f"未找到接口: {interface_name}")

        # 步骤3：获取API详细信息
        api_detail = await self.get_api_detail(product_short, api_info.name)

        return {
            "product_name": target_product_name,
            "product_short": product_short,
            "api_basic_info": api_info.model_dump(),
            "api_detail": api_detail
        }
