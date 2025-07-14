#!/bin/bash
set -e

# 华为云API分析MCP服务器 - 自动安装脚本
# 
# 特性:
# • 全自动安装，无需手动干预或重启终端
# • 智能Python 3.10检测与自动安装
# • 智能pip命令选择与依赖冲突解决
# • 环境变量自动配置，立即生效
# • 支持交互式和非交互式安装模式
#
# 使用方法: 
#   curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash
# 或指定分支: 
#   BRANCH=master curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash

REPO_URL="https://github.com/Lance52259/api-scan.git"
REPO_NAME="api-scan"
INSTALL_DIR="$HOME/.local/share/${REPO_NAME}"
BIN_DIR="$HOME/.local/bin"
EXECUTABLE_NAME="api-scan"

# 默认分支（可通过环境变量BRANCH覆盖）
DEFAULT_BRANCH="master"
INSTALL_BRANCH="${BRANCH:-$DEFAULT_BRANCH}"

# 调试模式（可通过环境变量DEBUG=1启用）
DEBUG_MODE="${DEBUG:-0}"

# 全局变量
PIP_CMD=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🔧 $1${NC}"
}

print_debug() {
    if [ "$DEBUG_MODE" = "1" ]; then
        echo -e "${CYAN}🐛 DEBUG: $1${NC}"
    fi
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查并修复dpkg中断问题
fix_dpkg_interruption() {
    local max_retries=3
    local retry_count=0
    local wait_time=5
    
    while [ $retry_count -lt $max_retries ]; do
        print_info "尝试修复dpkg中断问题 (尝试 $((retry_count + 1))/$max_retries)..."
        
        if sudo dpkg --configure -a; then
            print_success "已修复dpkg中断问题"
            return 0
        else
            ((retry_count++))
            if [ $retry_count -lt $max_retries ]; then
                print_warning "修复失败，等待 ${wait_time} 秒后重试..."
                sleep $wait_time
            fi
        fi
    done
    
    print_error "修复dpkg中断问题失败（已重试 $max_retries 次）"
    print_info "建议手动运行以下命令："
    echo "   sudo dpkg --configure -a"
    echo "   sudo apt-get update"
    echo "   sudo apt-get install -f"
    return 1
}

# 检查dpkg状态并自动修复
check_and_fix_dpkg() {
    print_info "检查dpkg状态..."
    
    # 检查是否存在锁文件
    local lock_files=(
        "/var/lib/dpkg/lock"
        "/var/lib/dpkg/lock-frontend"
        "/var/lib/apt/lists/lock"
        "/var/cache/apt/archives/lock"
    )
    
    local found_locks=false
    for lock_file in "${lock_files[@]}"; do
        if [ -f "$lock_file" ]; then
            found_locks=true
            print_warning "发现dpkg/apt锁文件: $lock_file"
        fi
    done
    
    if [ "$found_locks" = true ]; then
        print_info "尝试清理锁文件..."
        for lock_file in "${lock_files[@]}"; do
            if [ -f "$lock_file" ]; then
                if sudo rm -f "$lock_file"; then
                    print_success "已删除锁文件: $lock_file"
                else
                    print_error "无法删除锁文件: $lock_file"
                fi
            fi
        done
    fi
    
    # 检查dpkg状态
    if ! sudo dpkg --status dpkg >/dev/null 2>&1 || [ -f "/var/lib/dpkg/updates" ] || [ -f "/var/lib/apt/lists/partial" ]; then
        print_warning "检测到dpkg/apt可能存在问题，尝试修复..."
        
        # 尝试修复dpkg
        if ! fix_dpkg_interruption; then
            # 如果修复失败，尝试更激进的修复方案
            print_warning "常规修复失败，尝试强制修复..."
            
            # 清理可能损坏的dpkg状态
            if sudo rm -rf /var/lib/dpkg/updates/* 2>/dev/null; then
                print_info "已清理dpkg更新状态"
            fi
            
            # 清理可能损坏的apt列表
            if sudo rm -rf /var/lib/apt/lists/partial/* 2>/dev/null; then
                print_info "已清理apt部分下载列表"
            fi
            
            # 重新初始化apt/dpkg
            print_info "重新初始化apt/dpkg..."
            if sudo apt-get clean && sudo apt-get update --fix-missing; then
                print_success "apt/dpkg重新初始化成功"
                return 0
            else
                print_error "apt/dpkg重新初始化失败"
                return 1
            fi
        fi
    else
        print_success "dpkg状态正常"
        return 0
    fi
}

# 检查sudo权限
check_sudo_access() {
    if ! sudo -v &>/dev/null; then
        print_error "需要sudo权限来安装依赖"
        print_info "请确保您有sudo权限，或联系系统管理员"
        exit 1
    fi
    print_success "sudo权限检查通过"
}

# 自动安装 Python 3.10
install_python310() {
    print_step "开始安装 Python 3.10.13..."
    
    # 检查是否为支持的系统
    if ! command_exists apt-get; then
        print_error "自动安装 Python 3.10 仅支持 Ubuntu/Debian 系统"
        print_info "请手动安装 Python 3.10 后重新运行此脚本"
        exit 1
    fi
    
    # 创建临时目录
    local temp_dir=$(mktemp -d)
    local original_dir=$(pwd)
    
    print_info "使用临时目录: $temp_dir"
    
    # 错误处理函数
    cleanup_python_install() {
        print_info "清理临时文件..."
        cd "$original_dir"
        rm -rf "$temp_dir"
    }
    
    # 设置错误时清理
    trap cleanup_python_install EXIT
    
    # 执行安装步骤
    cd "$temp_dir" || {
        print_error "无法进入临时目录"
        exit 1
    }
    
    # 检查并修复dpkg/apt
    if ! check_and_fix_dpkg; then
        print_error "无法修复dpkg/apt问题"
        exit 1
    fi
    
    # 更新包管理器
    print_info "更新包管理器..."
    local update_retries=3
    local update_retry_count=0
    
    while [ $update_retry_count -lt $update_retries ]; do
        if sudo apt-get update; then
            break
        else
            ((update_retry_count++))
            if [ $update_retry_count -lt $update_retries ]; then
                print_warning "更新失败，尝试修复并重试 ($update_retry_count/$update_retries)..."
                check_and_fix_dpkg
                sleep 5
            else
                print_error "更新包管理器失败"
                exit 1
            fi
        fi
    done
    
    # 安装编译依赖
    print_info "安装编译依赖..."
    local install_retries=3
    local install_retry_count=0
    
    while [ $install_retry_count -lt $install_retries ]; do
        if sudo apt-get install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget; then
            break
        else
            ((install_retry_count++))
            if [ $install_retry_count -lt $install_retries ]; then
                print_warning "安装失败，尝试修复并重试 ($install_retry_count/$install_retries)..."
                check_and_fix_dpkg
                sleep 5
            else
                print_error "安装编译依赖失败"
                exit 1
            fi
        fi
    done
    
    # 下载 Python 3.10.13
    print_info "下载 Python 3.10.13 源码..."
    if ! wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tar.xz; then
        print_error "下载 Python 源码失败"
        exit 1
    fi
    
    # 解压
    print_info "解压源码..."
    if ! tar -xf Python-3.10.13.tar.xz; then
        print_error "解压源码失败"
        exit 1
    fi
    
    cd Python-3.10.13 || {
        print_error "无法进入 Python 源码目录"
        exit 1
    }
    
    # 配置编译选项
    print_info "配置编译选项..."
    if ! ./configure --enable-optimizations; then
        print_error "配置编译选项失败"
        exit 1
    fi
    
    # 编译（使用所有可用CPU核心）
    print_info "编译 Python 3.10.13（这可能需要几分钟）..."
    if ! make -j $(nproc); then
        print_error "编译 Python 失败"
        exit 1
    fi
    
    # 安装
    print_info "安装 Python 3.10.13..."
    if ! sudo make altinstall; then
        print_error "安装 Python 失败"
        exit 1
    fi
    
    # 验证安装
    if command_exists python3.10; then
        local installed_version=$(python3.10 --version 2>&1)
        print_success "Python 3.10 安装成功: $installed_version"
    else
        print_error "Python 3.10 安装失败"
        exit 1
    fi
    
    # 清理临时文件
    cleanup_python_install
    trap - EXIT
    
    print_success "Python 3.10.13 安装完成"
}

# 检查并安装依赖
check_dependencies() {
    print_step "检查系统依赖..."
    
    local missing_deps=()
    local optional_missing=()
    
    # 检查git
    if ! command_exists git; then
        missing_deps+=("git")
        print_warning "缺少 git - 必需用于代码下载"
    else
        print_success "git 已安装: $(git --version | head -1)"
    fi
    
    # 检查python3.10
    if ! command_exists python3.10; then
        print_warning "缺少 python3.10 - 必需的运行时环境"
        
        # 询问是否自动安装
        echo ""
        print_info "检测到系统没有 python3.10 命令"
        print_info "MCP服务器需要 Python 3.10 或更高版本"
        echo ""
        
        # 检查是否为交互式终端
        if [ -t 0 ]; then
            echo -n "是否自动安装 Python 3.10.13? (y/N): "
            read -r response
            case "$response" in
                [yY]|[yY][eE][sS])
                    install_python310
                    ;;
                *)
                    print_info "跳过自动安装"
                    missing_deps+=("python3.10")
                    ;;
            esac
        else
            # 非交互式模式，直接安装
            print_info "非交互式模式，自动安装 Python 3.10.13"
            install_python310
        fi
    else
        local python_version=$(python3.10 --version 2>&1)
        print_success "python3.10 已安装: $python_version"
        
        # 检查Python版本是否满足要求（MCP需要Python >=3.10）
        local python_major=$(python3.10 -c "import sys; print(sys.version_info.major)")
        local python_minor=$(python3.10 -c "import sys; print(sys.version_info.minor)")
        
        if [ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]; then
            print_warning "Python版本可能过低 ($python_version)，MCP建议使用Python 3.10+，但将尝试继续"
        else
            print_success "Python版本满足要求 ($python_version)"
        fi
    fi
    
    # 智能选择pip命令（改进版本）
    local pip_cmd=""
    
    print_debug "开始pip命令检测..."
    print_debug "Python 3.10 路径: $(which python3.10 2>/dev/null || echo '未找到')"
    
    # 优先级1: 测试 python3.10 -m pip 是否可用
    if command_exists python3.10; then
        print_info "测试 python3.10 -m pip 可用性..."
        print_debug "尝试: python3.10 -m pip --version"
        if python3.10 -m pip --version >/dev/null 2>&1; then
            pip_cmd="python3.10 -m pip"
            local pip_version=$(python3.10 -m pip --version 2>&1)
            print_success "使用 python3.10 -m pip: $pip_version"
        else
            print_debug "python3.10 -m pip 不可用"
        fi
    fi
    
    # 优先级2: 如果上面失败，尝试独立的 pip3.10
    if [ -z "$pip_cmd" ] && command_exists pip3.10; then
        print_info "测试独立 pip3.10 可用性..."
        print_debug "pip3.10 路径: $(which pip3.10)"
        print_debug "pip3.10 shebang 检查: $(head -1 $(which pip3.10) 2>/dev/null || echo '无法读取')"
        
        # 测试pip3.10是否能正常工作
        print_debug "尝试: pip3.10 --version"
        if pip3.10 --version >/dev/null 2>&1; then
            pip_cmd="pip3.10"
            local pip_version=$(pip3.10 --version 2>&1)
            print_success "pip3.10 已安装且可用: $pip_version"
            
            # 检查pip3.10是否与python3.10兼容
            local pip_python_version=$(pip3.10 show pip 2>/dev/null | grep "Location:" | grep -o "python[0-9]\.[0-9]*" | head -1)
            print_debug "pip3.10 关联的Python版本: $pip_python_version"
            if [[ "$pip_python_version" != "python3.10" && "$pip_python_version" != "" ]]; then
                print_warning "检测到pip3.10可能不兼容Python 3.10，将回退到 python3.10 -m pip"
                pip_cmd="python3.10 -m pip"
            fi
        else
            print_warning "pip3.10 存在但无法正常工作，尝试其他方案"
            print_debug "pip3.10 错误输出: $(pip3.10 --version 2>&1 || echo '命令执行失败')"
        fi
    fi
    
    # 优先级3: 尝试 pip3
    if [ -z "$pip_cmd" ] && command_exists pip3; then
        print_info "测试 pip3 可用性..."
        if pip3 --version >/dev/null 2>&1; then
            pip_cmd="pip3"
            local pip_version=$(pip3 --version 2>&1)
            print_success "pip3 已安装: $pip_version"
            
            # 检查pip3是否与python3.10兼容
            local pip_python_version=$(pip3 show pip 2>/dev/null | grep "Location:" | grep -o "python[0-9]\.[0-9]*" | head -1)
            if [[ "$pip_python_version" != "python3.10" && "$pip_python_version" != "" ]]; then
                print_warning "检测到pip3可能不兼容Python 3.10，将回退到 python3.10 -m pip"
                pip_cmd="python3.10 -m pip"
            fi
        fi
    fi
    
    # 优先级4: 尝试确保 pip 模块安装
    if [ -z "$pip_cmd" ] && command_exists python3.10; then
        print_info "尝试安装 pip 模块..."
        # 尝试安装 ensurepip
        if python3.10 -m ensurepip --user >/dev/null 2>&1; then
            print_success "成功安装 pip 模块"
            pip_cmd="python3.10 -m pip"
        else
            print_warning "无法自动安装 pip 模块"
        fi
    fi
    
    # 如果所有方法都失败
    if [ -z "$pip_cmd" ]; then
        missing_deps+=("python3-pip")
        print_error "无法找到可用的 pip 命令"
        print_info "请手动安装 pip："
        echo "   sudo apt install python3.10-pip  # Ubuntu/Debian"
        echo "   或者"
        echo "   python3.10 -m ensurepip --user"
    fi
    
    # 将pip命令保存到全局变量供后续使用
    PIP_CMD="$pip_cmd"
    print_info "最终选择的pip命令: $PIP_CMD"
    
    # 检查curl（用于更新功能）
    if ! command_exists curl; then
        optional_missing+=("curl")
        print_info "curl 未安装 - 更新功能可能受限"
    else
        print_success "curl 已安装"
    fi
    
    # 检查wget（curl的备选）
    if ! command_exists wget && ! command_exists curl; then
        optional_missing+=("wget")
        print_info "wget 未安装 - 建议安装curl或wget用于下载功能"
    fi
    
    # 处理缺失的必需依赖
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "缺少必要系统依赖: ${missing_deps[*]}"
        echo ""
        print_info "请根据您的操作系统安装这些依赖:"
        echo ""
        echo "📋 Ubuntu/Debian:"
        echo "   sudo apt update && sudo apt install -y ${missing_deps[*]}"
        echo ""
        echo "📋 CentOS/RHEL 7/8:"
        echo "   sudo yum install -y ${missing_deps[*]}"
        echo ""
        echo "📋 CentOS/RHEL 9+/Fedora:"
        echo "   sudo dnf install -y ${missing_deps[*]}"
        echo ""
        echo "📋 macOS (需要Homebrew):"
        echo "   brew install ${missing_deps[*]}"
        echo ""
        echo "📋 Arch Linux:"
        echo "   sudo pacman -S ${missing_deps[*]}"
        echo ""
        
        # 提供自动安装选项（如果检测到支持的系统）
        if command_exists apt-get; then
            echo "🔧 检测到apt包管理器，您可以运行以下命令自动安装:"
            echo "   sudo apt update && sudo apt install -y ${missing_deps[*]}"
        elif command_exists yum; then
            echo "🔧 检测到yum包管理器，您可以运行以下命令自动安装:"
            echo "   sudo yum install -y ${missing_deps[*]}"
        elif command_exists dnf; then
            echo "🔧 检测到dnf包管理器，您可以运行以下命令自动安装:"
            echo "   sudo dnf install -y ${missing_deps[*]}"
        elif command_exists pacman; then
            echo "🔧 检测到pacman包管理器，您可以运行以下命令自动安装:"
            echo "   sudo pacman -S ${missing_deps[*]}"
        fi
        
        echo ""
        print_error "请安装缺失依赖后重新运行此脚本"
        exit 1
    fi
    
    # 提示可选依赖
    if [ ${#optional_missing[@]} -gt 0 ]; then
        print_info "建议安装可选依赖以获得更好体验: ${optional_missing[*]}"
    fi
    
    print_success "系统依赖检查通过"
}

# 创建必要目录
create_directories() {
    print_step "创建安装目录..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    
    print_success "目录创建完成"
}

# 克隆或更新仓库
clone_or_update_repo() {
    print_step "获取最新代码..."
    
    # 设置目标分支（可以通过环境变量覆盖）
    local target_branch="${INSTALL_BRANCH}"
    
    if [ -d "$INSTALL_DIR/.git" ]; then
        print_info "检测到已有安装，正在更新..."
        cd "$INSTALL_DIR"
        
        # 获取远程更新
        git fetch origin || {
            print_warning "获取远程更新失败，尝试继续使用本地版本"
            return 0
        }
        
        # 检查目标分支是否存在
        if git ls-remote --heads origin "$target_branch" | grep -q "$target_branch"; then
            print_info "切换到分支: $target_branch"
            git checkout "$target_branch" 2>/dev/null || git checkout -b "$target_branch" "origin/$target_branch"
            git reset --hard "origin/$target_branch"
            print_success "代码更新完成 (分支: $target_branch)"
        else
            print_warning "分支 $target_branch 不存在，尝试使用 master 分支"
            git checkout master 2>/dev/null || git checkout -b master origin/master
            git reset --hard origin/master
            print_success "代码更新完成 (分支: master)"
        fi
    else
        print_info "从GitHub克隆仓库..."
        if [ -d "$INSTALL_DIR" ]; then
            rm -rf "$INSTALL_DIR"
        fi
        
        # 克隆仓库
        if git clone "$REPO_URL" "$INSTALL_DIR"; then
            cd "$INSTALL_DIR"
            
            # 尝试切换到目标分支
            if git ls-remote --heads origin "$target_branch" | grep -q "$target_branch"; then
                print_info "切换到分支: $target_branch"
                git checkout "$target_branch"
                print_success "代码克隆完成 (分支: $target_branch)"
            else
                print_warning "分支 $target_branch 不存在，使用默认分支"
                print_success "代码克隆完成 (默认分支)"
            fi
        else
            print_error "代码克隆失败"
            exit 1
        fi
    fi
    
    # 验证关键文件存在
    local required_files=("requirements.txt" "run_cursor_server.py" "src/scan/cursor_optimized_server.py")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        print_error "关键文件缺失: ${missing_files[*]}"
        print_warning "这可能表示分支不完整或仓库结构有问题"
        
        # 如果当前在非master分支，尝试切换到master
        if [ "$target_branch" != "master" ]; then
            print_info "尝试切换到master分支..."
            if git checkout master 2>/dev/null; then
                print_info "已切换到master分支，重新检查文件..."
                missing_files=()
                for file in "${required_files[@]}"; do
                    if [ ! -f "$file" ]; then
                        missing_files+=("$file")
                    fi
                done
                
                if [ ${#missing_files[@]} -eq 0 ]; then
                    print_success "在master分支找到所有必需文件"
                else
                    print_error "即使在master分支也缺失文件，安装无法继续"
                    exit 1
                fi
            else
                print_error "无法切换到master分支，安装无法继续"
                exit 1
            fi
        else
            print_error "关键文件缺失，安装无法继续"
            exit 1
        fi
    fi
}

# 创建备用requirements文件
create_fallback_requirements() {
    local strategy_name="$1"
    local packages="$2"
    local fallback_file="requirements_${strategy_name}.txt"
    
    print_info "创建备用requirements文件: $fallback_file"
    echo "$packages" | tr ' ' '\n' > "$fallback_file"
    echo "$fallback_file"
}

# 安装Python依赖
install_python_deps() {
    print_step "检查和安装Python依赖..."
    
    cd "$INSTALL_DIR"
    
    # 检查requirements.txt是否存在
    if [ ! -f "requirements.txt" ]; then
        print_error "未找到requirements.txt文件"
        exit 1
    fi
    
    # 如果没有可用的pip命令，尝试修复
    if [ -z "$PIP_CMD" ]; then
        print_warning "没有可用的pip命令，尝试修复..."
        
        # 尝试通过ensurepip安装pip
        if command_exists python3.10; then
            print_info "尝试通过ensurepip安装pip..."
            if python3.10 -m ensurepip --user --default-pip 2>/dev/null; then
                print_success "成功安装pip模块"
                PIP_CMD="python3.10 -m pip"
            else
                print_error "无法自动安装pip，请手动安装"
                echo "请运行: python3.10 -m ensurepip --user"
                exit 1
            fi
        else
            print_error "Python 3.10不可用，无法继续"
            exit 1
        fi
    fi
    
    print_info "使用pip命令: $PIP_CMD"
    
    # 检查pip命令是否真的可用
    if ! $PIP_CMD --version >/dev/null 2>&1; then
        print_warning "pip命令无法正常工作，尝试修复..."
        
        # 如果是独立的pip3.10出现问题，回退到python -m pip
        if [[ "$PIP_CMD" == "pip3.10" ]] && command_exists python3.10; then
            print_info "回退到 python3.10 -m pip..."
            PIP_CMD="python3.10 -m pip"
            
            # 如果还是不行，尝试重新安装pip
            if ! $PIP_CMD --version >/dev/null 2>&1; then
                print_info "尝试重新安装pip模块..."
                if python3.10 -m ensurepip --user --upgrade 2>/dev/null; then
                    print_success "pip模块重新安装成功"
                else
                    print_error "无法修复pip，请手动处理"
                    echo "建议运行:"
                    echo "  python3.10 -m ensurepip --user --upgrade"
                    echo "  或"
                    echo "  sudo apt install python3.10-pip"
                    exit 1
                fi
            fi
        else
            print_error "pip命令无法工作，安装无法继续"
            exit 1
        fi
    fi
    
    # 确认pip命令可用后继续
    local pip_version=$($PIP_CMD --version 2>&1)
    print_success "确认pip可用: $pip_version"
    
    # 检查pip版本并升级如果需要
    print_info "检查pip版本..."
    
    # 首先尝试升级pip
    if $PIP_CMD install --user --upgrade pip >/dev/null 2>&1; then
        print_success "pip升级成功"
    else
        print_warning "pip升级失败，继续使用当前版本"
    fi
    
    # 更新包索引（对于老版本的pip特别重要）
    print_info "更新包索引..."
    $PIP_CMD install --user --upgrade setuptools wheel >/dev/null 2>&1 || {
        print_warning "setuptools/wheel更新失败，继续执行"
    }
    
    # 预定义的兼容版本组合
    local compatibility_sets=(
        # 策略1: 最新稳定版本（推荐）
        "mcp>=1.0.0 httpx>=0.27.0 pydantic>=1.9.0,<3.0.0 PyYAML>=6.0"
        # 策略2: MCP 1.0兼容版本
        "mcp==1.0.0 httpx>=0.27.0 pydantic>=1.9.0,<2.0.0 PyYAML>=6.0"
        # 策略3: 保守版本（如果新版本有问题）
        "mcp==1.0.0 httpx==0.27.0 pydantic==1.10.21 PyYAML==6.0"
    )
    
    print_step "尝试智能解决依赖冲突..."
    
    # 首先尝试直接安装requirements.txt
    print_info "尝试策略0: 直接安装requirements.txt..."
    if $PIP_CMD install --user -r requirements.txt --no-deps >/dev/null 2>&1; then
        # 无依赖安装成功，现在安装依赖
        if $PIP_CMD install --user -r requirements.txt >/dev/null 2>&1; then
            print_success "直接安装成功"
            verify_python_packages
            return 0
        fi
    fi
    
    print_warning "直接安装失败，尝试兼容性策略..."
    
    # 尝试不同的兼容性策略
    local strategy_num=1
    for compatibility_set in "${compatibility_sets[@]}"; do
        print_info "尝试策略${strategy_num}: 兼容版本组合"
        echo "   版本组合: $compatibility_set"
        
        # 解析包规格
        local packages=($compatibility_set)
        local install_success=true
        
        # 逐个安装包以更好地控制冲突
        for package_spec in "${packages[@]}"; do
            local package_name=$(echo "$package_spec" | sed 's/[><=!].*//' | tr -d '[:space:]')
            print_info "安装包: $package_spec"
            
            if ! $PIP_CMD install --user "$package_spec" --force-reinstall >/dev/null 2>&1; then
                print_warning "包 $package_spec 安装失败"
                install_success=false
                break
            fi
        done
        
        if [ "$install_success" = true ]; then
            print_success "策略${strategy_num}安装成功"
            verify_python_packages
            return 0
        else
            print_warning "策略${strategy_num}失败，尝试下一个策略..."
        fi
        
        ((strategy_num++))
    done
    
    # 如果所有策略都失败，尝试最后的救援方案
    print_warning "所有预定义策略失败，尝试救援安装..."
    
    # 救援策略：逐个安装核心包
    local core_packages=("PyYAML>=6.0" "pydantic>=1.9.0" "httpx>=0.27.0" "mcp>=1.0.0")
    local rescue_success=true
    
    for package_spec in "${core_packages[@]}"; do
        local package_name=$(echo "$package_spec" | sed 's/[><=!].*//' | tr -d '[:space:]')
        print_info "救援安装: $package_spec"
        
        # 尝试多种安装方式
        if $PIP_CMD install --user "$package_spec" >/dev/null 2>&1; then
            print_success "成功安装: $package_spec"
        elif $PIP_CMD install --user "$package_name" >/dev/null 2>&1; then
            print_success "成功安装: $package_name (最新版本)"
        else
            print_error "救援安装失败: $package_spec"
            rescue_success=false
            
            # 尝试特殊处理
            case "$package_name" in
                "mcp")
                    print_info "尝试安装MCP的特定版本..."
                    if $PIP_CMD install --user "mcp==1.0.0" --no-deps >/dev/null 2>&1; then
                        print_success "成功安装MCP 1.0.0 (无依赖模式)"
                    fi
                    ;;
                "httpx")
                    print_info "尝试安装兼容的httpx版本..."
                    if $PIP_CMD install --user "httpx==0.27.0" >/dev/null 2>&1; then
                        print_success "成功安装httpx 0.27.0"
                    fi
                    ;;
                "pydantic")
                    print_info "尝试安装pydantic v1..."
                    if $PIP_CMD install --user "pydantic<2.0.0" >/dev/null 2>&1; then
                        print_success "成功安装pydantic v1"
                    fi
                    ;;
            esac
        fi
    done
    
    # 最终验证
    verify_python_packages
    
    if [ "$rescue_success" = false ]; then
        print_warning "部分依赖安装可能有问题，但继续执行"
        print_info "如果遇到问题，请手动运行以下命令："
        echo "   $PIP_CMD install --user --force-reinstall mcp httpx pydantic PyYAML"
    fi
}

