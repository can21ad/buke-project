// 相似视频推荐服务
import axios from 'axios';

const PYTHON_API_URL = process.env.NEXT_PUBLIC_PYTHON_API_URL || 'http://localhost:8000';

export interface SimilarVideo {
  bvid: string;
  title: string;
  video_url: string;
  cover_url: string;
  cover_local: string;
  views: number;
  play_count: number;
  comment_count: number;
  duration: string;
  duration_str: string;
  upload_date: string;
  date: string;
  summary: string;
  episode: number;
  part: string;
  similarity: number;
}

export interface SearchFilters {
  sort_by?: 'views' | 'stat2' | 'date';
  min_views?: number;
  min_comments?: number;
  max_duration?: number;
}

export interface SimilarVideosResponse {
  code: number;
  message: string;
  data: {
    total: number;
    videos: SimilarVideo[];
  };
}

export const similarVideoService = {
  /**
   * 获取相似视频推荐
   */
  async getSimilarVideos(bvid: string, top_n: number = 5): Promise<SimilarVideo[]> {
    try {
      const response = await axios.get<SimilarVideosResponse>(
        `${PYTHON_API_URL}/api/similar`,
        { params: { bvid, top_n } }
      );
      
      if (response.data.code === 200) {
        return response.data.data.videos;
      }
      return [];
    } catch (error) {
      console.error('获取相似视频失败:', error);
      return [];
    }
  },
  
  /**
   * 语义搜索
   */
  async semanticSearch(
    keyword: string, 
    top_n: number = 10,
    filters?: SearchFilters
  ): Promise<SimilarVideo[]> {
    console.log('[similarVideoService] 开始语义搜索:', { keyword, top_n, filters });
    try {
      const url = `${PYTHON_API_URL}/api/search`;
      const params = { 
        keyword, 
        top_n,
        ...filters
      };
      console.log('[similarVideoService] 请求URL:', url);
      console.log('[similarVideoService] 请求参数:', params);
      
      const response = await axios.get<SimilarVideosResponse>(url, { params });
      
      console.log('[similarVideoService] API响应状态:', response.status);
      console.log('[similarVideoService] API响应code:', response.data.code);
      console.log('[similarVideoService] API返回视频数:', response.data.data?.videos?.length || 0);
      
      if (response.data.code === 200 && response.data.data?.videos) {
        return response.data.data.videos;
      }
      console.warn('[similarVideoService] API返回异常:', response.data.message || '未知错误');
      return [];
    } catch (error: any) {
      console.error('[similarVideoService] 语义搜索失败:', error.message);
      if (error.response) {
        console.error('[similarVideoService] 错误响应:', error.response.status, error.response.data);
      }
      throw error; // 抛出错误让上层处理
    }
  }
};

export default similarVideoService;
