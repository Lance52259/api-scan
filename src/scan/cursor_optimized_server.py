"""Cursor优化的MCP服务器实现 - 针对Cursor MCP集成优化"""

import asyncio
import json
import sys
import logging
import signal
import os
import re
from typing import Dict, Any, List, Optional, AsyncIterator
from .client import HuaweiCloudApiClient
from .yaml_exporter import YamlExporter

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
                "description": "获取华为云指定产品的API接口详细信息。当用户询问特定华为云产品的API详情、请求参数、响应格式、使用方法时自动调用。支持查询API文档、接口规范、参数说明等。当用户提到'导出'、'YAML'、'文件'、'保存'、'下载'、'生成文件'时，自动设置export_yaml=true导出YAML文件。",
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
                        },
                        "export_yaml": {
                            "type": "boolean",
                            "description": "是否导出为YAML文件。当用户明确提到'导出'、'YAML'、'文件'、'保存'、'下载'、'生成文件'、'导出为文件'、'输出文件'时设置为true，否则默认false"
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "YAML文件输出目录。用户指定'项目根目录'、'当前目录'时使用'.'，其他情况默认为'api_exports'"
                        }
                    },
                    "required": ["product_name", "interface_name"]
                }
            },
            "list_huawei_cloud_products": {
                "description": "列出华为云所有可用的产品和服务。当用户询问华为云有哪些产品、服务列表、产品目录、或想了解华为云提供的服务时自动调用。包含计算、存储、网络、数据库、AI等各类服务。当用户提到'导出'、'YAML'、'文件'、'保存'、'下载'、'生成文件'时，自动设置export_yaml=true导出YAML文件。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "export_yaml": {
                            "type": "boolean",
                            "description": "是否导出为YAML文件。当用户明确提到'导出'、'YAML'、'文件'、'保存'、'下载'、'生成文件'、'导出为文件'、'输出文件'时设置为true，否则默认false"
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "YAML文件输出目录。用户指定'项目根目录'、'当前目录'时使用'.'，其他情况默认为'api_exports'"
                        }
                    },
                    "required": []
                }
            },
            "list_product_apis": {
                "description": "列出指定华为云产品的所有API接口列表。当用户询问某个产品有哪些API、接口列表、或想了解产品的API能力时自动调用。当用户提到'导出'、'YAML'、'文件'、'保存'、'下载'、'生成文件'时，自动设置export_yaml=true导出YAML文件。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "华为云产品名称，如'ECS'、'VPC'、'RDS'等"
                        },
                        "export_yaml": {
                            "type": "boolean",
                            "description": "是否导出为YAML文件。当用户明确提到'导出'、'YAML'、'文件'、'保存'、'下载'、'生成文件'、'导出为文件'、'输出文件'时设置为true，否则默认false"
                        },
                        "output_dir": {
                            "type": "string",
                            "description": "YAML文件输出目录。用户指定'项目根目录'、'当前目录'时使用'.'，其他情况默认为'api_exports'"
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

    def create_response(self, request_id: Any, result: Any = None, error: Any = None) -> Optional[Dict[str, Any]]:
        """创建标准JSON-RPC 2.0响应"""
        # 如果 request_id 为 None，这是通知类型请求，不应该发送响应
        if request_id is None:
            return None
        
        # 确保 id 是有效的类型（string 或 number）
        if not isinstance(request_id, (str, int, float)):
            # 如果 id 类型无效，尝试转换或跳过响应
            try:
                request_id = str(request_id)
            except:
                return None
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id
        }
        
        if error:
            response["error"] = error
        else:
            response["result"] = result
            
        return response

    async def handle_initialize(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    async def handle_list_offerings(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    async def handle_server_info(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    async def handle_tools_list(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    async def handle_tools_call(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理工具调用请求"""
        try:
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # 检查用户输入中是否包含导出相关关键词
            export_keywords = ["导出", "YAML", "yaml", "文件", "保存", "下载", "生成文件"]
            
            # 获取工具描述
            tool_desc = self.tools.get(tool_name, {}).get("description", "")
            
            # 检查用户请求中的内容
            user_request = str(request)
            
            # 如果工具描述中提到支持YAML导出，并且用户输入包含导出关键词
            if any(keyword in tool_desc for keyword in ["YAML", "导出"]) and any(keyword in user_request for keyword in export_keywords):
                # 设置导出参数
                arguments["export_yaml"] = True
                arguments["output_dir"] = "."
                print(f"已启用YAML导出功能，输出目录: {arguments['output_dir']}", file=sys.stderr)

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

    async def handle_resources_list(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理资源列表请求"""
        return self.create_response(
            request.get("id"),
            {"resources": []}
        )

    async def handle_prompts_list(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理提示列表请求"""
        return self.create_response(
            request.get("id"),
            {"prompts": []}
        )

    async def handle_ping(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
            export_yaml = arguments.get("export_yaml", False)
            output_dir = arguments.get("output_dir", "api_exports")
            
            # 智能处理输出目录
            if output_dir in [".", "当前目录", "项目根目录", "根目录", "当前项目", "项目下", "项目目录"]:
                output_dir = "."
            
            client = HuaweiCloudApiClient()
            async with client:
                products_response = await client.get_products()
                
                # 整理产品列表
                all_products = []
                for group in products_response.groups:
                    for product in group.products:
                        all_products.append(product.name)
                
                # 构建响应文本
                if all_products:
                    product_list = "\n".join([f"- {product}" for product in all_products])
                    response_text = f"华为云产品列表（共{len(all_products)}个）：\n\n{product_list}"
                else:
                    response_text = "无法获取产品列表"
                
                # 如果需要导出YAML
                yaml_info = ""
                if export_yaml:
                    try:
                        exporter = YamlExporter(output_dir)
                        
                        # 构建产品数据
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
                        
                        yaml_path = exporter.export_products_to_yaml(products_data)
                        
                        # 获取绝对路径用于更清晰的显示
                        abs_yaml_path = os.path.abspath(yaml_path)
                        
                        yaml_info = f"\n\n📄 产品列表YAML文件已成功导出到: {yaml_path}"
                        yaml_info += f"\n📍 完整路径: {abs_yaml_path}"
                        
                        # 如果是输出到当前目录，特别说明
                        if output_dir == ".":
                            yaml_info += f"\n✅ 已按要求导出到项目根目录"
                            
                    except Exception as e:
                        yaml_info = f"\n\n⚠️ YAML导出失败: {str(e)}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": response_text + yaml_info
                        }
                    ]
                }
                
        except Exception as e:
            raise Exception(f"获取产品列表失败: {str(e)}")

    async def _list_product_apis(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """列出指定产品的所有API"""
        try:
            product_name = arguments.get("product_name")
            export_yaml = arguments.get("export_yaml", False)
            output_dir = arguments.get("output_dir", "api_exports")
            
            # 智能处理输出目录
            if output_dir in [".", "当前目录", "项目根目录", "根目录", "当前项目", "项目下", "项目目录"]:
                output_dir = "."
            
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
                
                # 构建响应文本
                if apis:
                    api_list = "\n".join([f"- {api.summary}" for api in apis])
                    response_text = f"产品'{product_name}'的API列表（共{len(apis)}个）：\n\n{api_list}"
                else:
                    response_text = f"未找到产品'{product_name}'的API列表"
                
                # 如果需要导出YAML
                yaml_info = ""
                if export_yaml and apis:
                    try:
                        exporter = YamlExporter(output_dir)
                        apis_data = [api.model_dump() for api in apis]
                        yaml_path = exporter.export_product_apis_to_yaml(product_name, apis_data)
                        
                        # 获取绝对路径用于更清晰的显示
                        abs_yaml_path = os.path.abspath(yaml_path)
                        
                        yaml_info = f"\n\n📄 {product_name}的API列表YAML文件已成功导出到: {yaml_path}"
                        yaml_info += f"\n📍 完整路径: {abs_yaml_path}"
                        
                        # 如果是输出到当前目录，特别说明
                        if output_dir == ".":
                            yaml_info += f"\n✅ 已按要求导出到项目根目录"
                            
                    except Exception as e:
                        yaml_info = f"\n\n⚠️ YAML导出失败: {str(e)}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": response_text + yaml_info
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
            export_yaml = arguments.get("export_yaml", False)
            output_dir = arguments.get("output_dir", "api_exports")
            
            # 智能处理输出目录
            if output_dir in [".", "当前目录", "项目根目录", "根目录", "当前项目", "项目下", "项目目录"]:
                output_dir = "."
            
            if not product_name or not interface_name:
                raise ValueError("缺少必需参数: product_name 和 interface_name")
            
            client = HuaweiCloudApiClient()
            async with client:
                api_info = await client.get_api_info_by_user_input(product_name, interface_name)
                
                if api_info:
                    # 构建响应文本
                    response_text = (f"华为云API信息：\n\n"
                                   f"产品：{api_info.get('product_name', 'N/A')}\n"
                                   f"接口名称：{api_info.get('api_basic_info', {}).get('summary', 'N/A')}\n"
                                   f"接口描述：{api_info.get('api_basic_info', {}).get('description', 'N/A')}\n"
                                   f"请求方法：{api_info.get('api_basic_info', {}).get('method', 'N/A')}\n"
                                   f"详细信息：{json.dumps(api_info.get('api_detail', {}), ensure_ascii=False, indent=2)}")
                    
                    # 如果需要导出YAML
                    yaml_info = ""
                    if export_yaml:
                        try:
                            exporter = YamlExporter(output_dir)
                            yaml_path = exporter.export_api_detail_to_yaml(api_info)
                            
                            # 获取绝对路径用于更清晰的显示
                            abs_yaml_path = os.path.abspath(yaml_path)
                            
                            yaml_info = f"\n\n📄 YAML文件已成功导出到: {yaml_path}"
                            yaml_info += f"\n📍 完整路径: {abs_yaml_path}"
                            
                            # 如果是输出到当前目录，特别说明
                            if output_dir == ".":
                                yaml_info += f"\n✅ 已按要求导出到项目根目录"
                                
                        except Exception as e:
                            yaml_info = f"\n\n⚠️ YAML导出失败: {str(e)}"
                    
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": response_text + yaml_info
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
        print("3. 测试YAML导出", file=sys.stderr)
        print("4. 退出", file=sys.stderr)
        
        while True:
            try:
                choice = input("请选择操作 (1-4): ")
                
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
                    print("测试YAML导出功能...", file=sys.stderr)
                    export_choice = input("选择导出类型 (1-产品列表/2-API详情): ")
                    
                    if export_choice == "1":
                        print("正在导出产品列表为YAML...", file=sys.stderr)
                        result = await self._list_products({"export_yaml": True})
                        print(result["content"][0]["text"], file=sys.stderr)
                    elif export_choice == "2":
                        product = input("请输入产品名称: ")
                        interface = input("请输入接口名称: ")
                        print(f"正在导出{product}的{interface}接口信息为YAML...", file=sys.stderr)
                        try:
                            result = await self._get_api_info({
                                "product_name": product,
                                "interface_name": interface,
                                "export_yaml": True
                            })
                            print(result["content"][0]["text"], file=sys.stderr)
                        except Exception as e:
                            print(f"导出失败: {str(e)}", file=sys.stderr)
                    else:
                        print("无效选择", file=sys.stderr)
                        
                elif choice == "4":
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
                    # 尝试提取 request_id，如果无法提取则视为通知类型请求
                    request_id = request.get("id")
                    response = await self.handle_request(request)
                    
                    # 只有非通知类型的请求才需要响应
                    if response is not None:
                        response_json = json.dumps(response, ensure_ascii=False)
                        print(response_json, flush=True)
                    
                except json.JSONDecodeError as e:
                    # JSON解析错误，尝试从原始行中提取 id
                    # 如果无法解析JSON，则无法获取 id，跳过响应
                    try:
                        # 尝试简单提取 id（如果可能）
                        id_match = re.search(r'"id"\s*:\s*([^,}\]]+)', line)
                        if id_match:
                            id_str = id_match.group(1).strip().strip('"\'')
                            try:
                                request_id = int(id_str) if id_str.isdigit() else id_str
                            except:
                                request_id = id_str
                        else:
                            request_id = None
                        
                        if request_id is not None:
                            error_response = self.create_response(
                                request_id,
                                error={"code": -32700, "message": "Parse error"}
                            )
                            if error_response is not None:
                                response_json = json.dumps(error_response, ensure_ascii=False)
                                print(response_json, flush=True)
                    except:
                        # 如果无法提取 id，跳过响应（这是通知类型或格式完全错误的请求）
                        pass
                    
                except Exception as e:
                    # 其他错误，尝试从请求中获取 id
                    try:
                        request_id = request.get("id") if 'request' in locals() else None
                        if request_id is not None:
                            error_response = self.create_response(
                                request_id,
                                error={"code": -32603, "message": f"Internal error: {str(e)}"}
                            )
                            if error_response is not None:
                                response_json = json.dumps(error_response, ensure_ascii=False)
                                print(response_json, flush=True)
                    except:
                        # 如果无法处理错误响应，跳过
                        pass
                    
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
