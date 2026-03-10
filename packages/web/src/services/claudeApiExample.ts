/**
 * Claude API 使用示例
 * 演示如何调用 Claude API 生成内容
 */

import { claudeApiService } from './claudeApiService';

/**
 * 测试 Claude API 调用
 */
export async function testClaudeApi() {
  try {
    console.log('开始测试 Claude API...');

    // 测试基本对话
    const basicResponse = await claudeApiService.generateContent([
      {
        role: 'user',
        content: 'Hello, how are you?'
      }
    ]);
    console.log('基本对话响应:', basicResponse);

    // 测试视频总结
    const videoTitle = '【第123期】恐怖灵异故事合集';
    const videoContent = '本期包含3个恐怖故事：1. 深夜楼道里的脚步声 2. 废弃医院的鬼影 3. 乡村老宅的神秘事件。观众纷纷表示被吓到了。';
    const summary = await claudeApiService.generateVideoSummary(videoTitle, videoContent);
    console.log('视频总结:', summary);

    // 测试关键词提取
    const keywords = await claudeApiService.extractKeywords(videoContent);
    console.log('提取的关键词:', keywords);

    console.log('Claude API 测试完成！');
  } catch (error) {
    console.error('测试 Claude API 失败:', error);
  }
}

/**
 * 生成恐怖故事创意
 */
export async function generateHorrorStoryIdeas(prompt: string): Promise<string> {
  return claudeApiService.generateContent([
    {
      role: 'system',
      content: '你是一个专业的恐怖故事作家，请根据用户的提示生成恐怖故事创意。'
    },
    {
      role: 'user',
      content: `请根据以下提示生成恐怖故事创意：${prompt}`
    }
  ]);
}

/**
 * 分析恐怖故事主题
 */
export async function analyzeHorrorTheme(story: string): Promise<string> {
  return claudeApiService.generateContent([
    {
      role: 'system',
      content: '你是一个恐怖文学分析师，请分析以下恐怖故事的主题、氛围和恐怖元素。'
    },
    {
      role: 'user',
      content: `请分析以下恐怖故事：${story}`
    }
  ]);
}
