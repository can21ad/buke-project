import puppeteer from 'puppeteer';
import cheerio from 'cheerio';
import axios from 'axios';

interface BilibiliCrawlerConfig {
  channelId: string;
  seriesFilter: string;
  maxVideos: number;
  rateLimit: {
    requestsPerSecond: number;
    concurrentRequests: number;
  };
}

interface VideoInfo {
  bvid: string;
  aid: string;
  title: string;
  description: string;
  coverUrl: string;
  duration: number;
  pubDate: string;
  viewCount: number;
  danmakuCount: number;
  commentCount: number;
  seriesName: string;
  episodeNumber: number;
}

interface CommentInfo {
  rpid: string;
  memberMid: string;
  memberName: string;
  content: string;
  likeCount: number;
  replyCount: number;
  ctime: string;
  parentId?: string;
}

export class BilibiliCrawler {
  private config: BilibiliCrawlerConfig;
  private browser: puppeteer.Browser | null = null;

  constructor(config: BilibiliCrawlerConfig) {
    this.config = config;
  }

  async initialize() {
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  // 获取视频列表
  async getVideoList(): Promise<VideoInfo[]> {
    try {
      const page = await this.browser?.newPage();
      if (!page) throw new Error('Browser not initialized');

      const url = `https://space.bilibili.com/${this.config.channelId}/video`;
      await page.goto(url, { waitUntil: 'networkidle2' });

      // 等待视频列表加载
      await page.waitForSelector('.video-list .video-item');

      // 滚动加载更多视频
      for (let i = 0; i < 5; i++) {
        await page.evaluate(() => {
          window.scrollTo(0, document.body.scrollHeight);
        });
        await page.waitForTimeout(2000);
      }

      const html = await page.content();
      const $ = cheerio.load(html);

      const videos: VideoInfo[] = [];
      $('.video-list .video-item').each((index, element) => {
        if (videos.length >= this.config.maxVideos) return false;

        const title = $(element).find('.title').text().trim();
        if (!title.includes(this.config.seriesFilter)) return true;

        const link = $(element).find('.title').attr('href') || '';
        const bvidMatch = link.match(/BV[0-9A-Za-z]+/);
        const bvid = bvidMatch ? bvidMatch[0] : '';

        if (!bvid) return true;

        const coverUrl = $(element).find('.cover img').attr('src') || '';
        const duration = this.parseDuration($(element).find('.length').text().trim());
        const pubDate = $(element).find('.time').text().trim();
        const viewCount = this.parseCount($(element).find('.play').text().trim());
        const danmakuCount = this.parseCount($(element).find('.dm').text().trim());

        videos.push({
          bvid,
          aid: '', // 需要通过API获取
          title,
          description: '', // 需要通过API获取
          coverUrl,
          duration,
          pubDate,
          viewCount,
          danmakuCount,
          commentCount: 0, // 需要通过API获取
          seriesName: this.config.seriesFilter,
          episodeNumber: this.parseEpisodeNumber(title),
        });
      });

      await page.close();
      return videos;
    } catch (error) {
      console.error('获取视频列表失败:', error);
      return [];
    }
  }

  // 获取视频详情
  async getVideoDetail(bvid: string): Promise<VideoInfo | null> {
    try {
      const apiUrl = `https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`;
      const response = await axios.get(apiUrl);
      const data = response.data.data;

      return {
        bvid: data.bvid,
        aid: data.aid.toString(),
        title: data.title,
        description: data.desc,
        coverUrl: data.pic,
        duration: data.duration,
        pubDate: new Date(data.pubdate * 1000).toISOString(),
        viewCount: data.stat.view,
        danmakuCount: data.stat.danmaku,
        commentCount: data.stat.reply,
        seriesName: this.config.seriesFilter,
        episodeNumber: this.parseEpisodeNumber(data.title),
      };
    } catch (error) {
      console.error(`获取视频详情失败 (${bvid}):`, error);
      return null;
    }
  }

  // 获取评论
  async getComments(bvid: string, page: number = 1, pageSize: number = 20): Promise<CommentInfo[]> {
    try {
      const apiUrl = `https://api.bilibili.com/x/v2/reply?type=1&oid=${bvid}&pn=${page}&ps=${pageSize}`;
      const response = await axios.get(apiUrl);
      const data = response.data.data.replies || [];

      return data.map((comment: any) => ({
        rpid: comment.rpid.toString(),
        memberMid: comment.member.mid.toString(),
        memberName: comment.member.uname,
        content: comment.content.message,
        likeCount: comment.like,
        replyCount: comment.reply_count,
        ctime: new Date(comment.ctime * 1000).toISOString(),
      }));
    } catch (error) {
      console.error(`获取评论失败 (${bvid}):`, error);
      return [];
    }
  }

  // 解析时长
  private parseDuration(duration: string): number {
    const parts = duration.split(':').map(Number);
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    return 0;
  }

  // 解析播放数
  private parseCount(count: string): number {
    if (count.includes('万')) {
      return Math.floor(parseFloat(count) * 10000);
    }
    return parseInt(count) || 0;
  }

  // 解析期数
  private parseEpisodeNumber(title: string): number {
    const match = title.match(/第(\d+)期/);
    return match ? parseInt(match[1]) : 0;
  }

  // 启动爬取
  async crawl() {
    console.log('开始爬取B站视频...');
    
    await this.initialize();
    
    try {
      const videos = await this.getVideoList();
      console.log(`获取到 ${videos.length} 个视频`);

      for (const video of videos) {
        console.log(`处理视频: ${video.title}`);
        
        // 获取视频详情
        const detail = await this.getVideoDetail(video.bvid);
        if (detail) {
          console.log(`详情: ${detail.title}, 播放量: ${detail.viewCount}`);
        }

        // 获取评论
        const comments = await this.getComments(video.bvid);
        console.log(`获取到 ${comments.length} 条评论`);

        // 等待速率限制
        await new Promise(resolve => setTimeout(resolve, 1000 / this.config.rateLimit.requestsPerSecond));
      }
    } finally {
      await this.close();
    }

    console.log('B站爬取完成');
  }
}