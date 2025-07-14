# 华为云API分析MCP服务器

基于 Model Context Protocol (MCP) 的华为云API文档查询工具，专为Cursor IDE优化。

## ✨ 特性

- 🔍 **智能API查询** - 通过自然语言查询华为云API文档
- 🤖 **Cursor集成** - 在Cursor Agent模式中自动识别并调用工具
- 🌐 **全局命令** - 一键安装，任意路径使用
- 📊 **完整覆盖** - 支持280+华为云产品和服务
- 🔧 **易于维护** - 内置状态检查和诊断功能
- 🐍 **Python 3.10 自动安装** - 自动检测并安装 Python 3.10（Ubuntu/Debian）

## 🚀 快速开始

### 一键安装
```bash
# 使用 curl 安装（推荐）
curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash

# 或使用 wget
wget -qO- https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash

# 或克隆后安装
git clone https://github.com/Lance52259/api-scan.git
cd api-scan
./install.sh
```

### Python 3.10 自动安装
如果系统没有 Python 3.10，安装脚本会自动：
- 检测系统环境（支持 Ubuntu/Debian）
- 询问是否安装 Python 3.10.13
- 自动下载、编译和安装 Python 3.10
- 安装完成后继续 MCP 服务器安装

详细信息请参考：[Python 3.10 自动安装功能](docs/PYTHON_AUTO_INSTALL.md)

### 配置Cursor
在Cursor MCP设置中添加：
```json
{
  "mcpServers": {
    "api_scan": {
      "command": "api-scan",
      "args": ["--run"]
    }
  }
}
```

## 📋 命令参考

| 命令 | 功能 | 用途 |
|------|------|------|
| `api-scan --run` | 启动MCP服务器 | Cursor配置使用 |
| `api-scan --test` | 交互式测试 | 功能验证 |
| `api-scan --check` | 状态检查 | 诊断问题 |
| `api-scan --help` | 显示帮助 | 查看用法 |

## 🎯 支持的查询

### 产品列表
```
华为云有哪些产品和服务？
我想了解华为云提供的所有服务
```

### API列表  
```
华为云ECS有哪些API接口？
RDS产品提供哪些API？
```

### API详细信息
```
我需要创建云服务器的API详细信息
华为云对象存储上传文件的API怎么用？
```

## 🔧 技术架构

- **协议**: JSON-RPC 2.0 (MCP标准)
- **Python版本**: 3.10+ (自动安装支持)
- **工具数量**: 3个核心工具
- **产品覆盖**: 280+华为云产品
- **兼容性**: Ubuntu/Debian (自动安装), 其他系统需手动安装Python

## 📁 项目结构

```
api-scan/
├── api-scan                           # 全局命令行工具
├── install.sh                         # 增强安装脚本（支持Python自动安装）
├── run_cursor_server.py               # MCP服务器启动器
├── yaml_export_tool.py                # YAML导出工具
├── src/scan/
│   ├── cursor_optimized_server.py     # 核心MCP服务器
│   ├── client.py                      # 华为云API客户端
│   ├── yaml_exporter.py               # YAML导出模块
│   └── models.py                      # 数据模型
├── docs/
│   ├── INSTALL_GUIDE.md                     # 安装指南
│   ├── CURSOR_AUTO_TOOL_USAGE.md            # 使用指南
│   ├── PYTHON_AUTO_INSTALL.md               # Python自动安装说明
│   ├── YAML_EXPORT_GUIDE.md                 # YAML导出功能指南
│   └── DEPENDENCY_CONFLICT_RESOLUTION.md    # 依赖冲突解决方案
└── requirements.txt                         # 依赖声明
```

## 🛠️ 开发

### 运行测试
```bash
# 协议兼容性测试
python3 test_cursor_mcp.py

# 交互式功能测试  
api-scan --test

# 状态检查
api-scan --check
```

### 调试
```bash
# 查看服务器日志
api-scan --run > server.log 2>&1

# 检查配置
api-scan --help
```

## 🐍 Python 环境要求

### 自动安装（推荐）
- **支持系统**: Ubuntu/Debian
- **自动检测**: 缺少 Python 3.10 时自动安装
- **安装版本**: Python 3.10.13
- **编译优化**: 启用优化选项

### 手动安装
对于其他系统，请手动安装 Python 3.10+：
```bash
# CentOS/RHEL
sudo dnf install python3.10 python3.10-pip

# macOS
brew install python@3.10

# Arch Linux
sudo pacman -S python310
```

## 📖 文档

- [安装指南](docs/INSTALL_GUIDE.md) - 详细的安装和配置说明
- [使用指南](docs/CURSOR_AUTO_TOOL_USAGE.md) - Cursor Agent模式使用方法
- [Python自动安装](docs/PYTHON_AUTO_INSTALL.md) - Python 3.10 自动安装功能详解
- [YAML导出指南](docs/YAML_EXPORT_GUIDE.md) - YAML导出功能详细说明
- [依赖冲突解决](docs/DEPENDENCY_CONFLICT_RESOLUTION.md) - 依赖版本冲突解决方案

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**让华为云API查询变得更简单！** 🎉
