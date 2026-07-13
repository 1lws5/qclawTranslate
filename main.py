# -*- coding: utf-8 -*-
"""
qclawTranslate v1.5.2 — 翻译+TTS（CosyVoice WS + MCI播放 + 原生热键）
"""
import sys, os, json, ssl, time, tempfile, threading, traceback, uuid, ctypes, urllib.request, urllib.parse, urllib.error
from ctypes import wintypes

# 在主线程提前加载 comtypes，避免后台线程首次 import 触发 COM 初始化冲突
import comtypes.client as _cc
from comtypes.gen.UIAutomationClient import CUIAutomation8 as _CUIA8, IUIAutomationTextPattern as _IUIA_TP

from PyQt5.QtCore    import Qt, QTimer, pyqtSignal, QObject, QAbstractNativeEventFilter
from PyQt5.QtGui     import QFont, QIcon
from PyQt5.QtWidgets import *

from config import load_config, save_config

def _tr_cfg(cfg):
    """快捷取翻译云端配置"""
    return cfg["translate"]["cloud"]

def _tts_cfg(cfg):
    """快捷取 TTS 云端配置"""
    return cfg["tts"]["cloud"]

APP_NAME = "qclawTranslate"
VERSION  = "1.5.2"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ━━━━━━━━━━━━━━━━━━━━ 全局异常钩子 ━━━━━━━━━━━━━━━━━━━━
_LOG_PATH = os.path.join(BASE_DIR, "error.log")

def _log_error(exc_type, exc_value, exc_tb):
    """所有未捕获异常写日志"""
    with open(_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"[ERROR] {exc_type.__name__}: {exc_value}\n")
        traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _log_error

# ━━━━━━━━━━━━━━━━━━━━ QSS ━━━━━━━━━━━━━━━━━━━━
QSS = r'''
QMainWindow                 { background:#0d1117; }
QWidget                     { font-family:"Segoe UI","Microsoft YaHei UI"; font-size:13px; color:#e6edf3; }
QFrame#card                 { background:#161b22; border:1px solid #21262d; border-radius:12px; }
QTextEdit                   { background:#0d1117; border:1px solid #21262d; border-radius:10px; padding:16px 18px; color:#e6edf3; font-size:14px; }
QTextEdit:focus             { border:1px solid #58a6ff; background:#0d1117; }
QTextEdit[readOnly="true"]  { background:#0d1117; }
QScrollBar:vertical         { background:transparent; width:8px; margin:4px 0; }
QScrollBar::handle:vertical { background:#30363d; border-radius:4px; min-height:36px; }
QScrollBar::handle:vertical:hover { background:#58a6ff; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0px; }
QScrollBar:horizontal       { background:transparent; height:8px; }
QScrollBar::handle:horizontal { background:#30363d; border-radius:4px; min-width:36px; }
QScrollBar::handle:horizontal:hover { background:#58a6ff; }
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width:0px; }
QComboBox                   { background:#21262d; border:1px solid #30363d; border-radius:8px; padding:10px 16px; color:#e6edf3; font-size:13px; min-height:22px; }
QComboBox:hover             { border-color:#58a6ff; }
QComboBox:focus             { border-color:#58a6ff; background:#161b22; }
QComboBox::drop-down        { border:none; padding-right:10px; width:24px; }
QComboBox::down-arrow       { image:none; width:0px; }
QComboBox QAbstractItemView { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:6px; selection-background-color:#1f6feb44; outline:none; }
QPushButton#btn-primary     { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #3a5afc,stop:1 #5b7cff); color:#fff; border:1px solid #5b7cff; border-radius:8px; padding:10px 24px; font-weight:600; font-size:13px; }
QPushButton#btn-primary:hover   { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4e6eff,stop:1 #7890ff); border-color:#7890ff; }
QPushButton#btn-primary:pressed { background:#2a4aec; border-color:#2a4aec; }
QPushButton#btn-primary:disabled { background:#21262d; color:#6e7681; border-color:#30363d; }
QPushButton#btn-tts         { background:#21262d; color:#e6edf3; border:1px solid #30363d; border-radius:8px; padding:10px 18px; font-weight:600; font-size:13px; }
QPushButton#btn-tts:hover   { background:#30363d; border-color:#58a6ff; color:#58a6ff; }
QPushButton#btn-tts:pressed { background:#161b22; }
QPushButton#btn-swap        { background:#21262d; color:#adb1b8; border:1px solid #30363d; border-radius:22px; font-size:18px; font-weight:bold; padding:0px; min-width:40px;max-width:40px;min-height:40px;max-height:40px; }
QPushButton#btn-swap:hover  { background:#1f6feb33; border-color:#58a6ff; color:#58a6ff; }
QPushButton#btn-settings    { background:transparent; color:#adb1b8; border:1px solid #30363d; border-radius:8px; font-size:16px; padding:6px 12px; }
QPushButton#btn-settings:hover { background:#30363d; color:#58a6ff; border-color:#58a6ff; }
QDialog                     { background:#161b22; border:1px solid #30363d; border-radius:16px; }
QLineEdit                   { background:#0d1117; border:1px solid #30363d; border-radius:8px; padding:10px 14px; color:#e6edf3; font-size:13px; }
QLineEdit:focus             { border-color:#58a6ff; background:#0d1117; }
QLabel#status               { color:#adb1b8; font-size:12px; }
QLabel#section-title        { color:#e6edf3; font-size:15px; font-weight:700; padding-bottom:4px; }
QTabWidget::pane            { background:#161b22; border:1px solid #30363d; border-radius:12px; top:-1px; }
QTabBar::tab                { background:#21262d; color:#adb1b8; border:1px solid #30363d; border-bottom:none; border-radius:8px 8px 0px 0px; padding:10px 22px; margin-right:3px; font-weight:600; }
QTabBar::tab:selected       { background:#161b22; color:#58a6ff; border-bottom-color:#161b22; }
QTabBar::tab:hover:!selected { background:#30363d; color:#e6edf3; }
QCheckBox                   { spacing:10px; }
QCheckBox::indicator        { width:20px;height:20px;border-radius:5px;border:1px solid #30363d;background:#0d1117; }
QCheckBox::indicator:checked { background:#58a6ff;border-color:#58a6ff; }
QToolTip                    { background:#161b22; color:#e6edf3; border:1px solid #30363d; border-radius:6px; padding:6px 10px; font-size:12px; }
QListWidget#nav             { background:#0d1117; border:none; border-right:1px solid #21262d; outline:none; }
QListWidget#nav::item       { padding:14px 20px; color:#adb1b8; border:none; }
QListWidget#nav::item:selected { background:#161b22; color:#58a6ff; border-left:3px solid #58a6ff; }
QListWidget#nav::item:hover { background:#161b22; color:#e6edf3; }
QRadioButton                { spacing:8px; color:#e6edf3; font-size:13px; }
QRadioButton::indicator     { width:18px; height:18px; border-radius:9px; border:2px solid #30363d; background:#0d1117; }
QRadioButton::indicator:checked { background:#58a6ff; border-color:#58a6ff; }
QSlider::groove:horizontal   { background:#21262d; height:4px; border-radius:2px; }
QSlider::handle:horizontal   { background:#58a6ff; width:16px; height:16px; margin:-6px 0; border-radius:8px; }
QSlider::sub-page:horizontal { background:#58a6ff; border-radius:2px; }
'''

# ━━━━━━━━━━━━━━━━━━━━ 信号桥（线程→UI） ━━━━━━━━━━━━━━━━━━━━
class _Bridge(QObject):
    """跨线程信号桥：不依赖 QThread，纯 QObject"""
    translate_result = pyqtSignal(dict)
    translate_chunk  = pyqtSignal(str)   # 流式翻译片段
    tts_result       = pyqtSignal(tuple)
    test_tr          = pyqtSignal(dict)
    test_tts         = pyqtSignal(tuple)

_bridge = _Bridge()  # 全局单例

