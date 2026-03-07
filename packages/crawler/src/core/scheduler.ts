import cron from 'node-cron';

interface SchedulerConfig {
  crawlers: Array<{
    crawl: () => Promise<void>;
  }>;
  schedule: {
    initialCrawl: boolean;
    incrementalCrawl: string; // cron表达式
    fullCrawl: string; // cron表达式
  };
}

export class Scheduler {
  private config: SchedulerConfig;
  private jobs: cron.ScheduledTask[] = [];
  private isRunning = false;

  constructor(config: SchedulerConfig) {
    this.config = config;
  }

  async start() {
    if (this.isRunning) {
      console.log('调度器已经在运行');
      return;
    }

    this.isRunning = true;

    // 初始爬取
    if (this.config.schedule.initialCrawl) {
      console.log('执行初始爬取...');
      await this.runCrawlers();
    }

    // 增量爬取定时任务
    const incrementalJob = cron.schedule(
      this.config.schedule.incrementalCrawl,
      async () => {
        console.log('执行增量爬取...');
        await this.runCrawlers();
      }
    );
    this.jobs.push(incrementalJob);

    // 全量爬取定时任务
    const fullJob = cron.schedule(
      this.config.schedule.fullCrawl,
      async () => {
        console.log('执行全量爬取...');
        await this.runCrawlers();
      }
    );
    this.jobs.push(fullJob);

    console.log('调度器启动成功');
    console.log(`增量爬取计划: ${this.config.schedule.incrementalCrawl}`);
    console.log(`全量爬取计划: ${this.config.schedule.fullCrawl}`);
  }

  async stop() {
    if (!this.isRunning) {
      return;
    }

    // 停止所有定时任务
    for (const job of this.jobs) {
      job.stop();
    }
    this.jobs = [];
    this.isRunning = false;

    console.log('调度器已停止');
  }

  private async runCrawlers() {
    for (const crawler of this.config.crawlers) {
      try {
        await crawler.crawl();
      } catch (error) {
        console.error('爬虫执行失败:', error);
      }
    }
  }

  // 手动触发爬取
  async triggerCrawl() {
    console.log('手动触发爬取...');
    await this.runCrawlers();
  }
}