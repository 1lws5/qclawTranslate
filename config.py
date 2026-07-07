"""qclawTranslate v1.4 - 配置文件（翻译 + CosyVoice WebSocket TTS）"""

import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    # ═══ 翻译引擎 ═══
    "translate_api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "translate_api_key": "",
    "translate_model": "qwen-plus",     # 默认用 qwen-plus 翻译
    "translate_extra_body": "",         # 可选额外 JSON 参数

    # ═══ TTS 引擎 (CosyVoice WebSocket) ═══
    "tts_ws_url": "wss://ws-c80jgdae5squls8x.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference",
    "tts_api_key": "sk-ws-H.RPXHRRM.5kzO.MEUCIQCKEQ-cu8FyE7369QEfi2kxdrBSydUDzQc5reToEaGoIwIgPJ0MR9fZ9ERl00pisWQ9m1pdgmvENiOlq5tEZ-4_tLM",
    "tts_model": "cosyvoice-v3-flash",
    "tts_voice": "longanyang",

    # ═══ 通用 ═══
    "start_on_boot": False,
    "tray_minimize": True,
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
