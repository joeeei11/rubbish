![Language](https://img.shields.io/badge/language-Python-blue) ![License](https://img.shields.io/badge/license-MIT-green)

# proj-Python-GarbageClassification-Platform

**基于深度学习的垃圾分类识别平台，前后端分离 + Docker 部署，支持图片上传实时识别。**

## 功能特性

- AI 模型垃圾图像分类（自定义 CNN）
- 垃圾知识库与百科查询
- 用户历史记录与文章系统
- Flask 后端 + Docker 容器化
- 垃圾分类标准数据集与标签管理

## 快速开始

### 环境要求

- Docker & Docker Compose
- Python >= 3.9（本地开发）

### 安装步骤

```bash
git clone https://github.com/joeeei11/proj-Python-GarbageClassification-Platform.git
cd proj-Python-GarbageClassification-Platform
docker compose up -d
```

### 基础用法

```bash
# 本地训练 AI 模型
cd backend && python ai_model/train.py
```
