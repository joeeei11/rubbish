"""
WSGI 入口
生产环境由 Gunicorn 调用此模块
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
