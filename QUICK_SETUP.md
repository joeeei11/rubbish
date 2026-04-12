# ⚡ 快速环境配置指南 - 可直接复制粘贴

> 针对**零基础、新电脑**的快速配置方案。选择你的操作系统，逐行复制粘贴执行。

---

## 🪟 Windows 用户（推荐用 PowerShell）

### 第一步：下载并安装基础软件

打开 PowerShell **以管理员身份运行**，逐条执行：

```powershell
# 1. 安装 Python 3.10（使用 Chocolatey）
choco install python --version=3.10.0 -y

# 2. 安装 MySQL 8.0
choco install mysql -y

# 3. 安装 Redis
choco install redis-64 -y

# 4. 安装 Node.js LTS
choco install nodejs-lts -y

# 5. 安装 Git
choco install git -y
```

**如果没有安装 Chocolatey**，先运行以下命令安装它：

```powershell
# 在 PowerShell 中以管理员身份运行
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### 第二步：验证安装

```powershell
python --version
mysql --version
node --version
npm --version
git --version
```

如果都显示版本号，说明安装成功 ✅

### 第三步：启动 MySQL 和 Redis

```powershell
# 启动 MySQL 服务
net start MySQL80

# 启动 Redis 服务
redis-server

# 新开一个 PowerShell 窗口，验证 Redis
redis-cli ping
# 应该返回 PONG
```

### 第四步：创建 MySQL 数据库

```powershell
# 打开 MySQL 命令行
mysql -u root -p

# 输入密码（初次安装默认无密码，直接回车）
# 然后在 MySQL 提示符下输入以下命令：
```

在 MySQL 提示符下执行：
```sql
CREATE DATABASE garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

### 第五步：克隆项目并配置

```powershell
# 进入你想放项目的目录（例如 D:\ 或 C:\Users\YourName\Desktop）
cd D:\

# 克隆项目
git clone https://github.com/your-org/garbage-classifier.git
cd garbage-classifier

# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 升级 pip
pip install --upgrade pip

# 安装 PyTorch（CPU 版本，推荐）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装项目依赖
pip install -r requirements.txt
```

### 第六步：配置环境变量

```powershell
# 复制环境配置文件
copy .env.example .env

# 用记事本或 VS Code 打开 .env 文件编辑
notepad .env
# 或者用 VS Code
code .env
```

编辑 `.env` 文件，修改以下几行（根据你的 MySQL 密码）：

```env
FLASK_ENV=development
SECRET_KEY=my-secret-key-12345-change-this
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/garbage_db
REDIS_URL=redis://localhost:6379/0
WECHAT_APP_ID=test_app_id
WECHAT_APP_SECRET=test_app_secret
BAIDU_ASR_APP_ID=test_baidu_id
BAIDU_ASR_API_KEY=test_baidu_key
BAIDU_ASR_SECRET_KEY=test_baidu_secret
```

### 第七步：初始化数据库

```powershell
# 确保还在 backend/ 目录，虚拟环境已激活

# 初始化迁移
flask db init

# 生成迁移脚本
flask db migrate -m "初始化数据表"

# 执行迁移（创建表）
flask db upgrade

# 导入种子数据
python scripts/seed_data.py
```

验证数据库：
```powershell
mysql -u root -p garbage_db -e "SHOW TABLES;"
```

### 第八步：启动后端

```powershell
# 确保虚拟环境已激活
flask run --port=5000
```

看到 `Running on http://127.0.0.1:5000` 说明成功！ 🎉

### 第九步：配置小程序

打开新的 PowerShell 窗口：

```powershell
# 回到项目根目录
cd D:\garbage-classifier

# 进入小程序目录
cd miniprogram

# 安装 npm 依赖
npm install

# 在微信开发者工具中：
# 1. 打开项目：garbage-classifier\miniprogram\
# 2. 点击工具 → 构建 npm
# 3. 点击预览或编译
```

### 第十步：完整验证

```powershell
# 终端 1：启动 Redis
redis-server

# 终端 2：启动 MySQL
net start MySQL80

# 终端 3：启动后端
cd D:\garbage-classifier\backend
.\venv\Scripts\Activate.ps1
flask run --port=5000

# 终端 4：打开微信开发者工具
# 打开 D:\garbage-classifier\miniprogram\
# 点击预览或编译
```

