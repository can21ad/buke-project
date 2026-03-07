'use client';
import React, { useState, useEffect } from 'react';
import Link from 'next/link';

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

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('');
  const [stories, setStories] = useState<Story[]>([]);
  const [hotStories, setHotStories] = useState<Story[]>([]);
  const [theme, setTheme] = useState('');
  const [keywords, setKeywords] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'heat' | 'mention'>('heat');
  const [episodeRank, setEpisodeRank] = useState<EpisodeRankItem[]>([]);

  useEffect(() => {
    fetch('/data/buke_top_stories.json')
      .then(res => res.json())
      .then((data: DataResponse) => {
        setStories(data.stories || []);
        setHotStories((data.stories || []).slice(0, 5));
        setTheme(data.theme || '');
        setKeywords(data.keywords || []);
        setEpisodeRank(data.episode_rank || []);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Failed to load stories:', err);
        setIsLoading(false);
      });
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery) {
      setIsLoading(true);
      setTimeout(() => {
        const filtered = stories.filter(story => 
          story.name.includes(searchQuery) || 
          story.title.includes(searchQuery) ||
          story.review.includes(searchQuery) ||
          story.tags.some(tag => tag.includes(searchQuery))
        );
        setStories(filtered);
        setIsLoading(false);
      }, 300);
    }
  };

  const handleSort = (type: 'heat' | 'mention') => {
    setSortBy(type);
    const sorted = [...stories].sort((a, b) => 
      type === 'heat' ? b.heat - a.heat : b.mention_count - a.mention_count
    );
    setStories(sorted);
  };

  const handleJump = (url: string) => {
    window.open(url, '_blank');
  };

  const formatTime = (seconds: number) => {
    if (seconds === 0) return '开头';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-12">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div className="flex items-center mb-4 md:mb-0">
            <h1 className="text-4xl font-bold text-primary">怖客</h1>
            <span className="ml-3 text-sm text-gray-400">恐怖灵异内容聚合平台</span>
          </div>
          <form onSubmit={handleSearch} className="w-full md:w-1/3">
            <div className="flex">
              <input
                type="text"
                placeholder="搜索故事..."
                className="input flex-1"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button type="submit" className="btn btn-primary ml-2">
                搜索
              </button>
            </div>
          </form>
        </div>
      </header>

      {/* 主题推荐 */}
      {theme && (
        <section className="mb-8">
          <div className="bg-darker p-4 rounded-lg border border-gray-700">
            <h3 className="text-lg font-semibold text-secondary mb-2">📌 本期主题</h3>
            <p className="text-gray-300">{theme}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {keywords.map((kw, i) => (
                <span key={i} className="text-xs bg-primary bg-opacity-20 text-primary px-2 py-1 rounded">
                  #{kw}
                </span>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* 提及排行榜 */}
      {episodeRank.length > 0 && (
        <section className="mb-10">
          <h2 className="text-2xl font-bold mb-4 flex items-center">
            <span className="mr-2">📊</span>
            提及排行榜 TOP {episodeRank.length}
          </h2>
          <div className="bg-darker rounded-lg border border-gray-700 overflow-hidden">
            <div className="divide-y divide-gray-800">
              {episodeRank.map((item) => (
                <div
                  key={item.rank}
                  className="flex items-center justify-between px-4 py-3 hover:bg-black/40 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="w-6 text-center text-sm font-bold text-primary">
                      #{item.rank}
                    </span>
                    <span className="text-sm text-gray-200">{item.name}</span>
                  </div>
                  <div className="text-xs text-gray-400">
                    提及 {item.mention_count} 次
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="mb-12">
        <h2 className="text-2xl font-bold mb-6 flex items-center">
          <span className="text-primary mr-2">🔥</span>
          热门故事 TOP 5
        </h2>
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="card">
                <div className="skeleton h-32 mb-3"></div>
                <div className="skeleton h-4 w-3/4 mb-2"></div>
                <div className="skeleton h-3 w-1/2"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {hotStories.map((story, index) => (
              <Link 
                key={story.id} 
                href={`/stories/${story.id}`}
                className="card hover:scale-105 group"
              >
                <div className="relative h-32 mb-3 overflow-hidden rounded bg-darker flex items-center justify-center">
                  <span className="text-4xl">📹</span>
                  <div className="absolute top-2 left-2 bg-primary text-white text-xs font-bold px-2 py-1 rounded">
                    #{index + 1}
                  </div>
                  <div className="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                    {formatTime(story.timestamp)}
                  </div>
                </div>
                <h3 className="font-semibold text-sm line-clamp-2 mb-2 group-hover:text-primary">
                  {story.name}
                </h3>
                <div className="flex items-center text-xs text-gray-400 mb-2">
                  <span className="mr-3">🔥 {Math.round(story.heat)}</span>
                  <span>📢 {story.mention_count}次</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {story.tags.slice(0, 2).map((tag, i) => (
                    <span key={i} className="text-xs bg-darker px-2 py-1 rounded border border-gray-700">
                      {tag}
                    </span>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold flex items-center">
            <span className="text-secondary mr-2">📖</span>
            全部故事 ({stories.length})
          </h2>
          <div className="flex space-x-2">
            <button 
              onClick={() => handleSort('heat')}
              className={`btn text-sm ${sortBy === 'heat' ? 'btn-primary' : 'btn-secondary'}`}
            >
              按热度
            </button>
            <button 
              onClick={() => handleSort('mention')}
              className={`btn text-sm ${sortBy === 'mention' ? 'btn-primary' : 'btn-secondary'}`}
            >
              按提及
            </button>
          </div>
        </div>
        
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="card">
                <div className="skeleton h-32 mb-4"></div>
                <div className="skeleton h-6 w-3/4 mb-2"></div>
                <div className="skeleton h-4 w-full mb-2"></div>
                <div className="skeleton h-4 w-2/3 mb-4"></div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stories.map((story) => (
              <div key={story.id} className="card">
                <div className="flex">
                  <div className="w-1/3 mr-4">
                    <div className="relative h-32 rounded overflow-hidden bg-darker flex items-center justify-center">
                      <div className="text-center">
                        <span className="text-3xl">📹</span>
                        <div className="text-xs text-gray-400 mt-1">{story.name}</div>
                      </div>
                      <div className="absolute bottom-1 right-1 bg-black bg-opacity-70 text-white text-xs px-1 rounded">
                        {formatTime(story.timestamp)}
                      </div>
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold mb-2 line-clamp-2 text-sm">
                      {story.name}
                    </h3>
                    <p className="text-xs text-gray-400 mb-2 line-clamp-3">
                      {story.review.substring(0, 60)}...
                    </p>
                    <div className="flex items-center text-xs text-gray-400 mb-2">
                      <span className="mr-3">🔥 {Math.round(story.heat)}</span>
                      <span>📢 {story.mention_count}次</span>
                    </div>
                    <div className="flex space-x-2">
                      <Link
                        href={`/stories/${story.id}`}
                        className="btn btn-secondary text-xs"
                      >
                        详情
                      </Link>
                      <button
                        onClick={() => handleJump(story.jump_url)}
                        className="btn btn-primary text-xs"
                      >
                        一键直达
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}