# qclawTranslate v1.4.0 — CosyVoice WebSocket TTS 迁移

## 背景
v1.3.0 TTS 用 DashScope HTTP REST + OSS 下载链路，延迟 3-5 秒。用户要求提速。

## 方案
切换到阿里云 CosyVoice WebSocket 流式 TTS API。

## 关键参数
- **Workspace ID**: `ws-c80jgdae5squls8x`
- **API Host**: `wss://ws-c80jgdae5squls8x.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference`
- **模型**: `cosyvoice-v3-flash`
- **音色**: `longanyang` (龙安阳)
- **API Key**: 与翻译/DashScope 同一把（Bearer Auth）

## 测试结果
| 指标 | 旧 HTTP 链路 | 新 WebSocket 链路 |
|---|---|---|
| 延迟 | ~3-5s | **~1.5s** |
| 请求数 | 3 次 HTTP | 1 次 WS 连接 |
| 输出 | WAV 整块 (126KB) | MP3 流式 21 分片 (54KB) |
| 临时文件 | 需要 | 不需要（内存拼合） |

## 代码变更
- `main.py` v1.3.0→v1.4.0:
  - `tts_synthesize()`: 从 HTTP POST→OSS URL→GET 改为 WebSocket `run-task`→`continue-task`→`finish-task` 协议
  - `play_wav()` → `play_audio()`: PowerShell SoundPlayer → ShellExecute 默认播放器
  - 设置对话框 TTS Tab: 去掉 HTTP URL/extra_body，改为 WS 地址
- `config.py`: 默认值更新为 CosyVoice 参数
- `config.json`: 预填 Workspace 专属域名 + Key + 模型

## 交互协议
```
Client → run-task(model, voice, format=mp3, ...)
Server → task-started
Client → continue-task(text) + finish-task
Server → binary chunks × N → result-generated ... → task-finished
```
