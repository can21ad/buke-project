#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书文案编辑器
功能：编辑文案、插入emoji、添加话题标签、预览效果
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import os
from datetime import datetime

class XiaohongshuEditor:
    """小红书文案编辑器"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("小红书文案编辑器 v1.0")
        self.root.geometry("900x700")
        self.root.configure(bg='#FF2442')  # 小红书红色
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#FF2442')
        self.style.configure('TLabel', background='#FF2442', foreground='white', font=('微软雅黑', 10))
        self.style.configure('TButton', font=('微软雅黑', 10))
        
        self.create_widgets()
        self.load_templates()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(
            main_frame, 
            text="✨ 小红书文案编辑器 ✨", 
            font=('微软雅黑', 20, 'bold'),
            bg='#FF2442',
            fg='white'
        )
        title_label.pack(pady=10)
        
        # 内容编辑区
        content_frame = ttk.LabelFrame(main_frame, text="文案内容", padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 标题输入
        tk.Label(content_frame, text="标题:", font=('微软雅黑', 11), bg='white').pack(anchor='w')
        self.title_entry = tk.Entry(content_frame, font=('微软雅黑', 12), width=80)
        self.title_entry.pack(fill=tk.X, pady=5)
        
        # 正文编辑
        tk.Label(content_frame, text="正文:", font=('微软雅黑', 11), bg='white').pack(anchor='w')
        self.content_text = scrolledtext.ScrolledText(
            content_frame, 
            wrap=tk.WORD, 
            font=('微软雅黑', 11),
            height=15,
            width=80
        )
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=10)
        
        # Emoji按钮
        emoji_btn = tk.Button(
            toolbar, 
            text="😊 插入Emoji", 
            command=self.show_emoji_picker,
            bg='#FF6B6B',
            fg='white',
            font=('微软雅黑', 10),
            relief=tk.FLAT
        )
        emoji_btn.pack(side=tk.LEFT, padx=5)
        
        # 话题标签按钮
        hashtag_btn = tk.Button(
            toolbar, 
            text="# 添加话题", 
            command=self.show_hashtag_picker,
            bg='#4ECDC4',
            fg='white',
            font=('微软雅黑', 10),
            relief=tk.FLAT
        )
        hashtag_btn.pack(side=tk.LEFT, padx=5)
        
        # 模板按钮
        template_btn = tk.Button(
            toolbar, 
            text="📋 使用模板", 
            command=self.show_templates,
            bg='#45B7D1',
            fg='white',
            font=('微软雅黑', 10),
            relief=tk.FLAT
        )
        template_btn.pack(side=tk.LEFT, padx=5)
        
        # 预览按钮
        preview_btn = tk.Button(
            toolbar, 
            text="👁 预览", 
            command=self.preview_content,
            bg='#96CEB4',
            fg='white',
            font=('微软雅黑', 10),
            relief=tk.FLAT
        )
        preview_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存按钮
        save_btn = tk.Button(
            toolbar, 
            text="💾 保存", 
            command=self.save_content,
            bg='#FFEAA7',
            fg='#2D3436',
            font=('微软雅黑', 10),
            relief=tk.FLAT
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空按钮
        clear_btn = tk.Button(
            toolbar, 
            text="🗑 清空", 
            command=self.clear_content,
            bg='#DFE6E9',
            fg='#2D3436',
            font=('微软雅黑', 10),
            relief=tk.FLAT
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        self.status_label = tk.Label(
            main_frame, 
            text="就绪 | 字数: 0", 
            font=('微软雅黑', 9),
            bg='#FF2442',
            fg='white'
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        # 绑定字数统计
        self.content_text.bind('<KeyRelease>', self.update_word_count)
    
    def load_templates(self):
        """加载文案模板"""
        self.templates = {
            '争议观点': """💥 {标题}

姐妹们，今天看到一个观点真的让我破防了😤

{内容}

说实话，这个观点真的很有争议，但我不得不说...

✨ 核心观点：
1. 
2. 
3. 

你们觉得呢？评论区聊聊👇

