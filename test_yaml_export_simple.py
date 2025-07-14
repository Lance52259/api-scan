#!/usr/bin/env python3.10
"""
YAML导出功能简化测试脚本
用于验证YAML导出功能的基本正确性
"""

import sys
import os
import tempfile
import shutil

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_yaml_basic():
    """测试PyYAML基本功能"""
    print("🔍 测试PyYAML基本功能...")
    try:
        import yaml
        print(f"✅ PyYAML 版本: {yaml.__version__}")
        
        # 测试基本序列化
        test_data = {"test": "data", "number": 123}
        yaml_str = yaml.dump(test_data, default_flow_style=False, allow_unicode=True)
        parsed_data = yaml.safe_load(yaml_str)
        
        if parsed_data == test_data:
            print("✅ PyYAML 序列化/反序列化测试通过")
            return True
        else:
            print("❌ PyYAML 序列化/反序列化测试失败")
            return False
    except Exception as e:
        print(f"❌ PyYAML 测试失败: {e}")
        return False

def test_yaml_exporter():
    """测试YamlExporter基本功能"""
    print("🔍 测试YamlExporter基本功能...")
    try:
        from scan.yaml_exporter import YamlExporter
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="yaml_test_")
        print(f"📁 临时目录: {temp_dir}")
        
        try:
            # 创建导出器
            exporter = YamlExporter(temp_dir)
            print("✅ YamlExporter 创建成功")
            
            # 测试头部生成
            header = exporter.generate_yaml_header("测试标题", "测试描述")
            if "metadata" in header and "title" in header["metadata"]:
                print("✅ YAML头部生成测试通过")
            else:
                print("❌ YAML头部生成测试失败")
                return False
            
            # 测试数据清理
            test_data = {"string": "test", "number": 123, "list": [1, 2, 3]}
            cleaned = exporter.clean_data_for_yaml(test_data)
            if cleaned == test_data:
                print("✅ 数据清理功能测试通过")
            else:
                print("❌ 数据清理功能测试失败")
                return False
            
            # 测试产品导出
            mock_products = {
                "groups": [{
                    "name": "测试组",
                    "products": [{
                        "name": "测试产品",
                        "productshort": "test",
                        "description": "测试描述"
                    }]
                }]
            }
            
            output_path = exporter.export_products_to_yaml(mock_products, "test_products.yml")
            if os.path.exists(output_path):
                print("✅ 产品列表导出测试通过")
                print(f"📄 输出文件: {output_path}")
            else:
                print("❌ 产品列表导出测试失败")
                return False
            
            return True
            
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir)
            print(f"🧹 清理临时目录: {temp_dir}")
            
    except Exception as e:
        print(f"❌ YamlExporter 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_yaml_cli():
    """测试YamlExportCLI基本功能"""
    print("🔍 测试YamlExportCLI基本功能...")
    try:
        from scan.yaml_exporter import YamlExportCLI
        
        temp_dir = tempfile.mkdtemp(prefix="yaml_cli_test_")
        print(f"📁 临时目录: {temp_dir}")
        
        try:
            cli = YamlExportCLI(temp_dir)
            print("✅ YamlExportCLI 创建成功")
            return True
            
        finally:
            shutil.rmtree(temp_dir)
            print(f"🧹 清理临时目录: {temp_dir}")
            
    except Exception as e:
        print(f"❌ YamlExportCLI 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 华为云API分析MCP服务器 - YAML导出功能简化测试")
    print("=" * 60)
    
    tests = [
        ("PyYAML基本功能", test_yaml_basic),
        ("YamlExporter功能", test_yaml_exporter),
        ("YamlExportCLI功能", test_yaml_cli),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 测试:")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                failed += 1
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} 测试异常: {e}")
        print("-" * 40)
    
    print("\n📊 测试结果汇总:")
    print("=" * 60)
    print(f"总计: {len(tests)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    
    if failed == 0:
        print("🎉 所有测试通过！YAML导出功能正常")
        sys.exit(0)
    else:
        print("⚠️ 部分测试失败，请检查YAML导出功能")
        sys.exit(1)

if __name__ == "__main__":
    main() 