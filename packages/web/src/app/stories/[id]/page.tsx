'use client';
import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

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
  ai_summary?: {
    model_result: string;
    summary: string;
    outline: string[];
    keywords: string[];
    source: string;
  };
}

interface DataResponse {
  stories: Story[];
}

export default function StoryDetail() {
  const params = useParams();
  const router = useRouter();
  const [story, setStory] = useState<Story | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const storyId = Number(params.id);

  useEffect(() => {
    fetch('/data/buke_top_stories.json')
      .then(res => res.json())
      .then((data: DataResponse) => {
        if (storyId > 0 && storyId <= data.stories.length) {
          setStory(data.stories[storyId - 1]);
        }
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Failed to load story:', err);
        setIsLoading(false);
      });
  }, [storyId]);

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="card">
          <div className="skeleton h-64 mb-6"></div>
          <div className="skeleton h-8 w-3/4 mb-4"></div>
          <div className="skeleton h-4 w-full mb-4"></div>
          <div className="skeleton h-4 w-2/3 mb-6"></div>
        </div>
      </div>
    );
  }

  if (!story) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="card text-center py-16">
          <h2 className="text-2xl font-bold mb-4">故事不存在</h2>
          <p className="text-gray-400 mb-6">抱歉，您访问的故事不存在或已被删除</p>
          <button
            onClick={() => router.push('/')}
            className="btn btn-primary"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const handleJump = () => {
    window.open(story.jump_url, '_blank');
  };

  const formatTime = (seconds: number) => {
    if (seconds === 0) return '开头';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center mb-6">
        <button
          onClick={() => router.push('/')}
          className="btn btn-secondary mr-4"
        >
          ← 返回
        </button>
        <h1 className="text-2xl font-bold">故事详情</h1>
      </div>

      <div className="card mb-8">
        <div className="mb-6">
          <div className="relative h-64 mb-4 rounded overflow-hidden bg-darker flex items-center justify-center">
            <span className="text-6xl">📹</span>
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <button
                onClick={handleJump}
                className="bg-primary hover:bg-red-600 text-white px-6 py-3 rounded-full flex items-center transition-all duration-300 hover:scale-110"
              >
                <span className="mr-2">▶</span>
                一键直达观看
              </button>
            </div>
          </div>
          <div className="flex flex-wrap items-center text-sm text-gray-400">
            <span className="mr-4">
              BV号: {story.bvid}
            </span>
            <span className="mr-4">
              时间点: {formatTime(story.timestamp)}
            </span>
            <span>
              来源: {story.author}
            </span>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-4">{story.name}</h2>
          <p className="text-gray-400 text-sm mb-4">{story.title}</p>
          
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2 flex items-center">
              <span className="text-secondary mr-2">📖</span>
              故事内容
            </h3>
            <div className="bg-darker p-4 rounded border border-gray-700">
              <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                {story.review}
              </p>
            </div>
          </div>

          {story.ai_summary && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2 flex items-center">
                <span className="text-primary mr-2">🤖</span>
                AI视频总结
                {story.ai_summary.source && (
                  <span className="ml-2 text-xs bg-primary bg-opacity-20 text-primary px-2 py-1 rounded">
                    {story.ai_summary.source === 'subtitle' ? '字幕生成' : 
                     story.ai_summary.source === 'description' ? '简介' : 'AI总结'}
                  </span>
                )}
              </h3>
              <div className="bg-gradient-to-r from-darker to-gray-900 p-4 rounded border border-primary border-opacity-30">
                <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">
                  {story.ai_summary.summary || story.ai_summary.model_result}
                </p>
                {story.ai_summary.keywords && story.ai_summary.keywords.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <span className="text-sm text-gray-400 mr-2">关键词:</span>
                    {story.ai_summary.keywords.map((kw, idx) => (
                      <span key={idx} className="inline-block bg-primary bg-opacity-20 text-primary text-xs px-2 py-1 rounded mr-2 mb-2">
                        {kw}
                      </span>
                    ))}
                  </div>
                )}
                {story.ai_summary.outline && story.ai_summary.outline.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <span className="text-sm text-gray-400 block mb-2">内容大纲:</span>
                    <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                      {story.ai_summary.outline.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2 flex items-center">
              <span className="text-secondary mr-2">🏷️</span>
              标签
            </h3>
            <div className="flex flex-wrap gap-2">
              {story.tags.map((tag, index) => (
                <span key={index} className="bg-darker px-3 py-1 rounded-full text-sm border border-gray-700">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-2 flex items-center">
              <span className="text-secondary mr-2">⏱️</span>
              时间标记
            </h3>
            <div className="flex flex-wrap gap-2">
              {story.time_markers.map((marker, index) => (
                <span key={index} className="bg-darker px-3 py-1 rounded text-sm border border-gray-700">
                  {marker}
                </span>
              ))}
            </div>
          </div>

          {story.related_bvs.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2 flex items-center">
                <span className="text-secondary mr-2">🔗</span>
                相关BV号
              </h3>
              <div className="flex flex-wrap gap-2">
                {story.related_bvs.map((bvid, index) => (
                  <button
                    key={index}
                    onClick={() => window.open(`https://www.bilibili.com/video/${bvid}`, '_blank')}
                    className="bg-darker px-3 py-1 rounded text-sm border border-gray-700 hover:text-primary"
                  >
                    {bvid}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="text-secondary mr-2">📊</span>
            热度数据
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-darker p-4 rounded text-center">
              <div className="text-2xl font-bold text-primary mb-1">
                {Math.round(story.heat)}
              </div>
              <div className="text-sm text-gray-400">热度分数</div>
            </div>
            <div className="bg-darker p-4 rounded text-center">
              <div className="text-2xl font-bold text-primary mb-1">
                {story.mention_count}
              </div>
              <div className="text-sm text-gray-400">提及次数</div>
            </div>
            <div className="bg-darker p-4 rounded text-center">
              <div className="text-2xl font-bold text-primary mb-1">
                {story.length}
              </div>
              <div className="text-sm text-gray-400">字数</div>
            </div>
            <div className="bg-darker p-4 rounded text-center">
              <div className="text-2xl font-bold text-primary mb-1">
                {formatTime(story.timestamp)}
              </div>
              <div className="text-sm text-gray-400">时间点</div>
            </div>
          </div>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={handleJump}
            className="btn btn-primary flex-1"
          >
            🔗 前往B站观看
          </button>
          <button
            onClick={() => {
              navigator.clipboard.writeText(story.jump_url);
              alert('链接已复制到剪贴板！');
            }}
            className="btn btn-secondary flex-1"
          >
            📋 复制链接
          </button>
        </div>
      </div>
    </div>
  );
}