---

## 🍎 macOS 用户

### 第一步：安装 Homebrew（如果还未安装）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 第二步：安装所有软件

```bash
# 安装 Python
brew install python@3.10

# 安装 MySQL
brew install mysql

# 安装 Redis
brew install redis

# 安装 Node.js
brew install node

# 安装 Git
brew install git

# 启动服务
brew services start mysql
brew services start redis
```

### 第三步：验证安装

```bash
python3 --version
mysql --version
redis-cli ping
node --version
npm --version
git --version
```

### 第四步：创建数据库

```bash
# 打开 MySQL
mysql -u root

# 在 MySQL 提示符下执行
CREATE DATABASE garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

### 第五步：克隆项目并配置

```bash
# 进入项目目录（例如 ~/Desktop 或 ~/projects）
cd ~/Desktop

# 克隆项目
git clone https://github.com/your-org/garbage-classifier.git
cd garbage-classifier

# 进入后端
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装 PyTorch（CPU 版本）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装依赖
pip install -r requirements.txt
```

### 第六步：配置环境变量

```bash
# 复制环境文件
cp .env.example .env

# 编辑 .env（用你喜欢的编辑器）
vim .env  # 或 nano .env 或用 VS Code 打开
```

编辑 `.env`：
```env
FLASK_ENV=development
SECRET_KEY=my-secret-key-12345
DATABASE_URL=mysql+pymysql://root:@localhost:3306/garbage_db
REDIS_URL=redis://localhost:6379/0
WECHAT_APP_ID=test_app_id
WECHAT_APP_SECRET=test_app_secret
BAIDU_ASR_APP_ID=test_baidu_id
BAIDU_ASR_API_KEY=test_baidu_key
BAIDU_ASR_SECRET_KEY=test_baidu_secret
```

### 第七步：初始化数据库

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 初始化迁移
flask db init

# 生成迁移脚本
flask db migrate -m "初始化数据表"

# 执行迁移
flask db upgrade

# 导入种子数据
python scripts/seed_data.py
```

验证：
```bash
mysql -u root garbage_db -e "SHOW TABLES;"
```

### 第八步：启动后端

```bash
flask run --port=5000
```

### 第九步：配置小程序

新开一个终端：
```bash
cd ~/Desktop/garbage-classifier/miniprogram
npm install

# 在微信开发者工具中打开 miniprogram/ 目录
# 点击工具 → 构建 npm
```

### 第十步：完整启动

```bash
# 终端 1：Redis 已通过 brew services 启动
# 终端 2：MySQL 已通过 brew services 启动

# 终端 3：启动后端
cd ~/Desktop/garbage-classifier/backend
source venv/bin/activate
flask run --port=5000

# 终端 4：打开微信开发者工具
# 打开 ~/Desktop/garbage-classifier/miniprogram/
```

---

## 🐧 Linux 用户（Ubuntu/Debian）

### 第一步：更新系统

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 第二步：安装所有软件

```bash
# 安装 Python 和 pip
sudo apt-get install -y python3.10 python3-pip python3-venv

# 安装 MySQL
sudo apt-get install -y mysql-server

# 安装 Redis
sudo apt-get install -y redis-server

# 安装 Node.js
sudo apt-get install -y nodejs npm

# 安装 Git
sudo apt-get install -y git

# 启动服务
sudo systemctl start mysql
sudo systemctl start redis-server
sudo systemctl enable mysql
sudo systemctl enable redis-server
```

### 第三步：验证安装

```bash
python3 --version
mysql --version
redis-cli ping
node --version
npm --version
git --version
```

### 第四步：创建数据库

```bash
# 打开 MySQL
mysql -u root -p

# 在 MySQL 提示符下
CREATE DATABASE garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

### 第五步：克隆项目

```bash
# 进入项目目录
cd ~/projects  # 或其他位置

# 克隆项目
git clone https://github.com/your-org/garbage-classifier.git
cd garbage-classifier

# 进入后端
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装 PyTorch（CPU 版本）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装依赖
pip install -r requirements.txt
```

### 第六步：配置环境变量

```bash
# 复制环境文件
cp .env.example .env

