'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { similarVideoService, SimilarVideo } from '../services/similarVideoService';

interface AIRecommendationsProps {
  currentBvid?: string;
  className?: string;
  title?: string;
}

const AIRecommendations: React.FC<AIRecommendationsProps> = ({
  currentBvid,
  className = '',
  title = '猜你喜欢'
}) => {
  const [allVideos, setAllVideos] = useState<SimilarVideo[]>([]);
  const [displayVideos, setDisplayVideos] = useState<SimilarVideo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const fetchSimilarVideos = useCallback(async () => {
    if (!currentBvid) {
      setError('缺少视频ID');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 获取更多视频，以便换一换
      const videos = await similarVideoService.getSimilarVideos(currentBvid, 10);
      setAllVideos(videos);
      
      // 显示前5个
      setDisplayVideos(videos.slice(0, 5));
      setPage(0);
    } catch (err) {
      console.error('获取相似视频失败:', err);
      setError('加载失败');
    } finally {
      setLoading(false);
    }
  }, [currentBvid]);

  useEffect(() => {
    fetchSimilarVideos();
  }, [fetchSimilarVideos]);

  const handleRefresh = () => {
    if (allVideos.length <= 5) {
      // 如果视频不足5个，重新获取
      fetchSimilarVideos();
      return;
    }
    
    // 换一批显示
    const nextPage = (page + 1) % Math.ceil(allVideos.length / 5);
    const start = nextPage * 5;
    const end = start + 5;
    setDisplayVideos(allVideos.slice(start, end));
    setPage(nextPage);
  };

  const handleVideoClick = (video: SimilarVideo) => {
    if (video.video_url) {
      window.open(video.video_url, '_blank');
    } else if (video.bvid) {
      window.open(`https://www.bilibili.com/video/${video.bvid}`, '_blank');
    }
  };

  if (loading) {
    return (
      <div className={`bg-gray-900/40 border border-gray-800 rounded-lg p-4 animate-pulse ${className}`}>
        <div className="h-4 bg-gray-700 rounded w-32 mb-4"></div>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3">
              <div className="w-16 h-12 bg-gray-700 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-3 bg-gray-700 rounded w-3/4"></div>
                <div className="h-2 bg-gray-700 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || displayVideos.length === 0) {
    return null;
  }

  return (
    <div className={`bg-gradient-to-br from-gray-900/60 to-black/60 border border-gray-700 rounded-lg overflow-hidden ${className}`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center">
              <span className="text-sm">🤖</span>
            </div>
            <span className="font-semibold text-gray-200">{title}</span>
          </div>
          
          <button
            onClick={handleRefresh}
            className="text-xs text-gray-400 hover:text-purple-400 flex items-center gap-1 transition-colors"
            title="换一批推荐"
          >
            <span>换一批</span>
            <span>🔄</span>
          </button>
        </div>
        
        <div className="space-y-3">
          {displayVideos.map((video, index) => (
            <div
              key={`${video.bvid}-${page}`}
              className="flex gap-3 p-3 bg-black/40 rounded-lg cursor-pointer hover:bg-black/60 transition-colors group"
              onClick={() => handleVideoClick(video)}
            >
              <div className="relative flex-shrink-0">
                <div className="w-16 h-12 rounded overflow-hidden bg-gray-800">
                  {video.cover_url ? (
                    <img
                      src={video.cover_url}
                      alt={video.title}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xl">
                      📹
                    </div>
                  )}
                </div>
                <div className="absolute -top-1 -left-1 w-5 h-5 bg-purple-600 rounded-full flex items-center justify-center text-xs font-bold text-white">
                  {index + 1}
                </div>
              </div>
              
              <div className="flex-1 min-w-0">
                <h4 className="text-sm font-medium text-gray-200 line-clamp-1 group-hover:text-purple-400 transition-colors">
                  {video.title}
                </h4>
                <p className="text-xs text-gray-500 line-clamp-1 mt-1">
                  {video.views} · {video.comment_count}条评论
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs bg-purple-900/30 text-purple-400 px-2 py-0.5 rounded">
                    相似度 {Math.round(video.similarity * 100)}%
                  </span>
                  {video.duration && (
                    <span className="text-xs text-gray-500">
                      {video.duration}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="flex-shrink-0 self-center">
                <span className="text-gray-500 group-hover:text-purple-400 transition-colors">→</span>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 pt-3 border-t border-gray-800">
          <div className="text-xs text-gray-500 flex items-center justify-between">
            <span>基于AI语义分析相似内容</span>
            <span>🧠 智能推荐</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIRecommendations;