# ━━━━━━━━━━━━━━━━━━━━ 语言 ━━━━━━━━━━━━━━━━━━━━
LANGUAGES = [
    ("auto","🌐 自动检测"), ("zh-Hans","🇨🇳 中文简体"), ("zh-Hant","🇹🇼 中文繁体"),
    ("en","🇺🇸 English"), ("ja","🇯🇵 日本語"), ("ko","🇰🇷 한국어"),
    ("fr","🇫🇷 Français"), ("de","🇩🇪 Deutsch"), ("es","🇪🇸 Español"),
    ("pt","🇵🇹 Português"), ("ru","🇷🇺 Русский"), ("ar","🇸🇦 العربية"),
    ("it","🇮🇹 Italiano"), ("th","🇹🇭 ไทย"), ("vi","🇻🇳 Tiếng Việt"),
    ("id","🇮🇩 Indonesia"), ("tr","🇹🇷 Türkçe"), ("nl","🇳🇱 Nederlands"),
    ("pl","🇵🇱 Polski"), ("sv","🇸🇪 Svenska"),
]

_TTS_LANG = {"zh-Hans":"Chinese","zh-Hant":"Chinese","en":"English","ja":"Japanese",
             "ko":"Korean","fr":"French","de":"German","es":"Spanish","pt":"Portuguese","ru":"Russian"}

# ━━━━━━━━━━━━━━━━━━━━ 网络工具 ━━━━━━━━━━━━━━━━━━━━
import http.client
from urllib.parse import urlparse

_tr_conn = None  # 模块级翻译 API 连接对象
_tr_lock = threading.Lock()  # 连接复用锁

def _reset_tr_conn():
    """重置翻译 API 连接（连接坏了时调用）"""
    global _tr_conn
    with _tr_lock:
        _tr_conn = None

def _ssl():
    c = ssl.create_default_context(); c.check_hostname = False; c.verify_mode = ssl.CERT_NONE; return c

def _get_tr_conn(url):
    """复用翻译 API 的 HTTPS 连接"""
    global _tr_conn
    with _tr_lock:
        if _tr_conn is None:
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or 443
            _tr_conn = http.client.HTTPSConnection(host, port, context=_ssl(), timeout=30)
        return _tr_conn

def _http_post(url, body_dict, headers_extra=None, timeout=20):
    """HTTP POST JSON → (status, data_or_err)，复用 TCP 连接"""
    hdrs = {"Content-Type":"application/json"}
    if headers_extra: hdrs.update(headers_extra)
    body_bytes = json.dumps(body_dict).encode("utf-8")
    try:
        conn = _get_tr_conn(url)
        parsed = urlparse(url)
        path = parsed.path + ("?" + parsed.query if parsed.query else "")
        conn.request("POST", path, body=body_bytes, headers=hdrs)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        if 200 <= resp.status < 300:
            return True, json.loads(data)
        else:
            return False, f"HTTP {resp.status}: {data[:500]}"
    except Exception as e:
        _reset_tr_conn()
        return False, str(e)

def _http_get_bytes(url, timeout=20):
    """HTTP GET → (status, bytes_or_err)"""
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, context=_ssl(), timeout=timeout)
        return True, resp.read()
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)

# ━━━━━━━━━━━━━━━━━━━━ 翻译 ━━━━━━━━━━━━━━━━━━━━
_GOOGLE_MAP = {"zh-Hans":"zh-CN","zh-Hant":"zh-TW","he":"iw","auto":"auto"}

def _g(code):
    return _GOOGLE_MAP.get(code, code.split("-")[0])

def ai_translate(cfg, text, src_lang, tgt_lang, on_chunk=None):
    """翻译主入口。on_chunk callback 用于流式输出，每收到一段文本就回调一次。"""
    if not text or not text.strip():
        return {"success":False,"error":"文本为空"}

    url     = _tr_cfg(cfg)["api_url"].strip()
    api_key = _tr_cfg(cfg)["api_key"].strip()
    model   = _tr_cfg(cfg)["model"].strip()

    if url and api_key:
        # OpenAI 兼容模式
        src_name = dict(LANGUAGES).get(src_lang, src_lang)
        tgt_name = dict(LANGUAGES).get(tgt_lang, tgt_lang)
        src_d = src_name.split(" ",1)[-1] if " " in src_name else src_name
        tgt_d = tgt_name.split(" ",1)[-1] if " " in tgt_name else tgt_name

        sys_prompt = (f"你是一个专业的翻译引擎。将以下文本从{src_d}翻译成{tgt_d}。"
                      f"只输出翻译结果，不要任何解释。保持格式和标点。")

        body = {"model":model,"messages":[
            {"role":"system","content":sys_prompt},
            {"role":"user","content":text},
        ],"temperature":0.3,"max_tokens":max(4096,len(text)*4),"stream":True}

        extra = _tr_cfg(cfg)["extra_body"].strip()
        if extra:
            try: body.update(json.loads(extra))
            except: pass

        hdrs = {"Content-Type":"application/json",
                "Authorization":f"Bearer {api_key}",
                "User-Agent":"qclawTranslate/1.3"}
        body_bytes = json.dumps(body).encode("utf-8")

        # ── streaming 模式 ──
        try:
            conn = _get_tr_conn(url)
            parsed = urlparse(url)
            path = parsed.path + ("?" + parsed.query if parsed.query else "")
            conn.request("POST", path, body=body_bytes, headers=hdrs)
            resp = conn.getresponse()

            if resp.status != 200:
                err = resp.read().decode("utf-8")[:500]
                return {"success":False,"error":f"HTTP {resp.status}: {err}"}

            full_text = ""
            buffer = ""
            for line in resp:
                buffer += line.decode("utf-8")
                while "\n" in buffer:
                    single, buffer = buffer.split("\n", 1)
                    single = single.strip()
                    if not single or not single.startswith("data:"):
                        continue
                    data_str = single[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_text += content
                            if on_chunk:
                                on_chunk(content)
                    except Exception:
                        continue

            if full_text.strip():
                return {"success":True,"text":full_text.strip()}
            # streaming 拿到空结果，fallback 到非 streaming
        except Exception:
            _reset_tr_conn()

        # ── fallback: 非 streaming 模式 ──
        body["stream"] = False
        body_bytes2 = json.dumps(body).encode("utf-8")
        try:
            conn = _get_tr_conn(url)
            parsed = urlparse(url)
            path = parsed.path + ("?" + parsed.query if parsed.query else "")
            conn.request("POST", path, body=body_bytes2, headers=hdrs)
            resp = conn.getresponse()
            data = resp.read().decode("utf-8")
            if 200 <= resp.status < 300:
                content = json.loads(data)["choices"][0]["message"]["content"].strip()
                if on_chunk:
                    on_chunk(content)
                return {"success":True,"text":content}
            else:
                return {"success":False,"error":f"HTTP {resp.status}: {data[:500]}"}
        except Exception as e:
            _reset_tr_conn()
            return {"success":False,"error":str(e)}

    # 兜底：Google 免费翻译
    try:
        p = {"client":"gtx","ie":"UTF-8","oe":"UTF-8","dj":1,
             "dt":["t","bd","at","ex","ld","md","rw","rm","ss","qc"],
             "sl":_g(src_lang),"tl":_g(tgt_lang),"q":text}
        u = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(p, doseq=True)
        ok, d = _http_get_bytes(u, timeout=10)
        if ok:
            d2 = json.loads(d.decode("utf-8"))
            out = "".join(x.get("trans","") or x.get("text","") for x in d2.get("sentences",[]))
            return {"success":True,"text":out.strip()}
        return {"success":False,"error":f"Google: {d}"}
    except Exception as e:
        return {"success":False,"error":f"Google 翻译失败: {e}"}


# ━━━━━━━━━━━━━━━━━━━━ TTS (CosyVoice WebSocket 流式) ━━━━━━━━━━━━━━━━━━━━

def tts_synthesize(cfg, text, lang_hint=None):
    """
    CosyVoice WebSocket 流式 TTS。
    返回 (ok, bytes_or_err) — bytes 直接是 MP3 二进制。
    """
    api_key = _tts_cfg(cfg)["api_key"].strip()
    ws_url  = _tts_cfg(cfg)["ws_url"].strip()
    model   = _tts_cfg(cfg)["model"].strip()
    voice   = _tts_cfg(cfg)["voice"].strip()

    if not api_key or not ws_url:
        return False, "请先配置 TTS WebSocket 地址和 Key"

    try:
        import websocket
    except ImportError:
        return False, "缺少 websocket-client 库: pip install websocket-client"

    task_id  = str(uuid.uuid4())
    chunks   = []
    error    = [None]
    done     = threading.Event()

    def _on_open(ws):
        run_msg = {
            "header": {"action": "run-task", "task_id": task_id, "streaming": "duplex"},
            "payload": {
                "task_group": "audio", "task": "tts", "function": "SpeechSynthesizer",
                "model": model,
                "parameters": {"text_type": "PlainText", "voice": voice, "format": "mp3",
                               "sample_rate": 22050, "volume": 50, "rate": 1.0, "pitch": 1.0},
                "input": {}
            }
        }
        ws.send(json.dumps(run_msg))

    def _on_msg(ws, msg):
        if isinstance(msg, bytes):
            chunks.append(msg)
            return
        try:
            evt = json.loads(msg)
            event = evt.get("header", {}).get("event", "")
            if event == "task-started":
                ws.send(json.dumps({
                    "header": {"action": "continue-task", "task_id": task_id, "streaming": "duplex"},
                    "payload": {"input": {"text": text}}
                }))
                ws.send(json.dumps({
                    "header": {"action": "finish-task", "task_id": task_id, "streaming": "duplex"},
                    "payload": {"input": {}}
                }))
            elif event == "task-failed":
                error[0] = evt.get("header", {}).get("error_message", "Unknown")
                done.set()
            elif event == "task-finished":
                done.set()
        except Exception:
            pass

    def _on_err(ws, err):
        error[0] = str(err)
        done.set()

    def _on_close(ws, code, msg):
        if not done.is_set():
            done.set()

    ws_app = websocket.WebSocketApp(
        ws_url,
        header={"Authorization": f"Bearer {api_key}"},
        on_open=_on_open, on_message=_on_msg, on_error=_on_err, on_close=_on_close
    )
    t = threading.Thread(
        target=lambda: ws_app.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}),
        daemon=True
    )
    t.start()

    if not done.wait(timeout=15):
        ws_app.close()
        return False, "TTS 超时"

    if error[0]:
        return False, error[0]

    combined = b"".join(chunks)
    if not combined:
        return False, "TTS 返回空音频"
    return True, combined


