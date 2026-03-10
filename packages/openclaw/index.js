const { execSync } = require('child_process');

// 配置OpenClaw环境变量
process.env.OPENCLAW_MODEL_PROVIDER = 'openai';
process.env.OPENCLAW_MODEL_API_KEY = 'sk-S6Q7NxPxQUNY7gWP1RRC3cTeRuJ2mjPY42CRS3WShl5KrSE3';
process.env.OPENCLAW_MODEL_BASE_URL = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
process.env.OPENCLAW_MODEL_MODEL = 'qwen-max';
// 配置桥接服务
process.env.OPENCLAW_GATEWAY_BRIDGE_ENABLED = 'true';
process.env.OPENCLAW_GATEWAY_BRIDGE_PORT = '18790';

console.log('正在配置OpenClaw...');
console.log('通义千问API配置已完成');
console.log('模型: qwen-max');
console.log('API URL: https://dashscope.aliyuncs.com/compatible-mode/v1');

// 启动OpenClaw网关
console.log('正在启动OpenClaw网关...');
try {
  execSync('openclaw gateway --allow-unconfigured', { stdio: 'inherit' });
} catch (error) {
  console.error('启动失败:', error.message);
  console.error('请检查OpenClaw的安装和配置是否正确');
}