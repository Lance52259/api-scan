#!/usr/local/bin/python3.10
"""启动Cursor优化的华为云API分析MCP服务器 - 生产版"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scan.cursor_optimized_server import main

if __name__ == "__main__":
    import asyncio
    # 强制生产模式：禁用测试模式检测
    sys.stdin = sys.stdin  # 确保stdin可用但不是tty
    
    # Python 3.6兼容性
    try:
        asyncio.run(main())
    except AttributeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
