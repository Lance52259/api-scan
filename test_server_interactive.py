#!/usr/bin/env python3
"""交互式测试华为云API分析MCP服务器"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scan.cursor_optimized_server import CursorOptimizedMCPServer

async def main():
    """测试模式主函数"""
    server = CursorOptimizedMCPServer()
    await server.test_mode()

if __name__ == "__main__":
    import asyncio
    print("=== 华为云API分析MCP服务器 - 交互式测试模式 ===")
    
    # Python 3.6兼容性
    try:
        asyncio.run(main())
    except AttributeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
