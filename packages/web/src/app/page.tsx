'use client';
import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import AISummaryBox from '../components/AISummaryBox';
import VisitorStatsPanel from '../components/VisitorStatsPanel';
import AIRecommendations from '../components/AIRecommendations';
import { analyticsService } from '../services/analyticsService';

// 全局样式
const GlobalStyles = () => (
  <style jsx global>{`
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateX(20px);
      }
      to {
        opacity: 1;
        transform: translateX(0);
      }
    }
    
    @keyframes pulse {
      0%, 100% {
        box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4);
      }
      50% {
        box-shadow: 0 0 0 10px rgba(220, 38, 38, 0);
      }
    }
    
    @keyframes float {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-10px);
      }
    }
    
    .animate-fade-in {
      animation: fadeIn 0.5s ease-out forwards;
    }
    
    .animate-slide-in {
      animation: slideIn 0.3s ease-out forwards;
    }
    
    .animate-float {
      animation: float 3s ease-in-out infinite;
    }
    
    .animate-pulse {
      animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    .scrollbar-thin {
      scrollbar-width: thin;
    }
    
    .scrollbar-thin::-webkit-scrollbar {
      width: 4px;
    }
    
    .scrollbar-thin::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.3);
    }
    
    .scrollbar-thin::-webkit-scrollbar-thumb {
      background: rgba(107, 33, 168, 0.5);
      border-radius: 2px;
    }
    
    .scrollbar-thin::-webkit-scrollbar-thumb:hover {
      background: rgba(107, 33, 168, 0.8);
    }
  `}</style>
);

interface Story {
  id: number;
  name: string;
  title: string;
  bvid: string;
  timestamp: number;
  heat: number;
  mention_count: number;
  review: string;
  length: number;
  author: string;
  tags: string[];
  time_markers: string[];
  related_bvs: string[];
  jump_url: string;
}

interface EpisodeRankItem {
  name: string;
  mention_count: number;
  rank: number;
}

interface DataResponse {
  generated_at: string;
  version: string;
  total_stories: number;
  theme: string;
  keywords: string[];
  stories: Story[];
  episode_rank?: EpisodeRankItem[];
}

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
}

interface VideoDbResponse {
  generated_at: string;
  version: string;
  total_videos: number;
  videos: VideoItem[];
}

interface HelpComment {
  id: number;
  content: string;
  author: string;
  like: number;
  time: number;
  keyword: string;
  reply_count: number;
  has_replies: boolean;
  replies: {
    id: number;
    content: string;
    author: string;
    like: number;
    time: number;
  }[];
  weight: number;
}

interface Top10Video {
  rank: number;
  bvid: string;
  episode: number;
  title: string;
  play_count: number;
  cover_url: string;
  cover_local: string;
  comment_count: number;
  timestamp?: number;
  comments: HelpComment[];
}

interface Top10Response {
  generated_at: string;
  total_videos: number;
  total_comments: number;
  keywords: string[];
  videos: Top10Video[];
}

interface ZhizhenStory {
  order: number;
  name: string;
  color: string;
  bvid: string;
  episode: number;
  part: string;
  title: string;
  timestamp: number;
  time_str: string;
  cover_url: string;
  cover_local: string;
}

interface ZhizhenSeries {
  id: string;
  title: string;
  description: string;
  stories: ZhizhenStory[];
}

interface ZhizhenResponse {
  generated_at: string;
  series: ZhizhenSeries[];
}

