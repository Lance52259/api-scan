#!/bin/bash
set -e

# 华为云API分析MCP服务器 - 自动安装脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/br_core_codes/install.sh | bash
# 或指定分支: BRANCH=master curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/br_core_codes/install.sh | bash

REPO_URL="https://github.com/Lance52259/api-scan.git"
REPO_NAME="api-scan"
INSTALL_DIR="$HOME/.local/share/${REPO_NAME}"
BIN_DIR="$HOME/.local/bin"
EXECUTABLE_NAME="api-scan"

# 默认分支（可通过环境变量BRANCH覆盖）
DEFAULT_BRANCH="br_core_codes"
INSTALL_BRANCH="${BRANCH:-$DEFAULT_BRANCH}"

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
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
    
    # 检查python3
    if ! command_exists python3; then
        missing_deps+=("python3")
        print_warning "缺少 python3 - 必需的运行时环境"
    else
        local python_version=$(python3 --version 2>&1)
        print_success "python3 已安装: $python_version"
        
        # 检查Python版本是否满足要求（MCP需要Python >=3.10）
        local python_major=$(python3 -c "import sys; print(sys.version_info.major)")
        local python_minor=$(python3 -c "import sys; print(sys.version_info.minor)")
        
        if [ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]; then
            print_warning "Python版本可能过低 ($python_version)，MCP建议使用Python 3.10+，但将尝试继续"
        fi
    fi
    
    # 检查pip3
    if ! command_exists pip3; then
        missing_deps+=("python3-pip")
        print_warning "缺少 pip3 - 必需用于Python包管理"
    else
        local pip_version=$(pip3 --version 2>&1)
        print_success "pip3 已安装: $pip_version"
    fi
    
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

# 安装Python依赖
install_python_deps() {
    print_step "检查和安装Python依赖..."
    
    cd "$INSTALL_DIR"
    
    # 检查requirements.txt是否存在
    if [ ! -f "requirements.txt" ]; then
        print_error "未找到requirements.txt文件"
        exit 1
    fi
    
    # 检查pip3版本并升级如果需要
    print_info "检查pip版本..."
    pip3 install --user --upgrade pip || {
        print_warning "pip升级失败，继续使用当前版本"
    }
    
    # 读取requirements.txt并逐个检查安装依赖
    print_info "分析依赖包要求..."
    local requirements_failed=false
    local missing_packages=()
    
    while IFS= read -r line || [ -n "$line" ]; do
        # 跳过空行和注释
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        
        # 提取包名（去掉版本要求）
        local package_spec="$line"
        local package_name=$(echo "$package_spec" | sed 's/[><=!].*//' | tr -d '[:space:]')
        
        if [ -n "$package_name" ]; then
            print_info "检查包: $package_name"
            
            # 检查包是否已安装
            if ! python3 -c "import $package_name" >/dev/null 2>&1; then
                # 对于mcp包的特殊处理（常见的导入名称可能不同）
                if [ "$package_name" = "mcp" ]; then
                    # 尝试检查是否有mcp相关的安装
                    if ! python3 -c "import mcp; print('MCP version:', mcp.__version__)" >/dev/null 2>&1; then
                        missing_packages+=("$package_spec")
                        print_warning "包 $package_name 未安装或版本不符合要求"
                    else
                        print_success "包 $package_name 已安装"
                    fi
                else
                    missing_packages+=("$package_spec")
                    print_warning "包 $package_name 未安装"
                fi
            else
                print_success "包 $package_name 已安装"
            fi
        fi
    done < requirements.txt
    
    # 如果有缺失的包，尝试安装
    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_step "自动安装缺失的依赖包..."
        echo "需要安装的包: ${missing_packages[*]}"
        
        # 尝试安装每个缺失的包
        for package_spec in "${missing_packages[@]}"; do
            local package_name=$(echo "$package_spec" | sed 's/[><=!].*//' | tr -d '[:space:]')
            print_info "正在安装: $package_spec"
            
            # 使用用户级安装避免权限问题
            if pip3 install --user "$package_spec"; then
                print_success "成功安装: $package_spec"
                
                # 验证安装
                if [ "$package_name" = "mcp" ]; then
                    if python3 -c "import mcp; print('MCP version:', mcp.__version__)" >/dev/null 2>&1; then
                        print_success "MCP包验证通过"
                    else
                        print_warning "MCP包安装后验证失败，但继续执行"
                    fi
                else
                    if python3 -c "import $package_name" >/dev/null 2>&1; then
                        print_success "包 $package_name 验证通过"
                    else
                        print_warning "包 $package_name 安装后验证失败"
                    fi
                fi
            else
                print_error "安装失败: $package_spec"
                requirements_failed=true
            fi
        done
    else
        print_success "所有Python依赖包已满足要求"
    fi
    
    # 最终验证：尝试安装整个requirements.txt（以防遗漏）
    print_step "执行完整依赖安装验证..."
    if pip3 install --user -r requirements.txt; then
        print_success "Python依赖安装和验证完成"
    else
        print_warning "完整依赖验证有警告，但继续执行"
    fi
    
    # 如果有关键失败，提示用户
    if [ "$requirements_failed" = true ]; then
        print_warning "某些依赖安装失败，可能影响功能"
        print_info "您可以稍后手动运行: pip3 install --user -r $INSTALL_DIR/requirements.txt"
    fi
}

