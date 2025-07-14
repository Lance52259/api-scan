# YAML导出功能使用指南

## 🎯 功能概述

华为云API分析MCP服务器现在支持将API信息导出为YAML文件，方便用户保存、分享和处理API文档。

## 📋 支持的导出类型

### 1. 产品列表导出
导出华为云所有产品和服务的完整列表。

### 2. 产品API列表导出
导出指定产品的所有API接口列表。

### 3. API详细信息导出
导出指定API的完整详细信息，包括请求参数、响应格式等。

### 4. 批量API导出
从规格文件批量导出多个API的详细信息到单个文件。

## 🚀 使用方法

### 方法一：通过MCP工具（在Cursor中使用）

在Cursor Agent模式中，你可以直接请求导出YAML文件：

```
请导出华为云所有产品列表为YAML文件
请导出弹性云服务器的API列表为YAML文件  
请导出弹性云服务器的创建云服务器API详细信息为YAML文件
```

MCP工具会自动识别导出请求并生成YAML文件。

### 方法二：通过命令行工具

#### 导出所有产品列表
```bash
api-scan --yaml --products
```

#### 导出指定产品的API列表
```bash
api-scan --yaml --product-apis "弹性云服务器"
api-scan --yaml --product-apis "对象存储服务"
```

#### 导出API详细信息
```bash
api-scan --yaml --api-detail "弹性云服务器" "创建云服务器"
api-scan --yaml --api-detail "云应用" "新增/修改弹性伸缩策略"
```

#### 批量导出API详细信息
```bash
# 使用示例规格文件
api-scan --yaml --multiple-apis examples/api_specs_example.txt

# 使用自定义规格文件
api-scan --yaml --multiple-apis my_apis.txt
```

#### 指定输出目录
```bash
api-scan --yaml --products --output-dir /path/to/output
api-scan --yaml --api-detail "弹性云服务器" "创建云服务器" --output-dir ./exports
```

#### 查看YAML工具帮助
```bash
api-scan --yaml --help
```

### 方法三：直接使用YAML导出工具

```bash
# 进入安装目录
cd ~/.local/share/api-scan

# 直接使用YAML导出工具
python3.10 yaml_export_tool.py --products
python3.10 yaml_export_tool.py --product-apis "弹性云服务器"
python3.10 yaml_export_tool.py --api-detail "弹性云服务器" "创建云服务器"
```

## 📁 输出文件格式

### 产品列表文件
- **文件名**: `huawei_cloud_products.yml`
- **内容**: 所有华为云产品的结构化信息

### 产品API列表文件
- **文件名**: `<产品名>_apis.yml`
- **内容**: 指定产品的所有API接口信息

### API详细信息文件
- **文件名**: `<产品名>_<接口名>_detail.yml`
- **内容**: 单个API的完整详细信息

### 批量API文件
- **文件名**: `multiple_apis.yml`
- **内容**: 多个API的详细信息集合

## 📄 YAML文件结构

所有导出的YAML文件都包含以下结构：

```yaml
metadata:
  title: "文件标题"
  description: "文件描述"
  generated_at: "2024-01-15T10:30:00"
  generator: "华为云API分析MCP服务器"
  version: "1.0.0"

# 具体内容根据导出类型而定
products:          # 产品列表
apis:             # API列表
api:              # 单个API详情
```

## 🔧 批量导出规格文件格式

创建一个文本文件，每行一个API，格式为：`产品名,接口名`

```txt
# 示例：api_specs.txt
弹性云服务器,创建云服务器
弹性云服务器,删除云服务器
对象存储服务,上传对象
云应用,新增/修改弹性伸缩策略
```

支持的特性：
- 以 `#` 开头的行为注释
- 空行会被忽略
- 自动跳过格式错误的行

## 💡 使用示例

### 示例1：导出ECS相关API
```bash
# 1. 导出ECS产品的所有API列表
api-scan --yaml --product-apis "弹性云服务器"

# 2. 导出创建云服务器API的详细信息
api-scan --yaml --api-detail "弹性云服务器" "创建云服务器"

# 3. 导出删除云服务器API的详细信息
api-scan --yaml --api-detail "弹性云服务器" "删除云服务器"
```

### 示例2：批量导出多个服务的API
```bash
# 创建规格文件
cat > my_apis.txt << EOF
弹性云服务器,创建云服务器
弹性云服务器,删除云服务器
对象存储服务,上传对象
对象存储服务,下载对象
云应用,新增/修改弹性伸缩策略
EOF

# 批量导出
api-scan --yaml --multiple-apis my_apis.txt
```

### 示例3：导出到指定目录
```bash
# 创建输出目录
mkdir -p ./api_docs

# 导出到指定目录
api-scan --yaml --products --output-dir ./api_docs
api-scan --yaml --product-apis "弹性云服务器" --output-dir ./api_docs
```

## 🔍 在Cursor中使用YAML导出

在Cursor Agent模式中，你可以使用自然语言请求导出：

```
用户：请帮我导出华为云弹性云服务器的创建云服务器API详细信息为YAML文件

AI：我来帮您导出华为云弹性云服务器的创建云服务器API详细信息为YAML文件。

[MCP工具会自动调用get_huawei_cloud_api_info，并设置export_yaml=true]

✅ API详细信息已导出到: api_exports/弹性云服务器_创建云服务器_detail.yml
```

## 📊 输出示例

### 产品列表YAML示例
```yaml
metadata:
  title: "华为云产品列表"
  description: "华为云所有可用产品和服务的完整列表"
  generated_at: "2024-01-15T10:30:00"
  generator: "华为云API分析MCP服务器"
  version: "1.0.0"

products:
  count: 280
  items:
    - name: "弹性云服务器"
      product_short: "ecs"
      description: "提供可伸缩的计算服务"
      group: "计算"
    - name: "对象存储服务"
      product_short: "obs"
      description: "提供海量、安全、可靠的云存储服务"
      group: "存储"
```

### API详细信息YAML示例
```yaml
metadata:
  title: "弹性云服务器 - 创建云服务器"
  description: "华为云弹性云服务器产品的创建云服务器接口详细信息"
  generated_at: "2024-01-15T10:30:00"
  generator: "华为云API分析MCP服务器"
  version: "1.0.0"

api:
  product:
    name: "弹性云服务器"
    short: "ecs"
  basic_info:
    id: "create_server"
    name: "CreateServer"
    summary: "创建云服务器"
    method: "POST"
    tags: "服务器管理"
  detail:
    # 完整的API详细信息...
```

## 🎉 总结

YAML导出功能为华为云API分析MCP服务器提供了强大的数据导出能力，支持：

- ✅ 多种导出类型（产品列表、API列表、API详情、批量导出）
- ✅ 灵活的命令行工具
- ✅ Cursor Agent模式自动识别
- ✅ 结构化的YAML输出格式
- ✅ 批量处理能力
- ✅ 自定义输出目录

无论是开发者文档整理、API集成参考，还是系统集成规划，YAML导出功能都能为您提供便利的数据处理方案。 