# ========================================
# 垃圾分类项目 - Windows 一键安装脚本
# 用 PowerShell 管理员身份运行此脚本
# ========================================

Write-Host "🚀 开始安装垃圾分类项目环境..." -ForegroundColor Green

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "❌ 请以管理员身份运行此脚本！" -ForegroundColor Red
    exit 1
}

# 第一步：安装 Chocolatey（如果未安装）
Write-Host "`n📦 检查 Chocolatey..." -ForegroundColor Cyan
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "正在安装 Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
} else {
    Write-Host "✅ Chocolatey 已安装" -ForegroundColor Green
}

# 第二步：安装软件
Write-Host "`n📥 开始安装软件包..." -ForegroundColor Cyan

$packages = @(
    "python --version=3.10.0",
    "mysql",
    "redis-64",
    "nodejs-lts",
    "git"
)

foreach ($package in $packages) {
    Write-Host "正在安装: $package"
    choco install $package -y --no-progress
}

Write-Host "`n✅ 软件安装完成！" -ForegroundColor Green

# 第三步：验证安装
Write-Host "`n🔍 验证安装..." -ForegroundColor Cyan
python --version
mysql --version
node --version
npm --version
git --version

# 第四步：启动 MySQL 和 Redis
Write-Host "`n🔧 启动数据库服务..." -ForegroundColor Cyan
net start MySQL80
Write-Host "✅ MySQL 已启动" -ForegroundColor Green

# 第五步：创建数据库
Write-Host "`n📊 创建数据库..." -ForegroundColor Cyan
$mysqlInit = @"
CREATE DATABASE IF NOT EXISTS garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"@

echo $mysqlInit | mysql -u root

Write-Host "✅ 数据库已创建" -ForegroundColor Green

# 第六步：项目配置
Write-Host "`n📂 配置项目环境..." -ForegroundColor Cyan

$projectPath = Get-Location
cd "$projectPath\backend"

# 创建虚拟环境
Write-Host "创建 Python 虚拟环境..."
python -m venv venv

# 激活虚拟环境
& ".\venv\Scripts\Activate.ps1"

# 升级 pip
Write-Host "升级 pip..."
pip install --upgrade pip -q

# 安装 PyTorch
Write-Host "安装 PyTorch（CPU 版本）..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu -q

# 安装项目依赖
Write-Host "安装项目依赖..."
pip install -r requirements.txt -q

Write-Host "✅ Python 依赖安装完成" -ForegroundColor Green

# 第七步：配置 .env 文件
Write-Host "`n⚙️  配置环境变量..." -ForegroundColor Cyan

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env 文件已创建" -ForegroundColor Green
    Write-Host "📝 请编辑 .env 文件，修改 MySQL 密码和其他配置" -ForegroundColor Yellow
} else {
    Write-Host "✅ .env 文件已存在" -ForegroundColor Green
}

# 第八步：初始化数据库表
Write-Host "`n🗄️  初始化数据库表..." -ForegroundColor Cyan

Write-Host "执行数据库迁移..."
flask db init 2>$null
flask db migrate -m "初始化数据表" -q 2>$null
flask db upgrade -q 2>$null

Write-Host "导入种子数据..."
python scripts/seed_data.py -q 2>$null

Write-Host "✅ 数据库初始化完成" -ForegroundColor Green

# 第九步：小程序配置
Write-Host "`n📱 配置小程序环境..." -ForegroundColor Cyan

cd "$projectPath\miniprogram"

if (-not (Test-Path "node_modules")) {
    Write-Host "安装 npm 依赖..."
    npm install -q
    Write-Host "✅ npm 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ node_modules 已存在" -ForegroundColor Green
}

# 完成
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ 环境配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`n📋 接下来的步骤：" -ForegroundColor Cyan
Write-Host "1. 编辑 backend\.env 文件，修改 MySQL 密码"
Write-Host "2. 启动 Redis: redis-server"
Write-Host "3. 启动后端: cd backend && .\venv\Scripts\Activate.ps1 && flask run --port=5000"
Write-Host "4. 在微信开发者工具中打开 miniprogram\ 文件夹"
Write-Host "5. 在开发者工具中点击：工具 → 构建 npm"

Write-Host "`n📖 详细文档: 查看 QUICK_SETUP.md 或 DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan

Write-Host "`n🎉 祝你部署顺利！" -ForegroundColor Green
