'use client';
import React, { useState } from 'react';
import Link from 'next/link';

const stories = [
  {
    id: 1,
    title: '三霄娘娘抱走我的孩子后许诺我家女娃三代平安',
    summary: '一个关于民间信仰与神秘力量的故事，讲述者描述了三霄娘娘的传说...',
    heatScore: 1234.56,
    mentionCount: 89,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169下】三霄娘娘抱走我的孩子',
      cover: 'https://i0.hdslb.com/bfs/archive/8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a.jpg',
    },
    timeInfo: {
      startTime: 754,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=754&p=1',
    },
    tags: ['灵异', '民间传说', '真实经历'],
  },
  {
    id: 2,
    title: '悉尼蓝山深处的恐怖巨人',
    summary: '澳洲蓝山的神秘巨人传说，露营者的恐怖遭遇...',
    heatScore: 987.45,
    mentionCount: 67,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169下】悉尼蓝山深处的恐怖巨人',
      cover: 'https://i1.hdslb.com/bfs/archive/9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f.jpg',
    },
    timeInfo: {
      startTime: 1200,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=1200&p=1',
    },
    tags: ['恐怖', '国外', '真实经历'],
  },
  {
    id: 3,
    title: '病患脑部开刀血液溅入医学生眼睛',
    summary: '医学生在手术中意外接触到病患血液，从此世界变得不同...',
    heatScore: 876.34,
    mentionCount: 56,
    video: {
      bvid: 'BV1xx411c7mD',
      title: '【道听途说169上】病患脑部开刀血液溅入医学生眼睛',
      cover: 'https://i2.hdslb.com/bfs/archive/8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a9e8f9a.jpg',
    },
    timeInfo: {
      startTime: 300,
      partNumber: 1,
      jumpUrl: 'https://www.bilibili.com/video/BV1xx411c7mD?t=300&p=1',
    },
    tags: ['医院', '灵异', '细思极恐'],
  },
];

export default function Search() {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState(stories);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (keyword) {
      setIsLoading(true);
      setTimeout(() => {
        const filtered = stories.filter(story => 
          story.title.includes(keyword) || 
          story.summary.includes(keyword)
        );
        setResults(filtered);
        setIsLoading(false);
      }, 500);
    } else {
      setResults(stories);
    }
  };

  const handleJump = (url: string) => {
    window.open(url, '_blank');
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-8">
        <h1 className="text-3xl font-bold">搜索结果</h1>
      </div>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex max-w-2xl">
          <input
            type="text"
            placeholder="搜索故事..."
            className="input flex-1"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
          <button type="submit" className="btn btn-primary ml-2">
            搜索
          </button>
        </div>
      </form>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card">
              <div className="skeleton h-48 mb-4"></div>
              <div className="skeleton h-6 w-3/4 mb-2"></div>
              <div className="skeleton h-4 w-full mb-2"></div>
              <div className="skeleton h-4 w-2/3 mb-4"></div>
              <div className="flex space-x-2">
                <div className="skeleton h-8 w-20 rounded"></div>
                <div className="skeleton h-8 w-20 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <div className="mb-6">
            <p className="text-gray-400">
              共找到 {results.length} 条结果
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((story) => (
              <div key={story.id} className="card">
                <div className="flex">
                  <div className="w-1/3 mr-4">
                    <div className="relative h-32 rounded overflow-hidden">
                      <img
                        src={story.video.cover}
                        alt={story.title}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold mb-2 line-clamp-2">
                      {story.title}
                    </h3>
                    <p className="text-sm text-gray-400 mb-3 line-clamp-2">
                      {story.summary}
                    </p>
                    <div className="flex items-center text-xs text-gray-400 mb-3">
                      <span className="mr-3">🔥 {Math.round(story.heatScore)}</span>
                      <span>📢 {story.mentionCount}</span>
                    </div>
                    <div className="flex space-x-2">
                      <Link
                        href={`/stories/${story.id}`}
                        className="btn btn-secondary text-xs"
                      >
                        详情
                      </Link>
                      <button
                        onClick={() => handleJump(story.timeInfo.jumpUrl)}
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
        </div>
      )}
    </div>
  );
}