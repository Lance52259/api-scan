"""Huawei Cloud API client for fetching API documentation"""

import httpx
from typing import List, Optional, Dict, Any
import json
from .models import ProductsResponse, ApisResponse, ApiBasicInfo, Product
import sys


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
        """根据接口名称查找API信息（智能匹配）"""
        all_apis = await self.get_all_apis(product_short)
        
        # 策略1：精确匹配（最高优先级）
        for api in all_apis:
            if interface_name == api.summary:
                print(f"✅ 精确匹配成功: '{interface_name}' = '{api.summary}'", file=sys.stderr)
                return api
        
        # 策略2：最佳包含匹配（中等优先级）
        # 优先返回与用户查询最接近的API，避免返回包含额外词汇的API
        best_containment_match = None
        best_containment_score = 0
        
        for api in all_apis:
            # 计算包含匹配的分数
            score = self._calculate_containment_score(interface_name, api.summary)
            if score > best_containment_score:
                best_containment_score = score
                best_containment_match = api
        
        if best_containment_match and best_containment_score > 0.5:
            print(f"🔍 最佳包含匹配成功: '{interface_name}' → '{best_containment_match.summary}' (分数: {best_containment_score:.2f})", file=sys.stderr)
            return best_containment_match
        
        # 策略3：相似度匹配（最低优先级）
        best_match = None
        best_score = 0
        best_match_info = ""
        
        for api in all_apis:
            # 计算相似度分数
            score = self._calculate_similarity(interface_name, api.summary)
            if score > best_score and score > 0.6:  # 相似度阈值
                best_score = score
                best_match = api
                best_match_info = f"'{api.summary}' (相似度: {score:.2f})"
        
        if best_match:
            print(f"🎯 相似度匹配成功: '{interface_name}' → {best_match_info}", file=sys.stderr)
            return best_match
        
        print(f"❌ 未找到匹配的API: '{interface_name}'", file=sys.stderr)
        return None
    
    def _calculate_similarity(self, query: str, api_name: str) -> float:
        """计算查询字符串与API名称的相似度"""
        query_lower = query.lower()
        api_lower = api_name.lower()
        
        # 如果查询是API名称的子字符串，给予较高分数
        if query_lower in api_lower:
            return 0.8
        
        # 如果API名称是查询的子字符串，给予中等分数
        if api_lower in query_lower:
            return 0.7
        
        # 计算共同字符数量
        common_chars = sum(1 for c in query_lower if c in api_lower)
        total_chars = len(query_lower) + len(api_lower)
        
        if total_chars == 0:
            return 0.0
        
        # 基础相似度分数
        base_score = common_chars / total_chars
        
        # 华为云API常用关键词，按重要性分组
        core_keywords = ['重装', '服务器', '实例', '云服务器', '弹性云服务器']
        action_keywords = ['创建', '删除', '修改', '更新', '查询', '获取', '列表', '详情']
        resource_keywords = ['上传', '下载', '备份', '恢复', '迁移', '扩容', '缩容']
        status_keywords = ['启动', '停止', '重启', '暂停', '恢复', '挂起']
        
        # 计算关键词匹配分数
        keyword_score = 0.0
        
        # 核心关键词匹配给予更高分数
        for keyword in core_keywords:
            if keyword in query_lower and keyword in api_lower:
                keyword_score += 0.15  # 核心关键词权重更高
        
        # 动作关键词匹配
        for keyword in action_keywords:
            if keyword in query_lower and keyword in api_lower:
                keyword_score += 0.1
        
        # 资源操作关键词匹配
        for keyword in resource_keywords:
            if keyword in query_lower and keyword in api_lower:
                keyword_score += 0.1
        
        # 状态操作关键词匹配
        for keyword in status_keywords:
            if keyword in query_lower and keyword in api_lower:
                keyword_score += 0.1
        
        # 特殊处理：重装服务器相关
        if '重装' in query_lower and '重装' in api_lower:
            keyword_score += 0.2  # 重装关键词给予额外分数
        
        if '服务器' in query_lower and '服务器' in api_lower:
            keyword_score += 0.15  # 服务器关键词给予额外分数
        
        # 最终相似度分数
        final_score = base_score + keyword_score
        return min(1.0, final_score)

    def _calculate_containment_score(self, query: str, api_name: str) -> float:
        """计算包含匹配的分数，优先返回与查询最接近的API"""
        query_lower = query.lower()
        api_lower = api_name.lower()
        
        # 如果查询完全包含在API名称中
        if query_lower in api_lower:
            # 计算额外词汇的惩罚分数
            extra_words = self._count_extra_words(query_lower, api_lower)
            
            # 基础分数：完全匹配给予最高分
            base_score = 1.0
            
            # 额外词汇惩罚：每多一个词扣0.3分，确保词汇数量少的API分数更高
            penalty = extra_words * 0.3
            
            # 确保分数不会低于0.1
            return max(0.1, base_score - penalty)
        
        # 如果API名称完全包含在查询中
        if api_lower in query_lower:
            return 0.6
        
        # 计算共同词汇
        common_words = self._get_common_words(query_lower, api_lower)
        query_words = self._extract_words(query_lower)
        api_words = self._extract_words(api_lower)
        
        if not query_words:
            return 0.0
        
        # 基础分数：共同词汇比例
        base_score = len(common_words) / len(query_words)
        
        # 额外词汇惩罚：API名称中每多一个不相关的词扣0.2分
        extra_words = len(api_words) - len(common_words)
        penalty = min(0.6, extra_words * 0.2)
        
        # 位置奖励：如果共同词汇在API名称中的位置与查询中的位置完全匹配，给予奖励
        position_bonus = 0.0
        if len(common_words) >= 2:
            # 检查词汇顺序是否完全匹配
            query_positions = self._get_word_positions(query_lower, common_words)
            api_positions = self._get_word_positions(api_lower, common_words)
            
            # 如果位置完全匹配，给予奖励
            if query_positions == api_positions:
                position_bonus = 0.3
        
        final_score = base_score - penalty + position_bonus
        return max(0.0, min(1.0, final_score))
    
    def _count_extra_words(self, query: str, api_name: str) -> int:
        """计算API名称中相对于查询的额外词汇数量"""
        # 华为云API常见词汇
        common_words = [
            '重装', '服务器', '实例', '云服务器', '弹性云服务器', '批量', '创建', '删除', 
            '修改', '更新', '查询', '获取', '列表', '详情', '上传', '下载', '备份', 
            '恢复', '迁移', '扩容', '缩容', '启动', '停止', '重启', '暂停', '恢复', '挂起',
            '管理', '应用', '组', '服务', '资源', '配置', '设置', '策略', '规则', '权限',
            '镜像', '的'
        ]
        
        # 提取查询和API名称中的词汇
        query_words = set()
        api_words = set()
        
        # 从查询中提取词汇
        for word in common_words:
            if word in query:
                query_words.add(word)
        
        # 从API名称中提取词汇
        for word in common_words:
            if word in api_name:
                api_words.add(word)
        
        # 计算额外词汇数量
        extra_words = len(api_words - query_words)
        
        # 特殊处理：如果API名称包含"批量"而查询不包含，给予额外惩罚
        if '批量' in api_name and '批量' not in query:
            extra_words += 2  # "批量"词汇给予额外惩罚
        
        return extra_words
    
    def _count_chinese_words(self, text: str) -> int:
        """计算中文词汇数量（按常见词汇分割）"""
        # 常见的中文词汇分隔符和关键词
        separators = ['的', '和', '与', '或', '及', '等', '等', '、', '，', '；', '：']
        
        # 华为云API常见词汇
        common_words = [
            '重装', '服务器', '实例', '云服务器', '弹性云服务器', '批量', '创建', '删除', 
            '修改', '更新', '查询', '获取', '列表', '详情', '上传', '下载', '备份', 
            '恢复', '迁移', '扩容', '缩容', '启动', '停止', '重启', '暂停', '恢复', '挂起',
            '管理', '应用', '组', '服务', '资源', '配置', '设置', '策略', '规则', '权限'
        ]
        
        # 按常见词汇分割
        words = []
        remaining = text
        
        # 先按分隔符分割
        for sep in separators:
            if sep in remaining:
                parts = remaining.split(sep)
                remaining = parts[0]  # 取第一部分继续处理
                if parts[0]:
                    words.append(parts[0])
                for part in parts[1:]:
                    if part:
                        words.append(part)
        
        # 如果还有剩余文本，按常见词汇分割
        if remaining:
            for word in common_words:
                if word in remaining:
                    parts = remaining.split(word)
                    if parts[0]:
                        words.append(parts[0])
                    words.append(word)
                    remaining = parts[-1] if len(parts) > 1 else ""
            
            # 如果还有剩余文本，作为一个词汇
            if remaining:
                words.append(remaining)
        
        # 过滤空字符串并返回词汇数量
        return len([w for w in words if w.strip()])
    
    def _get_common_words(self, query: str, api_name: str) -> list:
        """获取查询和API名称中的共同词汇"""
        query_words = self._extract_words(query)
        api_words = self._extract_words(api_name)
        
        # 返回共同词汇
        return list(set(query_words) & set(api_words))
    
    def _extract_words(self, text: str) -> list:
        """提取文本中的词汇"""
        # 华为云API常见词汇
        common_words = [
            '重装', '服务器', '实例', '云服务器', '弹性云服务器', '批量', '创建', '删除', 
            '修改', '更新', '查询', '获取', '列表', '详情', '上传', '下载', '备份', 
            '恢复', '迁移', '扩容', '缩容', '启动', '停止', '重启', '暂停', '恢复', '挂起',
            '管理', '应用', '组', '服务', '资源', '配置', '设置', '策略', '规则', '权限'
        ]
        
        words = []
        for word in common_words:
            if word in text:
                words.append(word)
        
        return words
    
    def _get_word_positions(self, text: str, words: list) -> list:
        """获取词汇在文本中的位置"""
        positions = []
        for word in words:
            pos = text.find(word)
            if pos != -1:
                positions.append(pos)
        return sorted(positions)

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