export default function Home() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [videoSearchQuery, setVideoSearchQuery] = useState('');
  const [stories, setStories] = useState<Story[]>([]);
  const [allStories, setAllStories] = useState<Story[]>([]);
  const [theme, setTheme] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [episodeRank, setEpisodeRank] = useState<EpisodeRankItem[]>([]);
  const [allVideos, setAllVideos] = useState<VideoItem[]>([]);
  const [videoSearchResults, setVideoSearchResults] = useState<VideoItem[]>([]);
  const [showVideoResults, setShowVideoResults] = useState(false);
  const [top10Videos, setTop10Videos] = useState<Top10Video[]>([]);
  const [top10Loading, setTop10Loading] = useState(true);
  const [expandedVideo, setExpandedVideo] = useState<number | null>(null);
  const [zhizhenSeries, setZhizhenSeries] = useState<ZhizhenSeries[]>([]);
  const [zhizhenLoading, setZhizhenLoading] = useState(true);
  const [showSearchPanel, setShowSearchPanel] = useState(false);

  useEffect(() => {
    // 记录页面浏览事件
    analyticsService.trackPageView('home');
    
    fetch('/data/buke_top_stories.json')
      .then(res => res.json())
      .then((data: DataResponse) => {
        setStories(data.stories || []);
        setAllStories(data.stories || []);
        setTheme(data.theme || '');
        setKeywords(data.keywords || []);
        setEpisodeRank(data.episode_rank || []);
      })
      .catch(err => {
        console.error('Failed to load stories:', err);
      });
    
    fetch('/data/buke_all_episodes.json')
      .then(res => res.json())
      .then((data: VideoDbResponse) => {
        const list = data.videos || [];
        const withEpisode = list.filter(v => v.episode && v.episode > 0)
          .sort((a, b) => b.episode - a.episode);
        const withoutEpisode = list.filter(v => !v.episode || v.episode === 0)
          .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime());
        setAllVideos([...withEpisode, ...withoutEpisode]);
      })
      .catch(err => {
        console.error('Failed to load videos:', err);
      });
    
    fetch('/data/top10_help_comments.json')
      .then(res => res.json())
      .then((data: Top10Response) => {
        setTop10Videos(data.videos || []);
        setTop10Loading(false);
      })
      .catch(err => {
        console.error('Failed to load top10:', err);
        setTop10Loading(false);
      });
    
    fetch('/data/zhizhen_series.json')
      .then(res => res.json())
      .then((data: ZhizhenResponse) => {
        setZhizhenSeries(data.series || []);
        setZhizhenLoading(false);
      })
      .catch(err => {
        console.error('Failed to load zhizhen:', err);
        setZhizhenLoading(false);
      });
  }, []);

  const handleStorySearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery) {
      const filtered = allStories.filter(story => 
        story.name.includes(searchQuery) || 
        story.title.includes(searchQuery) ||
        story.review.includes(searchQuery) ||
        story.tags.some(tag => tag.includes(searchQuery))
      );
      setStories(filtered);
    } else {
      setStories(allStories);
    }
  };

  const handleVideoSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (videoSearchQuery.trim()) {
      const query = videoSearchQuery.toLowerCase().trim();
      const results = allVideos.filter(v => 
        v.title.toLowerCase().includes(query) ||
        v.bvid.toLowerCase().includes(query) ||
        (v.episode && v.episode.toString().includes(query))
      ).slice(0, 6);
      setVideoSearchResults(results);
      setShowVideoResults(true);
    } else {
      setShowVideoResults(false);
      setVideoSearchResults([]);
    }
  };

  const handleVideoSearchChange = (value: string) => {
    setVideoSearchQuery(value);
    if (value.trim()) {
      const query = value.toLowerCase().trim();
      const results = allVideos.filter(v => 
        v.title.toLowerCase().includes(query) ||
        v.bvid.toLowerCase().includes(query) ||
        (v.episode && v.episode.toString().includes(query))
      ).slice(0, 6);
      setVideoSearchResults(results);
      setShowVideoResults(true);
    } else {
      setShowVideoResults(false);
      setVideoSearchResults([]);
    }
  };

  const goToVideosWithSearch = () => {
    if (videoSearchQuery.trim()) {
      router.push(`/videos?search=${encodeURIComponent(videoSearchQuery)}`);
    } else {
      router.push('/videos');
    }
  };

  const handleVideoJump = (video: VideoItem) => {
    // 记录视频点击事件
    analyticsService.trackVideoClick(video.bvid);
    const url = video.video_url || `https://www.bilibili.com/video/${video.bvid}`;
    window.open(url, '_blank');
  };

  const formatPlayCount = (count: number) => {
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)}万`;
    }
    return count.toString();
  };

  const formatCommentTime = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  const toggleVideoExpand = (rank: number) => {
    setExpandedVideo(expandedVideo === rank ? null : rank);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-gray-950 to-black relative overflow-hidden">
      <GlobalStyles />
      <div className="fixed inset-0 pointer-events-none opacity-5">
        <div className="absolute top-0 left-0 w-full h-full bg-[url('/images/horror-pattern.png')] bg-repeat"></div>
      </div>
      
      <div className="fixed top-4 right-4 z-50 flex items-center gap-4">
        {/* 查看全部视频按钮 */}
        <Link
          href="/videos"
          className="px-4 py-2 bg-gradient-to-r from-red-600 to-red-800 text-white text-sm font-bold rounded-lg hover:from-red-700 hover:to-red-900 transition-all duration-300 shadow-lg shadow-red-900/30 hover:shadow-red-900/50 animate-pulse"
        >
          📺 全部视频
        </Link>
        
        {/* 搜索按钮 - 跳转到AI搜索页面 */}
        <button
          onClick={() => router.push('/ai-search')}
          className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 flex items-center justify-center hover:from-purple-700 hover:to-pink-700 transition-all duration-300 shadow-lg shadow-purple-900/30 hover:shadow-purple-900/50"
        >
          <span className="text-xl">🔍</span>
        </button>
      </div>
      
      <div className="container mx-auto px-4 py-8 relative z-10">
        <header className="mb-12 text-center animate-fade-in">
          <div className="relative inline-block animate-float">
            <h1 className="text-6xl md:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-600 via-red-500 to-orange-600 tracking-wider drop-shadow-2xl">
              怖客
            </h1>
            <div className="absolute -top-4 -right-4 text-4xl animate-pulse">👻</div>
            <div className="absolute -bottom-2 -left-4 text-3xl opacity-50 animate-float" style={{ animationDelay: '0.5s' }}>💀</div>
          </div>
          <p className="mt-4 text-gray-500 text-sm tracking-widest animate-fade-in" style={{ animationDelay: '0.3s' }}>
            ⚜ 恐怖灵异内容聚合平台 ⚜
          </p>
          <div className="mt-6 flex justify-center gap-8 text-gray-600 text-xs animate-fade-in" style={{ animationDelay: '0.6s' }}>
            <span className="flex items-center gap-1 hover:text-red-400 transition-colors duration-300"><span className="text-red-500">●</span> 灵异故事</span>
            <span className="flex items-center gap-1 hover:text-purple-400 transition-colors duration-300"><span className="text-purple-500">●</span> 都市传说</span>
            <span className="flex items-center gap-1 hover:text-blue-400 transition-colors duration-300"><span className="text-blue-500">●</span> 民间怪谈</span>
          </div>
        </header>

        <section className="mb-16 animate-fade-in" style={{ animationDelay: '0.8s' }}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl animate-float">👑</span>
            <div>
              <h2 className="text-2xl font-bold text-red-400">至臻系列</h2>
              <p className="text-sm text-gray-500">精选故事串联 · 沉浸式体验</p>
            </div>
          </div>
          
          {zhizhenLoading ? (
            <div className="bg-gray-900/50 rounded-lg p-6 animate-pulse">
              <div className="h-32 bg-gray-800 rounded"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {zhizhenSeries.map((series) => (
                <div key={series.id} className="bg-gradient-to-r from-gray-900/80 to-black/80 rounded-xl p-6 border border-gray-800 shadow-2xl shadow-black/50">
                  <div className="mb-6">
                    <h3 className="text-2xl font-bold text-red-400 flex items-center gap-2">
                      <span className="text-red-600">◆</span>
                      {series.title}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">{series.description}</p>
                  </div>
                  
                  <div className="overflow-x-auto pb-4 -mx-2 px-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                    <div className="flex items-center gap-6 min-w-max">
                      {series.stories.map((story, index) => (
                        <React.Fragment key={story.order}>
                          <div 
                            className="flex-shrink-0 w-72 bg-black/60 rounded-xl overflow-hidden cursor-pointer group border border-gray-800 hover:border-red-800 transition-all duration-300 hover:shadow-lg hover:shadow-red-900/30"
                            onClick={() => {
                              // 记录视频点击事件
                              analyticsService.trackVideoClick(story.bvid);
                              const url = `https://www.bilibili.com/video/${story.bvid}?t=${story.timestamp}`;
                              window.open(url, '_blank');
                            }}
                          >
                            <div className="relative h-40 overflow-hidden">
                              {story.cover_local || story.cover_url ? (
                                <img
                                  src={story.cover_local ? `/${story.cover_local}` : story.cover_url}
                                  alt={story.title}
                                  className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                />
                              ) : (
                                <div className="w-full h-full bg-gray-900 flex items-center justify-center text-4xl">
                                  📹
                                </div>
                              )}
                              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent"></div>
                              <div className="absolute bottom-2 left-2 right-2">
                                <span 
                                  className="inline-block text-lg font-black px-3 py-1 rounded"
                                  style={{ 
                                    color: story.color === 'black' ? '#666' : story.color,
                                    backgroundColor: story.color === 'white' ? 'rgba(255,255,255,0.2)' : 
                                                    story.color === 'red' ? 'rgba(220,38,38,0.3)' : 
                                                    'rgba(0,0,0,0.5)'
                                  }}
                                >
                                  {story.name}
                                </span>
                              </div>
                            </div>
                            <div className="p-4">
                              <div className="flex items-center gap-2 mb-2">
                                {story.episode > 0 ? (
                                  <span className="text-xs text-gray-400">第{story.episode}期{story.part}</span>
                                ) : (
                                  <span className="text-xs text-gray-400">{story.part}</span>
                                )}
                                <span className="text-xs text-red-500 font-bold ml-auto">⏱ {story.time_str}</span>
                              </div>
                              <p className="text-sm text-gray-300 line-clamp-2">
                                {story.title.replace(/【[^】]+】/, '')}
                              </p>
                            </div>
                          </div>
                          
                          {index < series.stories.length - 1 && (
                            <div className="flex-shrink-0 text-3xl text-red-600 font-bold animate-pulse">
                              →
                            </div>
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mb-16 animate-fade-in" style={{ animationDelay: '1s' }}>
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl animate-float">🔥</span>
            <div>
              <h2 className="text-2xl font-bold text-orange-400">大家都在看 TOP 10</h2>
              <p className="text-sm text-gray-500">播放量最高 · 求助评论精选</p>
            </div>
          </div>
          
          {top10Loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-gray-900/50 rounded-lg p-4 animate-pulse">
                  <div className="h-16 bg-gray-800 rounded"></div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid gap-4">
              {top10Videos.map((video) => (
                <div key={video.bvid} className="bg-gradient-to-r from-gray-900/60 to-black/60 rounded-lg border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors">
                  <div 
                    className="flex items-start gap-4 p-4 cursor-pointer"
                    onClick={() => {
                      // 记录AI总结查看事件
                      analyticsService.trackAISummaryView(video.bvid);
                      toggleVideoExpand(video.rank);
                    }}
                  >
                    <div className="relative flex-shrink-0">
                      <div className="w-20 h-14 rounded overflow-hidden">
                        <img
                          src={video.cover_local ? `/${video.cover_local}` : video.cover_url}
                          alt={video.title}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="absolute -top-2 -left-2 w-6 h-6 bg-red-600 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-lg">
                        {video.rank}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          // 记录AI总结查看事件
                          analyticsService.trackAISummaryView(video.bvid);
                          setExpandedVideo(expandedVideo === video.rank ? null : video.rank);
                        }}
                        className="absolute -bottom-2 -left-2 w-6 h-6 bg-gradient-to-r from-purple-600 to-red-600 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-lg hover:shadow-xl hover:shadow-purple-500/50 transition-all"
                        title="查看AI总结"
                      >
                        AI
                      </button>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-200 line-clamp-1 mb-1 group-hover:text-red-400">
                        {video.title}
                      </h3>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        {video.episode > 0 && (
                          <span className="bg-purple-900/50 text-purple-400 px-2 py-0.5 rounded">
                            第{video.episode}期
                          </span>
                        )}
                        <span>▶ {formatPlayCount(video.play_count)}</span>
                        <span>💬 {video.comment_count}条求助</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        // 记录视频点击事件
                        analyticsService.trackVideoClick(video.bvid);
                        const baseUrl = `https://www.bilibili.com/video/${video.bvid}`;
                        const url = video.timestamp ? `${baseUrl}?t=${video.timestamp}` : baseUrl;
                        window.open(url, '_blank');
                      }}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors flex-shrink-0"
                    >
                      观看
                    </button>
                  </div>
                  
                  {expandedVideo === video.rank && (
                    <div className="border-t border-gray-800 p-4 bg-black/40">
                      <AISummaryBox 
                        bvid={video.bvid}
                        title={video.title}
                        compact={false}
                        className="mb-4"
                      />
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
                          <span>💬</span>
                          求助评论精选
                        </h4>
                        <div className="max-h-64 overflow-y-auto space-y-2">
                          {video.comments.slice(0, 5).map((comment) => (
                            <div key={comment.id} className="bg-gray-900/50 rounded p-3">
                              <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs text-red-400 font-medium">{comment.author.length > 2 ? comment.author[0] + '*'.repeat(comment.author.length - 1) : comment.author}</span>
                              <span className="text-xs text-gray-600">{formatCommentTime(comment.time)}</span>
                              <span className="text-xs bg-red-900/30 text-red-400 px-1.5 rounded">{comment.keyword}</span>
                            </div>
                              <p className="text-sm text-gray-400 line-clamp-2">{comment.content}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {theme && (
          <section className="mb-12 animate-fade-in" style={{ animationDelay: '1.2s' }}>
            <div className="bg-gradient-to-r from-purple-900/30 to-black/30 rounded-lg p-6 border border-purple-800/30 hover:border-purple-700/50 transition-all duration-300 shadow-lg shadow-purple-900/20">
              <h3 className="text-lg font-bold text-purple-400 mb-2 flex items-center gap-2">
                <span className="animate-float">📌</span>
                本期主题
              </h3>
              <p className="text-gray-300 mb-3">{theme}</p>
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw, i) => (
                  <span key={i} className="text-xs bg-purple-900/40 text-purple-300 px-3 py-1 rounded-full border border-purple-700/30 hover:bg-purple-800/60 hover:border-purple-600/50 transition-all duration-200">
                    #{kw}
                  </span>
                ))}
              </div>
            </div>
          </section>
        )}

        {episodeRank.length > 0 && (
          <section className="mb-16 animate-fade-in" style={{ animationDelay: '1.4s' }}>
            <div className="flex items-center gap-3 mb-6">
              <span className="text-3xl animate-float">📊</span>
              <h2 className="text-2xl font-bold text-blue-400">提及排行榜</h2>
            </div>
            <div className="bg-gray-900/40 rounded-lg border border-gray-800 overflow-hidden hover:border-blue-800/50 transition-all duration-300 shadow-lg shadow-blue-900/10">
              <div className="divide-y divide-gray-800">
                {episodeRank.slice(0, 5).map((item, index) => (
                  <div
                    key={item.rank}
                    className="flex items-center justify-between px-4 py-3 hover:bg-gray-800/30 transition-colors duration-200 animate-fade-in"
                    style={{ animationDelay: `${1.5 + index * 0.1}s` }}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 rounded-full bg-blue-900/50 flex items-center justify-center text-xs font-bold text-blue-400 hover:bg-blue-800/70 transition-colors duration-200">
                        {item.rank}
                      </span>
                      <span className="text-gray-300 hover:text-blue-400 transition-colors duration-200">{item.name}</span>
                    </div>
                    <span className="text-xs text-gray-500 hover:text-blue-400 transition-colors duration-200">{item.mention_count}次提及</span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* 版本2新增：访客统计和AI推荐 */}
        <section className="mb-16 animate-fade-in" style={{ animationDelay: '1.6s' }}>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="animate-fade-in" style={{ animationDelay: '1.7s' }}>
              <div className="flex items-center gap-3 mb-6">
                <span className="text-3xl animate-float">📈</span>
                <h2 className="text-2xl font-bold text-green-400">访客统计</h2>
              </div>
              <VisitorStatsPanel showDetails={true} />
            </div>
            
            <div className="animate-fade-in" style={{ animationDelay: '1.8s' }}>
              <div className="flex items-center gap-3 mb-6">
                <span className="text-3xl animate-float">🎯</span>
                <h2 className="text-2xl font-bold text-purple-400">猜你喜欢</h2>
              </div>
              
              {/* 简洁搜索框 - 跳转到AI搜索页面 */}
              <div 
                className="bg-gradient-to-br from-gray-900/60 to-black/60 border border-gray-700 rounded-lg p-4 mb-4 cursor-pointer hover:border-purple-500 transition-colors"
                onClick={() => router.push('/ai-search')}
              >
                <div className="flex items-center gap-3 text-gray-400">
                  <span className="text-xl">🔍</span>
                  <span className="flex-1">搜索视频...</span>
                  <span className="text-sm bg-purple-900/30 text-purple-400 px-2 py-1 rounded">AI智能</span>
                </div>
              </div>
              
              {/* 默认推荐 */}
              <AIRecommendations 
                currentBvid="BV1W8h9znETX"
                title="猜你喜欢"
              />
            </div>
          </div>
        </section>

        <footer className="mt-20 pt-8 border-t border-gray-800">
          <div className="text-center mb-8">
            <div className="inline-block bg-gradient-to-r from-purple-900/40 to-red-900/40 rounded-xl p-6 border border-purple-800/30">
              <h3 className="text-lg font-bold text-purple-300 mb-2 flex items-center justify-center gap-2">
                <span className="text-2xl">🔮</span>
                AI算命 · 命理玄学
              </h3>
              <p className="text-sm text-gray-400 mb-4">探索命运之谜，揭示人生玄机</p>
              <a
                href="https://canmingli.netlify.app/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block px-6 py-3 bg-gradient-to-r from-purple-600 to-red-600 hover:from-purple-700 hover:to-red-700 text-white font-bold rounded-lg transition-all duration-300 shadow-lg shadow-purple-900/30 hover:shadow-purple-900/50"
              >
                立即体验 →
              </a>
            </div>
          </div>
          
          <div className="text-center text-gray-600 text-sm">
            <div className="flex justify-center items-center gap-4 mb-4">
              <span className="text-gray-500">友情链接:</span>
              <a
                href="https://canmingli.netlify.app/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-400 hover:text-purple-300 transition-colors"
              >
                AI算命
              </a>
            </div>
            <p className="text-gray-700">© 2024 怖客 · 恐怖灵异内容聚合平台</p>
            <p className="text-gray-800 text-xs mt-2">⚠️ 本站内容仅供娱乐，请勿迷信</p>
            <div className="mt-4 p-4 bg-gray-900/50 border border-gray-800 rounded-lg max-w-2xl mx-auto">
              <p className="text-red-400 font-bold mb-2">重要声明</p>
              <p className="text-gray-300 text-sm">本平台为非商业学习交流平台，所有内容仅供交流，不得用于商业用途。</p>
              <p className="text-gray-300 text-sm mt-2">AI 总结数据来源于 B 站的 CC 弹幕，同样不用于商业。</p>
              <p className="text-gray-300 text-sm mt-2">若有侵权，请联系我们，我们将立刻删除相关内容。</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
