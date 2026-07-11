# -*- coding: utf-8 -*-
"""
qclawTranslate 取词诊断脚本
用途：模拟热键触发后的完整取词流程，采集诊断数据
使用：在 Edge/Anki 中选中文字后，命令行运行 python diag_selection.py
"""
import sys, os, time, ctypes
from ctypes import wintypes, byref, sizeof, Structure, Union, c_uint, c_ushort, c_ulong

# 把 qclawTranslate 源码目录加入 sys.path，以便 import 其 UIA 函数
sys.path.insert(0, r"D:\qclawTranslate")

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

CF_UNICODETEXT = 13

# ━━━━━━━━━━━━━━━━━━━━ 纯 ctypes 剪贴板 ━━━━━━━━━━━━

def diag_get_clipboard_text():
    """纯 ctypes 读剪贴板，返回 (成功标志, 内容或错误信息)"""
    if not user32.OpenClipboard(None):
        err = kernel32.GetLastError()
        return False, f"OpenClipboard failed, GetLastError={err}"
    try:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return True, None  # 成功打开但无文本
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            err = kernel32.GetLastError()
            return False, f"GetClipboardData failed, GetLastError={err}"
        ptr = kernel32.GlobalLock(h)
        if not ptr:
            err = kernel32.GetLastError()
            return False, f"GlobalLock failed, GetLastError={err}"
        try:
            text = ctypes.wstring_at(ptr)
            return True, text
        finally:
            kernel32.GlobalUnlock(h)
    finally:
        user32.CloseClipboard()


# ━━━━━━━━━━━━━━━━━━━━ 诊断版 SendInput Ctrl+C ━━━━━━━━━━━━

def diag_send_ctrl_c():
    """诊断版 SendInput Ctrl+C，打印每步结果"""

    class KI(Structure):
        _fields_ = [("wVk", c_ushort), ("wScan", c_ushort), ("dwFlags", c_ulong),
                    ("time", c_ulong), ("dwExtraInfo", ctypes.POINTER(c_ulong))]
    class IU(Union):
        _fields_ = [("ki", KI)]
    class INP(Structure):
        _fields_ = [("type", c_ulong), ("u", IU)]
    KEYEVENTF_KEYUP = 0x0002

    def _send_diag(vk, up=False, label=""):
        inp = INP()
        inp.type = 1
        inp.u.ki.wVk = vk
        if up:
            inp.u.ki.dwFlags = KEYEVENTF_KEYUP
        ret = user32.SendInput(1, byref(inp), sizeof(INP))
        err = kernel32.GetLastError()
        print(f"    SendInput({label}): ret={ret}, GetLastError={err}")

    # 打印发送前的按键物理状态
    ctrl_state = user32.GetAsyncKeyState(0x11) & 0x8000
    q_state = user32.GetAsyncKeyState(0x51) & 0x8000
    e_state = user32.GetAsyncKeyState(0x45) & 0x8000
    print(f"  物理按键状态: Ctrl={'按下' if ctrl_state else '未按'}, Q={'按下' if q_state else '未按'}, E={'按下' if e_state else '未按'}")

    # 释放 Ctrl（和现有代码一样）
    _send_diag(0x11, True, "Ctrl up (释放)")
    time.sleep(0.02)

    # 重新发 Ctrl+C
    _send_diag(0x11, False, "Ctrl down")
    time.sleep(0.01)
    _send_diag(0x43, False, "C down")
    time.sleep(0.01)
    _send_diag(0x43, True, "C up")
    time.sleep(0.01)
    _send_diag(0x11, True, "Ctrl up")
    time.sleep(0.03)


# ━━━━━━━━━━━━━━━━━━━━ 诊断版 UIA 取词 ━━━━━━━━━━━━

