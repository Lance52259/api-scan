# 华为云API分析MCP服务器 - 全局命令安装指南

## 🚀 快速安装

### 1. 一键安装
```bash
curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash
```

### 2. 验证安装
```bash
# 在任意目录测试
cd /tmp
api-scan --help
api-scan --check
```

## 📋 命令参考

### 基本用法
```bash
api-scan [选项]
```

### 可用选项

| 选项 | 说明 | 用途 |
|------|------|------|
| `--run` | 启动MCP服务器(生产模式) | Cursor配置使用 |
| `--test` | 启动交互式测试模式 | 手动功能测试 |
| `--check` | 检查服务器状态 | 诊断问题 |
| `--install` | 安装到系统PATH | 首次安装 |
| `--help` | 显示帮助信息 | 查看用法 |

## 🔧 Cursor配置更新

### 新的Cursor MCP配置
现在可以使用全局命令配置Cursor：

```json
{
  "mcpServers": {
    "api_scan": {
      "command": "wsl",
      "args": ["/home/huawei/.local/bin/api-scan", "--run"]
    }
  }
}
```

**配置文件位置**：
- Linux: `~/.config/Cursor/User/globalStorage/cursor.mcp/mcp_config.json`
- Windows: `%APPDATA%\Cursor\User\globalStorage\cursor.mcp\mcp_config.json`
- macOS: `~/Library/Application Support/Cursor/User/globalStorage/cursor.mcp/mcp_config.json`

### 对比：旧配置 vs 新配置

**旧配置** (不再推荐):
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

**新配置** (推荐):
```json
{
  "mcpServers": {
    "api_scan": {
      "command": "wsl",
      "args": ["/home/huawei/.local/bin/api-scan", "--run"]
    }
  }
}
```

**新配置的优势**：
- ✅ 不需要指定`cwd`路径
- ✅ 在任何目录都能工作
- ✅ 更简洁的配置
- ✅ 便于版本管理和迁移

## 💡 使用示例

### 日常操作
```bash
# 检查服务器状态
api-scan --check

# 启动测试模式
api-scan --test

# 启动生产服务器(通常由Cursor调用)
api-scan --run
```

### 故障排除
```bash
# 检查是否所有依赖都正常
api-scan --check

# 如果有问题，可以运行交互式测试
api-scan --test
```

### 系统维护
```bash
# 重新安装/更新命令
cd /home/huawei/go/src/github.com/Lance52259/api-scan
./api-scan --install
```

## 🔍 功能特性

### 智能路径管理
- 自动检测服务器根目录
- 无需手动设置工作目录
- 支持从任意位置调用

### 完整的生命周期管理
- 安装：`--install`
- 运行：`--run`
- 测试：`--test`
- 诊断：`--check`

### Python环境兼容
- 自动检测Python可执行文件
- Python 3.6+ 兼容性
- 错误处理和友好提示

## ✅ 验证清单

安装完成后，确认以下功能：

- [ ] `api-scan --help` 显示帮助信息
- [ ] `api-scan --check` 通过所有检查
- [ ] `api-scan --test` 可以启动交互式测试
- [ ] 在任意目录都能执行 `api-scan` 命令
- [ ] Cursor MCP配置使用新的简化配置

## 🎯 下一步

1. **更新Cursor配置**：使用新的简化配置
2. **重启Cursor**：让新配置生效
3. **测试Agent模式**：在Cursor Agent模式中测试自动工具调用

---

**现在您拥有了一个完整的、可在任意位置使用的华为云API分析命令行工具！** 🎉