#观点分享 #深度思考 #社会观察 #女生必看""",
            
            '干货分享': """📚 {标题}

干货预警！今天分享一个超实用的内容👇

{内容}

🔥 重点总结：
1. 
2. 
3. 

收藏起来慢慢看！

#干货分享 #知识分享 #女生必看 #自我提升""",
            
            '情感共鸣': """🌸 {标题}

姐妹们，今天想和大家聊聊这个话题💭

{内容}

💡 我的感悟：
1. 
2. 
3. 

希望每个姐妹都能被温柔以待✨

#女性成长 #情感共鸣 #自我成长 #女生必看""",
            
            '热点评论': """🔥 {标题}

最近这个话题太火了，忍不住想说几句👇

{内容}

💭 我的看法：
1. 
2. 
3. 

你们怎么看？欢迎讨论👇

#热点话题 #观点分享 #社会观察"""
        }
    
    def show_emoji_picker(self):
        """显示Emoji选择器"""
        emoji_window = tk.Toplevel(self.root)
        emoji_window.title("选择Emoji")
        emoji_window.geometry("400x300")
        
        # 常用Emoji分类
        emojis = {
            '表情': ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚'],
            '手势': ['👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '👇', '☝️', '✋', '🤚', '🖐️', '👋', '🤝', '🙏', '💪'],
            '物品': ['💄', '💋', '👄', '🦷', '👅', '👂', '🦻', '👃', '👣', '👁️', '👀', '🧠', '🫀', '🫁', '🦷', '🦴', '👓', '🕶️', '🥽', '👔'],
            '符号': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️']
        }
        
        notebook = ttk.Notebook(emoji_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for category, emoji_list in emojis.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=category)
            
            for i, emoji in enumerate(emoji_list):
                btn = tk.Button(
                    frame, 
                    text=emoji, 
                    font=('Arial', 16),
                    width=3,
                    command=lambda e=emoji: self.insert_emoji(e, emoji_window)
                )
                btn.grid(row=i//5, column=i%5, padx=5, pady=5)
    
    def insert_emoji(self, emoji, window):
        """插入Emoji"""
        self.content_text.insert(tk.INSERT, emoji)
        window.destroy()
        self.update_word_count()
    
    def show_hashtag_picker(self):
        """显示话题标签选择器"""
        hashtags = [
            '#观点分享', '#深度思考', '#社会观察', '#女生必看',
            '#独立思考', '#女性成长', '#干货分享', '#知识分享',
            '#情感共鸣', '#自我提升', '#热点话题', '#生活感悟',
            '#职场干货', '#情感树洞', '#日常分享', '#种草',
            '#避雷', '#测评', '#教程', '#经验分享'
        ]
        
        hashtag_window = tk.Toplevel(self.root)
        hashtag_window.title("选择话题标签")
        hashtag_window.geometry("400x400")
        
        canvas = tk.Canvas(hashtag_window)
        scrollbar = ttk.Scrollbar(hashtag_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        for i, tag in enumerate(hashtags):
            btn = tk.Button(
                scrollable_frame,
                text=tag,
                font=('微软雅黑', 10),
                command=lambda t=tag: self.insert_hashtag(t, hashtag_window)
            )
            btn.grid(row=i//2, column=i%2, padx=10, pady=5, sticky='ew')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def insert_hashtag(self, hashtag, window):
        """插入话题标签"""
        self.content_text.insert(tk.INSERT, hashtag + ' ')
        window.destroy()
        self.update_word_count()
    
    def show_templates(self):
        """显示模板选择"""
        template_window = tk.Toplevel(self.root)
        template_window.title("选择模板")
        template_window.geometry("500x400")
        
        tk.Label(
            template_window,
            text="选择文案模板",
            font=('微软雅黑', 14, 'bold')
        ).pack(pady=10)
        
        for name, template in self.templates.items():
            btn = tk.Button(
                template_window,
                text=name,
                font=('微软雅黑', 12),
                width=20,
                command=lambda t=template: self.apply_template(t, template_window)
            )
            btn.pack(pady=5)
    
    def apply_template(self, template, window):
        """应用模板"""
        title = self.title_entry.get() or "标题"
        content = self.content_text.get("1.0", tk.END).strip() or "在这里输入内容..."
        
        filled_template = template.format(标题=title, 内容=content)
        
        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", filled_template)
        window.destroy()
        self.update_word_count()
    
    def preview_content(self):
        """预览内容"""
        title = self.title_entry.get()
        content = self.content_text.get("1.0", tk.END)
        
        preview_window = tk.Toplevel(self.root)
        preview_window.title("预览效果")
        preview_window.geometry("400x600")
        preview_window.configure(bg='white')
        
        # 模拟小红书界面
        tk.Label(
            preview_window,
            text="📱 小红书预览",
            font=('微软雅黑', 16, 'bold'),
            bg='white'
        ).pack(pady=10)
        
        # 标题
        tk.Label(
            preview_window,
            text=title,
            font=('微软雅黑', 14, 'bold'),
            bg='white',
            wraplength=350
        ).pack(pady=10)
        
        # 内容
        content_label = tk.Label(
            preview_window,
            text=content,
            font=('微软雅黑', 11),
            bg='white',
            wraplength=350,
            justify=tk.LEFT
        )
        content_label.pack(pady=10, padx=20)
        
        # 互动按钮
        btn_frame = tk.Frame(preview_window, bg='white')
        btn_frame.pack(pady=20)
        
        tk.Label(btn_frame, text="❤️ 点赞", font=('微软雅黑', 10), bg='white').pack(side=tk.LEFT, padx=10)
        tk.Label(btn_frame, text="💬 评论", font=('微软雅黑', 10), bg='white').pack(side=tk.LEFT, padx=10)
        tk.Label(btn_frame, text="⭐ 收藏", font=('微软雅黑', 10), bg='white').pack(side=tk.LEFT, padx=10)
    
    def save_content(self):
        """保存内容"""
        title = self.title_entry.get()
        content = self.content_text.get("1.0", tk.END)
        
        if not title and not content.strip():
            messagebox.showwarning("警告", "内容为空！")
            return
        
        # 选择保存位置
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filepath:
            data = {
                'title': title,
                'content': content,
                'created_at': datetime.now().isoformat(),
                'word_count': len(content)
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"文案已保存到:\n{filepath}")
    
    def clear_content(self):
        """清空内容"""
        if messagebox.askyesno("确认", "确定要清空所有内容吗？"):
            self.title_entry.delete(0, tk.END)
            self.content_text.delete("1.0", tk.END)
            self.update_word_count()
    
    def update_word_count(self, event=None):
        """更新字数统计"""
        content = self.content_text.get("1.0", tk.END)
        count = len(content) - 1  # 减去最后的换行符
        self.status_label.config(text=f"就绪 | 字数: {count}")

def main():
    """主函数"""
    root = tk.Tk()
    app = XiaohongshuEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()