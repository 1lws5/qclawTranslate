"""qclawTranslate v1.5.3 - 配置文件（嵌套结构，支持翻译/TTS/发音/字幕）"""

import json
import os
import sys

# PyInstaller onefile 模式下 __file__ 指向临时解压目录，需用 sys.executable 定位 exe 所在目录
if getattr(sys, 'frozen', False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(_BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    # ═══ 翻译引擎 ═══
    "translate": {
        "engine": "cloud",            # "cloud" | "local"
        "cloud": {
            "provider": "custom",      # 固定 custom，不预设厂家
            "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "api_key": "",
            "model": "qwen-turbo",
            "extra_body": "",          # 可选 JSON 字符串
        },
        "local": {
            "provider": "none",        # "none" | 下拉框选已安装模型
            "model_path": "",
            "api_url": "",             # 本地推理服务地址（如有）
        },
    },

    # ═══ TTS 引擎 ═══
    "tts": {
        "engine": "cloud",            # "cloud" | "local"
        "cloud": {
            "provider": "custom",
            "ws_url": "wss://ws-c80jgdae5squls8x.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference",
            "api_key": "",
            "model": "cosyvoice-v3-flash",
            "voice": "longanyang",
        },
        "local": {
            "provider": "none",        # "none" | "edge-tts" | 其他
            "model_path": "",
        },
        "playback": {
            "speed": 1.0,             # 0.5 ~ 2.0
            "cache_enabled": True,
            "cache_dir": "./tts_cache",
        },
    },

    # ═══ 发音分析（Phase B 预留） ═══
    "pronunciation": {
        "engine": "local",
        "local": {
            "asr_model": "none",       # "none" | "whisperx" | "sherpa-onnx"
            "alignment_model": "none", # "none" | "wav2vec2"
            "scoring_language": "en-us",
            "weights": {
                "accuracy": 0.5,
                "fluency": 0.3,
                "completeness": 0.2,
            },
        },
        "cloud": {
            "provider": "none",
            "api_url": "",
            "api_key": "",
        },
    },

    # ═══ 实时字幕（Phase C 预留） ═══
    "subtitle": {
        "engine": "local",
        "local": {
            "asr_model": "none",       # "none" | "sherpa-onnx-zipformer"
            "vad_model": "none",       # "none" | "silero-vad"
        },
    },

    # ═══ 通用 ═══
    "general": {
        "start_on_boot": False,
        "tray_minimize": True,
        "theme": "dark",              # "dark" | "light"
        "language": "zh-CN",
    },
}


def _migrate_old_config(cfg):
    """把 v1.5.2 的 flat config 迁移到 v1.5.3 嵌套结构"""
    # 检测是否已经是新格式
    if "translate" in cfg and isinstance(cfg["translate"], dict):
        return cfg  # 已是新格式

    # 从 flat 提取并构建新结构
    new_cfg = json.loads(json.dumps(DEFAULT_CONFIG))  # 深拷贝默认值

    # 翻译
    new_cfg["translate"]["cloud"]["api_url"]    = cfg.get("translate_api_url", "")
    new_cfg["translate"]["cloud"]["api_key"]    = cfg.get("translate_api_key", "")
    new_cfg["translate"]["cloud"]["model"]      = cfg.get("translate_model", "qwen-turbo")
    new_cfg["translate"]["cloud"]["extra_body"] = cfg.get("translate_extra_body", "")

    # TTS
    new_cfg["tts"]["cloud"]["ws_url"]   = cfg.get("tts_ws_url", "")
    new_cfg["tts"]["cloud"]["api_key"]  = cfg.get("tts_api_key", "")
    new_cfg["tts"]["cloud"]["model"]    = cfg.get("tts_model", "cosyvoice-v3-flash")
    new_cfg["tts"]["cloud"]["voice"]    = cfg.get("tts_voice", "longanyang")

    # 通用
    new_cfg["general"]["start_on_boot"] = cfg.get("start_on_boot", False)
    new_cfg["general"]["tray_minimize"] = cfg.get("tray_minimize", True)

    return new_cfg


def _fill_defaults(cfg):
    """递归补齐缺失的默认字段（保留用户已设置的值）"""
    def _fill(target, default):
        for k, v in default.items():
            if k not in target:
                target[k] = json.loads(json.dumps(v))
            elif isinstance(v, dict) and isinstance(target[k], dict):
                _fill(target[k], v)
        return target
    return _fill(cfg, DEFAULT_CONFIG)


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg = _migrate_old_config(cfg)  # 迁移旧格式
            cfg = _fill_defaults(cfg)       # 补齐缺失字段
            return cfg
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CONFIG))


def save_config(cfg):
    os.makedirs(_BASE_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
