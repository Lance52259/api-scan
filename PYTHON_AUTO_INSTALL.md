# Python 3.10 自动安装功能

## 🎯 功能概述

安装脚本现在支持自动检测并安装 Python 3.10.13，当系统中缺少 `python3.10` 命令时会自动触发。

## 🔧 触发条件

- 系统中没有 `python3.10` 命令
- 仅支持 Ubuntu/Debian 系统（使用 apt 包管理器）
- MCP 服务器需要 Python 3.10 或更高版本

## 📋 安装步骤

当检测到缺少 `python3.10` 时，脚本会执行以下步骤：

### 1. 系统检查
- 检测是否为 Ubuntu/Debian 系统
- 确认 `apt-get` 包管理器可用

### 2. 用户确认
- **交互式模式**: 询问用户是否安装 Python 3.10.13
- **非交互式模式**: 自动安装

### 3. 环境准备
```bash
# 创建临时目录
temp_dir=$(mktemp -d)

# 更新包管理器
sudo apt update

# 安装编译依赖
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
```

### 4. 下载和编译
```bash
# 下载 Python 3.10.13 源码
wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tar.xz

# 解压
tar -xf Python-3.10.13.tar.xz
cd Python-3.10.13

# 配置编译选项
./configure --enable-optimizations

# 编译（使用所有可用CPU核心）
make -j $(nproc)

# 安装
sudo make altinstall
```

### 5. 验证和清理
- 验证 `python3.10` 命令可用
- 清理临时文件和目录
- 继续正常的安装流程

## 🚀 使用方法

### 交互式安装
```bash
./install.sh
```

当检测到缺少 Python 3.10 时，会提示：
```
ℹ️  检测到系统没有 python3.10 命令
ℹ️  MCP服务器需要 Python 3.10 或更高版本

是否自动安装 Python 3.10.13? (y/N): 
```

### 非交互式安装
```bash
# 通过管道自动确认
echo 'y' | ./install.sh

# 或者使用 curl 安装
curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash
```

## ⚠️ 注意事项

### 系统要求
- 仅支持 Ubuntu/Debian 系统
- 需要 sudo 权限
- 需要互联网连接下载源码

### 时间消耗
- 编译过程可能需要 5-15 分钟
- 取决于系统性能和 CPU 核心数

### 磁盘空间
- 编译过程需要约 500MB 临时空间
- 最终安装约占用 100MB

### 安全性
- 使用 `make altinstall` 避免覆盖系统默认 Python
- 不会影响现有的 Python 安装
- 临时文件自动清理

## 🔍 故障排除

### 编译依赖问题
如果编译依赖安装失败，请手动安装：
```bash
sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
```

### 下载失败
如果网络问题导致下载失败，可以：
1. 检查网络连接
2. 使用代理或镜像源
3. 手动下载并放置到临时目录

### 编译失败
如果编译过程失败：
1. 检查系统是否有足够的磁盘空间
2. 确认所有编译依赖已安装
3. 查看错误日志定位问题

### 权限问题
确保有 sudo 权限执行：
- `sudo apt update`
- `sudo apt install`
- `sudo make altinstall`

## 🎉 安装完成

安装成功后，你将看到：
```
✅ Python 3.10 安装成功: Python 3.10.13
✅ Python 3.10.13 安装完成
```

之后脚本会继续正常的 MCP 服务器安装流程。

## 🔄 更新说明

这个功能已集成到主安装脚本中，无需额外配置。当你运行安装脚本时，如果系统缺少 Python 3.10，会自动触发安装流程。

---

**让 Python 3.10 安装变得更简单！** 🐍✨ 