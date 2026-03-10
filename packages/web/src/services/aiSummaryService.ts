/**
 * AI总结服务
 * 为视频生成简洁的AI总结
 */

export interface VideoSummary {
  bvid: string;
  title: string;
  summary: string;
  generated_at: string;
  keywords: string[];
}

export interface SummaryResponse {
  generated_at: string;
  total_videos: number;
  success_count: number;
  summaries: VideoSummary[];
}

class AISummaryService {
  private summaries: Map<string, VideoSummary> = new Map();
  private isLoaded = false;

  /**
   * 加载AI总结数据
   */
  async loadSummaries(): Promise<void> {
    if (this.isLoaded) return;

    try {
      const response = await fetch('/data/ai_summaries.json');
      const data: SummaryResponse = await response.json();
      
      data.summaries.forEach(summary => {
        this.summaries.set(summary.bvid, summary);
      });
      
      this.isLoaded = true;
      console.log(`已加载 ${data.summaries.length} 个AI总结`);
    } catch (error) {
      console.error('加载AI总结数据失败:', error);
      // 使用模拟数据作为后备
      await this.loadMockSummaries();
    }
  }

  /**
   * 加载模拟数据（当真实数据不可用时）
   */
  private async loadMockSummaries(): Promise<void> {
    try {
      // 首先尝试从top10数据获取视频信息
      const top10Response = await fetch('/data/top10_help_comments.json');
      const top10Data = await top10Response.json();
      
      // 为每个视频生成模拟总结
      top10Data.videos.forEach((video: any, index: number) => {
        const mockSummary: VideoSummary = {
          bvid: video.bvid,
          title: video.title,
          summary: this.generateMockSummary(video.title, video.comments),
          generated_at: new Date().toISOString(),
          keywords: this.extractKeywords(video.title, video.comments)
        };
        this.summaries.set(video.bvid, mockSummary);
      });
      
      this.isLoaded = true;
      console.log(`已生成 ${top10Data.videos.length} 个模拟AI总结`);
    } catch (error) {
      console.error('加载模拟数据失败:', error);
    }
  }

  /**
   * 生成模拟总结
   */
  private generateMockSummary(title: string, comments: any[]): string {
    // 从标题提取关键信息
    const titleMatch = title.match(/【([^】]+)】/);
    const episode = titleMatch ? titleMatch[1] : '未知期数';
    
    // 从评论中提取常见关键词
    const commonKeywords = this.extractCommonKeywords(comments);
    
    // 生成简洁总结（50字以内）
    const summaries = [
      `${episode}精选恐怖故事，包含${commonKeywords.slice(0, 2).join('、')}等元素，观众热烈讨论。`,
      `本期聚焦${commonKeywords[0] || '灵异'}事件，${commonKeywords[1] ? `涉及${commonKeywords[1]}话题，` : ''}引发${comments.length}条求助评论。`,
      `恐怖内容聚合，涵盖${commonKeywords.slice(0, 3).join('、')}等主题，社区互动活跃。`,
      `${episode}期内容，以${commonKeywords[0] || '超自然'}现象为主，观众积极寻找故事出处。`,
      `灵异故事合集，包含${commonKeywords.length}个热门话题，${comments.length}条观众互动。`
    ];
    
    return summaries[Math.floor(Math.random() * summaries.length)];
  }

  /**
   * 提取关键词
   */
  private extractKeywords(title: string, comments: any[]): string[] {
    const keywords = new Set<string>();
    
    // 从标题提取关键词
    const titleWords = title.replace(/【[^】]+】/g, '')
      .split(/[^\u4e00-\u9fa5a-zA-Z0-9]+/)
      .filter(word => word.length > 1);
    
    titleWords.forEach(word => {
      if (word.length <= 4) {
        keywords.add(word);
      }
    });
    
    // 从评论中提取常见词
    const commentKeywords = this.extractCommonKeywords(comments);
    commentKeywords.forEach(keyword => keywords.add(keyword));
    
    // 添加默认关键词
    const defaultKeywords = ['恐怖', '灵异', '故事', '诡异', '超自然'];
    defaultKeywords.forEach(keyword => keywords.add(keyword));
    
    return Array.from(keywords).slice(0, 10);
  }

  /**
   * 从评论中提取常见关键词
   */
  private extractCommonKeywords(comments: any[]): string[] {
    if (!comments || comments.length === 0) return [];
    
    const wordCount: Map<string, number> = new Map();
    
    comments.forEach(comment => {
      if (comment.keyword && typeof comment.keyword === 'string') {
        const count = wordCount.get(comment.keyword) || 0;
        wordCount.set(comment.keyword, count + 1);
      }
      
      // 也可以从评论内容中提取关键词
      if (comment.content && typeof comment.content === 'string') {
        const words = comment.content.match(/[^\u4e00-\u9fa5a-zA-Z0-9]+/g) 
          ? comment.content.split(/[^\u4e00-\u9fa5a-zA-Z0-9]+/).filter((w: string) => w.length > 1)
          : [];
        
        words.forEach((word: string) => {
          if (word.length <= 4) { // 只考虑短词作为关键词
            const count = wordCount.get(word) || 0;
            wordCount.set(word, count + 1);
          }
        });
      }
    });
    
    // 按频率排序并返回前5个
    return Array.from(wordCount.entries())
      .sort((a, b) => b[1] - a[1])
      .map(entry => entry[0])
      .slice(0, 5);
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

  /**
   * 获取总结数量
   */
  getSummaryCount(): number {
    return this.summaries.size;
  }
}

// 创建单例实例
export const aiSummaryService = new AISummaryService();

// 预加载数据
aiSummaryService.loadSummaries().catch(console.error);