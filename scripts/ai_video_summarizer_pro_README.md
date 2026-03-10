# AI视频内容总结工具 - 使用说明

## 🎯 工具介绍

这是一个**实际可用**的AI视频内容总结工具，可以：
1. 获取B站视频信息
2. 提取视频字幕（如果有）
3. 使用AI模型（Kimi/GLM/DeepSeek）生成内容总结
4. 支持批量处理多个视频

## 📦 安装依赖

```bash
cd D:\怖客\scripts
pip install requests
```

## 🔧 配置API密钥

### 方式1：环境变量（推荐）
```powershell
# PowerShell
$env:BOBAPI_KEY="your-api-key-here"

# 或者永久设置
[Environment]::SetEnvironmentVariable("BOBAPI_KEY", "your-api-key", "User")
```

### 方式2：直接修改代码
编辑 `ai_video_summarizer_pro.py` 文件，修改以下部分：
```python
API_CONFIG = {
    "base_url": "https://bobdong.cn/",
    "api_key": "your-api-key-here",  # 直接填写你的API密钥
    "model": "Kimi-K2.5"
}
```

## 🚀 使用方法

### 1. 总结单个视频

```bash
# 使用BV号
python ai_video_summarizer_pro.py --bvid BV1jG411c7Fj

# 使用URL
python ai_video_summarizer_pro.py --url "https://www.bilibili.com/video/BV1jG411c7Fj"
```

### 2. 批量总结视频

创建一个文本文件 `videos.txt`，每行一个BV号：
```
BV1jG411c7Fj
BV1D1qpB6ECc
BV19SiFB1E1q
```

然后运行：
```bash
python ai_video_summarizer_pro.py --file videos.txt --output summaries.json
```

### 3. 不使用AI（仅获取信息）

```bash
python ai_video_summarizer_pro.py --bvid BV1jG411c7Fj --no-ai
```

## 📊 输出格式

工具会生成JSON格式的总结报告：

```json
{
  "generated_at": "2026-03-08T21:30:00",
  "total_videos": 1,
  "summaries": [
    {
      "bvid": "BV1jG411c7Fj",
      "title": "视频标题",
      "owner": "UP主名称",
      "duration": 3600,
      "view_count": 2482000,
      "content_source": "description",
      "summary": "AI生成的总结内容...",
      "has_subtitle": false,
      "generated_at": "2026-03-08T21:30:00"
    }
  ]
}
```

## 🔌 API支持

工具支持多个API提供商：

### 1. bobapi（推荐）
- 模型：Kimi-K2.5, GLM-5, MiniMax-M2.5
- 优点：国内访问快，中文优化好
- 配置：设置 `BOBAPI_KEY` 环境变量

### 2. OpenRouter（备用）
- 模型：deepseek/deepseek-chat 等
- 优点：模型选择多
- 配置：设置 `OPENROUTER_API_KEY` 环境变量

## 💡 工作原理

1. **获取视频信息**：通过B站API获取视频标题、描述、UP主等信息
2. **提取字幕**：尝试获取B站官方字幕（如果有）
3. **构建提示词**：将视频内容（字幕或描述）构建成AI提示词
4. **AI总结**：调用AI模型生成内容总结
5. **输出结果**：保存为JSON格式

## ⚠️ 注意事项

1. **API密钥**：必须配置有效的API密钥才能使用AI总结功能
2. **网络访问**：需要能访问B站API和AI API
3. **请求频率**：批量处理时会有延迟，避免请求过快
4. **字幕限制**：目前主要使用视频描述生成总结，字幕提取需要进一步完善
5. **内容长度**：过短的内容（<50字）无法生成有意义的总结

## 🛠️ 进阶使用

### 集成到现有系统

```python
from ai_video_summarizer_pro import VideoSummarizer

summarizer = VideoSummarizer()
result = summarizer.summarize_video("BV1jG411c7Fj")

if result:
    print(f"标题: {result['title']}")
    print(f"总结: {result['summary']}")
```

### 自定义总结长度

修改代码中的 `max_length` 参数：
```python
summary = self.ai_summarizer.summarize(
    content, 
    video_info['title'],
    max_length=300  # 改为300字
)
```

## 📞 故障排除

### 问题1：API调用失败
- 检查API密钥是否正确
- 检查网络连接
- 查看API余额是否充足

### 问题2：无法获取视频信息
- 检查BV号是否正确
- 检查视频是否存在
- 检查网络连接

### 问题3：总结质量不高
- 视频描述越详细，总结质量越高
- 有字幕的视频总结更准确
- 可以调整AI模型的temperature参数

## 🔄 更新计划

未来可能添加的功能：
1. 音频下载和语音转文字
2. 更智能的字幕提取
3. 多语言支持
4. 批量处理优化
5. Web界面

## 📝 许可证

MIT License - 自由使用和修改

---

**创建时间**: 2026-03-08
**版本**: 1.0.0
**作者**: AI Assistant