def play_audio(audio_bytes):
    """
    MCI 无窗口播放 — 不弹任何播放器窗口。
    在子线程同步播放，自动清理临时文件。
    """
    fd, path = tempfile.mkstemp(suffix=".mp3")
    with os.fdopen(fd, "wb") as f:
        f.write(audio_bytes)

    def _mci_play():
        alias = f"qtts_{uuid.uuid4().hex[:8]}"
        try:
            ctypes.windll.winmm.mciSendStringW(f'open "{path}" type MPEGVideo alias {alias}', None, 0, 0)
            ctypes.windll.winmm.mciSendStringW(f'play {alias} wait', None, 0, 0)
        finally:
            ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, 0)
            try: os.unlink(path)
            except: pass

    threading.Thread(target=_mci_play, daemon=True).start()


# ━━━━━━━━━━━━━━━━━━━━ 后台线程 ━━━━━━━━━━━━━━━━━━━━
def _bg_translate(cfg, text, src, dst):
    """后台翻译线程 → 流式发信号到 UI"""
    try:
        def on_chunk(content):
            _bridge.translate_chunk.emit(content)
        result = ai_translate(cfg, text, src, dst, on_chunk=on_chunk)
        _bridge.translate_result.emit(result)
    except Exception as e:
        _bridge.translate_result.emit({"success":False,"error":str(e)})

def _bg_tts(cfg, text, lang):
    try:
        result = tts_synthesize(cfg, text, lang)
        _bridge.tts_result.emit(result)
    except Exception as e:
        _bridge.tts_result.emit((False, str(e)))


# ━━━━━━━━━━━━━━━━━━━━ 读选中文字（Windows UI Automation） ━━━━━━━━━━━━━━━━━━━━

# 模块级缓存 UIA 对象，避免每次都重新创建
_uia_cache = None

def _get_uia():
    global _uia_cache
    if _uia_cache is None:
        _uia_cache = _cc.CreateObject(_CUIA8)
    return _uia_cache


def _get_selected_text():
    """通过 UIA 偏移截取直接读取焦点窗口选中文字。
    不碰 SendInput、不碰剪贴板、不抢焦点。"""
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    return _read_selection_uia(hwnd) or None


def _get_selected_with_position():
    """通过 UIA 偏移截取读取焦点窗口选中文字 + 选中区域坐标。
    返回 (text_or_None, (screen_x, screen_y)_or_None)。
    失败返回 (None, None)。"""
    try:
        uia = _get_uia()
        element = uia.GetFocusedElement()
        if element is None:
            return None, None

        tp = element.GetCurrentPattern(10014)
        if tp is None:
            return None, None

        tpi = tp.QueryInterface(_IUIA_TP)
        sel = tpi.GetSelection()
        if sel is None or sel.Length == 0:
            return None, None

        doc = tpi.DocumentRange
        full = doc.GetText(-1)
        if not full:
            return None, None

        # 偏移截取
        TPRE_Start, TPRE_End = 0, 1
        results = []
        last_rect = None
        for i in range(sel.Length):
            sr = sel.GetElement(i)
            try:
                c_start = doc.Clone()
                c_start.MoveEndpointByRange(TPRE_End, sr, TPRE_Start)
                lo = len(c_start.GetText(-1))
                c_end = doc.Clone()
                c_end.MoveEndpointByRange(TPRE_End, sr, TPRE_End)
                hi = len(c_end.GetText(-1))
                if 0 <= lo < hi <= len(full):
                    results.append(full[lo:hi])
            except Exception:
                continue
            # 坐标
            try:
                rects = sr.GetBoundingRectangles()
                if rects and rects.Length > 0:
                    last_rect = rects.GetElement(rects.Length - 1)
            except Exception:
                pass

        result = ''.join(results).strip()

        if last_rect is not None:
            mid_x = int((last_rect.left + last_rect.right) / 2)
            pos = (mid_x, int(last_rect.top))
        elif element.CurrentBoundingRectangle is not None:
            r = element.CurrentBoundingRectangle
            mid_x = int((r.left + r.right) / 2)
            pos = (mid_x, int(r.top))
        else:
            pos = None

        return result, pos

    except Exception:
        return None, None


# ━━ 剪贴板安全读写（托盘菜单 _clip_from_clipboard 仍用 Ctrl+C 路径）━━━
def _get_clipboard_text():
    """安全读取剪贴板文本，失败返回 None"""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            return None
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        return None


def _set_clipboard_text(text):
    """安全写入剪贴板文本"""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass


# ━━ UIA 递归查找 & 偏移截取 ━━
def _find_text_pattern_recursive(uia, element, depth=0, max_depth=5, max_children=50):
    """递归遍历 UIA 子元素树，找到有选中的 TextPattern 并返回。
    返回 IUIAutomationTextPattern 或 None。"""
    if depth > max_depth:
        return None
    try:
        tp = element.GetCurrentPattern(10014)  # UIA_TextPatternId
        if tp:
            try:
                tpi = tp.QueryInterface(_IUIA_TP)
                sel = tpi.GetSelection()
                if sel and sel.Length > 0:
                    return tpi
            except Exception:
                pass
    except Exception:
        pass
    try:
        uia_children = element.FindAll(2, uia.CreateTrueCondition())
        if uia_children is None or uia_children.Length == 0:
            return None
        count = min(uia_children.Length, max_children)
        for i in range(count):
            child = uia_children.GetElement(i)
            r = _find_text_pattern_recursive(uia, child, depth + 1, max_depth, max_children)
            if r:
                return r
    except Exception:
        pass
    return None


