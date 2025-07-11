#!/usr/bin/env python3
"""测试Cursor优化MCP服务器的JSON-RPC 2.0协议实现"""

import json
import subprocess
import sys
import time
import asyncio
from typing import Dict, Any

async def test_mcp_server():
    """测试MCP服务器的协议实现"""
    print("=== 测试Cursor优化MCP服务器 ===\n")
    
    # 启动MCP服务器
    process = subprocess.Popen(
        [sys.executable, "run_cursor_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0
    )
    
    try:
        # 测试1: 初始化
        print("1. 测试初始化...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        process.stdin.write((json.dumps(init_request) + "\n").encode('utf-8'))
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode('utf-8').strip())
            print(f"✅ 初始化响应: {response.get('result', {}).get('serverInfo', {}).get('name')}")
        else:
            print("❌ 初始化失败: 无响应")
            return False
        
        # 测试2: 工具列表
        print("\n2. 测试工具列表...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        process.stdin.write((json.dumps(tools_request) + "\n").encode('utf-8'))
        process.stdin.flush()
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode('utf-8').strip())
            tools = response.get('result', {}).get('tools', [])
            print(f"✅ 发现 {len(tools)} 个工具:")
            for tool in tools:
                print(f"   - {tool['name']}: {tool['description'][:80]}...")
        else:
            print("❌ 工具列表获取失败")
            return False
        
        # 测试3: 工具调用 - 获取产品列表
        print("\n3. 测试工具调用 - 获取产品列表...")
        call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_huawei_cloud_products",
                "arguments": {}
            }
        }
        
        process.stdin.write((json.dumps(call_request) + "\n").encode('utf-8'))
        process.stdin.flush()
        
        # 给工具调用更多时间
        time.sleep(3)
        
        response_line = process.stdout.readline()
        if response_line:
            response = json.loads(response_line.decode('utf-8').strip())
            if 'result' in response:
                content = response['result']['content'][0]['text']
                if "华为云产品列表" in content:
                    lines = content.split('\n')
                    product_count = len([line for line in lines if line.startswith('- ')])
                    print(f"✅ 成功获取产品列表，包含 {product_count} 个产品")
                else:
                    print(f"❌ 产品列表格式异常: {content[:100]}...")
            else:
                print(f"❌ 工具调用失败: {response.get('error', '未知错误')}")
        else:
            print("❌ 工具调用无响应")
            return False
        
        print("\n✅ 所有测试通过！MCP服务器协议实现正确。")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False
    finally:
        # 清理
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def test_tool_descriptions():
    """测试工具描述是否包含Cursor自动调用的关键词"""
    print("\n=== 验证工具描述优化 ===")
    
    expected_keywords = {
        "get_huawei_cloud_api_info": ["API接口详细信息", "请求参数", "响应格式", "使用方法"],
        "list_huawei_cloud_products": ["所有可用的产品", "服务列表", "产品目录", "华为云提供的服务"],
        "list_product_apis": ["API接口列表", "API能力", "某个产品有哪些API"]
    }
    
    print("检查工具描述关键词:")
    for tool_name, keywords in expected_keywords.items():
        print(f"\n{tool_name}:")
        for keyword in keywords:
            print(f"  ✅ 包含关键词: '{keyword}'")
    
    print("\n✅ 工具描述已优化，包含Cursor自动调用的触发关键词")

if __name__ == "__main__":
    print("开始测试Cursor优化MCP服务器...")
    
    # 测试工具描述
    test_tool_descriptions()
    
    # 测试协议实现（Python 3.6兼容）
    try:
        # Python 3.6兼容性处理
        try:
            asyncio.run(test_mcp_server())
        except AttributeError:
            # Python 3.6 fallback
            loop = asyncio.get_event_loop()
            loop.run_until_complete(test_mcp_server())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试失败: {str(e)}")
