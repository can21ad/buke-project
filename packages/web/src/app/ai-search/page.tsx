'use client';

import React, { useEffect, useState, useMemo, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { analyticsService } from '../../services/analyticsService';
import { similarVideoService, SearchFilters, SimilarVideo } from '../../services/similarVideoService';

interface VideoItem {
  id: number;
  bvid: string;
  video_url?: string;
  cover_url: string;
  cover_local: string;
  play_count: number;
  comment_count: number;
  duration: number;
  duration_str: string;
  title: string;
  upload_date: string;
  episode: number;
  part: string;
  keywords?: { word: string; weight: number }[];
}

interface AISummaryItem {
  rank: number;
  bvid: string;
  title: string;
  owner: string;
  duration: number;
  view_count: number;
  summary: string;
  generated_at: string;
}

interface AISummariesResponse {
  generated_at: string;
  total: number;
  summaries: AISummaryItem[];
}

const VIDEOS_PER_PAGE = 12;

// 搜索参数组件
function SearchParamsWrapper({ children }: { children: (params: { keyword: string }) => React.ReactNode }) {
  const searchParams = useSearchParams();
  const keyword = searchParams.get('keyword') || '';
  return <>{children({ keyword })}</>;
}

// 主内容组件
function AISearchContent({ initialKeyword }: { initialKeyword: string }) {
  const [aiSearchQuery, setAiSearchQuery] = useState(initialKeyword);
  const [aiSearchResults, setAiSearchResults] = useState<SimilarVideo[]>([]);
  const [aiSearchLoading, setAiSearchLoading] = useState(false);
  const [aiFilters, setAiFilters] = useState<SearchFilters>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [aiSummaries, setAiSummaries] = useState<Map<string, string>>(new Map());

  useEffect(() => {
    analyticsService.trackPageView('ai-search');
    
    fetch('/data/csv_top10_summaries.json')
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data: AISummariesResponse | null) => {
        if (data && data.summaries) {
          const summaryMap = new Map<string, string>();
          data.summaries.forEach((item) => {
            summaryMap.set(item.bvid, item.summary);
          });
          setAiSummaries(summaryMap);
        }
      })
      .catch((err) => {
        console.log('AI summaries not available:', err);
      });
  }, []);

  useEffect(() => {
    if (aiSearchQuery.trim()) {
      const timer = setTimeout(async () => {
        setAiSearchLoading(true);
        try {
          const results = await similarVideoService.semanticSearch(aiSearchQuery, 30, aiFilters);
          setAiSearchResults(results);
          setCurrentPage(1);
        } catch (error) {
          console.error('AI搜索失败:', error);
          setAiSearchResults([]);
        } finally {
          setAiSearchLoading(false);
        }
      }, 500);
      return () => clearTimeout(timer);
    } else {
      setAiSearchResults([]);
    }
  }, [aiSearchQuery, aiFilters]);

  const formatPlayCount = (count: number | undefined) => {
    if (!count || typeof count !== 'number') return '0';
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)}万`;
    }
    return count.toString();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const filteredVideos = useMemo(() => {
    return aiSearchResults.map((aiVideo) => ({
      bvid: aiVideo.bvid,
      title: aiVideo.title,
      cover_url: aiVideo.cover_url,
      cover_local: aiVideo.cover_local || '',
      video_url: aiVideo.video_url,
      duration: 0,
      duration_str: aiVideo.duration || '',
      views: typeof aiVideo.views === 'number' ? aiVideo.views : 0,
      play_count: typeof aiVideo.views === 'number' ? aiVideo.views : 0,
      comment_count: typeof aiVideo.comment_count === 'number' ? aiVideo.comment_count : 0,
      episode: 0,
      part: '',
      keywords: [],
      upload_date: aiVideo.upload_date || '',
      created_at: '',
      updated_at: ''
    }));
  }, [aiSearchResults]);

  const totalPages = useMemo(() => {
    return Math.ceil(filteredVideos.length / VIDEOS_PER_PAGE);
  }, [filteredVideos.length]);

  const currentVideos = useMemo(() => {
    const start = (currentPage - 1) * VIDEOS_PER_PAGE;
    return filteredVideos.slice(start, start + VIDEOS_PER_PAGE);
  }, [filteredVideos, currentPage]);

  const handleJump = (video: any) => {
    analyticsService.trackVideoClick(video.bvid);
    const url = video.video_url || `https://www.bilibili.com/video/${video.bvid}`;
    window.open(url, '_blank');
  };

  const renderPagination = () => {
    if (totalPages <= 1) return null;

    const pages: (number | string)[] = [];
    const showPages = 5;
    
    if (totalPages <= showPages + 2) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      
      if (currentPage > 3) {
        pages.push('...');
      }
      
      let start = Math.max(2, currentPage - 1);
      let end = Math.min(totalPages - 1, currentPage + 1);
      
      if (currentPage <= 3) {
        end = Math.min(showPages, totalPages - 1);
      }
      
      if (currentPage >= totalPages - 2) {
        start = Math.max(2, totalPages - showPages);
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
      
      if (currentPage < totalPages - 2) {
        pages.push('...');
      }
      
      pages.push(totalPages);
    }

    return (
      <div className="flex justify-center items-center gap-2 mt-8">
        <button
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className={`px-4 py-2 rounded ${currentPage === 1 ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 'bg-red-600 text-white hover:bg-red-700'}`}
        >
          上一页
        </button>
        
        {pages.map((page, index) => (
          <button
            key={index}
            onClick={() => typeof page === 'number' && handlePageChange(page)}
            disabled={page === '...'}
            className={`px-4 py-2 rounded min-w-[40px] ${
              page === currentPage 
                ? 'bg-red-600 text-white' 
                : page === '...' 
                  ? 'bg-transparent text-gray-500 cursor-default' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {page}
          </button>
        ))}
        
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={`px-4 py-2 rounded ${currentPage === totalPages ? 'bg-gray-700 text-gray-500 cursor-not-allowed' : 'bg-red-600 text-white hover:bg-red-700'}`}
        >
          下一页
        </button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold mb-2 flex items-center gap-3">
                <span className="text-purple-400">🔍</span>
                AI智能搜索
              </h1>
              <p className="text-sm text-gray-400">
                {aiSearchResults.length > 0 
                  ? `找到 ${aiSearchResults.length} 个相关视频`
                  : '输入关键词搜索恐怖灵异视频'}
              </p>
            </div>
            <div className="flex gap-2">
              <Link href="/videos" className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm">
                全部视频
              </Link>
              <Link href="/" className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm">
                返回首页
              </Link>
            </div>
          </div>

          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                placeholder="输入关键词搜索，如：校园灵异、民间怪谈、医院..."
                className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                value={aiSearchQuery}
                onChange={(e) => setAiSearchQuery(e.target.value)}
              />
              <button 
                type="submit"
                disabled={aiSearchLoading}
                className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg font-medium"
              >
                {aiSearchLoading ? '搜索中...' : '搜索'}
              </button>
            </div>
            
            <div className="flex flex-wrap gap-2 text-sm">
              <select
                value={aiFilters.sort_by || ''}
                onChange={(e) => setAiFilters({...aiFilters, sort_by: e.target.value as any || undefined})}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-300"
              >
                <option value="">智能排序</option>
                <option value="views">浏览量最高</option>
                <option value="stat2">评论最多</option>
                <option value="date">最新更新</option>
              </select>
              
              <select
                value={aiFilters.min_views || ''}
                onChange={(e) => setAiFilters({...aiFilters, min_views: e.target.value ? Number(e.target.value) : undefined})}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-300"
              >
                <option value="">不限浏览量</option>
                <option value="10000">1万+</option>
                <option value="50000">5万+</option>
                <option value="100000">10万+</option>
                <option value="500000">50万+</option>
              </select>
              
              <select
                value={aiFilters.min_comments || ''}
                onChange={(e) => setAiFilters({...aiFilters, min_comments: e.target.value ? Number(e.target.value) : undefined})}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-300"
              >
                <option value="">不限评论</option>
                <option value="100">100+</option>
                <option value="500">500+</option>
                <option value="1000">1000+</option>
                <option value="5000">5000+</option>
              </select>
              
              <select
                value={aiFilters.max_duration || ''}
                onChange={(e) => setAiFilters({...aiFilters, max_duration: e.target.value ? Number(e.target.value) : undefined})}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-gray-300"
              >
                <option value="">不限时长</option>
                <option value="10">10分钟内</option>
                <option value="30">30分钟内</option>
                <option value="60">1小时内</option>
              </select>
            </div>
          </form>
        </header>

        {aiSearchLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-500"></div>
            <p className="text-gray-400 mt-4">AI搜索中...</p>
          </div>
        ) : filteredVideos.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg">
              {aiSearchQuery ? '未找到相关视频' : '请输入关键词开始搜索'}
            </p>
            {aiSearchQuery && (
              <p className="text-gray-500 text-sm mt-2">尝试更换搜索词或调整筛选条件</p>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {currentVideos.map((video, index) => {
                const globalIndex = (currentPage - 1) * VIDEOS_PER_PAGE + index + 1;
                return (
                  <div key={video.bvid} className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 flex flex-col">
                    <div className="relative h-40 mb-3">
                      <img
                        src={video.cover_local ? `/${video.cover_local}` : video.cover_url}
                        alt={video.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%231a1a2e" width="100" height="100"/><text x="50" y="50" text-anchor="middle" fill="%23666" font-size="12">封面加载失败</text></svg>';
                        }}
                      />
                      <div className="absolute top-2 left-2 bg-red-600 text-white text-xs font-bold px-2 py-1 rounded">
                        #{globalIndex}
                      </div>
                      <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                        {video.duration_str}
                      </div>
                    </div>
                    
                    <div className="px-3 flex-1">
                      <h3 className="font-semibold text-sm mb-2 line-clamp-2 text-white">
                        {video.title}
                      </h3>
                      
                      {aiSummaries.has(video.bvid) && (
                        <div className="mb-3 p-2 bg-purple-900/30 rounded border border-purple-700/30">
                          <div className="flex items-center gap-1 mb-1">
                            <span className="text-xs bg-purple-600 text-white px-1.5 py-0.5 rounded font-bold">AI</span>
                            <span className="text-xs text-purple-300">故事总结</span>
                          </div>
                          <p className="text-xs text-gray-300 line-clamp-2">
                            {aiSummaries.get(video.bvid)}
                          </p>
                        </div>
                      )}
                      
                      <div className="text-xs text-gray-400 mb-3">
                        <span className="mr-3">▶ {formatPlayCount(video.play_count)}</span>
                        <span className="mr-3">💬 {formatPlayCount(video.comment_count)}</span>
                        <span>📅 {video.upload_date}</span>
                      </div>
                    </div>
                    
                    <div className="px-3 pb-3 flex gap-2">
                      <button
                        onClick={() => handleJump(video)}
                        className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-medium"
                      >
                        一键直达
                      </button>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(video.bvid);
                          alert(`BV号已复制: ${video.bvid}`);
                        }}
                        className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm"
                      >
                        复制BV号
                      </button>
                    </div>
                    
                    <div className="px-3 pb-3 text-xs text-gray-500 text-center">
                      BV: {video.bvid}
                    </div>
                  </div>
                );
              })}
            </div>

            {renderPagination()}
          </>
        )}
      </div>
    </div>
  );
}

// 加载状态组件
function LoadingState() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-black flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-purple-500"></div>
        <p className="text-gray-400 mt-4">加载中...</p>
      </div>
    </div>
  );
}

// 主页面组件
export default function AISearchPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <SearchParamsWrapper>
        {({ keyword }) => <AISearchContent initialKeyword={keyword} />}
      </SearchParamsWrapper>
    </Suspense>
  );
}
