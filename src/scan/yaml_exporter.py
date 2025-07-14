"""YAML导出工具 - 将华为云API信息导出为YAML文件"""

import yaml
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from .client import HuaweiCloudApiClient


class YamlExporter:
    """YAML导出器"""
    
    def __init__(self, output_dir: str = "api_exports"):
        self.output_dir = output_dir
        self.expand_allof = True  # 默认展开allOf结构
        self.definitions_context = None  # 用于解析$ref引用
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def clean_data_for_yaml(self, data: Any) -> Any:
        """清理数据以便YAML序列化"""
        if isinstance(data, dict):
            # 处理OpenAPI的allOf结构
            if "allOf" in data and self.expand_allof:
                return self.resolve_allof_schema(data)
            return {k: self.clean_data_for_yaml(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.clean_data_for_yaml(item) for item in data]
        elif isinstance(data, str):
            return data
        elif data is None:
            return None
        elif isinstance(data, bool):
            return data
        elif isinstance(data, (int, float)):
            return data
        else:
            return str(data)
    
    def resolve_ref(self, ref: str) -> Dict[str, Any]:
        """解析$ref引用"""
        if not self.definitions_context or not ref.startswith("#/definitions/"):
            return {"$ref": ref}
        
        definition_name = ref.replace("#/definitions/", "")
        if definition_name in self.definitions_context:
            return self.definitions_context[definition_name]
        
        return {"$ref": ref}
    
    def resolve_allof_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """解析OpenAPI的allOf结构，将其合并为单一的schema"""
        if "allOf" not in schema:
            return schema
        
        resolved_schema = {}
        
        # 复制非allOf的属性
        for key, value in schema.items():
            if key != "allOf":
                resolved_schema[key] = self.clean_data_for_yaml(value)
        
        # 处理allOf中的每个schema
        for sub_schema in schema["allOf"]:
            if isinstance(sub_schema, dict):
                if "$ref" in sub_schema:
                    # 尝试解析$ref引用
                    ref_schema = self.resolve_ref(sub_schema["$ref"])
                    if "$ref" not in ref_schema:
                        # 成功解析，递归处理
                        merged_schema = self.clean_data_for_yaml(ref_schema)
                        self.merge_schemas(resolved_schema, merged_schema)
                    else:
                        # 保留$ref引用
                        if "allOf" not in resolved_schema:
                            resolved_schema["allOf"] = []
                        resolved_schema["allOf"].append(sub_schema)
                else:
                    # 合并直接定义的schema
                    merged_schema = self.clean_data_for_yaml(sub_schema)
                    self.merge_schemas(resolved_schema, merged_schema)
        
        # 去重required数组
        if "required" in resolved_schema and isinstance(resolved_schema["required"], list):
            resolved_schema["required"] = list(set(resolved_schema["required"]))
        
        return resolved_schema
    
    def merge_schemas(self, target: Dict[str, Any], source: Dict[str, Any]):
        """将source schema合并到target schema中"""
        # 合并properties
        if "properties" in source:
            if "properties" not in target:
                target["properties"] = {}
            target["properties"].update(source["properties"])
        
        # 合并required
        if "required" in source:
            if "required" not in target:
                target["required"] = []
            target["required"].extend(source["required"])
        
        # 合并其他属性
        for key, value in source.items():
            if key not in ["properties", "required"]:
                target[key] = value
    
    def generate_yaml_header(self, title: str, description: str = "") -> Dict[str, Any]:
        """生成YAML文件头部信息"""
        return {
            "metadata": {
                "title": title,
                "description": description,
                "generated_at": datetime.now().isoformat(),
                "generator": "华为云API分析MCP服务器",
                "version": "1.0.0"
            }
        }
    
    def export_products_to_yaml(self, products_data: Dict[str, Any], filename: str = "huawei_cloud_products.yml") -> str:
        """导出产品列表为YAML文件"""
        output_path = os.path.join(self.output_dir, filename)
        
        # 构建YAML数据结构
        yaml_data = self.generate_yaml_header(
            "华为云产品列表",
            "华为云所有可用产品和服务的完整列表"
        )
        
        # 提取产品信息
        products = []
        if "groups" in products_data:
            for group in products_data["groups"]:
                for product in group.get("products", []):
                    products.append({
                        "name": product.get("name", ""),
                        "product_short": product.get("productshort", ""),
                        "description": product.get("description", ""),
                        "group": group.get("name", "")
                    })
        
        yaml_data["products"] = {
            "count": len(products),
            "items": products
        }
        
        # 写入YAML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.clean_data_for_yaml(yaml_data),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2
            )
        
        return output_path
    
    def export_product_apis_to_yaml(self, product_name: str, apis_data: List[Dict[str, Any]], filename: str = None) -> str:
        """导出产品API列表为YAML文件"""
        if filename is None:
            # 尝试从APIs数据中获取product_short
            product_short = "unknown"
            if apis_data and len(apis_data) > 0:
                product_short = apis_data[0].get("product_short", "unknown")
            
            # 清理文件名中的特殊字符
            safe_product_short = product_short.replace(" ", "_").replace("/", "_").replace("-", "_")
            filename = f"{safe_product_short}_apis.yml"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 构建YAML数据结构
        yaml_data = self.generate_yaml_header(
            f"{product_name} API列表",
            f"华为云{product_name}产品的所有API接口列表"
        )
        
        yaml_data["product"] = {
            "name": product_name,
            "api_count": len(apis_data)
        }
        
        # 整理API信息
        apis = []
        for api in apis_data:
            apis.append({
                "id": api.get("id", ""),
                "name": api.get("name", ""),
                "alias_name": api.get("alias_name", ""),
                "summary": api.get("summary", ""),
                "method": api.get("method", ""),
                "tags": api.get("tags", ""),
                "product_short": api.get("product_short", ""),
                "info_version": api.get("info_version", "")
            })
        
        yaml_data["apis"] = apis
        
        # 写入YAML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.clean_data_for_yaml(yaml_data),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2
            )
        
        return output_path
    
    def export_api_detail_to_yaml(self, api_info: Dict[str, Any], filename: str = None) -> str:
        """导出API详细信息为YAML文件"""
        product_name = api_info.get("product_name", "unknown")
        api_summary = api_info.get("api_basic_info", {}).get("summary", "unknown")
        
        if filename is None:
            # 使用{product_short}_{api.detail.name}.yml格式，避免中文字符
            product_short = api_info.get("product_short", "unknown")
            api_detail = api_info.get("api_detail", {})
            api_name = api_detail.get("name", "unknown")
            
            # 清理文件名中的特殊字符
            safe_product_short = product_short.replace(" ", "_").replace("/", "_").replace("-", "_")
            safe_api_name = api_name.replace(" ", "_").replace("/", "_").replace("-", "_")
            
            filename = f"{safe_product_short}_{safe_api_name}.yml"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 设置definitions上下文用于解析$ref引用
        api_detail = api_info.get("api_detail", {})
        if "definitions" in api_detail:
            self.definitions_context = api_detail["definitions"]
        
        # 构建YAML数据结构
        yaml_data = self.generate_yaml_header(
            f"{product_name} - {api_summary}",
            f"华为云{product_name}产品的{api_summary}接口详细信息"
        )
        
        # 基本信息
        yaml_data["api"] = {
            "product": {
                "name": product_name,
                "short": api_info.get("product_short", "")
            },
            "basic_info": api_info.get("api_basic_info", {}),
            "detail": api_info.get("api_detail", {})
        }
        
        # 写入YAML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.clean_data_for_yaml(yaml_data),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2
            )
        
        # 清理上下文
        self.definitions_context = None
        
        return output_path
    
    def export_multiple_apis_to_yaml(self, apis_info: List[Dict[str, Any]], filename: str = "multiple_apis.yml") -> str:
        """导出多个API详细信息为单个YAML文件"""
        output_path = os.path.join(self.output_dir, filename)
        
        # 构建YAML数据结构
        yaml_data = self.generate_yaml_header(
            "华为云API详细信息集合",
            f"包含{len(apis_info)}个API的详细信息"
        )
        
        yaml_data["apis"] = {
            "count": len(apis_info),
            "items": []
        }
        
        for api_info in apis_info:
            api_data = {
                "product": {
                    "name": api_info.get("product_name", ""),
                    "short": api_info.get("product_short", "")
                },
                "basic_info": api_info.get("api_basic_info", {}),
                "detail": api_info.get("api_detail", {})
            }
            yaml_data["apis"]["items"].append(api_data)
        
        # 写入YAML文件
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.clean_data_for_yaml(yaml_data),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2
            )
        
        return output_path


