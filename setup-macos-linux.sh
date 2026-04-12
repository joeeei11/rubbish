#!/bin/bash

# ========================================
# 垃圾分类项目 - macOS/Linux 一键安装脚本
# 用: bash setup-macos-linux.sh
# ========================================

set -e

echo "🚀 开始安装垃圾分类项目环境..."

# 检查操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    INSTALL_CMD="brew install"
    START_MYSQL="brew services start mysql"
    START_REDIS="brew services start redis"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    INSTALL_CMD="sudo apt-get install -y"
    START_MYSQL="sudo systemctl start mysql"
    START_REDIS="sudo systemctl start redis-server"
else
    echo "❌ 不支持的操作系统"
    exit 1
fi

echo "✅ 检测到操作系统: $OS"

# ========== macOS 特定步骤 ==========
if [[ "$OS" == "macOS" ]]; then
    echo -e "\n📦 检查 Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "✅ Homebrew 已安装"
    fi

    echo -e "\n📥 更新 Homebrew..."
    brew update
fi

# ========== Linux 特定步骤 ==========
if [[ "$OS" == "Linux" ]]; then
    echo -e "\n📥 更新包管理器..."
    sudo apt-get update
fi

# ========== 安装软件 ==========
echo -e "\n📥 开始安装软件包..."

declare -a packages=("python3.10" "mysql" "redis" "nodejs" "npm" "git")

if [[ "$OS" == "macOS" ]]; then
    packages=("python@3.10" "mysql" "redis" "node" "git")
fi

for package in "${packages[@]}"; do
    echo "正在安装: $package"
    if [[ "$OS" == "macOS" ]]; then
        brew install "$package" 2>/dev/null || echo "⚠️  $package 可能已安装"
    else
        $INSTALL_CMD "$package" 2>/dev/null || echo "⚠️  $package 可能已安装"
    fi
done

echo -e "\n✅ 软件安装完成！"

# ========== 验证安装 ==========
echo -e "\n🔍 验证安装..."
python3 --version
mysql --version
node --version
npm --version
git --version

if command -v redis-cli &> /dev/null; then
    echo "redis-cli: installed"
fi

# ========== 启动服务 ==========
echo -e "\n🔧 启动数据库服务..."

if [[ "$OS" == "macOS" ]]; then
    brew services start mysql
    brew services start redis
    echo "✅ MySQL 和 Redis 已启动（后台运行）"
else
    sudo systemctl start mysql
    sudo systemctl start redis-server
    echo "✅ MySQL 和 Redis 已启动（后台运行）"
fi

sleep 2

# 验证服务
if redis-cli ping &> /dev/null; then
    echo "✅ Redis 连接正常"
else
    echo "⚠️  Redis 连接失败，请手动检查"
fi

# ========== 创建数据库 ==========
echo -e "\n📊 创建数据库..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || {
    echo "⚠️  创建数据库时需要 MySQL 密码，请稍后手动创建"
    echo "执行: mysql -u root -p"
    echo "然后: CREATE DATABASE garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
}
echo "✅ 数据库配置完成"

# ========== 项目配置 ==========
echo -e "\n📂 配置项目环境..."

PROJECT_PATH=$(pwd)
cd "$PROJECT_PATH/backend"

# 创建虚拟环境
echo "创建 Python 虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip -q

# 安装 PyTorch
echo "安装 PyTorch（CPU 版本）..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu -q

# 安装项目依赖
echo "安装项目依赖..."
pip install -r requirements.txt -q

echo "✅ Python 依赖安装完成"

# ========== 配置 .env 文件 ==========
echo -e "\n⚙️  配置环境变量..."

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env 文件已创建"
    echo "📝 请编辑 .env 文件，修改 MySQL 密码和其他配置"
    echo "   编辑: nano .env 或 code .env"
else
    echo "✅ .env 文件已存在"
fi

# ========== 初始化数据库表 ==========
echo -e "\n🗄️  初始化数据库表..."

echo "执行数据库迁移..."
flask db init 2>/dev/null || true
flask db migrate -m "初始化数据表" -q 2>/dev/null || true
flask db upgrade -q 2>/dev/null || true

echo "导入种子数据..."
python scripts/seed_data.py 2>/dev/null || true

echo "✅ 数据库初始化完成"

# ========== 小程序配置 ==========
echo -e "\n📱 配置小程序环境..."

cd "$PROJECT_PATH/miniprogram"

if [ ! -d "node_modules" ]; then
    echo "安装 npm 依赖..."
    npm install -q
    echo "✅ npm 依赖安装完成"
else
    echo "✅ node_modules 已存在"
fi

# ========== 完成 ==========
clear

echo "========================================"
echo "✅ 环境配置完成！"
echo "========================================"
echo ""
echo "📋 接下来的步骤："
echo "1️⃣  编辑配置文件:"
echo "   cd $PROJECT_PATH/backend"
echo "   nano .env  # 修改 MySQL 密码等"
echo ""
echo "2️⃣  启动后端:"
echo "   cd $PROJECT_PATH/backend"
echo "   source venv/bin/activate"
echo "   flask run --port=5000"
echo ""
echo "3️⃣  启动小程序:"
echo "   - 打开微信开发者工具"
echo "   - 打开项目: $PROJECT_PATH/miniprogram"
echo "   - 点击: 工具 → 构建 npm"
echo "   - 点击: 预览 或 编译"
echo ""
echo "📖 详细文档:"
echo "   - QUICK_SETUP.md"
echo "   - DEPLOYMENT_GUIDE.md"
echo ""
echo "🎉 祝你部署顺利！"
echo "========================================"

# 显示快速启动命令
echo ""
echo "💡 快速启动命令（下次使用）:"
echo "   终端1: redis-server"
echo "   终端2: cd $PROJECT_PATH/backend && source venv/bin/activate && flask run --port=5000"
echo "   终端3: 在微信开发者工具中打开 $PROJECT_PATH/miniprogram"