def _read_selection_uia(hwnd):
    """通过 UIA 偏移截取读取指定窗口中的选中文字。
    不碰 SendInput、不碰剪贴板、不抢焦点。
    返回选中文字（字符串）；失败或无选中返回空字符串。"""
    try:
        uia = _get_uia()
        element = uia.ElementFromHandle(hwnd)
        if element is None:
            return ""

        tpi = _find_text_pattern_recursive(uia, element)
        if tpi is None:
            return ""

        sel = tpi.GetSelection()
        doc = tpi.DocumentRange
        full = doc.GetText(-1)
        if not full:
            return ""

        TPRE_Start, TPRE_End = 0, 1
        results = []
        for i in range(sel.Length):
            sr = sel.GetElement(i)
            try:
                c_start = doc.Clone()
                c_start.MoveEndpointByRange(TPRE_End, sr, TPRE_Start)
                lo = len(c_start.GetText(-1))

                c_end = doc.Clone()
                c_end.MoveEndpointByRange(TPRE_End, sr, TPRE_End)
                hi = len(c_end.GetText(-1))

                if 0 <= lo < hi <= len(full):
                    results.append(full[lo:hi])
            except Exception:
                continue

        return ''.join(results)
    except Exception:
        return ""


def _read_selection(hwnd):
    """读取选中文字：UIA 偏移截取优先，失败回退 Ctrl+C。
    Notepad → UIA 偏移截取；Edge/Anki/Qt → Ctrl+C 回退。"""
    text = _read_selection_uia(hwnd)
    if text:
        return text
    return _copy_selection_fallback(hwnd)


def _bring_to_front_hwnd(hwnd):
    """尝试把目标窗口切换到前台，失败不抛异常"""
    try:
        user32 = ctypes.windll.user32
        cur = user32.GetForegroundWindow()
        if cur == hwnd:
            return
        ctid = user32.GetWindowThreadProcessId(cur, None)
        ttid = user32.GetWindowThreadProcessId(hwnd, None)
        if ctid != ttid:
            user32.AttachThreadInput(ttid, ctid, True)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        if ctid != ttid:
            user32.AttachThreadInput(ttid, ctid, False)
        time.sleep(0.05)
    except Exception:
        pass


def _send_ctrl_c_sendinput():
    """SendInput 模拟 Ctrl+C，含 key-down / key-up 配对"""
    try:
        from ctypes import byref, sizeof, Structure, Union, c_uint, c_ushort, c_ulong
        import ctypes.wintypes as wt
        class MI(Structure):
            _fields_ = [("dx", wt.LONG), ("dy", wt.LONG),
                        ("mouseData", c_ulong), ("dwFlags", c_ulong),
                        ("time", c_ulong), ("dwExtraInfo", ctypes.c_size_t)]
        class KI(Structure):
            _fields_ = [("wVk", c_ushort), ("wScan", c_ushort), ("dwFlags", c_ulong),
                        ("time", c_ulong), ("dwExtraInfo", ctypes.c_size_t)]
        class HI(Structure):
            _fields_ = [("uMsg", c_ulong), ("wParamL", c_ushort), ("wParamH", c_ushort)]
        class IU(Union):
            _fields_ = [("mi", MI), ("ki", KI), ("hi", HI)]
        class INP(Structure):
            _fields_ = [("type", c_ulong), ("u", IU)]
        KEYEVENTF_KEYUP = 0x0002
        def _send(vk, up=False):
            inp = INP()
            inp.type = 1
            inp.u.ki.wVk = vk
            if up:
                inp.u.ki.dwFlags = KEYEVENTF_KEYUP
            ctypes.windll.user32.SendInput(1, byref(inp), sizeof(INP))
        # ★ 新增：先释放 Ctrl 键（VK_CONTROL=0x11），清除热键残留的 Ctrl 按下状态
        _send(0x11, True)
        time.sleep(0.02)
        _send(0x11); time.sleep(0.01)
        _send(0x43); time.sleep(0.01)
        _send(0x43, True); time.sleep(0.01)
        _send(0x11, True); time.sleep(0.03)
    except Exception:
        pass


def _copy_selection_fallback(hwnd):
    """SendInput Ctrl+C 搬运选中文字。仅当 UIA 不可用时使用。
    不切焦点——Ctrl+C 直接发向前台窗口（即用户正在操作的窗口）。
    所有分支恢复剪贴板。返回文字或空串。"""
    if hwnd is None or hwnd == 0:
        return ""
    old_clip = _get_clipboard_text()
    # 不调用 _bring_to_front_hwnd——避免焦点切到 qclawTranslate 自身
    _send_ctrl_c_sendinput()
    deadline = time.perf_counter() + 1.2
    new_text = None
    while time.perf_counter() < deadline:
        current = _get_clipboard_text()
        if current is not None and current != old_clip:
            new_text = current
            break
        time.sleep(0.03)
    if old_clip is not None:
        _set_clipboard_text(old_clip)
    return new_text if new_text else ""


# --- RegisterHotKey 全局热键（Ctrl+Q/E） ---
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
VK_Q = 0x51
VK_E = 0x45
HOTKEY_ID_TRANSLATE = 1
HOTKEY_ID_TTS = 2


