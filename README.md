# 智能垃圾分类助手

基于深度学习的微信小程序，支持**图像识别、语音查询、文字搜索**三合一垃圾分类指导。

- 图像识别准确率：**85.02%**（MobileNetV3-Small，验证集 5007 张）
- 四分类：可回收物 / 厨余垃圾 / 有害垃圾 / 其他垃圾

---

## 技术栈

| 层 | 技术 |
|----|------|
| 小程序前端 | 微信小程序原生（WXML / WXSS / JS） |
| 后端框架 | Python Flask 3.0 |
| AI 推理 | PyTorch + MobileNetV3-Small |
| 数据库 | MySQL 8.0 + Redis 7 |
| 语音识别 | 百度智能云 ASR |
| 部署 | Docker + Nginx + Gunicorn |

---

## 快速启动（推荐 Docker）

### 前置条件

- Docker Desktop 已安装并运行
- 微信开发者工具（运行小程序）

### 第一步：克隆项目

```bash
git clone https://github.com/joeeei11/rubbish.git
cd rubbish
```

### 第二步：下载模型权重

从 Release 下载预训练权重，放到指定目录：

```bash
# 下载地址
https://github.com/joeeei11/rubbish/releases/download/v1.0.0/mobilenetv3_garbage.pth

# 放置路径
backend/ai_model/weights/mobilenetv3_garbage.pth
```

### 第三步：配置环境变量

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，填写以下**必填项**：

```env
SECRET_KEY=任意随机字符串，如：abc123xyz
WECHAT_APP_ID=你的微信小程序 AppID
WECHAT_APP_SECRET=你的微信小程序 AppSecret
```

> 其余配置（百度 ASR、腾讯云 COS）**留空不影响基本运行**，图像识别和文字搜索功能均可正常使用。

### 第四步：启动后端

```bash
docker-compose up -d
```

首次启动会自动完成：数据库初始化、表结构创建、知识库种子数据导入。

启动完成后验证：

```bash
curl http://localhost:5000/api/v1/health
# 返回 {"code": 200, "message": "success"} 即正常
```

### 第五步：启动小程序

1. 用微信开发者工具打开 `miniprogram/` 目录
2. 安装 npm 依赖：
   ```bash
   cd miniprogram
   npm install
   ```
3. 微信开发者工具中执行：**工具 → 构建 npm**
4. 开启**不校验合法域名**（本地调试用）
5. 将小程序请求 Base URL 改为 `http://localhost:5000`

---

## 本地开发（不用 Docker）

```bash
# 1. 安装 Python 依赖
cd backend
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 SECRET_KEY / DATABASE_URL / WECHAT_APP_*

# 3. 初始化数据库（需本地已运行 MySQL 和 Redis）
flask db upgrade
python scripts/seed_data.py

# 4. 启动
flask run --port=5000
```

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/user/login` | 微信登录 |
| GET  | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/classify/image` | 图像识别 |
| POST | `/api/v1/classify/voice` | 语音识别 |
| GET  | `/api/v1/classify/search` | 文字搜索 |
| GET  | `/api/v1/knowledge/graph` | 知识图谱 |
| GET  | `/api/v1/history` | 查询历史 |

统一响应格式：`{"code": 200, "message": "success", "data": {}}`

---

## 自行训练模型（可选）

如需用自己的数据集重新训练，将图片按分类放入：

```
data/garbage_dataset/
├── train/
│   ├── recyclable/
│   ├── kitchen/
│   ├── hazardous/
│   └── other/
└── val/
    └── （同上）
```

然后运行：

```bash
cd backend
python ai_model/train.py --epochs 50
```

---

## 目录结构

```
rubbish/
├── miniprogram/        # 微信小程序前端
├── backend/            # Flask 后端
│   ├── ai_model/       # 模型代码 + 权重目录
│   ├── app/            # 业务逻辑
│   ├── migrations/     # 数据库迁移
│   └── tests/          # 单元测试（42 个）
├── data/
│   └── knowledge_base.json
├── nginx/
└── docker-compose.yml
```
