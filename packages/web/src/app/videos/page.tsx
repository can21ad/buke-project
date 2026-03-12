'use client';

import React, { useEffect, useState, useMemo, Suspense, useCallback } from 'react';
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
  ai_summary?: string;
}

interface VideoDbResponse {
  generated_at: string;
  version: string;
  total_videos: number;
  videos: VideoItem[];
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

type CategoryType = 'all' | 'regular' | 'special' | 'urban';

const CATEGORY_LABELS: Record<CategoryType, string> = {
  all: '全部',
  regular: '道听途说正集',
  special: '道听途说特辑',
  urban: '都市传说',
};

const VideosContent = () => {
  const searchParams = useSearchParams();
  const [allVideos, setAllVideos] = useState<VideoItem[]>([]);
  const [aiSummaries, setAiSummaries] = useState<Map<string, string>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [pendingSearchQuery, setPendingSearchQuery] = useState(''); // 普通搜索的待提交关键词
  const [category, setCategory] = useState<CategoryType>('all');
  
  // AI语义搜索状态
  const [aiSearchQuery, setAiSearchQuery] = useState('');
  const [aiSearchResults, setAiSearchResults] = useState<SimilarVideo[]>([]);
  const [aiSearchLoading, setAiSearchLoading] = useState(false);
  const [aiFilters, setAiFilters] = useState<SearchFilters>({});
  const [searchMode, setSearchMode] = useState<'normal' | 'ai'>('normal');

  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    if (urlSearch) {
      setSearchQuery(urlSearch);
      // 如果URL有search参数，设置为AI搜索模式
      setAiSearchQuery(urlSearch);
      setSearchMode('ai');
    }
  }, [searchParams]);
  
  // AI搜索改为点击触发，移除自动搜索

  useEffect(() => {
    // 记录页面浏览事件
    analyticsService.trackPageView('videos');
    
    // 加载视频数据
    fetch('/data/buke_all_episodes.json')
      .then((res) => res.json())
      .then((data: VideoDbResponse) => {
        const list = data.videos || [];
        const withEpisode = list.filter(v => v.episode && v.episode > 0)
          .sort((a, b) => b.episode - a.episode);
        const withoutEpisode = list.filter(v => !v.episode || v.episode === 0)
          .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime());
        const sortedVideos = [...withEpisode, ...withoutEpisode];
        setAllVideos(sortedVideos);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load videos:', err);
        setIsLoading(false);
      });
    
    // 加载AI总结数据
    fetch('/data/csv_top10_summaries.json')
      .then((res) => {
        if (!res.ok) return null;
        return res.json();
      })
      .then((data: AISummariesResponse | null) => {
        if (data && data.summaries) {
          const summaryMap = new Map<string, string>();
          data.summaries.forEach(item => {
            summaryMap.set(item.bvid, item.summary);
          });
          setAiSummaries(summaryMap);
        }
      })
      .catch((err) => {
        console.log('AI summaries not available:', err);
      });
  }, []);

  const isSpecialVideo = (video: VideoItem): boolean => {
    return video.title.includes('特辑');
  };

  const isUrbanLegend = (video: VideoItem): boolean => {
    return !video.title.includes('道听途说');
  };

  const isRegularEpisode = (video: VideoItem): boolean => {
    return video.title.includes('道听途说') && video.episode > 0 && !isSpecialVideo(video);
  };

  const filteredVideos = useMemo(() => {
    console.log('[AI搜索] filteredVideos计算:', { searchMode, resultsCount: aiSearchResults.length, hasQuery: !!aiSearchQuery.trim() });
    
    // 如果是AI搜索模式且有搜索词，返回AI搜索结果
    if (searchMode === 'ai' && aiSearchQuery.trim()) {
      if (aiSearchResults.length === 0) {
        console.log('[AI搜索] 无搜索结果');
        return [];
      }
      
      console.log('[AI搜索] 映射结果到VideoItem格式');
      return aiSearchResults.map((aiVideo, index) => {
        const mapped = {
          id: index + 1,
          bvid: aiVideo.bvid,
          title: aiVideo.title,
          cover_url: aiVideo.cover_url,
          cover_local: aiVideo.cover_local || '',
          video_url: aiVideo.video_url,
          duration: 0,
          duration_str: aiVideo.duration_str || aiVideo.duration || '',
          views: aiVideo.play_count || aiVideo.views || 0,
          play_count: aiVideo.play_count || aiVideo.views || 0,
          comment_count: aiVideo.comment_count || 0,
          episode: aiVideo.episode || 0,
          part: aiVideo.part || '',
          keywords: [],
          upload_date: aiVideo.upload_date || aiVideo.date || '',
          ai_summary: aiVideo.summary || ''
        };
        console.log(`[AI搜索] 映射第${index + 1}条:`, { bvid: mapped.bvid, title: mapped.title?.substring(0, 20) });
        return mapped;
      }) as VideoItem[];
    }
    
    let result = allVideos;

    if (category === 'regular') {
      result = allVideos.filter(isRegularEpisode);
    } else if (category === 'special') {
      result = allVideos.filter(isSpecialVideo);
    } else if (category === 'urban') {
      result = allVideos.filter(isUrbanLegend);
    }

    if (pendingSearchQuery.trim()) {
      const query = pendingSearchQuery.toLowerCase().trim();
      result = result.filter(v => 
        (v.title && v.title.toLowerCase().includes(query)) ||
        (v.bvid && v.bvid.toLowerCase().includes(query)) ||
        (v.episode && v.episode.toString().includes(query))
      );
    }

    return result;
  }, [allVideos, category, pendingSearchQuery, searchMode, aiSearchResults]);

  const totalPages = useMemo(() => {
    return Math.ceil(filteredVideos.length / VIDEOS_PER_PAGE);
  }, [filteredVideos.length]);

  const currentVideos = useMemo(() => {
    const start = (currentPage - 1) * VIDEOS_PER_PAGE;
    return filteredVideos.slice(start, start + VIDEOS_PER_PAGE);
  }, [filteredVideos, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
  }, [category, searchQuery, searchMode, pendingSearchQuery]);

  const handleJump = (item: VideoItem) => {
    // 记录视频点击事件
    analyticsService.trackVideoClick(item.bvid);
    const url = item.video_url || `https://www.bilibili.com/video/${item.bvid}`;
    window.open(url, '_blank');
  };

  const formatPlayCount = (count: number | undefined) => {
    if (!count || typeof count !== 'number') return '0';
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)}万`;
    }
    return count.toString();
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPendingSearchQuery(searchQuery);
  };
  
  // AI语义搜索 - 手动触发
  const handleAISearch = useCallback(async () => {
    console.log('[AI搜索] 手动触发搜索:', aiSearchQuery.trim());
    
    if (!aiSearchQuery.trim()) {
      console.log('[AI搜索] 搜索词为空，跳过');
      return;
    }
    
    // 确保在AI模式
    if (searchMode !== 'ai') {
      console.log('[AI搜索] 切换到AI模式');
      setSearchMode('ai');
    }
    
    setAiSearchLoading(true);
    try {
      console.log('[AI搜索] 调用API:', { keyword: aiSearchQuery.trim(), filters: aiFilters });
      const results = await similarVideoService.semanticSearch(aiSearchQuery.trim(), 20, aiFilters);
      console.log('[AI搜索] API返回结果数:', results.length);
      setAiSearchResults(results);
    } catch (error) {
      console.error('[AI搜索] 搜索失败:', error);
      setAiSearchResults([]);
      alert('AI搜索失败，请检查网络连接或稍后重试');
    } finally {
      setAiSearchLoading(false);
    }
  }, [aiSearchQuery, aiFilters, searchMode]);
  
  // 切换到普通搜索
  const handleNormalSearch = () => {
    setSearchMode('normal');
    setAiSearchQuery('');
    setAiSearchResults([]);
    setPendingSearchQuery('');
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
        end = Math.min(totalPages - 1, showPages - 1);
      }
      if (currentPage >= totalPages - 2) {
        start = Math.max(2, totalPages - showPages + 2);
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
          className={`btn text-sm ${currentPage === 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary'}`}
        >
          上一页
        </button>
        
        {pages.map((page, index) => (
          <button
            key={index}
            onClick={() => typeof page === 'number' && handlePageChange(page)}
            disabled={page === '...'}
            className={`btn text-sm min-w-[40px] ${
              page === currentPage 
                ? 'btn-primary' 
                : page === '...' 
                  ? 'cursor-default' 
                  : 'btn-secondary'
            }`}
          >
            {page}
          </button>
        ))}
        
        <button
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className={`btn text-sm ${currentPage === totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary'}`}
        >
          下一页
        </button>
      </div>
    );
  };

  const getCategoryCount = (cat: CategoryType): number => {
    if (cat === 'all') return allVideos.length;
    if (cat === 'regular') return allVideos.filter(isRegularEpisode).length;
    if (cat === 'special') return allVideos.filter(isSpecialVideo).length;
    if (cat === 'urban') return allVideos.filter(isUrbanLegend).length;
    return 0;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              {searchMode === 'ai' && aiSearchQuery.trim() ? 'AI语义搜索' : '全部视频'}
            </h1>
            <p className="text-sm text-gray-400">
              {searchMode === 'ai' && aiSearchQuery.trim() ? (
                aiSearchLoading ? '搜索中...' : `找到 ${filteredVideos.length} 个相关视频`
              ) : (
                `共 ${allVideos.length} 个视频，当前分类 ${filteredVideos.length} 个`
              )}
            </p>
          </div>
          <Link href="/" className="btn btn-secondary text-sm">
            返回首页
          </Link>
        </div>

        <form onSubmit={handleSearch} className="mb-4">
          {/* 搜索模式切换 */}
          <div className="flex gap-2 mb-2">
            <button
              type="button"
              onClick={handleNormalSearch}
              className={`px-3 py-1 rounded text-sm ${searchMode === 'normal' ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300'}`}
            >
              普通搜索
            </button>
            <button
              type="button"
              onClick={() => {
                console.log('[AI搜索] 点击切换AI模式按钮');
                setSearchMode('ai');
              }}
              className={`px-3 py-1 rounded text-sm ${searchMode === 'ai' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300'}`}
            >
              AI语义搜索
            </button>
          </div>
          
          {searchMode === 'normal' ? (
            /* 普通搜索框 */
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="搜索视频标题、BV号或期数..."
                className="input flex-1"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit" className="btn btn-primary">
                搜索
              </button>
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => { setSearchQuery(''); setPendingSearchQuery(''); }}
                  className="btn btn-secondary"
                >
                  清除
                </button>
              )}
            </div>
          ) : (
            /* AI语义搜索框 + 高级过滤 */
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="输入关键词搜索，如：校园灵异、民间怪谈..."
                  className="input flex-1"
                  value={aiSearchQuery}
                  onChange={(e) => {
                    console.log('[AI搜索] 输入变化:', e.target.value);
                    setAiSearchQuery(e.target.value);
                  }}
                  onKeyDown={(e) => {
                    console.log('[AI搜索] 按键:', e.key);
                    if (e.key === 'Enter') {
                      console.log('[AI搜索] 回车触发搜索');
                      handleAISearch();
                    }
                  }}
                />
                <button 
                  type="button" 
                  onClick={handleAISearch}
                  disabled={aiSearchLoading || !aiSearchQuery.trim()}
                  className="btn btn-primary bg-purple-600 hover:bg-purple-700"
                >
                  {aiSearchLoading ? '搜索中...' : 'AI搜索'}
                </button>
              </div>
              
              {/* 高级过滤选项 */}
              <div className="flex flex-wrap gap-2 text-sm">
                <select
                  value={aiFilters.sort_by || ''}
                  onChange={(e) => {
                    setAiFilters({...aiFilters, sort_by: e.target.value as any || undefined});
                    setCurrentPage(1);
                  }}
                  className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-gray-300"
                >
                  <option value="">智能排序</option>
                  <option value="views">浏览量最高</option>
                  <option value="stat2">评论最多</option>
                  <option value="date">最新更新</option>
                </select>
                
                <select
                  value={aiFilters.min_views || ''}
                  onChange={(e) => {
                    setAiFilters({...aiFilters, min_views: e.target.value ? Number(e.target.value) : undefined});
                    setCurrentPage(1);
                  }}
                  className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-gray-300"
                >
                  <option value="">不限浏览量</option>
                  <option value="10000">1万+</option>
                  <option value="50000">5万+</option>
                  <option value="100000">10万+</option>
                  <option value="500000">50万+</option>
                </select>
                
                <select
                  value={aiFilters.min_comments || ''}
                  onChange={(e) => {
                    setAiFilters({...aiFilters, min_comments: e.target.value ? Number(e.target.value) : undefined});
                    setCurrentPage(1);
                  }}
                  className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-gray-300"
                >
                  <option value="">不限评论</option>
                  <option value="100">100+</option>
                  <option value="500">500+</option>
                  <option value="1000">1000+</option>
                </select>
                
                <select
                  value={aiFilters.max_duration || ''}
                  onChange={(e) => {
                    setAiFilters({...aiFilters, max_duration: e.target.value ? Number(e.target.value) : undefined});
                    setCurrentPage(1);
                  }}
                  className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-gray-300"
                >
                  <option value="">不限时长</option>
                  <option value="10">10分钟内</option>
                  <option value="30">30分钟内</option>
                  <option value="60">1小时内</option>
                </select>
              </div>
            </div>
          )}
        </form>

        <div className="flex flex-wrap gap-2">
          {(Object.keys(CATEGORY_LABELS) as CategoryType[]).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`btn text-sm ${category === cat ? 'btn-primary' : 'btn-secondary'}`}
            >
              {CATEGORY_LABELS[cat]} ({getCategoryCount(cat)})
            </button>
          ))}
        </div>
      </header>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((i) => (
            <div key={i} className="card">
              <div className="skeleton h-40 mb-4"></div>
              <div className="skeleton h-6 w-3/4 mb-2"></div>
              <div className="skeleton h-4 w-1/2"></div>
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="mb-4 flex justify-between items-center">
            <span className="text-sm text-gray-400">
              第 {currentPage} / {totalPages || 1} 页，当前显示 {currentVideos.length} 个视频
            </span>
            <span className="text-sm text-gray-400">
              每页 {VIDEOS_PER_PAGE} 个（4行×3列）
            </span>
          </div>

          {filteredVideos.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">没有找到匹配的视频</p>
              <p className="text-gray-500 text-sm mt-2">尝试更换搜索关键词或分类</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {currentVideos.map((video, index) => {
                const globalIndex = (currentPage - 1) * VIDEOS_PER_PAGE + index + 1;
                return (
                  <div key={video.bvid} className="card flex flex-col">
                    <div className="relative h-40 mb-4 rounded overflow-hidden bg-darker">
                      <img
                        src={video.cover_local ? video.cover_local : video.cover_url}
                        alt={video.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%231a1a2e" width="100" height="100"/><text x="50" y="50" text-anchor="middle" fill="%23666" font-size="12">封面加载失败</text></svg>';
                        }}
                      />
                      <div className="absolute top-2 left-2 bg-primary text-white text-xs font-bold px-2 py-1 rounded">
                        #{globalIndex}
                      </div>
                      <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                        {video.duration_str || `${Math.floor(video.duration / 60)}:${(video.duration % 60).toString().padStart(2, '0')}`}
                      </div>
                      {video.episode > 0 && (
                        <div className="absolute top-2 right-2 bg-secondary text-white text-xs px-2 py-1 rounded">
                          第{video.episode}期{video.part}
                        </div>
                      )}
                    </div>
                    
                    <h2 className="font-semibold text-sm mb-2 line-clamp-2 flex-1">
                      {video.title}
                    </h2>
                    
                    {video.keywords && video.keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {video.keywords.slice(0, 6).map((kw, idx) => (
                          <span
                            key={idx}
                            className="text-xs bg-primary bg-opacity-20 text-primary px-2 py-0.5 rounded border border-primary border-opacity-30"
                          >
                            {kw.word}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    {/* AI总结显示 */}
                    {aiSummaries.has(video.bvid) && (
                      <div className="mb-3 p-2 bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded border border-purple-700/30">
                        <div className="flex items-center justify-between gap-1 mb-1">
                          <div className="flex items-center gap-1">
                            <span className="text-xs bg-purple-600 text-white px-1.5 py-0.5 rounded font-bold">AI</span>
                            <span className="text-xs text-purple-300">故事总结</span>
                          </div>
                          <button 
                            id={`summary-btn-${video.bvid}`}
                            className="text-xs text-purple-400 hover:text-purple-300"
                            onClick={() => {
                              // 记录AI总结查看事件
                              analyticsService.trackAISummaryView(video.bvid);
                              const summaryElement = document.getElementById(`summary-${video.bvid}`);
                              const buttonElement = document.getElementById(`summary-btn-${video.bvid}`);
                              if (summaryElement && buttonElement) {
                                summaryElement.classList.toggle('line-clamp-3');
                                buttonElement.textContent = summaryElement.classList.contains('line-clamp-3') ? '全部' : '收起';
                              }
                            }}
                          >
                            全部
                          </button>
                        </div>
                        <p 
                          id={`summary-${video.bvid}`}
                          className="text-xs text-gray-300 line-clamp-3"
                        >
                          {aiSummaries.get(video.bvid)}
                        </p>
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-400 mb-3">
                      <span className="mr-3">▶ {formatPlayCount(video.play_count)}</span>
                      <span className="mr-3">💬 {formatPlayCount(video.comment_count)}</span>
                      <span>📅 {video.upload_date}</span>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleJump(video)}
                        className="btn btn-primary flex-1 text-xs"
                      >
                        一键直达
                      </button>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(video.bvid);
                          alert(`BV号已复制: ${video.bvid}`);
                        }}
                        className="btn btn-secondary text-xs"
                      >
                        复制BV号
                      </button>
                    </div>
                    
                    <div className="mt-2 text-xs text-gray-500 text-center">
                      BV: {video.bvid}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {renderPagination()}

          <div className="mt-8 p-4 bg-darker rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold mb-3">分类说明</h3>
            <div className="text-sm text-gray-400 space-y-1">
              <p>• <strong>全部</strong>：所有视频，有标号的按期数降序，无标号的按发布时间降序</p>
              <p>• <strong>道听途说正集</strong>：有期数标号的道听途说系列视频（不含特辑）</p>
              <p>• <strong>道听途说特辑</strong>：标题中包含"特辑"字样的视频</p>
              <p>• <strong>都市传说</strong>：不包含"道听途说"字样的其他视频</p>
            </div>
          </div>
          
          <div className="mt-8 p-4 bg-darker rounded-lg border border-gray-700 max-w-2xl mx-auto">
            <p className="text-red-400 font-bold mb-2">重要声明</p>
            <p className="text-gray-300 text-sm">本平台为非商业学习交流平台，所有内容仅供交流，不得用于商业用途。</p>
            <p className="text-gray-300 text-sm mt-2">AI 总结数据来源于 B 站的 CC 弹幕，同样不用于商业。</p>
            <p className="text-gray-300 text-sm mt-2">若有侵权，请联系我们，我们将立刻删除相关内容。</p>
          </div>
        </>
      )}
    </div>
  );
};

export default function AllVideosPage() {
  return (
    <Suspense fallback={<div className="container mx-auto px-4 py-8">加载中...</div>}>
      <VideosContent />
    </Suspense>
  );
}