class _NativeEventFilter(QAbstractNativeEventFilter):
    """拦截 WM_HOTKEY，分发到对应回调。"""
    def __init__(self, callback_map):
        super().__init__()
        self._cb = callback_map

    def nativeEventFilter(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                hid = msg.wParam
                cb = self._cb.get(hid)
                if cb:
                    cb()
                    return True, 0
        return False, 0


# ━━━━━━━━━━━━━━━━━━━━ 设置对话框 ━━━━━━━━━━━━━━━━━━━━
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(560, 480)
        self.resize(640, 680)
        self.cfg = load_config()
        self._build()

    def _fld(self, parent, label, value, placeholder="", password=False, tooltip=""):
        col = QVBoxLayout(); col.setSpacing(8)
        lbl = QLabel(label); lbl.setStyleSheet("font-size:13px;font-weight:600;color:#e6edf3;")
        if tooltip: lbl.setToolTip(tooltip)
        ed = QLineEdit(value); ed.setPlaceholderText(placeholder)
        if password: ed.setEchoMode(QLineEdit.Password)
        col.addWidget(lbl); col.addWidget(ed)
        parent.addLayout(col)
        return ed

    def _build(self):
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        card = QFrame(objectName="card"); card.setStyleSheet("padding:0;")
        lay = QVBoxLayout(card); lay.setSpacing(0); lay.setContentsMargins(28,24,28,24)

        # 标题栏 + 关闭按钮
        title_bar = QHBoxLayout()
        title = QLabel("⚙️  设置"); title.setStyleSheet("font-size:18px;font-weight:bold;color:#e6edf3;")
        title_bar.addWidget(title); title_bar.addStretch()
        close_btn = QPushButton("✕"); close_btn.setStyleSheet("background:transparent;color:#adb1b8;font-size:16px;border:none;padding:4px 8px;")
        close_btn.clicked.connect(self.reject)
        title_bar.addWidget(close_btn)
        lay.addLayout(title_bar)
        lay.addSpacing(24)

        # 主体：左侧导航 + 右侧面板
        body = QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0,0,0,0)

        self.nav = QListWidget(objectName="nav")
        self.nav.setFixedWidth(160)
        self.nav.addItem("📝 翻译引擎")
        self.nav.addItem("🔊 TTS 引擎")
        self.nav.addItem("🎤 发音分析")
        self.nav.addItem("💬 实时字幕")
        self.nav.addItem("⚙️ 通用设置")
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._on_nav_changed)
        body.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_translate_page())
        self.stack.addWidget(self._build_tts_page())
        self.stack.addWidget(self._build_pronunciation_page())
        self.stack.addWidget(self._build_subtitle_page())
        self.stack.addWidget(self._build_general_page())
        body.addWidget(self.stack, 1)

        lay.addLayout(body, 1)

        # 底部提示 + 按钮
        lay.addSpacing(20)
        hint = QLabel("💡 配置更改后需点击保存生效")
        hint.setStyleSheet("color:#6e7681;font-size:12px;padding:0 0 12px 0;")
        lay.addWidget(hint)
        bl = QHBoxLayout(); bl.setContentsMargins(0,0,0,0); bl.addStretch()
        c = QPushButton("取消"); c.setObjectName("btn-tts"); c.clicked.connect(self.reject)
        s = QPushButton("保存"); s.setObjectName("btn-primary"); s.clicked.connect(self._save)
        bl.addWidget(c); bl.addSpacing(10); bl.addWidget(s); lay.addLayout(bl)

        outer.addWidget(card)

    def _on_nav_changed(self, row):
        self.stack.setCurrentIndex(row)

    # ── 翻译引擎面板 ──
    def _build_translate_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setSpacing(20); l.setContentsMargins(24,16,24,16)

        # 云端/本地切换
        engine_row = QHBoxLayout()
        self.tr_engine_cloud = QRadioButton("云端"); self.tr_engine_cloud.setChecked(True)
        self.tr_engine_local = QRadioButton("本地")
        engine_row.addWidget(self.tr_engine_cloud); engine_row.addWidget(self.tr_engine_local)
        engine_row.addStretch(); l.addLayout(engine_row)

        # 云端面板
        self.tr_cloud_panel = QWidget()
        cl = QVBoxLayout(self.tr_cloud_panel); cl.setSpacing(20); cl.setContentsMargins(0,0,0,0)
        self.tr_url   = self._fld(cl,"API 地址", _tr_cfg(self.cfg)["api_url"],
                                   "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.tr_key   = self._fld(cl,"API Key",  _tr_cfg(self.cfg)["api_key"], "sk-xx", password=True)
        self.tr_model = self._fld(cl,"模型名称",   _tr_cfg(self.cfg)["model"], "qwen-plus / qwen-turbo ...")
        self.tr_extra = self._fld(cl,"额外参数", _tr_cfg(self.cfg)["extra_body"],'{"temperature":0.3}')
        cl.addSpacing(8); tr = QHBoxLayout(); tr.addStretch()
        tb = QPushButton("🔍 测试连接"); tb.setObjectName("btn-tts")
        self.tr_test = QLabel(""); self.tr_test.setStyleSheet("color:#6e7681;font-size:11px;")
        tb.clicked.connect(self._test_translate)
        tr.addWidget(tb); tr.addWidget(self.tr_test); tr.addStretch(); cl.addLayout(tr)
        l.addWidget(self.tr_cloud_panel)

        # 本地面板（预留禁用）
        self.tr_local_panel = QWidget(); self.tr_local_panel.setEnabled(False)
        ll = QVBoxLayout(self.tr_local_panel); ll.setSpacing(20); ll.setContentsMargins(0,0,0,0)
        ll.addWidget(QLabel("本地翻译引擎即将支持", styleSheet="color:#6e7681;font-size:13px;padding:20px 0;"))
        l.addWidget(self.tr_local_panel)

        self.tr_engine_cloud.toggled.connect(self._on_tr_engine_changed)
        l.addStretch()
        return page

    def _on_tr_engine_changed(self):
        cloud = self.tr_engine_cloud.isChecked()
        self.tr_cloud_panel.setVisible(cloud)
        self.tr_local_panel.setVisible(not cloud)

    # ── TTS 引擎面板 ──
    def _build_tts_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setSpacing(20); l.setContentsMargins(24,16,24,16)

        engine_row = QHBoxLayout()
        self.tts_engine_cloud = QRadioButton("云端"); self.tts_engine_cloud.setChecked(True)
        self.tts_engine_local = QRadioButton("本地")
        engine_row.addWidget(self.tts_engine_cloud); engine_row.addWidget(self.tts_engine_local)
        engine_row.addStretch(); l.addLayout(engine_row)

        # 云端面板
        self.tts_cloud_panel = QWidget()
        cl = QVBoxLayout(self.tts_cloud_panel); cl.setSpacing(20); cl.setContentsMargins(0,0,0,0)
        self.tts_ws    = self._fld(cl,"WS 地址",  _tts_cfg(self.cfg)["ws_url"],
                                    "wss://ws-xxx.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference")
        self.tts_key   = self._fld(cl,"API Key",  _tts_cfg(self.cfg)["api_key"], "sk-xx", password=True)
        self.tts_model = self._fld(cl,"TTS 模型", _tts_cfg(self.cfg)["model"], "cosyvoice-v3-flash")
        self.tts_voice = self._fld(cl,"音色",     _tts_cfg(self.cfg)["voice"], "longanyang / longxiaochun ...")
        cl.addSpacing(8); tr2 = QHBoxLayout(); tr2.addStretch()
        tb2 = QPushButton("🔊 试听"); tb2.setObjectName("btn-tts")
        self.tts_test = QLabel(""); self.tts_test.setStyleSheet("color:#6e7681;font-size:11px;")
        tb2.clicked.connect(self._test_tts)
        tr2.addWidget(tb2); tr2.addWidget(self.tts_test); tr2.addStretch(); cl.addLayout(tr2)
        l.addWidget(self.tts_cloud_panel)

        # 本地面板（预留禁用）
        self.tts_local_panel = QWidget(); self.tts_local_panel.setEnabled(False)
        ll = QVBoxLayout(self.tts_local_panel); ll.setSpacing(20); ll.setContentsMargins(0,0,0,0)
        ll.addWidget(QLabel("本地 TTS 引擎即将支持 (edge-tts)", styleSheet="color:#6e7681;font-size:13px;padding:20px 0;"))
        l.addWidget(self.tts_local_panel)

        self.tts_engine_cloud.toggled.connect(self._on_tts_engine_changed)

        # 播放设置
        l.addSpacing(12)
        speed_lbl = QLabel("语速"); speed_lbl.setStyleSheet("font-size:13px;font-weight:600;color:#e6edf3;")
        l.addWidget(speed_lbl)
        speed_row = QHBoxLayout(); speed_row.setSpacing(12)
        self.tts_speed = QSlider(Qt.Horizontal); self.tts_speed.setMinimum(50); self.tts_speed.setMaximum(200); self.tts_speed.setValue(int(self.cfg["tts"]["playback"]["speed"]*100))
        self.tts_speed_lbl = QLabel(f"{self.tts_speed.value()/100:.1f}x"); self.tts_speed_lbl.setStyleSheet("color:#adb1b8;font-size:13px;min-width:36px;")
        self.tts_speed.valueChanged.connect(lambda v: self.tts_speed_lbl.setText(f"{v/100:.1f}x"))
        speed_row.addWidget(self.tts_speed, 1); speed_row.addWidget(self.tts_speed_lbl)
        l.addLayout(speed_row)

        cache_row = QHBoxLayout()
        self.tts_cache = QCheckBox("启用本地缓存"); self.tts_cache.setChecked(self.cfg["tts"]["playback"]["cache_enabled"])
        cache_row.addWidget(self.tts_cache); cache_row.addStretch(); l.addLayout(cache_row)

        l.addStretch()
        return page

    def _on_tts_engine_changed(self):
        cloud = self.tts_engine_cloud.isChecked()
        self.tts_cloud_panel.setVisible(cloud)
        self.tts_local_panel.setVisible(not cloud)

    # ── 发音分析面板（Phase B 预留） ──
    def _build_pronunciation_page(self):
        page = QWidget(); page.setEnabled(False)
        l = QVBoxLayout(page); l.setSpacing(20); l.setContentsMargins(24,16,24,16)
        l.addWidget(QLabel("发音分析", objectName="section-title"))
        info = QLabel("🔒 即将推出\n\n预计支持：WhisperX + wav2vec2 音素级打分\n功能将在 Phase B 中实现")
        info.setStyleSheet("color:#6e7681;font-size:13px;padding:40px 0;")
        l.addWidget(info); l.addStretch()
        return page

    # ── 实时字幕面板（Phase C 预留） ──
    def _build_subtitle_page(self):
        page = QWidget(); page.setEnabled(False)
        l = QVBoxLayout(page); l.setSpacing(20); l.setContentsMargins(24,16,24,16)
        l.addWidget(QLabel("实时字幕", objectName="section-title"))
        info = QLabel("🔒 即将推出\n\n预计支持：sherpa-onnx 流式 ASR + VAD\n功能将在 Phase C 中实现")
        info.setStyleSheet("color:#6e7681;font-size:13px;padding:40px 0;")
        l.addWidget(info); l.addStretch()
        return page

    # ── 通用设置面板 ──
    def _build_general_page(self):
        page = QWidget(); l = QVBoxLayout(page); l.setSpacing(20); l.setContentsMargins(24,16,24,16)
        l.addWidget(QLabel("通用设置", objectName="section-title"))

        self.boot = QCheckBox("开机自启")
        self.boot.setChecked(self.cfg["general"]["start_on_boot"])
        l.addWidget(self.boot)

        self.tray_min = QCheckBox("最小化到托盘")
        self.tray_min.setChecked(self.cfg["general"]["tray_minimize"])
        l.addWidget(self.tray_min)

        l.addSpacing(8)
        theme_lbl = QLabel("主题"); theme_lbl.setStyleSheet("font-size:13px;font-weight:600;color:#e6edf3;")
        l.addWidget(theme_lbl)
        theme_row = QHBoxLayout()
        self.theme_combo = QComboBox(); self.theme_combo.addItem("深色", "dark"); self.theme_combo.addItem("浅色", "light")
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(self.cfg["general"].get("theme", "dark")))
        theme_row.addWidget(self.theme_combo, 1); theme_row.addStretch()
        l.addLayout(theme_row)

        lang_lbl = QLabel("界面语言"); lang_lbl.setStyleSheet("font-size:13px;font-weight:600;color:#e6edf3;")
        l.addWidget(lang_lbl)
        lang_row = QHBoxLayout()
        self.lang_combo = QComboBox(); self.lang_combo.addItem("简体中文", "zh-CN"); self.lang_combo.addItem("English", "en-US")
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(self.cfg["general"].get("language", "zh-CN")))
        lang_row.addWidget(self.lang_combo, 1); lang_row.addStretch()
        l.addLayout(lang_row)

        l.addStretch()
        return page

    def _save(self):
        c = self.cfg
        # 翻译
        c["translate"]["engine"] = "cloud" if self.tr_engine_cloud.isChecked() else "local"
        _tr_cfg(c)["api_url"]    = self.tr_url.text().strip()
        _tr_cfg(c)["api_key"]    = self.tr_key.text().strip()
        _tr_cfg(c)["model"]     = self.tr_model.text().strip()
        _tr_cfg(c)["extra_body"] = self.tr_extra.text().strip()
        # TTS
        c["tts"]["engine"] = "cloud" if self.tts_engine_cloud.isChecked() else "local"
        _tts_cfg(c)["ws_url"]   = self.tts_ws.text().strip()
        _tts_cfg(c)["api_key"]   = self.tts_key.text().strip()
        _tts_cfg(c)["model"]    = self.tts_model.text().strip()
        _tts_cfg(c)["voice"]    = self.tts_voice.text().strip()
        c["tts"]["playback"]["speed"] = self.tts_speed.value() / 100.0
        c["tts"]["playback"]["cache_enabled"] = self.tts_cache.isChecked()
        # 通用
        c["general"]["start_on_boot"] = self.boot.isChecked()
        c["general"]["tray_minimize"] = self.tray_min.isChecked()
        c["general"]["theme"] = self.theme_combo.currentData()
        c["general"]["language"] = self.lang_combo.currentData()
        save_config(c); _toggle_startup(c["general"]["start_on_boot"])
        self.accept()

    def _test_translate(self):
        cfg = {"translate": {"cloud": {
            "api_url":self.tr_url.text().strip(),
            "api_key":self.tr_key.text().strip(),
            "model":self.tr_model.text().strip(),
            "extra_body":self.tr_extra.text().strip(),
        }}}
        if not _tr_cfg(cfg)["api_url"] or not _tr_cfg(cfg)["api_key"]:
            self.tr_test.setText("❌ 请填写地址和Key"); self.tr_test.setStyleSheet("color:#f85149;font-size:11px;"); return
        self.tr_test.setText("⏳ 测试中…"); self.tr_test.setStyleSheet("color:#d29922;font-size:11px;")

        # 清理旧连接
        try: _bridge.test_tr.disconnect()
        except: pass
        _bridge.test_tr.connect(self._on_test_tr)

        threading.Thread(target=lambda: self._bg_test_tr(cfg), daemon=True).start()

    def _bg_test_tr(self, cfg):
        try:
            r = ai_translate(cfg, "Hello world!", "en", "zh-Hans")
            _bridge.test_tr.emit(r)
        except Exception as e:
            _bridge.test_tr.emit({"success":False,"error":str(e)})

    def _on_test_tr(self, r):
        if r["success"]:
            self.tr_test.setText(f"✓ {r['text'][:40]}"); self.tr_test.setStyleSheet("color:#56d364;font-size:11px;")
        else:
            self.tr_test.setText(f"❌ {str(r.get('error',''))[:80]}"); self.tr_test.setStyleSheet("color:#f85149;font-size:11px;")

    def _test_tts(self):
        cfg = {"tts": {"cloud": {
            "ws_url":self.tts_ws.text().strip(),
            "api_key":self.tts_key.text().strip(),
            "model":self.tts_model.text().strip(),
            "voice":self.tts_voice.text().strip(),
        }}}
        if not _tts_cfg(cfg)["ws_url"] or not _tts_cfg(cfg)["api_key"]:
            self.tts_test.setText("❌ 请填写地址和Key"); self.tts_test.setStyleSheet("color:#f85149;font-size:11px;"); return
        self.tts_test.setText("⏳ 合成中…"); self.tts_test.setStyleSheet("color:#d29922;font-size:11px;")

        try: _bridge.test_tts.disconnect()
        except: pass
        _bridge.test_tts.connect(self._on_test_tts)

        threading.Thread(target=lambda: self._bg_test_tts(cfg), daemon=True).start()

    def _bg_test_tts(self, cfg):
        try:
            r = tts_synthesize(cfg, "你好世界", "zh-Hans")
            _bridge.test_tts.emit(r)
        except Exception as e:
            _bridge.test_tts.emit((False, str(e)))

    def _on_test_tts(self, r):
        ok, data = r
        if ok:
            self.tts_test.setText("✓ 试听中…"); self.tts_test.setStyleSheet("color:#56d364;font-size:11px;")
            threading.Thread(target=lambda: play_audio(data), daemon=True).start()
        else:
            self.tts_test.setText(f"❌ {str(data)[:80]}"); self.tts_test.setStyleSheet("color:#f85149;font-size:11px;")