# 验证Python包安装
verify_python_packages() {
    print_step "验证Python包安装..."
    
    local verification_failed=false
    local required_packages=(
        "mcp:import mcp; import importlib.metadata; print('MCP version:', importlib.metadata.version('mcp'))"
        "httpx:import httpx; print('httpx version:', httpx.__version__)"
        "pydantic:import pydantic; print('pydantic version:', getattr(pydantic, '__version__', getattr(pydantic, 'VERSION', 'unknown')))"
        "PyYAML:import yaml; print('PyYAML version:', yaml.__version__)"
    )
    
    for package_info in "${required_packages[@]}"; do
        local package_name="${package_info%:*}"
        local import_test="${package_info#*:}"
        
        if python3.10 -c "$import_test" >/dev/null 2>&1; then
            local version_info=$(python3.10 -c "$import_test" 2>/dev/null)
            print_success "$package_name: $version_info"
        else
            print_error "$package_name: 未安装或导入失败"
            verification_failed=true
        fi
    done
    
    # 测试包之间的兼容性
    print_info "测试包兼容性..."
    if python3.10 -c "
import mcp, httpx, pydantic, yaml
print('✅ 所有包导入成功')

# 获取版本信息
try:
    import importlib.metadata
    mcp_version = importlib.metadata.version('mcp')
except ImportError:
    import pkg_resources
    mcp_version = pkg_resources.get_distribution('mcp').version

print(f'MCP: {mcp_version}')
print(f'httpx: {httpx.__version__}')
print(f'pydantic: {getattr(pydantic, \"__version__\", getattr(pydantic, \"VERSION\", \"unknown\"))}')
print(f'PyYAML: {yaml.__version__}')

# 测试基本功能
from mcp import ClientSession
from httpx import AsyncClient
print('✅ 基本功能导入测试通过')
" 2>/dev/null; then
        print_success "包兼容性测试通过"
    else
        print_warning "包兼容性测试失败，可能存在版本冲突"
        verification_failed=true
    fi
    
    if [ "$verification_failed" = true ]; then
        print_warning "依赖验证发现问题，但安装将继续"
        print_info "如果功能异常，请尝试重新安装："
        echo "   curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/master/install.sh | bash"
    else
        print_success "所有Python依赖验证通过"
    fi
}

