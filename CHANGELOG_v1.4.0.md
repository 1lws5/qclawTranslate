# qclawTranslate v1.4.0 — CosyVoice WS + MCI播放 + 原生热键

## 变更摘要

### 1. TTS 后端：HTTP REST → CosyVoice WebSocket 流式
- 端点：`wss://ws-c80jgdae5squls8x.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference`
- 协议：run-task → task-started → continue-task(text) → finish-task → binary chunks → task-finished
- 延迟：3-5s → ~1.5s（54KB MP3/21分片）
- 模型：`cosyvoice-v3-flash`，音色：`longanyang`

### 2. 播放器：ShellExecute → MCI 无窗口
- 旧：`cmd /c start` 弹出系统播放器
- 新：`winmm.mciSendStringW` 直接播放，零窗口
- 文件自动清理（播放后删除临时 MP3）

### 3. 热键：keyboard 库 → Windows RegisterHotKey
- 旧：`keyboard` 库（需管理员权限，不可靠）
- 新：`RegisterHotKey` + `QAbstractNativeEventFilter`（无需管理员，原生）
- Ctrl+Q：Copy → 粘贴到输入框 → 自动翻译
- Ctrl+E：Copy → 朗读剪贴板

### 4. 设置对话框
- TTS 配置从 HTTP URL → WebSocket 地址
- 移除 tts_extra_body 字段
- 默认预填 Workspace 专属域名 + Key