def diag_read_selection_uia(hwnd):
    """诊断版 UIA 取词，打印详细过程"""
    print(f"\n[2] UIA 取词诊断")
    print(f"  hwnd={hwnd} (0x{hwnd:X})")

    try:
        from main import _get_uia, _IUIA_TP
    except Exception as e:
        print(f"  import main 失败: {e}")
        return ""

    # 1. ElementFromHandle
    try:
        uia = _get_uia()
        element = uia.ElementFromHandle(hwnd)
        if element is None:
            print("  ElementFromHandle 返回 None")
            return ""
        print("  ElementFromHandle 成功")
    except Exception as e:
        print(f"  ElementFromHandle 异常: {e}")
        return ""

    # 2. 递归查找 TextPattern
    tp_count = [0]
    sel_count = [0]
    found_tpi = [None]

    def diag_find_tp(elem, depth=0, max_depth=5, max_children=50):
        if depth > max_depth:
            return
        try:
            tp = elem.GetCurrentPattern(10014)  # UIA_TextPatternId
            if tp:
                tp_count[0] += 1
                try:
                    tpi = tp.QueryInterface(_IUIA_TP)
                    sel = tpi.GetSelection()
                    if sel and sel.Length > 0:
                        sel_count[0] += sel.Length
                        print(f"  depth={depth} 找到 TextPattern #{tp_count[0]}, 选中区间数={sel.Length}")
                        doc = tpi.DocumentRange
                        full = doc.GetText(-1)
                        print(f"    full text 长度={len(full) if full else 0}")
                        for i in range(sel.Length):
                            sr = sel.GetElement(i)
                            TPRE_Start, TPRE_End = 0, 1
                            c_start = doc.Clone()
                            c_start.MoveEndpointByRange(TPRE_End, sr, TPRE_Start)
                            lo = len(c_start.GetText(-1))
                            c_end = doc.Clone()
                            c_end.MoveEndpointByRange(TPRE_End, sr, TPRE_End)
                            hi = len(c_end.GetText(-1))
                            print(f"    区间[{i}]: lo={lo}, hi={hi}, lo<hi={lo < hi}")
                            if 0 <= lo < hi <= len(full) if full else False:
                                print(f"    选中文本: \"{full[lo:hi][:100]}\"")
                        found_tpi[0] = tpi
                        return
                    else:
                        print(f"  depth={depth} 找到 TextPattern #{tp_count[0]}, 但无选中区间")
                except Exception as e:
                    print(f"  depth={depth} TextPattern QueryInterface 异常: {e}")
        except Exception:
            pass

        try:
            children = elem.FindAll(2, uia.CreateTrueCondition())
            if children is None or children.Length == 0:
                return
            count = min(children.Length, max_children)
            if depth == 0:
                print(f"  顶层子元素数: {children.Length} (遍历前 {count})")
            for i in range(count):
                child = children.GetElement(i)
                diag_find_tp(child, depth + 1, max_depth, max_children)
                if found_tpi[0] is not None:
                    return
        except Exception as e:
            print(f"  FindAll 异常: {e}")

    diag_find_tp(element)
    print(f"  汇总: 找到 {tp_count[0]} 个 TextPattern, {sel_count[0]} 个选中区间")

    if found_tpi[0] is None:
        return ""

    # 截取选中文本（同 main.py 逻辑）
    try:
        tpi = found_tpi[0]
        sel = tpi.GetSelection()
        doc = tpi.DocumentRange
        full = doc.GetText(-1)
        if not full:
            print("  DocumentRange.GetText 返回空")
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
            except Exception as e:
                print(f"  区间[{i}] 截取异常: {e}")
                continue
        return ''.join(results)
    except Exception as e:
        print(f"  UIA 截取异常: {e}")
        return ""


# ━━━━━━━━━━━━━━━━━━━━ 诊断版 Ctrl+C fallback ━━━━━━━━━━━━

