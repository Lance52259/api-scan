"""Cursor优化的MCP服务器实现 - 针对Cursor MCP集成优化"""

import asyncio
import json
import sys
import logging
import signal
from typing import Dict, Any, List, Optional, AsyncIterator
from .client import HuaweiCloudApiClient

# 配置最小日志，只记录严重错误到stderr
logging.basicConfig(
    level=logging.ERROR,  # 改为ERROR级别以减少干扰
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True  # 强制重新配置logging，Python 3.10支持
)
logger = logging.getLogger(__name__)

# 确保没有其他日志输出到stdout
for handler in logging.root.handlers[:]:
    if handler.stream == sys.stdout:
        logging.root.removeHandler(handler)


class CursorOptimizedMCPServer:
    """针对Cursor优化的MCP服务器"""

    def __init__(self):
        self.running = True
        # 修正工具名称：使用下划线而不是短横线（Cursor要求）
        self.tools = {
            "get_huawei_cloud_api_info": {
                "description": "获取华为云指定产品的API接口详细信息。当用户询问特定华为云产品的API详情、请求参数、响应格式、使用方法时自动调用。支持查询API文档、接口规范、参数说明等。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "华为云产品名称，如'ECS'、'云应用'、'对象存储服务'、'弹性云服务器'等"
                        },
                        "interface_name": {
                            "type": "string", 
                            "description": "API接口名称，如'创建云服务器'、'新增/修改弹性伸缩策略'、'上传对象'等"
                        }
                    },
                    "required": ["product_name", "interface_name"]
                }
            },
            "list_huawei_cloud_products": {
                "description": "列出华为云所有可用的产品和服务。当用户询问华为云有哪些产品、服务列表、产品目录、或想了解华为云提供的服务时自动调用。包含计算、存储、网络、数据库、AI等各类服务。",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_product_apis": {
                "description": "列出指定华为云产品的所有API接口列表。当用户询问某个产品有哪些API、接口列表、或想了解产品的API能力时自动调用。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "华为云产品名称，如'ECS'、'VPC'、'RDS'等"
                        }
                    },
                    "required": ["product_name"]
                }
            }
        }
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理信号"""
        self.running = False

    def create_response(self, request_id: Any, result: Any = None, error: Any = None) -> Dict[str, Any]:
        """创建标准JSON-RPC 2.0响应"""
        response = {
            "jsonrpc": "2.0",
            "id": request_id
        }
        
        if error:
            response["error"] = error
        else:
            response["result"] = result
            
        return response

    async def handle_initialize(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return self.create_response(
            request.get("id"),
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "api_scan",  # 使用下划线，避免短横线
                    "version": "1.0.0"
                }
            }
        )

    async def handle_list_offerings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理ListOfferings请求 - Cursor期望的标准方法"""
        return self.create_response(
            request.get("id"),
            {
                "tools": [
                    {
                        "name": name,
                        "description": tool["description"],
                        "inputSchema": tool["inputSchema"]
                    }
                    for name, tool in self.tools.items()
                ],
                "resources": [],
                "prompts": []
            }
        )

    async def handle_server_info(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理服务器信息请求"""
        return self.create_response(
            request.get("id"),
            {
                "name": "api_scan",
                "version": "1.0.0",
                "description": "华为云API分析MCP服务器",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                }
            }
        )

    async def handle_tools_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具列表请求"""
        tools = [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["inputSchema"]
            }
            for name, tool in self.tools.items()
        ]
        
        return self.create_response(request.get("id"), {"tools": tools})

    async def handle_tools_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        try:
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "get_huawei_cloud_api_info":
                result = await self._get_api_info(arguments)
            elif tool_name == "list_huawei_cloud_products":
                result = await self._list_products(arguments)
            elif tool_name == "list_product_apis":
                result = await self._list_product_apis(arguments)
            else:
                return self.create_response(
                    request.get("id"),
                    error={"code": -32601, "message": f"Unknown tool: {tool_name}"}
                )

            return self.create_response(request.get("id"), result)

        except Exception as e:
            return self.create_response(
                request.get("id"),
                error={"code": -32603, "message": f"Tool execution error: {str(e)}"}
            )

    async def handle_resources_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源列表请求"""
        return self.create_response(
            request.get("id"),
            {"resources": []}
        )

    async def handle_prompts_list(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理提示列表请求"""
        return self.create_response(
            request.get("id"),
            {"prompts": []}
        )

    async def handle_ping(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理ping请求"""
        return self.create_response(
            request.get("id"),
            {"status": "ok"}
        )

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理MCP请求"""
        method = request.get("method")
        
        try:
            if method == "initialize":
                return await self.handle_initialize(request)
            elif method == "initialized":
                # 这是通知，不需要响应
                return None
            elif method == "tools/list":
                return await self.handle_tools_list(request)
            elif method == "tools/call":
                return await self.handle_tools_call(request)
            elif method == "listOfferings":
                return await self.handle_list_offerings(request)
            elif method == "serverInfo":
                return await self.handle_server_info(request)
            elif method == "resources/list":
                return await self.handle_resources_list(request)
            elif method == "prompts/list":
                return await self.handle_prompts_list(request)
            elif method == "ping":
                return await self.handle_ping(request)
            else:
                return self.create_response(
                    request.get("id"),
                    error={"code": -32601, "message": f"Method not found: {method}"}
                )
        except Exception as e:
            return self.create_response(
                request.get("id"),
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            )

    async def _list_products(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """列出所有产品"""
        try:
            client = HuaweiCloudApiClient()
            async with client:
                products_response = await client.get_products()
                
                # 整理产品列表
                all_products = []
                for group in products_response.groups:
                    for product in group.products:
                        all_products.append(product.name)
                
                if all_products:
                    product_list = "\n".join([f"- {product}" for product in all_products])
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"华为云产品列表（共{len(all_products)}个）：\n\n{product_list}"
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "无法获取产品列表"
                            }
                        ]
                    }
                
        except Exception as e:
            raise Exception(f"获取产品列表失败: {str(e)}")

    async def _list_product_apis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """列出指定产品的所有API"""
        try:
            product_name = arguments.get("product_name")
            
            if not product_name:
                raise ValueError("缺少必需参数: product_name")
            
            client = HuaweiCloudApiClient()
            async with client:
                # 查找产品简称
                product_short = await client.find_product_short(product_name)
                if not product_short:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"未找到产品'{product_name}'"
                            }
                        ]
                    }
                
                # 获取API列表
                apis = await client.get_all_apis(product_short)
                
                if apis:
                    api_list = "\n".join([f"- {api.summary}" for api in apis])
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"产品'{product_name}'的API列表（共{len(apis)}个）：\n\n{api_list}"
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"未找到产品'{product_name}'的API列表"
                            }
                        ]
                    }
                
        except Exception as e:
            raise Exception(f"获取产品API列表失败: {str(e)}")

    async def _get_api_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取API信息"""
        try:
            product_name = arguments.get("product_name")
            interface_name = arguments.get("interface_name")
            
            if not product_name or not interface_name:
                raise ValueError("缺少必需参数: product_name 和 interface_name")
            
            client = HuaweiCloudApiClient()
            async with client:
                api_info = await client.get_api_info_by_user_input(product_name, interface_name)
                
                if api_info:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"华为云API信息：\n\n"
                                       f"产品：{api_info.get('product_name', 'N/A')}\n"
                                       f"接口名称：{api_info.get('api_basic_info', {}).get('summary', 'N/A')}\n"
                                       f"接口描述：{api_info.get('api_basic_info', {}).get('description', 'N/A')}\n"
                                       f"请求方法：{api_info.get('api_basic_info', {}).get('method', 'N/A')}\n"
                                       f"详细信息：{json.dumps(api_info.get('api_detail', {}), ensure_ascii=False, indent=2)}"
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text", 
                                "text": f"未找到产品'{product_name}'的接口'{interface_name}'"
                            }
                        ]
                    }
                
        except Exception as e:
            raise Exception(f"获取API信息失败: {str(e)}")

    async def read_stdin_lines(self) -> AsyncIterator[str]:
        """异步读取stdin行"""
        loop = asyncio.get_event_loop()
        while self.running:
            try:
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:  # EOF
                    break
                yield line.strip()
            except Exception:
                break

    async def test_mode(self):
        """测试模式"""
        print("=== Cursor优化MCP服务器测试模式 ===", file=sys.stderr)
        print("1. 测试产品列表查询", file=sys.stderr)
        print("2. 测试API信息查询", file=sys.stderr)
        print("3. 退出", file=sys.stderr)
        
        while True:
            try:
                choice = input("请选择操作 (1-3): ")
                
                if choice == "1":
                    print("正在获取华为云产品列表...", file=sys.stderr)
                    result = await self._list_products({})
                    content = result["content"][0]["text"]
                    # 只显示前20个产品，避免输出过长
                    lines = content.split("\n")
                    preview = "\n".join(lines[:25])
                    if len(lines) > 25:
                        preview += f"\n... 还有{len(lines)-25}行"
                    print(preview, file=sys.stderr)
                    
                elif choice == "2":
                    product = input("请输入产品名称: ")
                    interface = input("请输入接口名称: ")
                    print(f"正在查询{product}的{interface}接口信息...", file=sys.stderr)
                    try:
                        result = await self._get_api_info({
                            "product_name": product,
                            "interface_name": interface
                        })
                        print(result["content"][0]["text"], file=sys.stderr)
                    except Exception as e:
                        print(f"查询失败: {str(e)}", file=sys.stderr)
                        
                elif choice == "3":
                    print("退出测试模式", file=sys.stderr)
                    break
                else:
                    print("无效选择", file=sys.stderr)
                    
            except (EOFError, KeyboardInterrupt):
                print("\n退出测试模式", file=sys.stderr)
                break

    async def run(self):
        """运行MCP服务器"""
        # 输出启动信息到stderr以便调试
        print("MCP Server ready", file=sys.stderr, flush=True)
        
        # 生产模式：始终使用MCP协议，不检测终端
        try:
            async for line in self.read_stdin_lines():
                if not line or not self.running:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # 只有非通知类型的请求才需要响应
                    if response is not None:
                        response_json = json.dumps(response, ensure_ascii=False)
                        print(response_json, flush=True)
                    
                except json.JSONDecodeError:
                    # JSON解析错误，发送错误响应
                    error_response = self.create_response(
                        None,
                        error={"code": -32700, "message": "Parse error"}
                    )
                    response_json = json.dumps(error_response, ensure_ascii=False)
                    print(response_json, flush=True)
                    
                except Exception as e:
                    # 其他错误
                    error_response = self.create_response(
                        None,
                        error={"code": -32603, "message": f"Internal error: {str(e)}"}
                    )
                    response_json = json.dumps(error_response, ensure_ascii=False)
                    print(response_json, flush=True)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False


async def main():
    """主函数"""
    server = CursorOptimizedMCPServer()
    await server.run()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except AttributeError:
        # Python 3.6兼容性
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
