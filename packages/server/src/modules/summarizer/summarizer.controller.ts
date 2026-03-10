import express from 'express';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);
const router = express.Router();

// Python脚本路径
const PYTHON_SCRIPT = path.join(__dirname, '../../../../../scripts/simple_bv_summarizer.py');

// 处理BV号，获取故事内容
router.get('/summarize/:bvid', async (req, res) => {
  const { bvid } = req.params;
  
  try {
    console.log(`[*] 开始处理BV号: ${bvid}`);
    
    // 调用Python脚本，设置编码为UTF-8
    const { stdout, stderr } = await execAsync(`chcp 65001 && python "${PYTHON_SCRIPT}" ${bvid}`, {
      timeout: 120000, // 2分钟超时
      maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      encoding: 'utf8'
    });
    
    if (stderr && !stdout) {
      console.error('[-] Python脚本错误:', stderr);
      return res.status(500).json({
        code: 500,
        message: '处理失败',
        error: stderr
      });
    }
    
    // 解析Python脚本的输出
    const result = JSON.parse(stdout);
    
    console.log(`[+] 成功处理BV号: ${bvid}`);
    
    res.json({
      code: 200,
      data: result
    });
    
  } catch (error: any) {
    console.error('[-] 处理BV号失败:', error);
    res.status(500).json({
      code: 500,
      message: '处理失败',
      error: error.message
    });
  }
});

module.exports = router;
