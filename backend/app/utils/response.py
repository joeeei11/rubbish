"""
统一响应格式工具
所有接口均通过此模块返回响应，保证格式一致：
{"code": 200, "message": "success", "data": {}}
"""
from flask import jsonify


def success(data=None, message="success", http_status=200):
    """成功响应"""
    return jsonify({
        "code": 200,
        "message": message,
        "data": data if data is not None else {}
    }), http_status


def error(code, message, http_status=200):
    """业务错误响应（HTTP 状态码仍为 200，由 code 字段区分业务结果）"""
    return jsonify({
        "code": code,
        "message": message,
        "data": {}
    }), http_status


# 预定义业务错误码
class ErrorCode:
    # 通用
    PARAM_ERROR = 40001          # 参数错误
    UNAUTHORIZED = 40101         # 未登录或 token 无效
    TOKEN_EXPIRED = 40102        # token 已过期
    FORBIDDEN = 40301            # 无权限
    NOT_FOUND = 40401            # 资源不存在
    SERVER_ERROR = 50001         # 服务器内部错误

    # 业务
    CLASSIFY_FAILED = 42001      # 图像识别失败
    ASR_FAILED = 42002           # 语音识别失败
    CONFIDENCE_TOO_LOW = 42003   # 置信度过低
    WECHAT_AUTH_FAILED = 43001   # 微信授权失败
