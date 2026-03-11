// 数据埋点服务

// 事件类型定义
type EventType = 'video_click' | 'ai_summary_view' | 'page_view';

// 事件数据接口
interface EventData {
  bvid?: string;
  page?: string;
  timestamp: number;
}

// 埋点事件接口
interface TrackEvent {
  event_type: EventType;
  event_data: EventData;
  user_agent: string;
  ip?: string;
}

// 数据埋点服务类
class AnalyticsService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = '/api/v1/track';
  }

  /**
   * 记录事件
   * @param eventType 事件类型
   * @param eventData 事件数据
   */
  async trackEvent(eventType: EventType, eventData: Omit<EventData, 'timestamp'>): Promise<boolean> {
    try {
      const event: TrackEvent = {
        event_type: eventType,
        event_data: {
          ...eventData,
          timestamp: Date.now()
        },
        user_agent: navigator.userAgent
      };

      // 发送事件到后端
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(event)
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to track event:', error);
      // 即使失败也返回true，不影响用户体验
      return true;
    }
  }

  /**
   * 记录视频点击事件
   * @param bvid 视频BV号
   */
  trackVideoClick(bvid: string): Promise<boolean> {
    return this.trackEvent('video_click', { bvid });
  }

  /**
   * 记录AI总结查看事件
   * @param bvid 视频BV号
   */
  trackAISummaryView(bvid: string): Promise<boolean> {
    return this.trackEvent('ai_summary_view', { bvid });
  }

  /**
   * 记录页面浏览事件
   * @param page 页面名称
   */
  trackPageView(page: string): Promise<boolean> {
    return this.trackEvent('page_view', { page });
  }
}

// 导出单例实例
export const analyticsService = new AnalyticsService();
export default analyticsService;