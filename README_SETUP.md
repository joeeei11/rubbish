# 🚀 环境配置快速开始指南

> 针对**完全空白的电脑**，快速配置所有开发环境

---

## 📋 选择你的操作系统

### 🪟 Windows 用户

#### 方式 1：**一键安装脚本**（推荐）

```powershell
# 1. 用 PowerShell 以管理员身份打开（右键点击 PowerShell，选择"以管理员身份运行"）
# 2. 进入项目目录
cd D:\MYSOFTWAREOFtechnology\CodexFile\HaiNai.Rubbish\garbage-classifier

# 3. 运行脚本
powershell -ExecutionPolicy Bypass -File .\setup-windows.ps1

# 4. 等待脚本完成（大约 10-20 分钟）
# 5. 按照脚本输出的提示继续操作
```

**脚本会自动完成：**
- ✅ 安装 Python、MySQL、Redis、Node.js、Git
- ✅ 创建 Python 虚拟环境
- ✅ 安装 PyTorch 和项目依赖
- ✅ 创建数据库和数据表
- ✅ 配置小程序环境

#### 方式 2：**手动命令** (如果脚本有问题)

打开 PowerShell **以管理员身份运行**，从 `QUICK_SETUP.md` 中复制 Windows 部分的命令，逐行执行。

---

### 🍎 macOS 用户

#### 方式 1：**一键安装脚本**（推荐）

```bash
# 1. 打开终端
# 2. 进入项目目录
cd ~/path/to/garbage-classifier

# 3. 运行脚本
bash setup-macos-linux.sh

# 4. 根据提示输入密码（Homebrew 和 sudo 可能需要）
# 5. 等待脚本完成（大约 15-25 分钟）
```

**脚本会自动完成：**
- ✅ 安装 Homebrew（如果未安装）
- ✅ 安装 Python、MySQL、Redis、Node.js、Git
- ✅ 创建 Python 虚拟环境
- ✅ 安装 PyTorch 和项目依赖
- ✅ 创建数据库和数据表
- ✅ 配置小程序环境

#### 方式 2：**手动命令** (如果脚本有问题)

打开终端，从 `QUICK_SETUP.md` 中复制 macOS 部分的命令，逐行执行。

---

### 🐧 Linux 用户（Ubuntu/Debian）

#### 方式 1：**一键安装脚本**（推荐）

```bash
# 1. 打开终端
# 2. 进入项目目录
cd ~/path/to/garbage-classifier

# 3. 赋予脚本执行权限
chmod +x setup-macos-linux.sh

# 4. 运行脚本
bash setup-macos-linux.sh

# 5. 根据提示输入密码（sudo 需要）
# 6. 等待脚本完成（大约 15-25 分钟）
```

**脚本会自动完成：**
- ✅ 更新系统包
- ✅ 安装 Python、MySQL、Redis、Node.js、Git
- ✅ 创建 Python 虚拟环境
- ✅ 安装 PyTorch 和项目依赖
- ✅ 创建数据库和数据表
- ✅ 配置小程序环境

#### 方式 2：**手动命令** (如果脚本有问题)

打开终端，从 `QUICK_SETUP.md` 中复制 Linux 部分的命令，逐行执行。

---

## ⚙️ 配置环境变量（所有平台相同）

安装脚本完成后，需要配置 `.env` 文件：

```bash
# 进入后端目录
cd backend

# 编辑 .env 文件（用你喜欢的编辑器）
# Windows: notepad .env 或 code .env
# macOS/Linux: nano .env 或 code .env
code .env
```

编辑以下几行（**必须修改**）：

```env
# MySQL 密码（改成你的 MySQL 密码）
DATABASE_URL=mysql+pymysql://root:你的MySQL密码@localhost:3306/garbage_db

# 其他配置可以先保持默认值（用于测试）
FLASK_ENV=development
SECRET_KEY=my-secret-key-12345
REDIS_URL=redis://localhost:6379/0
WECHAT_APP_ID=test_app_id
WECHAT_APP_SECRET=test_app_secret
BAIDU_ASR_APP_ID=test_baidu_id
BAIDU_ASR_API_KEY=test_baidu_key
BAIDU_ASR_SECRET_KEY=test_baidu_secret
```

**保存文件** （Ctrl+S 或 Cmd+S）

---

## 🎯 完成后：启动项目

按照以下步骤启动项目（**每次都需要执行这些步骤**）：

