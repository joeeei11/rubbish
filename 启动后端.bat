@echo off
chcp 65001 >nul
title 垃圾分类后端服务

echo ========================================
echo   垃圾分类助手 - 后端服务启动
echo ========================================
echo.

:: 切换到后端目录
cd /d "%~dp0backend"

:: 检查 .env 文件
if not exist ".env" (
    echo [错误] 未找到 .env 文件，请先复制 .env.example 并填写配置
    echo 执行：copy .env.example .env
    pause
    exit /b 1
)

:: 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [信息] 使用虚拟环境 .venv
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [信息] 使用虚拟环境 venv
    call venv\Scripts\activate.bat
) else (
    echo [信息] 未检测到虚拟环境，使用系统 Python
)

:: 检查依赖
echo [信息] 检查依赖...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo [信息] 安装依赖中...
    pip install -r requirements.txt --user
)

:: 执行数据库迁移
echo [信息] 执行数据库迁移...
flask db upgrade
if errorlevel 1 (
    echo [警告] 数据库迁移失败，请检查数据库配置
)

:: 启动 Flask
echo.
echo [信息] 启动后端服务，端口 5000...
echo [信息] 按 Ctrl+C 停止服务
echo.
flask run --port=5000

pause
