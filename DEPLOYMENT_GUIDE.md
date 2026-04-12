# 🗑️ 智能垃圾分类助手小程序 - 完整部署指南

**目标受众**: 零基础用户 | **部署时间**: 1-2 小时 | **难度**: ⭐⭐ 中等

本指南将从头开始，一步步指导您在一台空白电脑上完整部署并运行这个垃圾分类小程序项目。

---

## 📋 目录

1. [系统要求](#系统要求)
2. [第一阶段：安装基础环境](#第一阶段安装基础环境)
3. [第二阶段：项目初始化](#第二阶段项目初始化)
4. [第三阶段：数据库配置](#第三阶段数据库配置)
5. [第四阶段：后端启动](#第四阶段后端启动)
6. [第五阶段：小程序配置](#第五阶段小程序配置)
7. [第六阶段：验证与测试](#第六阶段验证与测试)
8. [常见问题与解决方案](#常见问题与解决方案)
9. [快速启动检查表](#快速启动检查表)

---

## 📌 系统要求

### 硬件要求
| 项目 | 最低配置 | 推荐配置 |
|------|--------|--------|
| **CPU** | 4核心 | 8核心或以上 |
| **内存 (RAM)** | 8GB | 16GB 以上 |
| **硬盘空间** | 20GB 可用空间 | 50GB 可用空间 |
| **网络** | 有效的互联网连接 | 100Mbps 以上 |

### 操作系统支持
- ✅ Windows 10/11 (64-bit)
- ✅ macOS 10.15+
- ✅ Ubuntu 18.04 LTS+

### 需要安装的软件

| 软件 | 版本 | 用途 | 体积 |
|------|------|------|------|
| **Python** | 3.10+ | 后端开发语言 | ~100MB |
| **MySQL** | 8.0+ | 数据库 | ~400MB |
| **Redis** | 7.0+ | 缓存服务 | ~20MB |
| **Node.js** | 18+ LTS | 小程序 npm 依赖 | ~200MB |
| **Git** | 2.30+ | 版本控制 | ~50MB |
| **微信开发者工具** | 最新版 | 小程序开发/调试 | ~500MB |

**总体积**: ~1.3GB（不包括项目代码和数据集）

---

## 🚀 第一阶段：安装基础环境

### Windows 用户

#### 1. 安装 Python

1. 访问 [python.org](https://www.python.org/downloads/)
2. 下载 **Python 3.10** 或更高版本（选择 "Windows installer (64-bit)"）
3. 运行安装程序，**关键步骤**：
   - ✅ 勾选 `Add Python to PATH`（这很重要！）
   - ✅ 勾选 `Install pip`
   - 点击 `Install Now`
4. 验证安装：打开 `cmd` 或 `PowerShell`，输入：
   ```cmd
   python --version
   pip --version
   ```
   应该显示版本号，例如 `Python 3.10.0`

#### 2. 安装 MySQL

1. 访问 [MySQL 官网](https://dev.mysql.com/downloads/mysql/)
2. 下载 **MySQL 8.0 Community Server** (Windows (x86, 64-bit))
3. 运行安装程序：
   - 选择 `Developer Default`（默认选项）
   - 下一步 → MySQL Server 配置：
     - **Config Type**: `Development Machine`
     - **MySQL Port**: `3306`（默认）
     - **MySQL User**: 输入用户名（如 `root`）
     - **Password**: 设置一个**强密码**（例如 `Root@123456`）并记住它！
   - 完成安装
4. 验证安装：打开 `cmd`，输入：
   ```cmd
   mysql -u root -p
   ```
   输入密码后，如果看到 `mysql>` 提示符，说明安装成功
   输入 `EXIT;` 退出

#### 3. 安装 Redis

1. 访问 [Redis 官网](https://redis.io/download)
2. 向下滚动找到 **Windows** 版本，下载最新版本
3. 或者使用 Windows Package Manager：
   ```cmd
   choco install redis  # 需要先安装 Chocolatey
   ```
4. 安装后，在开始菜单搜索 "Redis"，启动 Redis 服务
5. 验证安装：打开新的 `cmd` 窗口，输入：
   ```cmd
   redis-cli ping
   ```
   应该返回 `PONG`

#### 4. 安装 Node.js

1. 访问 [nodejs.org](https://nodejs.org/)
2. 下载 **LTS 版本**（18.x 或更新）
3. 运行安装程序，使用默认选项即可
4. 验证安装：打开 `cmd`，输入：
   ```cmd
   node --version
   npm --version
   ```

#### 5. 安装 Git

1. 访问 [git-scm.com](https://git-scm.com/download/win)
2. 下载 64-bit 版本
3. 运行安装程序，一直点 `Next` 即可（使用默认配置）
4. 验证安装：打开 `cmd`，输入：
   ```cmd
   git --version
   ```

#### 6. 安装微信开发者工具

1. 访问 [开发者工具下载页面](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 下载 **稳定版**（选择 Windows 64-bit）
3. 运行安装程序，选择安装路径（推荐 `C:\Program Files\...`）
4. 安装完成后，用微信扫码登录

---

### macOS 用户

#### 快速安装（使用 Homebrew）

如果已安装 Homebrew，运行以下命令：

```bash
# 安装所需软件
brew install python@3.11
brew install mysql
brew install redis
brew install node
brew install git

# 启动 MySQL 和 Redis（后台服务）
brew services start mysql
brew services start redis
```

#### 手动安装

1. **Python**: 访问 [python.org](https://www.python.org/downloads/) 下载 macOS installer
2. **MySQL**: 访问 [MySQL 官网](https://dev.mysql.com/downloads/mysql/) 下载 macOS DMG 文件
3. **Redis**: 访问 [redis.io](https://redis.io/download) 下载源码，按说明编译
4. **Node.js**: 访问 [nodejs.org](https://nodejs.org/) 下载 macOS 版本
5. **微信开发者工具**: 访问[开发者工具页面](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)下载 macOS 版本

#### 验证所有软件

```bash
python3 --version
mysql --version
redis-cli ping          # 需要先启动 Redis
node --version
npm --version
git --version
```

---

### Linux 用户（Ubuntu/Debian）

```bash
# 更新包管理器
sudo apt-get update

# 安装所有依赖
sudo apt-get install -y python3.10 python3-pip
sudo apt-get install -y mysql-server
sudo apt-get install -y redis-server
sudo apt-get install -y nodejs npm
sudo apt-get install -y git

# 启动服务
sudo systemctl start mysql
sudo systemctl start redis-server

# 验证安装
python3 --version
mysql --version
redis-cli ping
node --version
git --version
```

---

## 📦 第二阶段：项目初始化

### 1. 克隆项目

打开终端/cmd，运行：

```bash
# 克隆项目到本地
git clone https://github.com/your-org/garbage-classifier.git
cd garbage-classifier

# 查看项目结构
ls -la  # macOS/Linux
dir     # Windows
```

**项目结构应该如下：**
```
garbage-classifier/
├── backend/              # 后端 Flask 应用
├── miniprogram/          # 微信小程序前端
├── data/                 # 数据集目录
├── docs/                 # 文档
├── docker-compose.yml    # Docker 配置（可选）
├── CLAUDE.md             # 项目说明
├── README.md
└── DEPLOYMENT_GUIDE.md   # 本文件
```

### 2. 创建虚拟环境（推荐，避免污染系统 Python）

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv  # Windows 用户
python3 -m venv venv # macOS/Linux 用户

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 验证激活成功（命令行前缀应该出现 (venv) 标记）
```

### 3. 安装 Python 依赖

```bash
# 升级 pip（确保能正常安装依赖）
pip install --upgrade pip

# 关键决策：选择安装 CPU 版本还是 GPU 版本的 PyTorch
# 如果电脑有 NVIDIA GPU，选择 CUDA 版本（速度快 10-30 倍）
# 否则选择 CPU 版本

# ===== 选项 A：CPU 版本（推荐大多数用户）=====
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# ===== 选项 B：GPU 版本（NVIDIA GPU 用户）=====
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装项目依赖
pip install -r requirements.txt

# 验证 PyTorch 安装
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```

**这一步可能需要 5-10 分钟，因为要下载较大的文件（PyTorch ~500MB）**

---

## 🗄️ 第三阶段：数据库配置

### 1. 创建数据库

#### Windows 用户

```cmd
# 打开 MySQL 客户端
mysql -u root -p

# 输入密码后，在 MySQL 提示符下运行：
CREATE DATABASE garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;  # 验证数据库已创建
EXIT;
```

#### macOS/Linux 用户

```bash
# 打开 MySQL 客户端
mysql -u root -p

# 输入密码后，在 MySQL 提示符下运行：
CREATE DATABASE garbage_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
EXIT;
```

### 2. 配置环境变量

在 `backend/` 目录下：

```bash
# 复制示例文件
cp .env.example .env  # macOS/Linux
copy .env.example .env # Windows

# 用你喜欢的编辑器打开 .env 文件（VS Code、记事本等）
```

编辑 `.env` 文件，填入以下内容（**根据你的实际配置修改**）：

```env
# Flask 配置
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-12345-change-this-in-production

# 数据库配置（根据你设置的 MySQL 密码修改）
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/garbage_db
REDIS_URL=redis://localhost:6379/0

# 微信配置（后续可以改成真实的，现在用测试值）
WECHAT_APP_ID=test_app_id_12345
WECHAT_APP_SECRET=test_app_secret_12345

# 百度语音识别配置（后续可以改成真实的）
BAIDU_ASR_APP_ID=test_baidu_app_id
BAIDU_ASR_API_KEY=test_baidu_api_key
BAIDU_ASR_SECRET_KEY=test_baidu_secret_key

# 腾讯云 COS 配置（如果使用云存储，后续配置）
COS_SECRET_ID=
COS_SECRET_KEY=
COS_BUCKET=
COS_REGION=ap-guangzhou

# 模型配置
MODEL_WEIGHTS_PATH=ai_model/weights/mobilenetv3_garbage.pth
MODEL_INPUT_SIZE=224
MODEL_CONFIDENCE_THRESHOLD=0.6
UPLOAD_FOLDER=uploads
```

### 3. 初始化数据库表（关键步骤！）

在 `backend/` 目录，虚拟环境激活的状态下运行：

```bash
# 初始化迁移环境（第一次运行）
flask db init

# 生成迁移脚本
flask db migrate -m "初始化数据表"

# 执行迁移，创建实际的数据库表
flask db upgrade

# 导入种子数据（垃圾分类知识库、分类标签等）
# 这一步很重要，否则数据库是空的！
python scripts/seed_data.py
```

**验证数据库创建成功：**

```bash
mysql -u root -p garbage_db -e "SHOW TABLES;"
```

应该看到多个表，例如 `users`, `categories`, `garbage_items` 等

---

## ⚙️ 第四阶段：后端启动

### 1. 启动 Redis（必须！）

#### Windows
```cmd
# 如果 Redis 已注册为服务，自动启动
# 否则手动启动（找到 Redis 安装目录）
redis-server.exe

# 验证 Redis 运行
redis-cli ping  # 应该返回 PONG
```

#### macOS/Linux
```bash
# 如果使用 Homebrew
brew services start redis
# 或者手动启动
redis-server

# 验证 Redis 运行（新终端）
redis-cli ping  # 应该返回 PONG
```

### 2. 启动 MySQL（必须！）

#### Windows
```cmd
# MySQL 通常已注册为 Windows 服务，自动启动
# 验证连接
mysql -u root -p
# 输入密码时看到 mysql> 提示符说明成功
EXIT;
```

#### macOS/Linux
```bash
# 如果使用 Homebrew
brew services start mysql
# 或者手动启动
mysql.server start

# 验证连接
mysql -u root -p
EXIT;
```

### 3. 启动 Flask 后端

```bash
# 确保还在 backend/ 目录，虚拟环境已激活
flask run --port=5000
```

**看到这样的输出说明启动成功：**
```
 * Environment: development
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### 4. 验证后端 API

打开浏览器或使用 curl，访问：

```
http://localhost:5000/api/v1/health
```

应该返回类似：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "ok"
  }
}
```

**如果一切正常，后端已成功启动！** 🎉

---

## 📱 第五阶段：小程序配置

### 1. 安装小程序依赖

```bash
# 从 backend/ 目录返回到项目根目录
cd ..

# 进入小程序目录
cd miniprogram

# 安装 npm 依赖（包括 ECharts 等）
npm install

# 验证安装成功（应该看到 node_modules/ 目录）
ls node_modules  # macOS/Linux
dir node_modules # Windows
```

### 2. 配置 API 地址

编辑 `miniprogram/utils/request.js` 文件，确保 API 地址正确：

```javascript
// request.js

const BASE_URL = 'http://localhost:5000/api/v1';  // 本地测试
// 或生产环境：
// const BASE_URL = 'https://your-domain.com/api/v1';

module.exports = {
  request: (options) => {
    // ...现有逻辑
    url: BASE_URL + options.url,
    // ...
  }
}
```

### 3. 在微信开发者工具中打开项目

1. 打开微信开发者工具
2. 点击菜单 `文件 → 打开项目`
3. 选择项目路径：`garbage-classifier/miniprogram/`
4. 输入你的 AppID（如果没有可以先跳过，使用测试号）
5. 点击 `打开`

### 4. 构建 npm（很重要！）

1. 在微信开发者工具菜单栏，点击 `工具 → 构建 npm`
2. 等待构建完成（会生成 `miniprogram_npm/` 目录）
3. 此时 ECharts 和其他 npm 包才能在小程序中使用

### 5. 预览或编译小程序

- **在开发者工具中预览**：点击菜单 `预览`，用微信扫码查看
- **真机测试**：点击菜单 `上传`，在手机微信中搜索小程序名称

---

## ✅ 第六阶段：验证与测试

### 验证清单

| 组件 | 验证命令 | 预期结果 |
|------|--------|--------|
| **Python** | `python --version` | 显示版本 3.10+ |
| **MySQL** | `mysql -u root -p` 后输入密码 | 连接成功，显示 `mysql>` |
| **Redis** | `redis-cli ping` | 返回 `PONG` |
| **Node.js** | `node --version` | 显示版本 18+ |
| **后端 API** | 访问 `http://localhost:5000/api/v1/health` | 返回 `{"code": 200, ...}` |
| **小程序** | 在微信开发者工具中运行 | 页面正常加载，无报错 |

### 功能测试（可选）

#### 测试图像分类

```bash
# 在后端目录运行测试
cd backend
pytest tests/test_ai_service.py -v
```

#### 测试 API 搜索功能

使用 Postman 或 curl 测试：

```bash
curl "http://localhost:5000/api/v1/classify/search?keyword=塑料瓶"
```

应该返回分类结果列表

#### 测试小程序登录

在微信开发者工具中：
1. 打开 `pages/index/` 页面
2. 点击任何功能按钮（拍照、语音、搜索）
3. 检查是否能正常调用后端 API

---

## 🆘 常见问题与解决方案

### 问题 1：ModuleNotFoundError: No module named 'torch'

**原因**: PyTorch 没有安装或虚拟环境未激活

**解决方案**:
```bash
# 检查虚拟环境是否激活（命令行应显示 (venv) 前缀）
# 如果没激活，运行：
venv\Scripts\activate  # Windows
source venv/bin/activate # macOS/Linux

# 重新安装 PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### 问题 2：Can't connect to MySQL server

**原因**: MySQL 服务未启动或密码错误

**解决方案**:
```bash
# 检查 MySQL 是否运行
mysql -u root -p
# 输入密码时看到 mysql> 说明连接成功

# 如果无法连接，重启 MySQL 服务
# Windows: 以管理员身份运行 cmd，输入 net start MySQL80
# macOS: brew services restart mysql
# Linux: sudo systemctl restart mysql
```

### 问题 3：Can't connect to Redis server

**原因**: Redis 服务未启动

**解决方案**:
```bash
# 启动 Redis
# Windows: 在 Redis 安装目录双击 redis-server.exe
# macOS: brew services start redis
# Linux: sudo systemctl start redis-server

# 验证 Redis 运行
redis-cli ping  # 应该返回 PONG
```

### 问题 4：Port 5000 is already in use

**原因**: 其他程序占用了 5000 端口

**解决方案**:
```bash
# 使用不同的端口启动 Flask
flask run --port=5001

# 或者杀死占用 5000 端口的进程
# Windows: netstat -ano | findstr :5000
# macOS/Linux: lsof -i :5000 | grep LISTEN
```

### 问题 5：小程序 API 调用失败，提示跨域错误

**原因**: CORS 配置问题或 API 地址错误

**解决方案**:
```javascript
// 检查 miniprogram/utils/request.js 中的 API 地址
// 应该是 http://localhost:5000/api/v1

// 检查后端 Flask app 是否已启动
// 在浏览器访问 http://localhost:5000/api/v1/health
```

### 问题 6：数据库表未创建

**原因**: `flask db upgrade` 未执行

**解决方案**:
```bash
# 检查迁移文件是否存在
ls backend/migrations/versions/

# 如果不存在，重新执行：
flask db migrate -m "初始化数据表"
flask db upgrade

# 验证表已创建
mysql -u root -p garbage_db -e "SHOW TABLES;"
```

### 问题 7：训练模型时报错 `CUDA out of memory`

**原因**: GPU 显存不足（使用 GPU 时）

**解决方案**:
```python
# 在 ai_model/train.py 中减小 batch_size
# 例如从 32 改为 8：
batch_size = 8

# 或者改用 CPU 训练（虽然慢）
# 修改 train.py 中的设备配置
device = torch.device('cpu')
```

### 问题 8：小程序在真机上无法调用 API

**原因**: 域名未配置白名单

**解决方案**:
- 在微信小程序后台管理，找到 `开发 → 开发设置 → 服务器域名`
- 添加你的后端服务器域名（例如 `api.example.com`）
- **本地开发时**：在微信开发者工具中勾选 `不校验合法域名、TLS 版本及 HTTPS 证书`

---

## 📊 快速启动检查表

使用这个检查表快速启动项目：

### ✅ 环境准备阶段（第一次设置）

- [ ] Python 3.10+ 已安装
- [ ] MySQL 8.0+ 已安装且运行
- [ ] Redis 7.0+ 已安装且运行
- [ ] Node.js 18+ LTS 已安装
- [ ] Git 已安装
- [ ] 微信开发者工具已安装

### ✅ 项目初始化阶段（第一次设置）

- [ ] 项目已克隆到本地
- [ ] Python 虚拟环境已创建
- [ ] Python 虚拟环境已激活（`(venv)` 标记出现）
- [ ] PyTorch 已安装（CPU 或 GPU 版本）
- [ ] 项目依赖已安装（`pip install -r requirements.txt`）
- [ ] `.env` 文件已配置
- [ ] 数据库已创建（`garbage_db`）
- [ ] 数据库表已初始化（`flask db upgrade`）
- [ ] 种子数据已导入（`python scripts/seed_data.py`）

### ✅ 每次启动时需要验证

```bash
# 1. 启动 Redis
redis-server    # 或在后台启动

# 2. 启动 MySQL（通常自动启动）
mysql -u root -p

# 3. 激活虚拟环境并启动后端
cd garbage-classifier/backend
source venv/bin/activate  # Windows: venv\Scripts\activate
flask run --port=5000

# 4. 在另一个终端，启动小程序
cd garbage-classifier/miniprogram
# 在微信开发者工具中打开并预览

# ✅ 完成！
```

### ✅ 快速验证命令

```bash
# 验证后端运行
curl http://localhost:5000/api/v1/health

# 验证数据库连接
mysql -u root -p -e "SELECT COUNT(*) FROM garbage_db.categories;"

# 验证 Redis 连接
redis-cli ping

# 查看后端日志
# 在启动后端的终端窗口查看实时日志
```

---

## 🎓 进阶：模型训练

如果你有自己的训练数据，可以训练自定义模型：

### 1. 准备数据集

数据应该放在 `data/garbage_dataset/` 目录：

```
data/garbage_dataset/
├── train/
│   ├── 可回收物/        # 分类名称作为文件夹
│   │   ├── img1.jpg
│   │   ├── img2.jpg
│   │   └── ...
│   ├── 有害垃圾/
│   ├── 厨余垃圾/
│   └── 其他垃圾/
└── val/
    ├── 可回收物/
    ├── 有害垃圾/
    ├── 厨余垃圾/
    └── 其他垃圾/
```

**数据量建议**:
- 每个类别训练集：800-2000 张
- 每个类别验证集：200-500 张
- 总计：5000-10000 张图片

### 2. 验证数据集

```bash
cd backend
python scripts/check_dataset.py
```

输出应该显示各类别的样本数量

### 3. 开始训练

```bash
# CPU 训练（推荐，稳定）
python ai_model/train.py --epochs 50

# GPU 训练（快，但需要 NVIDIA GPU）
python ai_model/train.py --epochs 50 --device cuda
```

**训练时间估计**:
- CPU: 2-5 小时
- GPU (RTX 3060): 30-60 分钟

### 4. 查看训练结果

训练完成后，权重文件会保存到：
```
backend/ai_model/weights/mobilenetv3_garbage.pth
```

查看训练日志：
```bash
# 查看训练过程中的准确率和损失
# 日志会打印在控制台上
```

---

## 📞 获取帮助

如果遇到问题：

1. **检查日志**: 查看后端控制台输出，通常会有详细错误信息
2. **查看本指南**: 使用 `Ctrl+F` 搜索关键词
3. **查看项目 README**: `garbage-classifier/README.md`
4. **运行测试**: `pytest tests/ -v` 诊断问题
5. **联系开发团队**: 检查项目的 Issues 或联系页面

---

## 📝 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-04-09 | 初版发布 |

---

**祝你部署顺利！** 🚀

如有任何问题，欢迎在项目 Issues 中反馈。
