/**
 * AI推荐服务
 * 基于内容和用户行为提供智能推荐
 */

export interface Recommendation {
  id: string;
  type: 'story' | 'video' | 'series';
  title: string;
  description: string;
  reason: string;
  score: number;
  metadata: {
    bvid?: string;
    episode?: number;
    cover?: string;
    tags?: string[];
  };
}

export interface UserPreference {
  viewedCategories: string[];
  likedTags: string[];
  lastViewed: string[];
  preferredLength: 'short' | 'medium' | 'long';
}

class AIRecommendationService {
  private recommendations: Map<string, Recommendation> = new Map();
  private userPreferences: UserPreference = {
    viewedCategories: [],
    likedTags: [],
    lastViewed: [],
    preferredLength: 'medium'
  };

  /**
   * 基于内容生成推荐
   */
  generateRecommendations(
    currentContent: any,
    allContent: any[],
    type: 'story' | 'video' | 'series'
  ): Recommendation[] {
    const recommendations: Recommendation[] = [];
    
    // 基于标签相似度推荐
    const tagBasedRecs = this.recommendByTags(currentContent, allContent, type);
    recommendations.push(...tagBasedRecs);
    
    // 基于热度推荐
    const popularRecs = this.recommendByPopularity(allContent, type, 3);
    recommendations.push(...popularRecs);
    
    // 基于系列关联推荐
    if (type === 'video' || type === 'story') {
      const seriesRecs = this.recommendBySeries(currentContent, allContent, type);
      recommendations.push(...seriesRecs);
    }
    
    // 去重并排序
    const uniqueRecs = this.deduplicateAndSort(recommendations);
    
    return uniqueRecs.slice(0, 5); // 返回前5个推荐
  }

  /**
   * 基于标签相似度推荐
   */
  private recommendByTags(
    current: any,
    allContent: any[],
    type: 'story' | 'video' | 'series'
  ): Recommendation[] {
    const currentTags = current.tags || [];
    const recommendations: Recommendation[] = [];
    
    allContent.forEach((item) => {
      if (item.id === current.id || item.bvid === current.bvid) return;
      
      const itemTags = item.tags || [];
      const commonTags = currentTags.filter((tag: string) => itemTags.includes(tag));
      
      if (commonTags.length > 0) {
        const score = commonTags.length / Math.max(currentTags.length, itemTags.length);
        
        recommendations.push({
          id: item.id || item.bvid,
          type,
          title: item.title || item.name,
          description: this.generateDescription(item, type),
          reason: `与您正在查看的内容有 ${commonTags.length} 个共同标签: ${commonTags.join(', ')}`,
          score: score * 0.8, // 标签相似度权重0.8
          metadata: {
            bvid: item.bvid,
            episode: item.episode,
            cover: item.cover_url || item.cover_local,
            tags: itemTags
          }
        });
      }
    });
    
    return recommendations;
  }

  /**
   * 基于热度推荐
   */
  private recommendByPopularity(
    allContent: any[],
    type: 'story' | 'video' | 'series',
    limit: number
  ): Recommendation[] {
    // 按播放量/提及次数排序
    const sorted = [...allContent].sort((a, b) => {
      const scoreA = a.play_count || a.mention_count || a.heat || 0;
      const scoreB = b.play_count || b.mention_count || b.heat || 0;
      return scoreB - scoreA;
    });
    
    return sorted.slice(0, limit).map((item, index) => ({
      id: item.id || item.bvid,
      type,
      title: item.title || item.name,
      description: this.generateDescription(item, type),
      reason: `热门内容，播放量 ${this.formatNumber(item.play_count || item.mention_count || 0)}`,
      score: 0.7 - (index * 0.1), // 热度权重，随排名递减
      metadata: {
        bvid: item.bvid,
        episode: item.episode,
        cover: item.cover_url || item.cover_local,
        tags: item.tags
      }
    }));
  }

  /**
   * 基于系列关联推荐
   */
  private recommendBySeries(
    current: any,
    allContent: any[],
    type: 'story' | 'video' | 'series'
  ): Recommendation[] {
    const currentEpisode = current.episode;
    if (!currentEpisode) return [];
    
    // 推荐同一系列的其他期数
    const seriesItems = allContent.filter((item) => {
      if (item.id === current.id || item.bvid === current.bvid) return false;
      return item.episode && Math.abs(item.episode - currentEpisode) <= 3;
    });
    
    return seriesItems.map((item) => ({
      id: item.id || item.bvid,
      type,
      title: item.title || item.name,
      description: this.generateDescription(item, type),
      reason: `同一系列，第${item.episode}期（您正在看第${currentEpisode}期）`,
      score: 0.9 - (Math.abs(item.episode - currentEpisode) * 0.1), // 越接近权重越高
      metadata: {
        bvid: item.bvid,
        episode: item.episode,
        cover: item.cover_url || item.cover_local,
        tags: item.tags
      }
    }));
  }

  /**
   * 生成描述
   */
  private generateDescription(item: any, type: 'story' | 'video' | 'series'): string {
    if (type === 'story') {
      return item.review || item.description || '精彩恐怖故事';
    } else if (type === 'video') {
      const duration = item.duration_str || '';
      const episode = item.episode > 0 ? `第${item.episode}期` : '';
      return `${episode} ${duration}`.trim() || '精彩视频内容';
    } else {
      return item.description || '系列内容';
    }
  }

  /**
   * 格式化数字
   */
  private formatNumber(num: number): string {
    if (num >= 10000) {
      return `${(num / 10000).toFixed(1)}万`;
    }
    return num.toString();
  }

  /**
   * 去重并排序推荐
   */
  private deduplicateAndSort(recommendations: Recommendation[]): Recommendation[] {
    const seen = new Set<string>();
    const unique: Recommendation[] = [];
    
    // 按分数排序
    const sorted = recommendations.sort((a, b) => b.score - a.score);
    
    sorted.forEach((rec) => {
      if (!seen.has(rec.id)) {
        seen.add(rec.id);
        unique.push(rec);
      }
    });
    
    return unique;
  }

  /**
   * 更新用户偏好
   */
  updateUserPreferences(preferences: Partial<UserPreference>): void {
    this.userPreferences = {
      ...this.userPreferences,
      ...preferences
    };
  }

  /**
   * 获取用户偏好
   */
  getUserPreferences(): UserPreference {
    return { ...this.userPreferences };
  }

  /**
   * 记录用户行为
   */
  recordUserAction(action: 'view' | 'like' | 'share', contentId: string, tags?: string[]): void {
    if (action === 'view') {
      this.userPreferences.lastViewed.unshift(contentId);
      if (this.userPreferences.lastViewed.length > 10) {
        this.userPreferences.lastViewed.pop();
      }
    }
    
    if (tags) {
      tags.forEach((tag) => {
        if (!this.userPreferences.likedTags.includes(tag)) {
          this.userPreferences.likedTags.push(tag);
        }
      });
    }
  }

  /**
   * 获取个性化推荐语
   */
  getRecommendationReason(recommendation: Recommendation): string {
    const reasons = [
      recommendation.reason,
      'AI智能推荐',
      '基于您的浏览历史',
      '热门内容',
      '相关推荐'
    ];
    
    return reasons[Math.floor(Math.random() * reasons.length)];
  }
}

// 创建单例实例
export const aiRecommendationService = new AIRecommendationService();