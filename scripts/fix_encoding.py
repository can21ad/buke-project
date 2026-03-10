# -*- coding: utf-8 -*-
"""
编码修复模块 - 解决Windows PowerShell中文乱码问题
在Python脚本开头导入此模块即可
"""

import sys
import os

# 设置标准输出编码为UTF-8
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 兼容性处理
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 测试
if __name__ == "__main__":
    print("✅ 编码修复模块已加载")
    print("中文测试：编码正常")
    print("特殊字符：日本語 한국어 Emoji 🎉")