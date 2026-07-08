# -*- coding: utf-8 -*-
"""最简验证：手动选中 Notepad 文字 → _read_selection_uia(RichEditD2DPT hwnd)"""
import sys, os, ctypes, time, io
sys.path.insert(0, os.path.dirname(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import comtypes.client as _cc
from comtypes.gen.UIAutomationClient import CUIAutomation8 as _CUIA8, IUIAutomationTextPattern as _IUIA_TP

user32 = ctypes.windll.user32

# ━━ Step 1: 确保 Notepad 前台 ━━
hwnd = user32.FindWindowW("Notepad", None)
while user32.GetForegroundWindow() != hwnd:
    cur = user32.GetForegroundWindow()
    ctid = user32.GetWindowThreadProcessId(cur, None)
    ttid = user32.GetWindowThreadProcessId(hwnd, None)
    if ctid != ttid: user32.AttachThreadInput(ttid, ctid, True)
    user32.SetForegroundWindow(hwnd); user32.BringWindowToTop(hwnd)
    if ctid != ttid: user32.AttachThreadInput(ttid, ctid, False)
    time.sleep(0.2)

# ━━ Step 2: 找 RichEditD2DPT 子窗口 ━━
edit_hwnd = None
@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
def enum_cb(h, _):
    global edit_hwnd
    cls = ctypes.create_unicode_buffer(128)
    user32.GetClassNameW(h, cls, 128)
    if cls.value == 'RichEditD2DPT':
        edit_hwnd = h
        return False  # stop
    return True
user32.EnumChildWindows(hwnd, enum_cb, None)
print(f"RichEditD2DPT hwnd={edit_hwnd}")

# ━━ Step 3: 直接通过 edit_hwnd 的 UIA 对象选中 ━━
uia = _cc.CreateObject(_CUIA8)
edit_el = uia.ElementFromHandle(edit_hwnd)
print(f"Element: name={repr(edit_el.CurrentName)} type={edit_el.CurrentControlType}")

tp = edit_el.GetCurrentPattern(10014)
tpi = tp.QueryInterface(_IUIA_TP)
doc = tpi.DocumentRange
full = doc.GetText(-1)
print(f"全文: {len(full)} 字 {repr(full[:50])}")

# 选中 [0:15] 字符
r = doc.Clone()
TPRE_Start, TPRE_End = 0, 1
r.MoveEndpointByUnit(TPRE_End, 0, -(len(full) - 15))  # End → position 15
r.Select()
time.sleep(0.05)

# 验证选中
sel = tpi.GetSelection()
sr = sel.GetElement(0)
print(f"选区: GetText={repr(sr.GetText(-1)[:30])} selLen={sel.Length}")
c_s = doc.Clone(); c_s.MoveEndpointByRange(TPRE_End, sr, TPRE_Start)
c_e = doc.Clone(); c_e.MoveEndpointByRange(TPRE_End, sr, TPRE_End)
lo = len(c_s.GetText(-1)); hi = len(c_e.GetText(-1))
print(f"偏移 [{lo}:{hi}] = {repr(full[lo:hi])}")

# ━━ Step 4: 调用 _read_selection_uia ━━
from main import _read_selection_uia, _get_uia

# 清缓存用新实例
import main; main._uia_cache = None

result = _read_selection_uia(edit_hwnd)
print(f"\n_read_selection_uia(edit_hwnd): {repr(result)}")
print(f"{'✅ PASS' if result==full[:15] else '❌ FAIL (expected: '+repr(full[:15])+')'}")

# 同样测试顶层 hwnd
result2 = _read_selection_uia(hwnd)
print(f"\n_read_selection_uia(top_hwnd): {repr(result2)}")
print(f"{'✅ PASS' if result2==full[:15] else '❌ FAIL'}")

# ━━ Step 5: 测试 _get_selected_text (GetForegroundWindow → _read_selection_uia) ━━
from main import _get_selected_text
r3 = _get_selected_text()
print(f"\n_get_selected_text(): {repr(r3)}")
print(f"{'✅ PASS' if r3==full[:15] else '❌ FAIL'}")

print("\n=== DONE ===")