# ━━━━━━━━━━━━━━━━━━━━ 主窗口 ━━━━━━━━━━━━━━━━━━━━
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self._setup_window()
        self._setup_ui()
        self._setup_tray()
        self._setup_hotkeys()
        self._debounce = QTimer(singleShot=True, interval=400, timeout=self._do_translate)
        self._last_text = ""
        self._translating = False
        self._tts_busy    = False

    def _setup_window(self):
        self.setWindowTitle(f"qclawTranslate")
        self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "qclaw.ico")))
        self.setMinimumSize(700, 540); self.resize(820, 620)
        r = QApplication.primaryScreen().geometry()
        self.move((r.width()-820)//2, (r.height()-620)//2)
        self.setStyleSheet(QSS)

    def _setup_ui(self):
        cw = QWidget(); cw.setStyleSheet("background:#0d1117;"); self.setCentralWidget(cw)
        m = QVBoxLayout(cw); m.setContentsMargins(20,16,20,20); m.setSpacing(14)

        # 标题栏
        h = QHBoxLayout()
        logo = QLabel("🦞", styleSheet="font-size:22px;padding:0 6px 0 0;")
        h.addWidget(logo)
        h.addWidget(QLabel("qclawTranslate", styleSheet="font-size:18px;font-weight:800;color:#58a6ff;"))
        h.addStretch()
        self.status = QLabel("就绪", objectName="status"); h.addWidget(self.status)
        h.addSpacing(12)
        hint = QLabel("Ctrl+Q 翻译  ·  Ctrl+E 朗读", styleSheet="color:#6e7681;font-size:11px;")
        h.addWidget(hint)
        h.addSpacing(8)
        sb = QPushButton("⚙"); sb.setObjectName("btn-settings"); sb.clicked.connect(self._settings); h.addWidget(sb)
        m.addLayout(h)

        # 语言栏
        lb = QHBoxLayout(); lb.setSpacing(10)
        self.src = QComboBox(); self.dst = QComboBox()
        for code, label in LANGUAGES:
            self.src.addItem(label, code); self.dst.addItem(label, code)
        self.src.setCurrentIndex(0); self.dst.setCurrentIndex(3)
        sw = QPushButton("⇄"); sw.setObjectName("btn-swap"); sw.clicked.connect(self._swap)
        lb.addWidget(QLabel("源语言")); lb.addWidget(self.src,2)
        lb.addWidget(sw,0,Qt.AlignCenter); lb.addWidget(QLabel("目标语言")); lb.addWidget(self.dst,2)
        m.addLayout(lb)

        # 输入
        ic = QFrame(objectName="card"); il = QVBoxLayout(ic); il.setContentsMargins(12,12,12,12)
        self.input_edit = QTextEdit(placeholderText="✍️ 输入文字，或选中后 Ctrl+Q 划词翻译…")
        self.input_edit.setMinimumHeight(110)
        self.input_edit.textChanged.connect(lambda: self._debounce.start())
        il.addWidget(self.input_edit)
        ib = QHBoxLayout(); ib.addStretch()
        self.cc = QLabel("0 字符", styleSheet="color:#6e7681;font-size:11px;"); ib.addWidget(self.cc); il.addLayout(ib)
        m.addWidget(ic,2)

        # 按钮
        ab = QHBoxLayout(); ab.setSpacing(10)
        self.btn_tr = QPushButton("🚀  翻译"); self.btn_tr.setObjectName("btn-primary")
        self.btn_tr.setMinimumWidth(110); self.btn_tr.clicked.connect(self._on_click_translate)
        self.btn_cp = QPushButton("📋 复制译文"); self.btn_cp.setObjectName("btn-tts")
        self.btn_cp.clicked.connect(lambda: self._copy(self.output_edit.toPlainText()))
        self.btn_src = QPushButton("🔊  朗读原文"); self.btn_src.setObjectName("btn-tts")
        self.btn_src.clicked.connect(lambda: self._on_click_tts(self.input_edit.toPlainText()))
        self.btn_dst = QPushButton("🔊  朗读译文"); self.btn_dst.setObjectName("btn-tts")
        self.btn_dst.clicked.connect(lambda: self._on_click_tts(self.output_edit.toPlainText()))
        ab.addWidget(self.btn_tr); ab.addWidget(self.btn_cp)
        ab.addStretch(); ab.addWidget(self.btn_src); ab.addWidget(self.btn_dst)
        m.addLayout(ab)

        # 输出
        oc = QFrame(objectName="card"); ol = QVBoxLayout(oc); ol.setContentsMargins(12,12,12,12)
        self.output_edit = QTextEdit(readOnly=True, placeholderText="📝 翻译结果将显示在这里…")
        self.output_edit.setMinimumHeight(110); ol.addWidget(self.output_edit)
        m.addWidget(oc,3)

        self.input_edit.textChanged.connect(lambda: self.cc.setText(f"{len(self.input_edit.toPlainText())} 字符"))

        # 连接信号桥
        _bridge.translate_result.connect(self._on_translate_result)
        _bridge.translate_chunk.connect(self._on_translate_chunk)
        _bridge.tts_result.connect(self._on_tts_result)

    # ── 托盘 ──
    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon_path = os.path.join(BASE_DIR, "qclaw.ico")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            # 没有图标文件时用标准图标兜底，确保托盘一定有图标
            self.tray.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray.setToolTip(f"{APP_NAME} v{VERSION} — 双击恢复窗口 | Ctrl+Q 翻译 | Ctrl+E 朗读")
        mm = QMenu()
        mm.setStyleSheet("QMenu{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:4px;}"
                         "QMenu::item{padding:8px 24px;border-radius:4px;}"
                         "QMenu::item:selected{background:#388bfd44;}")
        mm.addAction("📋 显示窗口", self._show)
        mm.addSeparator()
        mm.addAction("🔍 划词翻译", self._clip_translate)
        mm.addAction("🔊 划词朗读", self._clip_tts); mm.addSeparator()
        mm.addAction("⚙ 引擎设置", self._settings); mm.addSeparator()
        mm.addAction("❌ 退出", self._quit)
        self.tray.setContextMenu(mm)
        self.tray.activated.connect(lambda r: self._show() if r==QSystemTrayIcon.DoubleClick else None)
        self.tray.show()

    def _show(self):
        self.show(); self.raise_(); self.activateWindow(); self.input_edit.setFocus()
        # 任务栏闪烁提示
        ctypes.windll.user32.FlashWindow(int(self.winId()), True)

    def closeEvent(self, e):
        msg = QMessageBox(self)
        msg.setWindowTitle("qclawTranslate")
        msg.setText("关闭窗口时：")
        msg.setIcon(QMessageBox.Question)
        btn_exit = msg.addButton("退出程序", QMessageBox.DestructiveRole)
        btn_tray = msg.addButton("最小化到托盘", QMessageBox.AcceptRole)
        btn_cancel = msg.addButton("取消", QMessageBox.RejectRole)
        msg.setDefaultButton(btn_tray)
        msg.exec_()
        clicked = msg.clickedButton()
        if clicked == btn_exit:
            e.accept()
            self._quit()
        elif clicked == btn_tray:
            e.ignore()
            self.hide()
            self.tray.showMessage(APP_NAME,
                "已最小化到托盘 — 双击托盘图标恢复",
                QSystemTrayIcon.Information, 4000)
        else:
            e.ignore()

    def _quit(self):
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey(None, HOTKEY_ID_TRANSLATE)
        user32.UnregisterHotKey(None, HOTKEY_ID_TTS)
        self.tray.hide()
        QApplication.quit()

    # ── 划词 ──
    def _clip_translate(self):
        text = _get_selected_text()
        if text:
            self._show()
            self.input_edit.setPlainText(text)
            self._do_translate()
        else:
            self._show()

    def _clip_tts(self):
        text = _get_selected_text()
        if text:
            self._on_click_tts(text)

    def _copy(self, text):
        if not text: return
        try:
            import win32clipboard
            win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(text); win32clipboard.CloseClipboard()
            self.status.setText("✓ 已复制"); QTimer.singleShot(2000, lambda: self.status.setText(""))
        except:
            self.status.setText("✗ 复制失败")

    # ── 设置 ──
    def _settings(self):
        d = SettingsDialog(self)
        if d.exec_() == QDialog.Accepted:
            self.cfg = load_config()

    # ── 热键 ──
    def _setup_hotkeys(self):
        """RegisterHotKey 注册全局热键 Ctrl+Q / Ctrl+E"""
        user32 = ctypes.windll.user32
        user32.RegisterHotKey(None, HOTKEY_ID_TRANSLATE, MOD_CONTROL, VK_Q)
        user32.RegisterHotKey(None, HOTKEY_ID_TTS, MOD_CONTROL, VK_E)
        self._native_filter = _NativeEventFilter({
            HOTKEY_ID_TRANSLATE: self._hotkey_translate_action,
            HOTKEY_ID_TTS: self._hotkey_tts_action,
        })
        QApplication.instance().installNativeEventFilter(self._native_filter)

    def _hotkey_translate_action(self):
        """Ctrl+Q — 读取前台窗口选中文字→翻译（UIA优先，Ctrl+C回退）"""
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd == int(self.winId()):
            return

        text = _read_selection(hwnd)
        if not text or not text.strip():
            return

        text = text.replace('\r\n', '\n').replace('\r', '\n')
        self._show()
        self.input_edit.setPlainText(text)
        self._do_translate()

    def _hotkey_tts_action(self):
        """Ctrl+E — 读取前台窗口选中文字→朗读（UIA优先，Ctrl+C回退）"""
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if hwnd == int(self.winId()):
            return

        text = _read_selection(hwnd)
        if not text or not text.strip():
            return

        text = text.replace('\r\n', '\n').replace('\r', '\n')
        self._on_click_tts(text)

    # ── 翻译 ──
    def _on_click_translate(self):
        """按钮触动手动翻译 — 强制忽略 _last_text 去重"""
        self._last_text = ""  # 清除去重，允许手动重新翻译
        self._do_translate()

    def _do_translate(self):
        if self._translating:
            return
        text = self.input_edit.toPlainText().strip()
        if not text:
            self.output_edit.clear()
            return
        if text == self._last_text:
            return
        self._last_text = text
        self._translating = True
        self._streaming_text = ""
        self.output_edit.clear()

        self.btn_tr.setEnabled(False); self.btn_tr.setText("⏳ 翻译中…")
        self.status.setText("⏳ 翻译中…")

        src_code = self.src.currentData()
        dst_code = self.dst.currentData()
        cfg = dict(self.cfg)  # copy

        threading.Thread(target=lambda: _bg_translate(cfg, text, src_code, dst_code), daemon=True).start()

    def _on_translate_chunk(self, chunk):
        """流式翻译：逐块追加到输出框"""
        if not hasattr(self, '_streaming_text'):
            self._streaming_text = ""
        self._streaming_text += chunk
        self.output_edit.setPlainText(self._streaming_text)

    def _on_translate_result(self, result):
        self._translating = False
        self.btn_tr.setEnabled(True); self.btn_tr.setText("🚀  翻译")
        if result["success"]:
            # 流式已经逐块显示了，这里用最终完整结果覆盖一次（确保格式正确）
            self.output_edit.setPlainText(result["text"])
            self.status.setText("✓ 完成")
        else:
            err = str(result.get("error","未知错误"))
            self.status.setText(f"✗ {err}")
            self.output_edit.setPlainText(f"[翻译失败]\n{err}")

    # ── TTS ──
    def _on_click_tts(self, text):
        if self._tts_busy:
            return
        text = text.strip()
        if not text:
            return
        api_key = _tts_cfg(self.cfg)["api_key"].strip()
        ws_url  = _tts_cfg(self.cfg)["ws_url"].strip()
        if not api_key or not ws_url:
            QMessageBox.warning(self,"提示","请先在 ⚙ 设置中配置 TTS 引擎\n（WebSocket 地址 + Key + 模型名）")
            return

        self._tts_busy = True
        self.status.setText("🔊 合成中…")
        src_code = self.src.currentData()
        cfg = dict(self.cfg)

        threading.Thread(target=lambda: _bg_tts(cfg, text, src_code), daemon=True).start()

    def _on_tts_result(self, result):
        self._tts_busy = False
        ok, data = result
        if ok:
            self.status.setText("🔊 播放中…")
            play_audio(data)
            QTimer.singleShot(2000, lambda: self.status.setText("") if self.status.text().startswith("🔊") else None)
        else:
            err = str(data)
            self.status.setText(f"✗ {err}")
            QMessageBox.warning(self,"TTS 失败", err)

    # ── 交换 ──
    def _swap(self):
        src_code = self.src.currentData()
        dst_code = self.dst.currentData()
        # auto 只能做源语言，如果源是 auto，则把目标变源，源切换为上次目标的反向
        if src_code == "auto":
            # 源是 auto 时，把目标语言提到源，源切换为原目标语言
            self.src.setCurrentIndex(self.dst.currentIndex())
            # 目标切换为中文简体作为默认
            for i in range(self.dst.count()):
                if self.dst.itemData(i) == "zh-Hans":
                    self.dst.setCurrentIndex(i)
                    break
        else:
            si = self.src.currentIndex(); di = self.dst.currentIndex()
            self.src.setCurrentIndex(di); self.dst.setCurrentIndex(si)
        self._last_text = ""  # 允许重新翻译
        # 交换文本框内容
        o = self.output_edit.toPlainText(); i = self.input_edit.toPlainText()
        if o:
            self.input_edit.setPlainText(o); self.output_edit.setPlainText(i)
            self._do_translate()  # 交换后立即翻译


# ━━━━━━━━━━━━━━━━━━━━ 开机自启 ━━━━━━━━━━━━━━━━━━━━
_STARTUP_DIR = os.path.join(os.environ.get("APPDATA",""),
                            r"Microsoft\Windows\Start Menu\Programs\Startup")

def _toggle_startup(on):
    p = os.path.join(_STARTUP_DIR, "qclawTranslate.bat")
    if on:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p,"w",encoding="utf-8") as f:
                f.write(f'@echo off\nchcp 65001 >nul\ncd /d "{BASE_DIR}"\n'
                        f'start "" /B "C:\\Users\\Administrator\\AppData\\Local\\Python\\bin\\pythonw.exe" '
                        f'"{os.path.join(BASE_DIR,"main.py")}"\n')
        except: pass
    else:
        try: os.remove(p)
        except: pass