# 创建全局可执行文件
create_executable() {
    print_step "创建全局命令..."
    
    local executable_path="$BIN_DIR/$EXECUTABLE_NAME"
    
    # 创建包装脚本
    cat > "$executable_path" << EOF
#!/usr/bin/env python3
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
    return sys.executable or "python3"

def run_server():
    """启动MCP服务器(生产模式)"""
    print("🚀 启动华为云API分析MCP服务器...")
    
    try:
        os.chdir(INSTALL_DIR)
        subprocess.run([get_python_executable(), "run_cursor_server.py"])
    except KeyboardInterrupt:
        print("\n⏹️  服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
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
            "src/scan/client.py"
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
            print("   - get_huawei_cloud_api_info")
            print("   - list_huawei_cloud_products") 
            print("   - list_product_apis")
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
    
    install_script_url = f"https://raw.githubusercontent.com/Lance52259/api-scan/{os.environ.get('INSTALL_BRANCH', 'br_core_codes')}/install.sh"
    
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
        current_branch = os.environ.get('INSTALL_BRANCH', 'br_core_codes')
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

支持的MCP工具:
  - get_huawei_cloud_api_info    获取API详细信息
  - list_huawei_cloud_products   列出所有华为云产品
  - list_product_apis            列出产品的API列表

Cursor配置:
  在Cursor MCP设置中使用: $EXECUTABLE_NAME --run

更新方式:
  curl -fsSL https://raw.githubusercontent.com/Lance52259/api-scan/{os.environ.get('INSTALL_BRANCH', 'br_core_codes')}/install.sh | bash
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
    
    # 检查PATH中是否已包含BIN_DIR
    if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
        print_info "PATH已包含$BIN_DIR"
        return
    fi
    
    # 检测shell类型并更新相应的配置文件
    local shell_rc=""
    local shell_name=$(basename "$SHELL")
    
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
        echo "" >> "$shell_rc"
        echo "# 华为云API分析MCP服务器" >> "$shell_rc"
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$shell_rc"
        print_success "已添加到$shell_rc"
        print_warning "请运行 'source $shell_rc' 或重新打开终端以使PATH生效"
    else
        print_warning "无法自动配置PATH，请手动添加以下行到您的shell配置文件:"
        echo "export PATH=\"$BIN_DIR:\$PATH\""
    fi
}

# 验证安装
verify_installation() {
    print_step "验证安装..."
    
    # 临时添加到PATH进行测试
    export PATH="$BIN_DIR:$PATH"
    
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
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo -e "${CYAN}🎉 华为云API分析MCP服务器安装完成！${NC}"
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
}

# 主函数
main() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "  华为云API分析MCP服务器 - 自动安装脚本"
    echo "=================================================================="
    echo -e "${NC}"
    
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

# 运行主函数
main "$@"