# 创建全局可执行文件
create_executable() {
    print_step "创建全局命令..."
    
    local executable_path="$BIN_DIR/$EXECUTABLE_NAME"
    
    # 创建包装脚本
    cat > "$executable_path" << EOF
#!/usr/bin/env python3.10
"""
华为云API分析MCP服务器 - 全局命令行工具
自动安装版本
"""

import sys
import os

# 设置正确的安装路径和分支信息
INSTALL_DIR = "$INSTALL_DIR"
INSTALL_BRANCH = "$INSTALL_BRANCH"
DEFAULT_BRANCH = "$DEFAULT_BRANCH"

# 设置环境变量供子进程使用
os.environ['INSTALL_BRANCH'] = INSTALL_BRANCH
os.environ['DEFAULT_BRANCH'] = DEFAULT_BRANCH

sys.path.insert(0, os.path.join(INSTALL_DIR, 'src'))

# 导入主程序
import subprocess
import argparse

def get_python_executable():
    """获取Python可执行文件路径"""
    return sys.executable or "python3.10"

def run_server():
    """启动MCP服务器(生产模式)"""
    # 移除启动消息，避免干扰MCP协议通信
    # print("🚀 启动华为云API分析MCP服务器...")
    
    try:
        os.chdir(INSTALL_DIR)
        # 确保stderr用于错误信息，stdout专用于MCP协议
        subprocess.run([get_python_executable(), "run_cursor_server.py"])
    except KeyboardInterrupt:
        # 不输出停止信息，避免干扰
        pass
    except Exception as e:
        # 错误信息输出到stderr
        print(f"❌ 启动失败: {e}", file=sys.stderr)
        sys.exit(1)

def run_test():
    """启动交互式测试模式"""
    print("🔧 启动交互式测试模式...")
    
    try:
        os.chdir(INSTALL_DIR)
        subprocess.run([get_python_executable(), "test_server_interactive.py"])
    except KeyboardInterrupt:
        print("\n⏹️  测试模式已退出")
    except Exception as e:
        print(f"❌ 测试启动失败: {e}")
        sys.exit(1)

def run_yaml_export():
    """启动YAML导出工具"""
    print("📄 启动YAML导出工具...")
    
    try:
        os.chdir(INSTALL_DIR)
        # 传递命令行参数给yaml_export_tool.py
        args = sys.argv[2:]  # 跳过 'api-scan' 和 '--yaml'
        subprocess.run([get_python_executable(), "yaml_export_tool.py"] + args)
    except KeyboardInterrupt:
        print("\n⏹️  YAML导出已取消")
    except Exception as e:
        print(f"❌ YAML导出失败: {e}")
        sys.exit(1)

def check_status():
    """检查服务器状态"""
    print("🔍 检查华为云API分析MCP服务器状态...")
    
    try:
        os.chdir(INSTALL_DIR)
        
        # 检查必要文件
        required_files = [
            "run_cursor_server.py",
            "test_server_interactive.py", 
            "src/scan/cursor_optimized_server.py",
            "src/scan/client.py",
            "src/scan/yaml_exporter.py",
            "yaml_export_tool.py",
            "test_yaml_export_simple.py"
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print("❌ 缺少必要文件:")
            for file in missing_files:
                print(f"   - {file}")
            return False
        
        # 检查Python依赖
        print("🔍 检查Python依赖...")
        required_packages = [
            ("mcp", "import mcp; print('installed')"),
            ("httpx", "import httpx; print(httpx.__version__)"),
            ("pydantic", "import pydantic; print(pydantic.VERSION)"),
            ("PyYAML", "import yaml; print(yaml.__version__)")
        ]
        
        missing_packages = []
        for package_name, import_test in required_packages:
            try:
                result = subprocess.run(
                    [get_python_executable(), "-c", import_test],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    print(f"✅ {package_name}: {version}")
                else:
                    missing_packages.append(package_name)
                    print(f"❌ {package_name}: 未安装或版本不兼容")
            except:
                missing_packages.append(package_name)
                print(f"❌ {package_name}: 检查失败")
        
        if missing_packages:
            print("❌ 缺少必要的Python依赖包，请运行更新或重新安装")
            return False
        
        # 运行专门的YAML导出功能测试
        print("🔍 运行YAML导出功能完整测试...")
        try:
            result = subprocess.run(
                [get_python_executable(), "test_yaml_export_simple.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                print("✅ YAML导出功能完整测试通过")
                # 显示测试结果的关键信息
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if ('总计:' in line or '通过:' in line or '失败:' in line or 
                        '🎉 所有测试通过' in line or '⚠️ 部分测试失败' in line):
                        print(f"   {line}")
            else:
                print("❌ YAML导出功能测试失败")
                print(f"   错误: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ YAML导出功能测试执行失败: {e}")
            return False
        
        # 运行协议测试
        print("🧪 运行协议兼容性测试...")
        try:
            result = subprocess.run(
                [get_python_executable(), "test_cursor_mcp.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except TypeError:
            result = subprocess.run(
                [get_python_executable(), "test_cursor_mcp.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        if result.returncode == 0:
            print("✅ 服务器状态正常")
            print("✅ JSON-RPC 2.0协议测试通过")
            print("✅ 3个工具可用:")
            print("   - get_huawei_cloud_api_info (支持YAML导出)")
            print("   - list_huawei_cloud_products (支持YAML导出)") 
            print("   - list_product_apis (支持YAML导出)")
            print("✅ YAML导出工具可用")
            print("✅ 所有功能正常工作")
            return True
        else:
            print("❌ 协议测试失败")
            if hasattr(result, 'stderr') and result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        return False

def update():
    """更新安装"""
    print("🔄 更新华为云API分析MCP服务器...")
    
    # 重新运行安装脚本
    import urllib.request
    import tempfile
    
    install_script_url = f"https://raw.githubusercontent.com/Lance52259/api-scan/{os.environ.get('INSTALL_BRANCH', 'master')}/install.sh"
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            print("📥 下载最新安装脚本...")
            response = urllib.request.urlopen(install_script_url)
            content = response.read().decode('utf-8')
            f.write(content)
            f.flush()
            
            print("🔧 运行更新...")
            os.chmod(f.name, 0o755)
            subprocess.run(["/bin/bash", f.name])
            
            # 清理临时文件
            os.unlink(f.name)
            
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        current_branch = os.environ.get('INSTALL_BRANCH', 'master')
        print(f"请手动运行: curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/{current_branch}/install.sh | bash")

def show_help():
    """显示帮助信息"""
    print(f'''
🔧 华为云API分析MCP服务器 - 命令行工具

安装位置: {INSTALL_DIR}

用法:
  $EXECUTABLE_NAME --run       启动MCP服务器(用于Cursor配置)
  $EXECUTABLE_NAME --test      启动交互式测试模式
  $EXECUTABLE_NAME --check     检查服务器状态和依赖
  $EXECUTABLE_NAME --update    更新到最新版本
  $EXECUTABLE_NAME --yaml      启动YAML导出工具
  $EXECUTABLE_NAME --help      显示此帮助信息

示例:
  # 启动生产模式服务器(Cursor使用)
  $EXECUTABLE_NAME --run
  
  # 测试服务器功能
  $EXECUTABLE_NAME --test
  
  # 检查是否一切正常
  $EXECUTABLE_NAME --check
  
  # 更新到最新版本
  $EXECUTABLE_NAME --update
  
  # 导出所有产品列表为YAML
  $EXECUTABLE_NAME --yaml --products
  
  # 导出ECS API列表为YAML
  $EXECUTABLE_NAME --yaml --product-apis "弹性云服务器"
  
  # 导出API详细信息为YAML
  $EXECUTABLE_NAME --yaml --api-detail "弹性云服务器" "创建云服务器"

📄 YAML导出功能详解:
  $EXECUTABLE_NAME --yaml --products                          # 导出所有产品列表
  $EXECUTABLE_NAME --yaml --product-apis <产品名>             # 导出产品API列表
  $EXECUTABLE_NAME --yaml --api-detail <产品名> <接口名>       # 导出API详细信息
  $EXECUTABLE_NAME --yaml --multiple-apis <规格文件>          # 批量导出API
  $EXECUTABLE_NAME --yaml --output-dir <目录>                 # 指定输出目录
  $EXECUTABLE_NAME --yaml --help                              # YAML工具帮助

📁 YAML导出文件格式:
  - 产品列表: huawei_cloud_products.yml
  - 产品API: <产品名>_apis.yml  
  - API详情: <产品名>_<接口名>_detail.yml
  - 批量API: multiple_apis.yml
  - 默认输出目录: api_exports/

🔧 批量导出规格文件格式:
  创建文本文件，每行一个API，格式: 产品名,接口名
  示例:
    弹性云服务器,创建云服务器
    弹性云服务器,删除云服务器
    对象存储服务,上传对象

💡 自定义输出目录示例:
  $EXECUTABLE_NAME --yaml --products --output-dir ./my_exports
  $EXECUTABLE_NAME --yaml --api-detail "弹性云服务器" "创建云服务器" --output-dir /tmp/api_docs

🎯 在Cursor中使用YAML导出:
  在Cursor Agent模式中，可以直接用自然语言请求:
  "请导出华为云所有产品列表为YAML文件"
  "请导出弹性云服务器的API列表为YAML文件"
  "请导出弹性云服务器的创建云服务器API详细信息为YAML文件"

支持的MCP工具:
  - get_huawei_cloud_api_info    获取API详细信息 (支持YAML导出)
  - list_huawei_cloud_products   列出所有华为云产品 (支持YAML导出)
  - list_product_apis            列出产品的API列表 (支持YAML导出)

Cursor配置:
  在Cursor MCP设置中使用: $EXECUTABLE_NAME --run

更新方式:
  curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/{os.environ.get('INSTALL_BRANCH', 'master')}/install.sh | bash

🔍 依赖信息:
  - Python: 3.10+
  - MCP: 1.0.0+
  - httpx: 0.22.0+
  - pydantic: 1.9.0+
  - PyYAML: 6.0+ (YAML导出功能)
    '''.strip())

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="华为云API分析MCP服务器命令行工具",
        add_help=False
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--run', action='store_true', help='启动MCP服务器')
    group.add_argument('--test', action='store_true', help='启动测试模式')
    group.add_argument('--check', action='store_true', help='检查状态')
    group.add_argument('--update', action='store_true', help='更新到最新版本')
    group.add_argument('--yaml', action='store_true', help='启动YAML导出工具')
    group.add_argument('--help', action='store_true', help='显示帮助')
    
    args = parser.parse_args()
    
    if args.run:
        run_server()
    elif args.test:
        run_test()
    elif args.check:
        check_status()
    elif args.update:
        update()
    elif args.yaml:
        run_yaml_export()
    elif args.help:
        show_help()
    else:
        show_help()

if __name__ == "__main__":
    main()
EOF
    
    # 设置可执行权限
    chmod +x "$executable_path"
    
    print_success "全局命令创建完成: $executable_path"
}

# 更新PATH环境变量
update_path() {
    print_step "配置环境变量..."
    
    # 立即在当前shell中生效
    export PATH="$BIN_DIR:$PATH"
    print_info "已在当前会话中添加PATH: $BIN_DIR"
    
    # 检查PATH中是否已包含BIN_DIR
    if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
        print_success "PATH配置成功"
    fi
    
    # 检测shell类型并更新相应的配置文件
    local shell_rc=""
    local shell_name=$(basename "$SHELL")
    local config_updated=false
    
    case "$shell_name" in
        "bash")
            if [ -f "$HOME/.bashrc" ]; then
                shell_rc="$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                shell_rc="$HOME/.bash_profile"
            fi
            ;;
        "zsh")
            shell_rc="$HOME/.zshrc"
            ;;
        "fish")
            shell_rc="$HOME/.config/fish/config.fish"
            ;;
    esac
    
    if [ -n "$shell_rc" ]; then
        # 检查是否已经配置过，避免重复添加
        local path_config_line="export PATH=\"$BIN_DIR:\$PATH\""
        if ! grep -q "api-scan" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "# 华为云API分析MCP服务器" >> "$shell_rc"
            echo "$path_config_line" >> "$shell_rc"
            print_success "已添加到$shell_rc"
            config_updated=true
        else
            print_info "配置文件$shell_rc中已存在相关配置"
        fi
        
        # 自动应用配置而不是要求用户重启
        if [ "$config_updated" = true ]; then
            print_info "自动应用配置更改到当前会话..."
            # 在当前shell中source配置文件（静默处理）
            if [ -f "$shell_rc" ]; then
                source "$shell_rc" 2>/dev/null || {
                    print_debug "source配置文件时出现警告，但PATH已在当前会话中生效"
                }
            fi
            print_success "配置已自动生效，无需重启终端"
        fi
    else
        print_info "未检测到支持的shell配置文件，使用临时PATH设置"
        print_info "PATH已在当前会话中生效: $BIN_DIR"
    fi
    
    # 验证PATH是否正确设置
    if command_exists "$EXECUTABLE_NAME"; then
        print_success "命令行工具已可用"
    else
        print_debug "验证PATH设置: $PATH"
        print_info "命令行工具将在验证安装步骤中测试"
    fi
}

# 验证安装
verify_installation() {
    print_step "验证安装..."
    
    # PATH已经在update_path函数中设置，无需临时设置
    if command_exists "$EXECUTABLE_NAME"; then
        print_success "命令行工具安装成功"
        
        # 运行状态检查
        if "$EXECUTABLE_NAME" --check >/dev/null 2>&1; then
            print_success "功能测试通过"
        else
            print_warning "功能测试失败，但安装已完成"
        fi
    else
        print_error "安装失败：无法找到$EXECUTABLE_NAME命令"
        print_debug "当前PATH: $PATH"
        print_debug "查找$EXECUTABLE_NAME: $(which $EXECUTABLE_NAME 2>/dev/null || echo '未找到')"
        print_debug "BIN_DIR内容: $(ls -la $BIN_DIR/ 2>/dev/null || echo '目录不存在')"
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo -e "${CYAN}🎉 华为云API分析MCP服务器安装完成！${NC}"
    echo ""
    echo -e "${GREEN}✅ 安装特性:${NC}"
    echo "  • 全自动安装，无需手动干预"
    echo "  • 智能依赖冲突解决"
    echo "  • 环境变量自动配置，无需重启终端"
    echo "  • 支持非交互式安装模式"
    echo ""
    echo -e "${YELLOW}📋 使用方法:${NC}"
    echo "  $EXECUTABLE_NAME --help     # 查看帮助"
    echo "  $EXECUTABLE_NAME --check    # 检查状态"
    echo "  $EXECUTABLE_NAME --test     # 交互式测试"
    echo "  $EXECUTABLE_NAME --run      # 启动MCP服务器"
    echo "  $EXECUTABLE_NAME --update   # 更新到最新版本"
    echo ""
    echo -e "${YELLOW}🔧 Cursor配置:${NC}"
    echo '  {'
    echo '    "mcpServers": {'
    echo '      "api_scan": {'
    echo "        \"command\": \"$EXECUTABLE_NAME\","
    echo '        "args": ["--run"]'
    echo '      }'
    echo '    }'
    echo '  }'
    echo ""
    echo -e "${YELLOW}🔄 更新方法:${NC}"
    echo "  curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/${INSTALL_BRANCH}/install.sh | bash"
    echo ""
    echo -e "${YELLOW}💡 分支信息:${NC}"
    echo "  当前安装分支: $INSTALL_BRANCH"
    if [ "$INSTALL_BRANCH" != "$DEFAULT_BRANCH" ]; then
        echo "  默认分支: $DEFAULT_BRANCH"
        echo "  使用默认分支更新: BRANCH=$DEFAULT_BRANCH curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/$DEFAULT_BRANCH/install.sh | bash"
    fi
    echo ""
    echo -e "${YELLOW}🔧 依赖冲突解决:${NC}"
    echo "  本安装脚本包含智能依赖冲突解决机制："
    echo "  • 策略1: 最新稳定版本 (mcp>=1.0.0, httpx>=0.27.0, pydantic>=1.9.0,<3.0.0)"
    echo "  • 策略2: MCP 1.0兼容版本 (固定MCP版本,灵活其他包版本)"
    echo "  • 策略3: 保守版本 (所有包使用经过测试的稳定版本)"
    echo "  • 救援模式: 逐个安装核心包,处理特殊冲突"
    echo ""
    echo "  如果安装失败,可以手动运行:"
    echo "    pip3.10 install --user --force-reinstall mcp httpx pydantic PyYAML"
    echo ""
}

# 主函数
main() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "  华为云API分析MCP服务器 - 自动安装脚本"
    echo "=================================================================="
    echo -e "${NC}"
    
    # 检查sudo权限
    check_sudo_access
    
    # 检查并修复dpkg/apt
    if ! check_and_fix_dpkg; then
        print_error "无法修复系统包管理器问题，安装无法继续"
        exit 1
    fi
    
    # 继续其他安装步骤
    check_dependencies
    create_directories
    clone_or_update_repo
    install_python_deps
    create_executable
    update_path
    verify_installation
    show_usage
    
    print_success "安装完成！"
}

# 执行主函数
main "$@"
