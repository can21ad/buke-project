'use client';

import React, { useState, useEffect } from 'react';
import { visitorStatsService, VisitorStats } from '../services/visitorStatsService';

interface VisitorStatsPanelProps {
  className?: string;
  showDetails?: boolean;
}

const VisitorStatsPanel: React.FC<VisitorStatsPanelProps> = ({ 
  className = '',
  showDetails = false 
}) => {
  const [stats, setStats] = useState<VisitorStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 记录当前访问
    visitorStatsService.recordVisit(window.location.pathname);
    
    // 加载统计数据
    const loadStats = () => {
      const currentStats = visitorStatsService.getStats();
      setStats(currentStats);
      setLoading(false);
    };
    
    loadStats();
    
    // 每30秒更新一次在线人数
    const interval = setInterval(() => {
      const currentStats = visitorStatsService.getStats();
      setStats(currentStats);
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className={`bg-gray-900/40 border border-gray-800 rounded-lg p-4 animate-pulse ${className}`}>
        <div className="flex items-center justify-between">
          <div className="h-4 bg-gray-700 rounded w-20"></div>
          <div className="h-6 bg-gray-700 rounded w-16"></div>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className={`bg-gradient-to-br from-gray-900/60 to-black/60 border border-gray-700 rounded-lg overflow-hidden ${className}`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
              <span className="text-sm">📊</span>
            </div>
            <span className="font-semibold text-gray-200">访客统计</span>
          </div>
          
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-xs text-gray-400">实时</span>
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-400">
              {stats.totalVisitors.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">总访客</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-400">
              {stats.todayVisitors.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">今日</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">
              {stats.onlineVisitors}
            </div>
            <div className="text-xs text-gray-500 mt-1">在线</div>
          </div>
        </div>
        
        {showDetails && (
          <div className="mt-4 pt-4 border-t border-gray-800">
            <div className="text-xs text-gray-500">
              <div className="flex items-center justify-between mb-2">
                <span>最后更新</span>
                <span>{new Date(stats.lastUpdated).toLocaleTimeString('zh-CN')}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>数据状态</span>
                <span className="text-green-400">正常</span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="px-4 pb-3">
        <div className="text-xs text-gray-600 flex items-center justify-between">
          <span>实时统计中...</span>
          <span>🔄 30s</span>
        </div>
      </div>
    </div>
  );
};

export default VisitorStatsPanel;