#!/usr/bin/env python3.10
"""
华为云API信息YAML导出工具
独立的命令行工具，用于将华为云API信息导出为YAML文件
"""

import sys
import os
import asyncio
import argparse
from typing import List, Tuple

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scan.yaml_exporter import YamlExportCLI


def print_help():
    """显示帮助信息"""
    print("""
🔧 华为云API信息YAML导出工具

用法:
  python3.10 yaml_export_tool.py --products                           # 导出所有产品列表
  python3.10 yaml_export_tool.py --product-apis <产品名>              # 导出指定产品的API列表
  python3.10 yaml_export_tool.py --api-detail <产品名> <接口名>        # 导出指定API详细信息
  python3.10 yaml_export_tool.py --multiple-apis <规格文件>           # 导出多个API详细信息
  python3.10 yaml_export_tool.py --output-dir <目录>                  # 指定输出目录（默认：api_exports）

示例:
  # 导出所有产品列表
  python3.10 yaml_export_tool.py --products
  
  # 导出ECS的API列表
  python3.10 yaml_export_tool.py --product-apis "弹性云服务器"
  
  # 导出创建云服务器API的详细信息
  python3.10 yaml_export_tool.py --api-detail "弹性云服务器" "创建云服务器"
  
  # 导出多个API详细信息
  python3.10 yaml_export_tool.py --multiple-apis apis_spec.txt
  
  # 指定输出目录
  python3.10 yaml_export_tool.py --products --output-dir /path/to/output

多个API规格文件格式:
  每行一个API，格式为：产品名,接口名
  示例：
    弹性云服务器,创建云服务器
    弹性云服务器,删除云服务器
    对象存储服务,上传对象
    
输出文件:
  - 产品列表: huawei_cloud_products.yml
  - 产品API列表: <产品名>_apis.yml
  - API详细信息: <产品名>_<接口名>_detail.yml
  - 多个API: multiple_apis.yml
    """.strip())


def parse_multiple_apis_file(file_path: str) -> List[Tuple[str, str]]:
    """解析多个API规格文件"""
    api_specs = []
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return api_specs
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        product_name = parts[0].strip()
                        interface_name = parts[1].strip()
                        api_specs.append((product_name, interface_name))
                    else:
                        print(f"⚠️ 第{line_num}行格式错误，跳过: {line}")
                else:
                    print(f"⚠️ 第{line_num}行缺少逗号分隔符，跳过: {line}")
    
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
    
    return api_specs


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="华为云API信息YAML导出工具",
        add_help=False
    )
    
    # 动作选项
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--products', action='store_true', help='导出所有产品列表')
    action_group.add_argument('--product-apis', metavar='PRODUCT', help='导出指定产品的API列表')
    action_group.add_argument('--api-detail', nargs=2, metavar=('PRODUCT', 'INTERFACE'), help='导出指定API详细信息')
    action_group.add_argument('--multiple-apis', metavar='FILE', help='从文件导出多个API详细信息')
    action_group.add_argument('--help', action='store_true', help='显示帮助信息')
    
    # 配置选项
    parser.add_argument('--output-dir', default='api_exports', help='输出目录（默认：api_exports）')
    
    args = parser.parse_args()
    
    if args.help:
        print_help()
        return
    
    try:
        async with YamlExportCLI(args.output_dir) as exporter:
            if args.products:
                print("📋 导出所有华为云产品列表...")
                output_path = await exporter.export_all_products()
                print(f"🎉 导出完成！文件位置: {output_path}")
                
            elif args.product_apis:
                product_name = args.product_apis
                print(f"📋 导出{product_name}的API列表...")
                output_path = await exporter.export_product_apis(product_name)
                print(f"🎉 导出完成！文件位置: {output_path}")
                
            elif args.api_detail:
                product_name, interface_name = args.api_detail
                print(f"📋 导出{product_name}的{interface_name}接口详细信息...")
                output_path = await exporter.export_api_detail(product_name, interface_name)
                print(f"🎉 导出完成！文件位置: {output_path}")
                
            elif args.multiple_apis:
                spec_file = args.multiple_apis
                print(f"📋 从文件{spec_file}导出多个API详细信息...")
                
                api_specs = parse_multiple_apis_file(spec_file)
                if not api_specs:
                    print("❌ 没有找到有效的API规格")
                    return
                
                print(f"📋 找到{len(api_specs)}个API规格:")
                for i, (product, interface) in enumerate(api_specs, 1):
                    print(f"  {i}. {product} - {interface}")
                
                output_path = await exporter.export_multiple_api_details(api_specs)
                print(f"🎉 导出完成！文件位置: {output_path}")
                
    except KeyboardInterrupt:
        print("\n⏹️  用户取消操作")
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 检查Python版本
    if sys.version_info < (3, 10):
        print("❌ 需要Python 3.10或更高版本")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except AttributeError:
        # Python 3.6兼容性
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main()) 