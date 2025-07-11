# Cursor MCP 自动工具调用使用指南

## 🎯 让Cursor在聊天中自动识别并调用华为云API工具

您的华为云API分析MCP服务器已经完全配置并优化，可以在Cursor的Agent模式中自动识别用户意图并调用相应工具。

## ✅ 配置状态确认

经过测试验证：
- ✅ MCP服务器协议实现正确（JSON-RPC 2.0）
- ✅ 3个工具全部正常工作
- ✅ 成功获取280个华为云产品列表
- ✅ 工具描述已优化，包含自动调用触发关键词
- ✅ **生产版服务器不再进入测试模式**

## 🔧 最终配置步骤

### 1. 确认服务器正常运行
```bash
# 生产版服务器测试（应该返回JSON-RPC响应）
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | python3 run_cursor_server.py

# 交互式测试（如需要）
python3 test_server_interactive.py
```

### 2. 配置Cursor MCP
在Cursor MCP配置文件中添加：
```json
{
  "mcpServers": {
    "api_scan": {
      "command": "python3",
      "args": ["run_cursor_server.py"],
      "cwd": "/home/huawei/go/src/github.com/Lance52259/api-scan"
    }
  }
}
```

**配置文件位置**：
- Linux: `~/.config/Cursor/User/globalStorage/cursor.mcp/mcp_config.json`
- Windows: `%APPDATA%\Cursor\User\globalStorage\cursor.mcp\mcp_config.json`
- macOS: `~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp_config.json`

### 3. 重启Cursor
完全退出并重新启动Cursor，等待MCP连接建立。

## 🎮 自动工具调用示例

### ⭐ 重要：必须使用Agent模式
在Cursor中开始新对话时，确保选择**"Agent"模式**（带机器人图标），不是普通聊天模式。

### 触发 `list_huawei_cloud_products` 的查询：
```
华为云有哪些产品和服务？
我想了解华为云提供的所有服务
华为云的产品目录是什么？
华为云都有什么云服务可以用？
请显示华为云的服务列表
```

**期望结果**：Cursor自动调用工具，显示280+个华为云产品列表

### 触发 `list_product_apis` 的查询：
```
华为云ECS有哪些API接口？
RDS产品提供哪些API？
弹性云服务器产品的API列表
VPC服务有什么API可以调用？
请告诉我华为云存储服务的所有API
```

**期望结果**：Cursor自动查找产品并列出其API接口

### 触发 `get_huawei_cloud_api_info` 的查询：
```
我需要创建云服务器的API详细信息
请告诉我华为云ECS创建实例的API参数
华为云对象存储上传文件的API怎么用？
如何调用华为云RDS创建数据库实例的接口？
华为云负载均衡创建监听器的API详细说明
```

**期望结果**：Cursor自动获取具体API的详细信息和参数

### 复合查询（自动调用多个工具）：
```
我想使用华为云的存储服务，请帮我查看有哪些相关产品以及它们的API
比较华为云ECS和BMS的API差异
我需要搭建一个完整的云服务架构，请告诉我华为云有哪些相关服务和API
华为云的AI服务都有什么，以及主要的API接口是什么？
```

**期望结果**：Cursor智能分析需求，依次调用多个工具获取信息

## 🔍 验证自动调用是否工作

### 正确的工作流程：
1. **输入查询** → 在Agent模式下输入自然语言查询
2. **Cursor分析** → Cursor识别需要调用MCP工具
3. **显示工具调用** → 界面显示"正在调用工具 list_huawei_cloud_products..."
4. **显示结果** → 返回结构化的华为云信息

### 测试查询：
```
华为云有哪些产品？
```

**如果配置正确**，您应该看到：
- Cursor显示"正在调用工具..."
- 工具名称: `list_huawei_cloud_products`
- 返回280+个产品的格式化列表

## 🔧 故障排除

### 问题1：工具没有被自动调用
**原因**：
1. ❌ 没有使用Agent模式
2. ❌ MCP服务器未连接
3. ❌ 查询语言不够明确

**解决方案**：
1. ✅ 确保使用Agent模式
2. ✅ 检查Cursor设置 → MCP → 确认`api_scan`状态为Connected
3. ✅ 使用包含"华为云"、"API"、"产品"等关键词的查询

### 问题2：MCP服务器连接失败
**检查**：
```bash
# 1. 确认文件存在且可执行
ls -la run_cursor_server.py

# 2. 测试服务器功能
python3 run_cursor_server.py
# 应该进入测试模式

# 3. 检查Python环境
python3 --version
python3 -c "import asyncio, httpx; print('环境正常')"
```

### 问题3：权限或路径问题
```bash
# 确保正确的工作目录
cd /home/huawei/go/src/github.com/Lance52259/api-scan

# 确认绝对路径
pwd

# 在Cursor配置中使用完整绝对路径
```

## 📝 使用技巧

### 自然语言查询模式
✅ **推荐的查询方式**：
- 使用完整的句子：「我想了解华为云的存储服务」
- 包含具体需求：「我需要创建云服务器的API」
- 明确指定产品：「华为云ECS的API列表」

❌ **避免的查询方式**：
- 过于简短：「ECS」
- 模糊不清：「API」
- 没有上下文：「列表」

### 提高识别准确率
- 包含「华为云」关键词
- 明确说明需要查询的内容类型（产品、API、详细信息）
- 使用产品的常见名称（ECS、RDS、VPC等）

## 🚀 高级用法

### 场景化查询
```
我正在开发一个Web应用，需要用到华为云的计算、存储和数据库服务，请帮我查看相关的产品和API

我想实现文件上传下载功能，华为云有哪些存储相关的服务和API接口？

我需要搭建高可用架构，请告诉我华为云的负载均衡和弹性伸缩相关的API
```

### 对比分析
```
请比较华为云ECS和BMS服务的API差异

华为云的关系型数据库和NoSQL数据库都有哪些产品和API？

华为云AI服务和大数据服务的主要API接口对比
```

---

## ✅ 配置成功标志

当一切配置正确时，您将体验到：

1. **智能识别**：输入自然语言后，Cursor自动识别需要调用华为云API工具
2. **透明调用**：显示具体调用的工具名称和参数
3. **结构化结果**：返回格式良好的华为云产品和API信息
4. **上下文理解**：能够根据对话上下文智能选择合适的工具

**🎉 现在您可以在Cursor中通过自然语言直接查询华为云API信息了！**
