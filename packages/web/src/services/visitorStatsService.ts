/**
 * 访客统计服务
 * 追踪和记录网站访客信息
 */

export interface VisitorStats {
  totalVisitors: number;
  todayVisitors: number;
  onlineVisitors: number;
  lastUpdated: string;
}

export interface VisitorRecord {
  timestamp: number;
  ip: string;
  userAgent: string;
  page: string;
  referrer?: string;
}

class VisitorStatsService {
  private stats: VisitorStats = {
    totalVisitors: 0,
    todayVisitors: 0,
    onlineVisitors: 0,
    lastUpdated: new Date().toISOString()
  };
  
  private readonly STORAGE_KEY = 'buke_visitor_stats';
  private readonly TODAY_KEY = 'buke_today_visitors';
  private readonly LAST_VISIT_KEY = 'buke_last_visit_date';

  constructor() {
    this.loadStats();
    this.checkNewDay();
  }

  /**
   * 从localStorage加载统计数据
   */
  private loadStats(): void {
    if (typeof window === 'undefined') return;
    
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        this.stats = {
          ...this.stats,
          ...parsed,
          lastUpdated: new Date().toISOString()
        };
      }
    } catch (error) {
      console.error('加载访客统计失败:', error);
    }
  }

  /**
   * 保存统计数据到localStorage
   */
  private saveStats(): void {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.stats));
    } catch (error) {
      console.error('保存访客统计失败:', error);
    }
  }

  /**
   * 检查是否新的一天，重置今日访客数
   */
  private checkNewDay(): void {
    if (typeof window === 'undefined') return;
    
    try {
      const lastVisit = localStorage.getItem(this.LAST_VISIT_KEY);
      const today = new Date().toDateString();
      
      if (lastVisit !== today) {
        // 新的一天，重置今日访客数
        this.stats.todayVisitors = 0;
        localStorage.setItem(this.LAST_VISIT_KEY, today);
        this.saveStats();
      }
    } catch (error) {
      console.error('检查日期失败:', error);
    }
  }

  /**
   * 记录新访客
   */
  recordVisit(page: string = '/'): void {
    if (typeof window === 'undefined') return;
    
    // 检查是否是新会话（简单实现：检查sessionStorage）
    const sessionKey = 'buke_session_recorded';
    if (sessionStorage.getItem(sessionKey)) {
      // 已经记录过本次会话
      return;
    }
    
    // 标记本次会话已记录
    sessionStorage.setItem(sessionKey, 'true');
    
    // 更新统计数据
    this.stats.totalVisitors += 1;
    this.stats.todayVisitors += 1;
    this.stats.lastUpdated = new Date().toISOString();
    
    // 保存到localStorage
    this.saveStats();
    
    // 记录访客详情（可选）
    this.recordVisitorDetail(page);
  }

  /**
   * 记录访客详细信息
   */
  private recordVisitorDetail(page: string): void {
    if (typeof window === 'undefined') return;
    
    try {
      const record: VisitorRecord = {
        timestamp: Date.now(),
        ip: 'anonymous', // 实际应用中应该从服务器获取
        userAgent: navigator.userAgent,
        page: page,
        referrer: document.referrer || undefined
      };
      
      // 获取现有记录
      const recordsKey = 'buke_visitor_records';
      const existing = localStorage.getItem(recordsKey);
      const records: VisitorRecord[] = existing ? JSON.parse(existing) : [];
      
      // 添加新记录（限制最多保存100条）
      records.push(record);
      if (records.length > 100) {
        records.shift(); // 移除最旧的记录
      }
      
      localStorage.setItem(recordsKey, JSON.stringify(records));
    } catch (error) {
      console.error('记录访客详情失败:', error);
    }
  }

  /**
   * 获取当前统计数据
   */
  getStats(): VisitorStats {
    // 模拟在线访客数（基于今日访客的随机比例）
    const baseOnline = Math.max(1, Math.floor(this.stats.todayVisitors * 0.1));
    const randomVariation = Math.floor(Math.random() * 5) - 2; // -2 到 +2
    this.stats.onlineVisitors = Math.max(1, baseOnline + randomVariation);
    
    return { ...this.stats };
  }

  /**
   * 获取今日访客数
   */
  getTodayVisitors(): number {
    this.checkNewDay();
    return this.stats.todayVisitors;
  }

  /**
   * 获取总访客数
   */
  getTotalVisitors(): number {
    return this.stats.totalVisitors;
  }

  /**
   * 获取在线访客数（模拟）
   */
  getOnlineVisitors(): number {
    return this.getStats().onlineVisitors;
  }

  /**
   * 重置统计数据（仅用于测试）
   */
  resetStats(): void {
    this.stats = {
      totalVisitors: 0,
      todayVisitors: 0,
      onlineVisitors: 0,
      lastUpdated: new Date().toISOString()
    };
    this.saveStats();
  }

  /**
   * 增加模拟数据（用于演示）
   */
  addMockData(): void {
    // 添加一些模拟数据让统计看起来更真实
    this.stats.totalVisitors = 12580;
    this.stats.todayVisitors = 156;
    this.stats.lastUpdated = new Date().toISOString();
    this.saveStats();
  }
}

// 创建单例实例
export const visitorStatsService = new VisitorStatsService();

// 注意：不再添加模拟数据，从0开始真实统计