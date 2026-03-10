#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历PDF生成器
将Markdown简历转换为PDF格式
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re

# 注册中文字体
try:
    # 尝试使用系统自带的中文字体
    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
    chinese_font = 'SimSun'
except:
    try:
        pdfmetrics.registerFont(TTFont('MicrosoftYaHei', 'C:/Windows/Fonts/msyh.ttc'))
        chinese_font = 'MicrosoftYaHei'
    except:
        chinese_font = 'Helvetica'  #  fallback

def create_resume_pdf(output_path):
    """创建简历PDF"""
    
    # 创建PDF文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 创建样式
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle(
        'ChineseTitle',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=24,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading_style = ParagraphStyle(
        'ChineseHeading',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=14,
        spaceAfter=6,
        spaceBefore=12,
        textColor=colors.HexColor('#34495e'),
        borderColor=colors.HexColor('#3498db'),
        borderWidth=2,
        borderPadding=5
    )
    
    normal_style = ParagraphStyle(
        'ChineseNormal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    bullet_style = ParagraphStyle(
        'ChineseBullet',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        leading=14,
        leftIndent=20,
        bulletIndent=10
    )
    
    # 构建内容
    story = []
    
    # 标题
    story.append(Paragraph("个人简历", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 基本信息
    story.append(Paragraph("基本信息", heading_style))
    story.append(Paragraph("<b>姓名</b>: [待填写]", normal_style))
    story.append(Paragraph("<b>求职意向</b>: 产品经理 / 全栈开发工程师 / AI应用工程师", normal_style))
    story.append(Paragraph("<b>电话</b>: [待填写]", normal_style))
    story.append(Paragraph("<b>邮箱</b>: [待填写]", normal_style))
    story.append(Paragraph("<b>微信</b>: [待填写]", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 教育背景
    story.append(Paragraph("教育背景", heading_style))
    story.append(Paragraph("<b>[学校名称]</b> | <b>[专业名称]</b>", normal_style))
    story.append(Paragraph("[入学时间] - [毕业时间]", normal_style))
    story.append(Paragraph("• 主修课程: [待填写]", bullet_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 项目经历
    story.append(Paragraph("项目经历", heading_style))
    
    # 项目1
    story.append(Paragraph("<b>1. 怖客 (Buke) - 恐怖灵异内容聚合平台</b>", normal_style))
    story.append(Paragraph("<b>项目时间</b>: 2025.03 - 至今", normal_style))
    story.append(Paragraph("<b>项目角色</b>: 产品经理 + 全栈开发工程师", normal_style))
    story.append(Paragraph("<b>项目描述</b>:", normal_style))
    story.append(Paragraph("一款专注于全简中互联网恐怖灵异内容聚合的网页应用，通过爬虫技术收集B站博主《道听途说》系列的评论区数据，筛选用户推荐度高的故事内容进行整合展示。", normal_style))
    story.append(Paragraph("<b>核心功能</b>:", normal_style))
    story.append(Paragraph("• 智能爬虫系统: 基于Puppeteer + Cheerio构建，自动采集B站视频评论数据", bullet_style))
    story.append(Paragraph("• AI内容总结: 集成bobapi多模型(Kimi/GLM/MiniMax)，自动生成视频内容摘要", bullet_style))
    story.append(Paragraph("• 访客统计分析: 实时统计网站访问量、用户行为分析", bullet_style))
    story.append(Paragraph("• 智能推荐系统: 基于用户行为的AI内容推荐", bullet_style))
    story.append(Paragraph("• 求助评论挖掘: 自动识别并提取用户评论", bullet_style))
    story.append(Paragraph("<b>技术栈</b>: Next.js 14 + React 18 + TypeScript + Node.js + Python爬虫 + MySQL/Redis/ES", normal_style))
    story.append(Paragraph("<b>项目成果</b>: 407+视频数据，20+自动化脚本，AI视频总结工具", normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 项目2
    story.append(Paragraph("<b>2. 星灵占卜 - AI算命网站</b>", normal_style))
    story.append(Paragraph("<b>项目时间</b>: 2025.02 - 2025.03", normal_style))
    story.append(Paragraph("<b>项目角色</b>: 产品经理 + 前端开发工程师", normal_style))
    story.append(Paragraph("<b>项目描述</b>:", normal_style))
    story.append(Paragraph("一个神秘风格的在线占卜网站，提供塔罗占卜、每日运势、星座解析、梦境解读等功能。", normal_style))
    story.append(Paragraph("<b>核心功能</b>: 塔罗占卜、每日运势、星座解析、梦境解读", normal_style))
    story.append(Paragraph("<b>技术栈</b>: HTML5 + CSS3 + JavaScript", normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # 项目3
    story.append(Paragraph("<b>3. 无人机3D可视化项目</b>", normal_style))
    story.append(Paragraph("<b>项目时间</b>: 2024.12 - 2025.01", normal_style))
    story.append(Paragraph("<b>项目角色</b>: Python开发工程师", normal_style))
    story.append(Paragraph("<b>项目描述</b>:", normal_style))
    story.append(Paragraph("使用Python + Matplotlib实现的无人机3D可视化项目，包括3D无人机模型绘制、飞行路径可视化。", normal_style))
    story.append(Paragraph("<b>技术栈</b>: Python + Matplotlib + NumPy + mpl_toolkits.mplot3d", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 技能特长
    story.append(Paragraph("技能特长", heading_style))
    story.append(Paragraph("<b>编程语言</b>: Python (熟练), JavaScript/TypeScript (熟练), HTML/CSS (精通)", normal_style))
    story.append(Paragraph("<b>前端技术</b>: Next.js, React 18, Tailwind CSS", normal_style))
    story.append(Paragraph("<b>后端技术</b>: Node.js, Express, MySQL, Redis, Elasticsearch, Docker, Nginx", normal_style))
    story.append(Paragraph("<b>爬虫与AI</b>: Puppeteer, Cheerio, bobapi, OpenAI API", normal_style))
    story.append(Paragraph("<b>产品设计</b>: MVP设计, 功能优先级, 用户画像, 数据分析", normal_style))
    story.append(Spacer(1, 0.5*cm))
    
    # 生成PDF
    doc.build(story)
    print(f"✅ 简历PDF已生成: {output_path}")

if __name__ == "__main__":
    output_path = "D:/怖客/scripts/resume.pdf"
    create_resume_pdf(output_path)