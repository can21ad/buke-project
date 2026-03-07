'use client';

import React, { useEffect, useState, useMemo, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';

interface VideoItem {
  id: number;
  bvid: string;
  video_url: string;
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

interface VideoDbResponse {
  generated_at: string;
  version: string;
  total_videos: number;
  videos: VideoItem[];
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
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState<CategoryType>('all');

  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    if (urlSearch) {
      setSearchQuery(urlSearch);
    }
  }, [searchParams]);

  useEffect(() => {
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
    let result = allVideos;

    if (category === 'regular') {
      result = allVideos.filter(isRegularEpisode);
    } else if (category === 'special') {
      result = allVideos.filter(isSpecialVideo);
    } else if (category === 'urban') {
      result = allVideos.filter(isUrbanLegend);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = result.filter(v => 
        v.title.toLowerCase().includes(query) ||
        v.bvid.toLowerCase().includes(query) ||
        (v.episode && v.episode.toString().includes(query))
      );
    }

    return result;
  }, [allVideos, category, searchQuery]);

  const totalPages = useMemo(() => {
    return Math.ceil(filteredVideos.length / VIDEOS_PER_PAGE);
  }, [filteredVideos.length]);

  const currentVideos = useMemo(() => {
    const start = (currentPage - 1) * VIDEOS_PER_PAGE;
    return filteredVideos.slice(start, start + VIDEOS_PER_PAGE);
  }, [filteredVideos, currentPage]);

  useEffect(() => {
    setCurrentPage(1);
  }, [category, searchQuery]);

  const handleJump = (item: VideoItem) => {
    const url = item.video_url || `https://www.bilibili.com/video/${item.bvid}`;
    window.open(url, '_blank');
  };

  const formatPlayCount = (count: number) => {
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
            <h1 className="text-3xl font-bold mb-2">全部视频</h1>
            <p className="text-sm text-gray-400">
              共 {allVideos.length} 个视频，当前分类 {filteredVideos.length} 个
            </p>
          </div>
          <Link href="/" className="btn btn-secondary text-sm">
            返回首页
          </Link>
        </div>

        <form onSubmit={handleSearch} className="mb-4">
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
                onClick={() => setSearchQuery('')}
                className="btn btn-secondary"
              >
                清除
              </button>
            )}
          </div>
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
                        src={video.cover_local ? `/${video.cover_local}` : video.cover_url}
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
