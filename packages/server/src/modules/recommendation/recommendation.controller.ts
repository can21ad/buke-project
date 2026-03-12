import express from 'express';
import axios from 'axios';

const router = express.Router();

const PYTHON_API_URL = process.env.PYTHON_API_URL || 'http://localhost:8000';

// 测试路由
router.get('/test', (req, res) => {
  res.json({ message: 'recommendation controller works!' });
});

interface SimilarVideo {
  bvid: string;
  title: string;
  video_url: string;
  cover_url: string;
  views: number | string;
  comment_count: number | string;
  duration: string;
  upload_date: string;
  summary: string;
  similarity: number;
  rank: number;
}

interface ApiResponse {
  code: number;
  message: string;
  data: {
    total: number;
    videos: SimilarVideo[];
  };
}

router.get('/similar-videos', async (req, res) => {
  try {
    const { bvid, top_n = 5 } = req.query;
    
    if (!bvid) {
      return res.status(400).json({
        code: 400,
        message: '缺少bvid参数'
      });
    }
    
    const response = await axios.get<ApiResponse>(`${PYTHON_API_URL}/api/similar`, {
      params: { bvid, top_n }
    });
    
    res.json(response.data);
  } catch (error: any) {
    console.error('获取相似视频失败:', error.message);
    res.status(500).json({
      code: 500,
      message: '获取相似视频失败',
      error: error.message
    });
  }
});

router.get('/semantic-search', async (req, res) => {
  try {
    const { keyword, top_n = 5 } = req.query;
    
    if (!keyword) {
      return res.status(400).json({
        code: 400,
        message: '缺少keyword参数'
      });
    }
    
    const response = await axios.get(`${PYTHON_API_URL}/api/search`, {
      params: { keyword, top_n }
    });
    
    res.json(response.data);
  } catch (error: any) {
    console.error('语义搜索失败:', error.message);
    res.status(500).json({
      code: 500,
      message: '语义搜索失败',
      error: error.message
    });
  }
});

module.exports = router;
