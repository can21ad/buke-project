/**
 * 真正的AI总结服务
 * 基于视频数据（评论、标题等）生成有意义的总结
 */

export interface VideoSummary {
  bvid: string;
  title: string;
  summary: string;
  keyPoints: string[];
  themes: string[];
  generated_at: string;
}

export interface VideoData {
  bvid: string;
  title: string;
  episode: number;
  comments: Array<{
    content: string;
    keyword: string;
    replies?: Array<{
      content: string;
    }>;
  }>;
}

class RealAISummaryService {
  private summaries: Map<string, VideoSummary> = new Map();
  private isLoaded = false;

  /**
   * 加载并生成AI总结
   */
  async loadSummaries(): Promise<void> {
    if (this.isLoaded) return;

    try {
      // 只加载top10_help_comments.json中的总结数据（大家都在看部分）
      const top10Response = await fetch('/data/top10_help_comments.json');
      const top10Data = await top10Response.json();
      
      // 使用top10_help_comments.json中的总结数据
      for (const video of top10Data.videos) {
        if (video.summary) {
          const summary: VideoSummary = {
            bvid: video.bvid,
            title: video.title,
            summary: video.summary,
            keyPoints: [], // 没有keyPoints，可以留空
            themes: [], // 没有themes，可以留空
            generated_at: new Date().toISOString()
          };
          this.summaries.set(video.bvid, summary);
        }
      }
      
      this.isLoaded = true;
      console.log(`已加载 ${this.summaries.size} 个AI总结（仅top10）`);
    } catch (error) {
      console.error('加载AI总结失败:', error);
    }
  }

  /**
   * 基于真实视频数据生成有意义的总结
   */
  private generateRealSummary(video: VideoData): VideoSummary {
    const title = video.title;
    const comments = video.comments || [];
    const episode = video.episode;
    
    // 分析评论提取关键信息
    const analysis = this.analyzeComments(comments);
    
    // 从标题提取核心主题
    const mainTheme = this.extractThemeFromTitle(title);
    
    // 提取关键故事点
    const keyPoints = this.extractKeyPoints(comments, title);
    
    // 生成有意义的总结（基于实际数据）
    const summary = this.createMeaningfulSummary(title, episode, mainTheme, analysis, keyPoints);
    
    return {
      bvid: video.bvid,
      title: title,
      summary: summary,
      keyPoints: keyPoints.slice(0, 3),
      themes: analysis.themes.slice(0, 3),
      generated_at: new Date().toISOString()
    };
  }

  /**
   * 分析评论内容
   */
  private analyzeComments(comments: VideoData['comments']) {
    const themes: string[] = [];
    const storyTypes: string[] = [];
    const emotionalKeywords: string[] = [];
    
    // 分析评论内容
    comments.forEach(comment => {
      const content = comment.content || '';
      const keyword = comment.keyword || '';
      
      // 提取故事类型关键词
      if (content.includes('鬼') || content.includes('恐怖') || content.includes('吓人')) {
        storyTypes.push('恐怖灵异');
      }
      if (content.includes('找') || content.includes('求') || content.includes('哪一期')) {
        storyTypes.push('寻找出处');
      }
      if (content.includes('记得') || content.includes('小时候') || content.includes('以前')) {
        storyTypes.push('童年回忆');
      }
      
      // 提取情感关键词
      if (content.includes('阴影') || content.includes('害怕') || content.includes('恐惧')) {
        emotionalKeywords.push('心理阴影');
      }
      if (content.includes('急') || content.includes('求')) {
        emotionalKeywords.push('急切寻找');
      }
      
      // 从回复中提取答案
      if (comment.replies) {
        comment.replies.forEach(reply => {
          const replyContent = reply.content || '';
          // 如果回复包含"第X集"或"BV号"，说明找到了答案
          if (replyContent.match(/第\d+集/) || replyContent.match(/BV\w+/)) {
            themes.push('已解答');
          }
        });
      }
    });
    
    return {
      themes: Array.from(new Set(themes)),
      storyTypes: Array.from(new Set(storyTypes)),
      emotionalKeywords: Array.from(new Set(emotionalKeywords)),
      totalComments: comments.length
    };
  }

  /**
   * 从标题提取主题
   */
  private extractThemeFromTitle(title: string): string {
    // 提取方括号中的期数信息
    const episodeMatch = title.match(/【([^】]+)】/);
    const episodeInfo = episodeMatch ? episodeMatch[1] : '';
    
    // 提取核心主题词
    const themeKeywords = [
      '马戏团', '鬼', '灵异', '恐怖', '诡异', '神秘', '失踪', 
      '死亡', '灵魂', '附身', '诅咒', '预言', '梦境', '幻觉'
    ];
    
    for (const keyword of themeKeywords) {
      if (title.includes(keyword)) {
        return keyword;
      }
    }
    
    return '恐怖故事';
  }

  /**
   * 提取关键故事点
   */
  private extractKeyPoints(comments: VideoData['comments'], title: string): string[] {
    const keyPoints: string[] = [];
    
    // 从标题提取关键元素
    if (title.includes('马戏团')) {
      keyPoints.push('马戏团背景');
    }
    if (title.includes('拐走') || title.includes('失踪')) {
      keyPoints.push('人员失踪事件');
    }
    if (title.includes('狮子') || title.includes('猴子')) {
      keyPoints.push('动物相关');
    }
    
    // 从评论中提取关键信息
    comments.slice(0, 3).forEach(comment => {
      const content = comment.content || '';
      
      // 提取具体描述
      if (content.includes('女') && content.includes('蝴蝶结')) {
        keyPoints.push('女性角色+蝴蝶结元素');
      }
      if (content.includes('天空') && content.includes('字')) {
        keyPoints.push('天空异象');
      }
      if (content.includes('倒着走') || content.includes('倒走')) {
        keyPoints.push('倒着走的诡异行为');
      }
    });
    
    return keyPoints.length > 0 ? keyPoints : ['恐怖故事', '观众热议'];
  }

  /**
   * 创建有意义的总结
   */
  private createMeaningfulSummary(
    title: string, 
    episode: number, 
    theme: string,
    analysis: any,
    keyPoints: string[]
  ): string {
    const episodeStr = episode > 0 ? `第${episode}期` : '特别篇';
    
    // 基于真实数据构建总结
    let summary = `${episodeStr}：${theme}主题。`;
    
    // 添加关键元素
    if (keyPoints.length > 0) {
      summary += `包含${keyPoints.slice(0, 2).join('、')}。`;
    }
    
    // 添加观众反应
    if (analysis.emotionalKeywords.includes('心理阴影')) {
      summary += '给观众留下深刻印象。';
    }
    
    if (analysis.totalComments > 10) {
      summary += `${analysis.totalComments}条求助评论，社区讨论热烈。`;
    }
    
    // 确保在50字以内
    if (summary.length > 50) {
      summary = summary.substring(0, 47) + '...';
    }
    
    return summary;
  }

  /**
   * 获取视频的AI总结
   */
  getSummary(bvid: string): VideoSummary | null {
    return this.summaries.get(bvid) || null;
  }

  /**
   * 获取所有总结
   */
  getAllSummaries(): VideoSummary[] {
    return Array.from(this.summaries.values());
  }

  /**
   * 检查是否有某个视频的总结
   */
  hasSummary(bvid: string): boolean {
    return this.summaries.has(bvid);
  }
}

// 创建单例实例
export const realAISummaryService = new RealAISummaryService();