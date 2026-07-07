# qclawTranslate v1.2

> 开源翻译 + TTS 朗读工具  
> 翻译走大模型 /chat/completions 兼容 API  
> 所有参数可视化配置

## 使用

双击桌面 **qclawTranslate** → ⚙ 齿轮设置 → 填入 Key → 开用

## 快捷键

| 热键 | 功能 |
|------|------|
| Ctrl+Q | 划词翻译（自动复制→翻译） |
| Ctrl+E | 划词朗读（自动复制→TTS） |

## 引擎配置

设置分两个 Tab：

**📝 翻译** — OpenAI 兼容 /chat/completions
- API 地址、API Key、模型名、额外参数（JSON）
- 🔍 测试连接按钮
- 不填 API 则自动用 Google 免费翻译兜底

**🔊 TTS** — 语音合成
- API 地址、API Key、TTS 模型名、音色、额外参数
- 🔊 试听按钮

两个引擎可共用同一个 DashScope Key，也可以分别配置不同服务。
