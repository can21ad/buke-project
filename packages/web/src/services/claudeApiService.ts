/**
 * Claude API 服务
 * 用于调用 Claude AI 模型生成内容
 */

export interface ClaudeMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ClaudeResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

class ClaudeApiService {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey: string, baseUrl: string = 'https://api.edgefn.net/v1/chat/completions') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  /**
   * 调用 Claude API 生成内容
   */
  async generateContent(
    messages: ClaudeMessage[],
    model: string = 'DeepSeek-V3.2',
    temperature: number = 0.7
  ): Promise<string> {
    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model,
          messages,
          temperature,
          max_tokens: 1000
        })
      });

      if (!response.ok) {
        throw new Error(`API 请求失败: ${response.status} ${response.statusText}`);
      }

      const data: ClaudeResponse = await response.json();
      return data.choices[0].message.content;
    } catch (error) {
      console.error('调用 Claude API 失败:', error);
      throw error;
    }
  }

  /**
   * 生成视频总结
   */
  async generateVideoSummary(title: string, content: string): Promise<string> {
    const messages: ClaudeMessage[] = [
      {
        role: 'system',
        content: '你是一个专业的恐怖灵异内容摘要生成器，请用简洁的语言总结以下视频内容，控制在50字以内。'
      },
      {
        role: 'user',
        content: `视频标题: ${title}\n视频内容: ${content}\n请生成一个简洁的总结:`
      }
    ];

    return this.generateContent(messages);
  }

  /**
   * 提取关键词
   */
  async extractKeywords(text: string): Promise<string[]> {
    const messages: ClaudeMessage[] = [
      {
        role: 'system',
        content: '请从以下文本中提取最多5个关键词，用逗号分隔。'
      },
      {
        role: 'user',
        content: `文本: ${text}\n关键词:`
      }
    ];

    const response = await this.generateContent(messages);
    return response.split(',').map(keyword => keyword.trim()).filter(Boolean);
  }
}

// 创建单例实例
// 注意：这里的 API Key 应该从环境变量中获取，而不是硬编码
// 为了演示，我们暂时使用一个占位符
export const claudeApiService = new ClaudeApiService(
  process.env.NEXT_PUBLIC_CLAUDE_API_KEY || 'YOUR_API_KEY'
);
