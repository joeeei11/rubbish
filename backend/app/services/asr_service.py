"""
百度语音识别服务。
负责延迟加载 SDK、初始化客户端，并将 PCM 音频转换为文本。
"""
from __future__ import annotations

from typing import Optional

from flask import current_app


ASR_SAMPLE_RATE = 16000
ASR_DEV_PID = 1537  # 普通话输入法模型
SUPPORTED_AUDIO_FORMATS = {"pcm"}

_AIP_SPEECH_CLASS = None
_ASR_CLIENT = None


class ASRException(RuntimeError):
    """语音识别异常。"""


def _ensure_baidu_sdk():
    """按需导入百度 ASR SDK，避免未安装时阻塞非语音功能。"""
    global _AIP_SPEECH_CLASS

    if _AIP_SPEECH_CLASS is not None:
        return _AIP_SPEECH_CLASS

    try:
        from aip import AipSpeech
    except ModuleNotFoundError as exc:
        raise ASRException("未安装百度语音识别 SDK，请先安装 baidu-aip") from exc

    _AIP_SPEECH_CLASS = AipSpeech
    return _AIP_SPEECH_CLASS


def _get_credentials() -> tuple[str, str, str]:
    """读取百度 ASR 配置。"""
    app_id = str(current_app.config.get("BAIDU_ASR_APP_ID", "")).strip()
    api_key = str(current_app.config.get("BAIDU_ASR_API_KEY", "")).strip()
    secret_key = str(current_app.config.get("BAIDU_ASR_SECRET_KEY", "")).strip()

    if not app_id or not api_key or not secret_key:
        raise ASRException("未配置百度语音识别参数，请检查 .env")

    return app_id, api_key, secret_key


def get_asr_client(force_reload: bool = False):
    """单例获取百度语音识别客户端。"""
    global _ASR_CLIENT

    if _ASR_CLIENT is not None and not force_reload:
        return _ASR_CLIENT

    app_id, api_key, secret_key = _get_credentials()
    aip_speech = _ensure_baidu_sdk()
    _ASR_CLIENT = aip_speech(app_id, api_key, secret_key)
    return _ASR_CLIENT


def _normalize_audio_format(audio_format: Optional[str]) -> str:
    """归一化音频格式参数。"""
    normalized = (audio_format or "pcm").strip().lower().lstrip(".")
    if normalized not in SUPPORTED_AUDIO_FORMATS:
        raise ASRException("仅支持 PCM 音频格式")
    return normalized


def _normalize_recognized_text(text: str) -> str:
    """清理百度返回的末尾标点，提升搜索命中率。"""
    return (text or "").strip().rstrip("，。！？!?；;,. ")


def recognize_audio(audio_bytes: bytes, audio_format: str = "pcm") -> str:
    """
    调用百度 ASR 将音频转为文本。

    :param audio_bytes: PCM 原始音频字节
    :param audio_format: 音频格式，当前仅支持 pcm
    :return: 识别出的文字
    :raises ASRException: 识别失败或配置异常
    """
    if not audio_bytes:
        raise ASRException("音频内容为空")

    normalized_format = _normalize_audio_format(audio_format)
    client = get_asr_client()

    try:
        response = client.asr(
            audio_bytes,
            normalized_format,
            ASR_SAMPLE_RATE,
            {"dev_pid": ASR_DEV_PID},
        )
    except Exception as exc:
        raise ASRException("语音识别服务调用失败") from exc

    if not isinstance(response, dict):
        raise ASRException("语音识别返回格式异常")

    if response.get("err_no") != 0:
        raise ASRException(response.get("err_msg") or "语音识别失败")

    result_list = response.get("result") or []
    if not result_list:
        raise ASRException("未识别出有效文字")

    recognized_text = _normalize_recognized_text(result_list[0])
    if not recognized_text:
        raise ASRException("未识别出有效文字")

    return recognized_text
