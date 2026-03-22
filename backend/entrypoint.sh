#!/bin/bash
set -e

echo "[entrypoint] 等待 MySQL 就绪..."

# 等待 MySQL 可连接（最多 60 秒）
MAX_RETRIES=30
RETRY_COUNT=0
until python -c "
import pymysql, os
try:
    pymysql.connect(
        host='db', port=3306,
        user='root', password='password',
        database='garbage_db'
    )
    print('[entrypoint] MySQL 已就绪')
except Exception as e:
    print(f'[entrypoint] 连接错误: {e}')
    raise
"; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "[entrypoint] 错误：MySQL 等待超时（${MAX_RETRIES}次重试）"
        exit 1
    fi
    echo "[entrypoint] MySQL 未就绪，等待中...（${RETRY_COUNT}/${MAX_RETRIES}）"
    sleep 2
done

# 初始化数据库迁移（仅首次运行时需要）
if [ ! -f "migrations/env.py" ]; then
    echo "[entrypoint] 初始化数据库迁移..."
    rm -rf migrations/*
    flask db init

    # 清除可能残留的 alembic 版本记录（容器重启场景）
    python -c "
import pymysql
conn = pymysql.connect(host='db', port=3306, user='root', password='password', database='garbage_db')
cur = conn.cursor()
cur.execute('DROP TABLE IF EXISTS alembic_version')
conn.commit()
conn.close()
print('[entrypoint] 已清除旧版本跟踪')
"
fi

echo "[entrypoint] 执行数据库迁移..."
flask db migrate -m "自动迁移" 2>/dev/null || true
flask db upgrade

# 导入种子数据（幂等操作，可重复执行）
echo "[entrypoint] 导入种子数据..."
python scripts/seed_data.py

echo "[entrypoint] 启动 Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 120 wsgi:app