# ━━━━━━━━━━━━━━━━━━━━ 入口 ━━━━━━━━━━━━━━━━━━━━
def main():
    # 单实例锁 — Windows 标准互斥锁
    kernel32 = ctypes.windll.kernel32
    user32   = ctypes.windll.user32
    ERROR_ALREADY_EXISTS = 183
    mutex_name = f"Global\\{APP_NAME}_SingleInstance"
    mutex_handle = kernel32.CreateMutexW(None, False, mutex_name)
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        # 已有实例 → 激活已有窗口
        existing = user32.FindWindowW(None, "qclawTranslate")
        if existing:
            # 用 SW_SHOWNORMAL (1) 而非 SW_RESTORE，确保从 hidden 状态也能恢复
            user32.ShowWindow(existing, 1)   # SW_SHOWNORMAL
            user32.SetForegroundWindow(existing)
            user32.FlashWindow(existing, True)
        else:
            # 窗口标题找不到时尝试枚举所有顶级窗口
            def _enum_proc(hwnd, lparam):
                title = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(hwnd, title, 256)
                if user32.IsWindowVisible(hwnd) and "qclaw" in title.value.lower():
                    user32.ShowWindow(hwnd, 1)
                    user32.SetForegroundWindow(hwnd)
                    return False  # 停止枚举
                return True
            ENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_size_t, ctypes.c_size_t)
            user32.EnumWindows(ENUMPROC(_enum_proc), 0)
        sys.exit(0)

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setFont(QFont("Microsoft YaHei UI", 10))
    win = MainWindow()
    win.show()
    if load_config().get("start_on_boot", False):
        _toggle_startup(True)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