class YamlExportCLI:
    """YAML导出命令行工具"""
    
    def __init__(self, output_dir: str = "api_exports"):
        self.exporter = YamlExporter(output_dir)
        self.client = None
    
    async def __aenter__(self):
        self.client = HuaweiCloudApiClient()
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def export_all_products(self) -> str:
        """导出所有产品列表"""
        print("🔍 正在获取华为云产品列表...")
        products_response = await self.client.get_products()
        
        # 转换为字典格式
        products_data = {
            "groups": []
        }
        
        for group in products_response.groups:
            group_data = {
                "name": group.name,
                "products": []
            }
            for product in group.products:
                group_data["products"].append({
                    "name": product.name,
                    "productshort": product.productshort,
                    "description": product.description
                })
            products_data["groups"].append(group_data)
        
        output_path = self.exporter.export_products_to_yaml(products_data)
        print(f"✅ 产品列表已导出到: {output_path}")
        return output_path
    
    async def export_product_apis(self, product_name: str) -> str:
        """导出指定产品的API列表"""
        print(f"🔍 正在获取{product_name}的API列表...")
        
        # 查找产品简称
        product_short = await self.client.find_product_short(product_name)
        if not product_short:
            raise ValueError(f"未找到产品: {product_name}")
        
        # 获取API列表
        apis = await self.client.get_all_apis(product_short)
        apis_data = [api.model_dump() for api in apis]
        
        output_path = self.exporter.export_product_apis_to_yaml(product_name, apis_data)
        print(f"✅ {product_name}的API列表已导出到: {output_path}")
        return output_path
    
    async def export_api_detail(self, product_name: str, interface_name: str) -> str:
        """导出指定API的详细信息"""
        print(f"🔍 正在获取{product_name}的{interface_name}接口详细信息...")
        
        api_info = await self.client.get_api_info_by_user_input(product_name, interface_name)
        output_path = self.exporter.export_api_detail_to_yaml(api_info)
        print(f"✅ API详细信息已导出到: {output_path}")
        return output_path
    
    async def export_multiple_api_details(self, api_specs: List[tuple]) -> str:
        """导出多个API的详细信息到单个文件"""
        print(f"🔍 正在获取{len(api_specs)}个API的详细信息...")
        
        apis_info = []
        for i, (product_name, interface_name) in enumerate(api_specs, 1):
            print(f"  [{i}/{len(api_specs)}] 获取{product_name}的{interface_name}...")
            try:
                api_info = await self.client.get_api_info_by_user_input(product_name, interface_name)
                apis_info.append(api_info)
            except Exception as e:
                print(f"  ⚠️ 获取失败: {e}")
        
        if apis_info:
            output_path = self.exporter.export_multiple_apis_to_yaml(apis_info)
            print(f"✅ {len(apis_info)}个API详细信息已导出到: {output_path}")
            return output_path
        else:
            raise ValueError("没有成功获取任何API信息")


# 命令行接口函数
async def export_products_cli():
    """命令行导出产品列表"""
    async with YamlExportCLI() as exporter:
        return await exporter.export_all_products()


async def export_product_apis_cli(product_name: str):
    """命令行导出产品API列表"""
    async with YamlExportCLI() as exporter:
        return await exporter.export_product_apis(product_name)


async def export_api_detail_cli(product_name: str, interface_name: str):
    """命令行导出API详细信息"""
    async with YamlExportCLI() as exporter:
        return await exporter.export_api_detail(product_name, interface_name)


async def export_multiple_apis_cli(api_specs: List[tuple]):
    """命令行导出多个API详细信息"""
    async with YamlExportCLI() as exporter:
        return await exporter.export_multiple_api_details(api_specs) 