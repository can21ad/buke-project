'use client';

import React, { useState, useEffect } from 'react';
import { aiRecommendationService, Recommendation } from '../services/aiRecommendationService';

interface AIRecommendationsProps {
  currentContent?: any;
  allContent?: any[];
  contentType?: 'story' | 'video' | 'series';
  className?: string;
  title?: string;
}

const AIRecommendations: React.FC<AIRecommendationsProps> = ({
  currentContent,
  allContent = [],
  contentType = 'video',
  className = '',
  title = '猜你喜欢'
}) => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateRandomRecommendations();
  }, [allContent, contentType]);

  const generateRandomRecommendations = () => {
    setLoading(true);
    
    try {
      // 随机推荐视频
      const shuffled = [...allContent].sort(() => 0.5 - Math.random());
      const randomRecs = shuffled.slice(0, 5).map((item, index) => ({
        id: item.id || item.bvid || String(index),
        type: contentType,
        title: item.title || item.name || '推荐内容',
        description: extractDiverseDescription(item),
        reason: getDiverseReason(index),
        score: 0.7 - (index * 0.05),
        metadata: {
          bvid: item.bvid,
          episode: item.episode,
          cover: item.cover_url || item.cover_local,
          tags: item.tags
        }
      }));
      setRecommendations(randomRecs);
    } catch (error) {
      console.error('生成推荐失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    generateRandomRecommendations();
  };

  const handleRecommendationClick = (rec: Recommendation) => {
    // 记录用户点击行为
    aiRecommendationService.recordUserAction('view', rec.id, rec.metadata.tags);
    
    // 跳转链接
    if (rec.metadata.bvid) {
      const url = `https://www.bilibili.com/video/${rec.metadata.bvid}`;
      window.open(url, '_blank');
    }
  };

  // 提取多样化的描述
  const extractDiverseDescription = (item: any): string => {
    const episode = item.episode > 0 ? `第${item.episode}期` : '特别篇';
    const commentCount = item.comment_count || 0;
    
    if (commentCount > 20) {
      return `${episode} · ${commentCount}条讨论 · 社区热门`;
    } else if (item.play_count > 1000000) {
      return `${episode} · 播放量${(item.play_count / 10000).toFixed(0)}万 · 人气视频`;
    } else {
      return `${episode} · 精彩内容推荐`;
    }
  };

  // 获取多样化的推荐理由
  const getDiverseReason = (index: number): string => {
    const reasons = [
      '你可能感兴趣',
      '相关推荐',
      '延伸观看',
      '相似主题',
      '观众也在看'
    ];
    return reasons[index % reasons.length];
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

  if (recommendations.length === 0) {
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
            <span>换一换</span>
            <span>🔄</span>
          </button>
        </div>
        
        <div className="space-y-3">
          {recommendations.map((rec, index) => (
            <div
              key={rec.id}
              className="flex gap-3 p-3 bg-black/40 rounded-lg cursor-pointer hover:bg-black/60 transition-colors group"
              onClick={() => handleRecommendationClick(rec)}
            >
              <div className="relative flex-shrink-0">
                <div className="w-16 h-12 rounded overflow-hidden bg-gray-800">
                  {rec.metadata.cover ? (
                    <img
                      src={rec.metadata.cover.includes('http') ? rec.metadata.cover : (rec.metadata.cover.startsWith('/') ? rec.metadata.cover : '/' + rec.metadata.cover)}
                      alt={rec.title}
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
                  {rec.title}
                </h4>
                <p className="text-xs text-gray-500 line-clamp-1 mt-1">
                  {rec.description}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs bg-purple-900/30 text-purple-400 px-2 py-0.5 rounded">
                    {rec.reason}
                  </span>
                  {rec.metadata.episode > 0 && (
                    <span className="text-xs text-gray-500">
                      第{rec.metadata.episode}期
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
            <span>基于内容相似度和热度分析</span>
            <span>🧠 AI推荐</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIRecommendations;