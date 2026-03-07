'use client';

import React, { useEffect, useState } from 'react';

interface VideoItem {
  bvid: string;
  title: string;
  video_url: string;
  cover_url: string;
  views: string;
  stat2: string;
  duration: string;
  date: string;
  local_cover: string;
}

interface VideoDbResponse {
  generated_at: string;
  total: number;
  videos: VideoItem[];
}

export default function AllVideosPage() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/data/buke_all_episodes.json')
      .then((res) => res.json())
      .then((data: VideoDbResponse) => {
        const list = data.videos || [];
        // 选取前 10 条作为全部视频页展示
        setVideos(list.slice(0, 10));
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load videos:', err);
        setIsLoading(false);
      });
  }, []);

  const handleJump = (item: VideoItem) => {
    // 一键直达：优先使用数据库中的 video_url，其次根据 bvid 构造
    const url = item.video_url || `https://www.bilibili.com/video/${item.bvid}`;
    window.open(url, '_blank');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-2">全部视频</h1>
        <p className="text-sm text-gray-400">
          展示数据库中精选的 10 条视频记录，标题与封面图均与源数据完全对齐。
        </p>
      </header>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card">
              <div className="skeleton h-40 mb-4"></div>
              <div className="skeleton h-6 w-3/4 mb-2"></div>
              <div className="skeleton h-4 w-1/2"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => (
            <div key={video.bvid} className="card flex flex-col">
              <div className="relative h-40 mb-4 rounded overflow-hidden bg-darker">
                <img
                  src={video.local_cover || video.cover_url}
                  alt={video.title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-1 right-1 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                  {video.duration}
                </div>
              </div>
              <h2 className="font-semibold text-sm mb-2 line-clamp-2">{video.title}</h2>
              <div className="text-xs text-gray-400 mb-3">
                <span className="mr-3">播放：{video.views}</span>
                <span>发布日期：{video.date}</span>
              </div>
              <div className="mt-auto">
                <button
                  onClick={() => handleJump(video)}
                  className="btn btn-primary w-full text-xs"
                >
                  一键直达（BV：{video.bvid}）
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