# 编辑 .env
nano .env  # 或用 vim、VS Code
```

编辑 `.env`：
```env
FLASK_ENV=development
SECRET_KEY=my-secret-key-12345
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/garbage_db
REDIS_URL=redis://localhost:6379/0
WECHAT_APP_ID=test_app_id
WECHAT_APP_SECRET=test_app_secret
BAIDU_ASR_APP_ID=test_baidu_id
BAIDU_ASR_API_KEY=test_baidu_key
BAIDU_ASR_SECRET_KEY=test_baidu_secret
```

### 第七步：初始化数据库

```bash
# 激活虚拟环境
source venv/bin/activate

# 初始化迁移
flask db init

# 生成迁移脚本
flask db migrate -m "初始化数据表"

# 执行迁移
flask db upgrade

# 导入种子数据
python scripts/seed_data.py
```

验证：
```bash
mysql -u root -p garbage_db -e "SHOW TABLES;"
```

### 第八步：启动后端

```bash
flask run --port=5000
```

### 第九步：配置小程序

```bash
cd ~/projects/garbage-classifier/miniprogram
npm install

# 在微信开发者工具中打开 miniprogram/ 目录
```

### 第十步：完整启动

```bash
# 终端 1：Redis 和 MySQL 已通过 systemctl 运行

# 终端 2：启动后端
cd ~/projects/garbage-classifier/backend
source venv/bin/activate
flask run --port=5000

# 终端 3：微信开发者工具
# 打开 ~/projects/garbage-classifier/miniprogram/
```

---

## ✅ 完成检查

运行以下命令验证一切正常：

### Windows PowerShell
```powershell
# 1. 验证 Python
python -c "import torch; print('PyTorch OK')"

# 2. 验证 MySQL
mysql -u root -p -e "SELECT VERSION();"

# 3. 验证 Redis
redis-cli ping

# 4. 验证后端 API
curl http://localhost:5000/api/v1/health

# 5. 查看数据库表
mysql -u root -p garbage_db -e "SHOW TABLES;"
```

### macOS/Linux
```bash
# 1. 验证 Python
python3 -c "import torch; print('PyTorch OK')"

# 2. 验证 MySQL
mysql -u root -e "SELECT VERSION();"

# 3. 验证 Redis
redis-cli ping

# 4. 验证后端 API
curl http://localhost:5000/api/v1/health

# 5. 查看数据库表
mysql -u root garbage_db -e "SHOW TABLES;"
```

---

## 🚨 常见错误快速修复

### "Python not found"
```powershell
# 重启电脑或添加到 PATH
# 或重新安装 Python，确保勾选 "Add Python to PATH"
```

### "MySQL command not found"
```powershell
# Windows: 重启 PowerShell
# macOS/Linux: brew services restart mysql / sudo systemctl restart mysql
```

### "Port 5000 already in use"
```powershell
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### "Can't connect to Redis"
```powershell
# 确保 Redis 已启动
redis-server

# 或重启 Redis 服务
redis-cli shutdown
redis-server
```

### "Database connection failed"
检查 `.env` 文件中的 MySQL 密码是否正确，以及 MySQL 服务是否运行

---

## 📱 微信开发者工具设置

1. 下载：[开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开 → `文件 → 打开项目`
3. 选择：`garbage-classifier/miniprogram/`
4. 点击：`工具 → 构建 npm`
5. 点击：`预览` 用微信扫码查看

---

## 🎯 核心启动命令速记

### Windows
```powershell
# 终端 1：
redis-server

# 终端 2：
net start MySQL80

# 终端 3：
cd garbage-classifier\backend
.\venv\Scripts\Activate.ps1
flask run --port=5000

# 终端 4：
# 微信开发者工具打开 miniprogram 文件夹
```

### macOS/Linux
```bash
# Redis 和 MySQL 通常已自动启动

# 终端 1：
cd garbage-classifier/backend
source venv/bin/activate
flask run --port=5000

# 终端 2：
# 微信开发者工具打开 miniprogram 文件夹
```

---

**祝你配置顺利！** 🚀

遇到问题？查看 `DEPLOYMENT_GUIDE.md` 中的"常见问题"部分。