def diag_ctrl_c_fallback(hwnd):
    """诊断版 Ctrl+C fallback，打印详细过程"""
    print(f"\n[3] Ctrl+C fallback 诊断")

    # a. 旧剪贴板内容
    ok, old = diag_get_clipboard_text()
    if ok:
        old_display = repr(old[:80]) if old else repr(old)
        print(f"  旧剪贴板内容: {old_display}")
    else:
        print(f"  旧剪贴板读取失败: {old}")
        old = None

    # b/c/d. 发送 Ctrl+C
    print(f"  发送 Ctrl+C 序列:")
    diag_send_ctrl_c()

    # e. 轮询剪贴板
    print(f"  轮询剪贴板:")
    deadline = time.perf_counter() + 2.0
    poll_interval = 0.03
    poll_count = 0
    new_text = None
    while time.perf_counter() < deadline:
        poll_count += 1
        ok, current = diag_get_clipboard_text()
        if ok:
            cur_display = repr(current[:80]) if current else repr(current)
            changed = (current is not None) and (current != old)
            if changed:
                print(f"    [{poll_count}] OpenClipboard=True, 内容={cur_display}, 变化!")
                new_text = current
                break
            else:
                print(f"    [{poll_count}] OpenClipboard=True, 内容={cur_display}, 未变化")
        else:
            print(f"    [{poll_count}] OpenClipboard=False, {current}")

        time.sleep(poll_interval)

    if new_text:
        print(f"  取到文字: {repr(new_text[:100])}")
    else:
        print(f"  轮询超时（{poll_count} 次），剪贴板从未变化")
        print(f"  最终结果: 取词失败")

    return new_text or ""


# ━━━━━━━━━━━━━━━━━━━━ 主流程 ━━━━━━━━━━━━

def get_window_info(hwnd):
    """获取窗口标题和进程名"""
    # 标题
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value

    # 进程名
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, byref(pid))
    process_name = "?"
    try:
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        PROCESS_VM_READ = 0x0010
        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid.value)
        if h:
            try:
                psapi = ctypes.windll.psapi
                buf2 = ctypes.create_unicode_buffer(260)
                size = wintypes.DWORD(260)
                if psapi.GetModuleFileNameExW(h, None, buf2, size):
                    process_name = os.path.basename(buf2.value)
            finally:
                kernel32.CloseHandle(h)
    except Exception:
        pass

    return title, process_name, pid.value


def main():
    print("=" * 60)
    print("取词诊断开始")
    print("=" * 60)

    # [1] 前台窗口信息
    hwnd = user32.GetForegroundWindow()
    title, process_name, pid = get_window_info(hwnd)
    print(f"\n[1] 前台窗口信息")
    print(f"  hwnd: 0x{hwnd:X}" if hwnd else "  hwnd: 0 (无前台窗口)")
    print(f"  title: \"{title}\"")
    print(f"  process: {process_name} (PID={pid})")

    if not hwnd:
        print("\n无前台窗口，诊断终止")
        return

    # [2] UIA 取词诊断
    uia_result = diag_read_selection_uia(hwnd)
    uia_success = bool(uia_result)

    # [3] Ctrl+C fallback 诊断（UIA 失败时才走）
    ctrl_c_result = ""
    if not uia_success:
        ctrl_c_result = diag_ctrl_c_fallback(hwnd)
    else:
        print(f"\n[3] Ctrl+C fallback 诊断")
        print(f"  跳过（UIA 取词成功）")

    # [4] 诊断摘要
    print(f"\n{'=' * 60}")
    print(f"[4] 诊断摘要")
    print(f"{'=' * 60}")
    print(f"  前台窗口: {process_name} — \"{title}\"")
    print(f"  UIA: {'成功' if uia_success else '失败'}" + (f" — \"{uia_result[:80]}\"" if uia_success else ""))
    if not uia_success:
        print(f"  Ctrl+C: {'成功' if ctrl_c_result else '失败'}" + (f" — \"{ctrl_c_result[:80]}\"" if ctrl_c_result else ""))
    final = uia_result or ctrl_c_result
    print(f"  最终结果: {'取词成功' if final else '取词失败'}")
    if final:
        print(f"  文本: \"{final[:200]}\"")
    print()


if __name__ == "__main__":
    main()
