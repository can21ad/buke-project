'use client';
import React, { useEffect, useMemo, useState } from 'react';
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

interface DataResponse {
  generated_at?: string;
  version?: string;
  total_stories?: number;
  theme?: string;
  keywords?: string[];
  stories: Story[];
}

export default function StoryList() {
  const [stories, setStories] = useState<Story[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'heat' | 'mention'>('heat');

  useEffect(() => {
    fetch('/data/buke_top_stories.json')
      .then((res) => res.json())
      .then((data: DataResponse) => {
        setStories(data.stories || []);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load stories:', err);
        setIsLoading(false);
      });
  }, []);

  const sortedStories = useMemo(() => {
    const arr = [...stories];
    arr.sort((a, b) =>
      sortBy === 'heat' ? (b.heat || 0) - (a.heat || 0) : (b.mention_count || 0) - (a.mention_count || 0)
    );
    return arr;
  }, [stories, sortBy]);

  const handleJump = (url: string) => window.open(url, '_blank');

  const formatTime = (seconds: number) => {
    if (!seconds) return '开头';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold">故事列表</h1>
          <p className="text-sm text-gray-400 mt-1">来自：`/public/data/buke_top_stories.json`</p>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={() => setSortBy('heat')}
            className={`btn text-sm ${sortBy === 'heat' ? 'btn-primary' : 'btn-secondary'}`}
          >
            按热度
          </button>
          <button
            onClick={() => setSortBy('mention')}
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
              <div className="skeleton h-4 w-2/3"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedStories.map((story) => (
            <div key={story.id} className="card">
              <div className="flex">
                <div className="w-1/3 mr-4">
                  <div className="relative h-32 rounded overflow-hidden bg-darker flex items-center justify-center">
                    <div className="text-center">
                      <span className="text-3xl">📹</span>
                      <div className="text-xs text-gray-400 mt-1 line-clamp-2">{story.name}</div>
                    </div>
                    <div className="absolute bottom-1 right-1 bg-black bg-opacity-70 text-white text-xs px-1 rounded">
                      {formatTime(story.timestamp)}
                    </div>
                  </div>
                </div>

                <div className="flex-1">
                  <h3 className="font-semibold mb-2 line-clamp-2 text-sm">{story.name}</h3>
                  <p className="text-xs text-gray-400 mb-2 line-clamp-3">{(story.review || '').substring(0, 60)}...</p>
                  <div className="flex items-center text-xs text-gray-400 mb-2">
                    <span className="mr-3">🔥 {Math.round(story.heat || 0)}</span>
                    <span>📢 {story.mention_count || 0}次</span>
                  </div>

                  <div className="flex space-x-2">
                    <Link href={`/stories/${story.id}`} className="btn btn-secondary text-xs">
                      详情
                    </Link>
                    <button onClick={() => handleJump(story.jump_url)} className="btn btn-primary text-xs">
                      一键直达
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}