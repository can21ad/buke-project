'use client';

import React, { useState, useEffect } from 'react';
import { realAISummaryService, VideoSummary } from '../services/realAISummaryService';

interface AISummaryBoxProps {
  bvid: string;
  title?: string;
  className?: string;
  compact?: boolean;
}

const AISummaryBox: React.FC<AISummaryBoxProps> = ({ 
  bvid, 
  title,
  className = '',
  compact = false 
}) => {
  const [summary, setSummary] = useState<VideoSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const loadSummary = async () => {
      setLoading(true);
      try {
        // 确保服务已加载
        await realAISummaryService.loadSummaries();
        
        // 获取总结
        const videoSummary = realAISummaryService.getSummary(bvid);
        setSummary(videoSummary);
      } catch (error) {
        console.error('加载AI总结失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSummary();
  }, [bvid]);

  if (loading) {
    return (
      <div className={`bg-gray-900/40 border border-gray-800 rounded-lg p-3 animate-pulse ${className}`}>
        <div className="flex items-center gap-2 mb-2">
          <div className="w-4 h-4 bg-gray-700 rounded"></div>
          <div className="h-4 bg-gray-700 rounded w-24"></div>
        </div>
        <div className="space-y-2">
          <div className="h-3 bg-gray-700 rounded w-full"></div>
          <div className="h-3 bg-gray-700 rounded w-4/5"></div>
        </div>
      </div>
    );
  }

  if (!summary) {
    if (compact) return null;
    
    return (
      <div className={`bg-gray-900/30 border border-gray-800 rounded-lg p-3 ${className}`}>
        <div className="flex items-center gap-2 text-gray-500 text-sm">
          <span>🤖</span>
          <span>AI总结生成中...</span>
        </div>
      </div>
    );
  }

  const displaySummary = expanded || compact 
    ? summary.summary 
    : summary.summary.length > 50 
      ? summary.summary.substring(0, 50) + '...'
      : summary.summary;

  return (
    <div className={`bg-gradient-to-br from-gray-900/50 to-black/50 border border-gray-700 rounded-lg overflow-hidden hover:border-gray-600 transition-colors ${className}`}>
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-r from-purple-600 to-red-600 flex items-center justify-center">
              <span className="text-xs font-bold">AI</span>
            </div>
            <span className="text-xs font-semibold text-gray-300">智能总结</span>
          </div>
          
          {!compact && summary.summary.length > 50 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              {expanded ? '收起' : '展开'}
            </button>
          )}
        </div>
        
        <div className="mb-3">
          <p className="text-sm text-gray-300 leading-relaxed">
            {displaySummary}
          </p>
          {!compact && (
            <div className="mt-2 text-xs text-gray-500">
              <span>字数: {summary.summary.length}</span>
              {summary.summary.length > 50 && !expanded && (
                <span className="ml-2">(已截断)</span>
              )}
            </div>
          )}
        </div>
        
        {!compact && summary.keyPoints && summary.keyPoints.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {summary.keyPoints.slice(0, 4).map((keyPoint, index) => (
              <span 
                key={index}
                className="text-xs bg-gray-800/50 text-gray-400 px-2 py-0.5 rounded border border-gray-700"
              >
                {keyPoint}
              </span>
            ))}
          </div>
        )}
        
        {!compact && (
          <div className="mt-3 pt-2 border-t border-gray-800/50">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <span>🕐</span>
                <span>生成时间: {new Date(summary.generated_at).toLocaleDateString('zh-CN')}</span>
              </span>
              <span className="flex items-center gap-1">
                <span>📊</span>
                <span>AI分析</span>
              </span>
            </div>
          </div>
        )}
      </div>
      
      {compact && (
        <div className="px-3 pb-2">
          <div className="text-xs text-gray-500 flex items-center gap-1">
            <span>🤖</span>
            <span>AI总结</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default AISummaryBox;