### Windows PowerShell

打开 **4 个 PowerShell 窗口**：

```powershell
# 终端 1：启动 Redis
redis-server

# 终端 2：启动 MySQL
net start MySQL80

# 终端 3：启动后端
cd D:\...\garbage-classifier\backend
.\venv\Scripts\Activate.ps1
flask run --port=5000

# 终端 4：启动小程序
# 打开微信开发者工具
# 打开文件夹: D:\...\garbage-classifier\miniprogram
# 点击: 工具 → 构建 npm
# 点击: 预览 或 编译
```

### macOS/Linux

打开 **2 个终端**：

```bash
# 终端 1：启动后端
cd ~/path/to/garbage-classifier/backend
source venv/bin/activate
flask run --port=5000

# 终端 2：启动小程序
# 打开微信开发者工具
# 打开文件夹: ~/path/to/garbage-classifier/miniprogram
# 点击: 工具 → 构建 npm
# 点击: 预览 或 编译

# Redis 和 MySQL 已通过后台服务自动启动
# 验证: redis-cli ping   (应该返回 PONG)
```

---

## ✅ 验证一切正常

```bash
# 测试 Python
python -c "import torch; print('PyTorch OK')"

# 测试 MySQL
mysql -u root -p -e "SELECT VERSION();"

# 测试 Redis
redis-cli ping

# 测试后端 API（启动后端后）
curl http://localhost:5000/api/v1/health

# 测试数据库表（启动后端后）
mysql -u root -p garbage_db -e "SHOW TABLES;"
```

所有命令都返回成功，说明环境配置完成！ ✅

---

## 📚 文档说明

| 文件名 | 说明 | 何时查看 |
|------|------|--------|
| **README_SETUP.md** | 本文件，快速开始指南 | 首次配置时 |
| **QUICK_SETUP.md** | 详细的命令说明（可复制粘贴） | 脚本有问题或需要手动操作时 |
| **DEPLOYMENT_GUIDE.md** | 超详细的部署指南（包含截图和原理说明） | 学习如何部署或深入理解时 |

---

## 🆘 常见问题

### Q1：脚本运行失败，说"权限不足"

**Windows:** 确保以管理员身份运行 PowerShell
```powershell
# 右键点击 PowerShell → 以管理员身份运行
```

**macOS/Linux:** 确保脚本有执行权限
```bash
chmod +x setup-macos-linux.sh
```

### Q2：脚本完成后，编辑 .env 文件时不知道 MySQL 密码

**Windows:** 如果在安装时没有设置密码，默认密码是空的（直接回车）
```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/garbage_db
```

**macOS/Linux:** 通常也是空密码
```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/garbage_db
```

### Q3：运行后端时出错 "ModuleNotFoundError"

```bash
# 确保虚拟环境已激活（前缀应该显示 (venv)）
# Windows:
.\venv\Scripts\Activate.ps1

# macOS/Linux:
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### Q4：启动后端时说 "Port 5000 already in use"

```bash
# 改用其他端口
flask run --port=5001

# 或杀死占用 5000 的进程
# Windows: 
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

### Q5：小程序无法调用后端 API

1. 确认后端已启动：访问 `http://localhost:5000/api/v1/health` 应该返回 JSON
2. 检查 `miniprogram/utils/request.js` 中的 API 地址是否是 `http://localhost:5000/api/v1`
3. 在微信开发者工具中勾选 `不校验合法域名、TLS 版本及 HTTPS 证书`

---

## 🎓 下一步

配置完成后，可以：

1. **运行测试**
   ```bash
   cd backend
   pytest tests/ -v
   ```

2. **训练模型**（如有数据集）
   ```bash
   cd backend
   python ai_model/train.py --epochs 50
   ```

3. **查看 API 文档**
   ```
   http://localhost:5000/api/v1/health
   ```

4. **查看项目说明**
   ```
   cat CLAUDE.md
   cat README.md
   ```

---

## 📞 需要帮助？

1. **查看 QUICK_SETUP.md** - 每一步的详细命令说明
2. **查看 DEPLOYMENT_GUIDE.md** - 超详细的指南，包含截图和原理
3. **查看常见问题** - 本文档的最后一部分
4. **查看项目 Issues** - 可能已有类似问题的解决方案

---

**祝你配置顺利！** 🚀

> 本指南最后更新于：2026-04-10
