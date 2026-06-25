#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os

# ==================== 配置 ====================
SEND_KEY = os.environ.get('SEND_KEY', '')

# ==================== 功能函数 ====================

def fetch_papers(category="cs.AI", max_results=5):
    """从 arXiv 爬取最新论文"""
    url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=submittedDate&max_results={max_results}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return []
        
        root = ET.fromstring(response.text)
        papers = []
        
        for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
            title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
            summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
            published = entry.find('{http://www.w3.org/2005/Atom}published').text[:10]
            
            pdf_url = ""
            for link in entry.findall('{http://www.w3.org/2005/Atom}link'):
                if link.get('title') == 'pdf':
                    pdf_url = link.get('href')
                    break
            
            papers.append({
                'title': title,
                'summary': summary[:500] + "..." if len(summary) > 500 else summary,
                'published': published,
                'pdf_url': pdf_url
            })
        
        return papers
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        return []

def generate_html(papers):
    """生成漂亮的 HTML 网页"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI论文速递 - PhantomText</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 30px 20px;
            background: #f0f2f5;
            color: #1a1a2e;
        }}
        .header {{
            text-align: center;
            padding: 30px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }}
        .header h1 {{
            font-size: 32px;
            letter-spacing: 2px;
        }}
        .header .time {{
            opacity: 0.85;
            margin-top: 8px;
            font-size: 14px;
        }}
        .paper {{
            background: white;
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .paper:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.10);
        }}
        .paper .title {{
            font-size: 20px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 6px;
        }}
        .paper .title a {{
            color: #1a1a2e;
            text-decoration: none;
        }}
        .paper .title a:hover {{
            color: #667eea;
        }}
        .paper .meta {{
            color: #888;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .paper .summary {{
            color: #444;
            line-height: 1.7;
            font-size: 15px;
        }}
        .paper .link {{
            display: inline-block;
            margin-top: 12px;
            background: #667eea;
            color: white;
            padding: 6px 18px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .paper .link:hover {{
            background: #5a6fd6;
        }}
        .footer {{
            text-align: center;
            color: #aaa;
            font-size: 13px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        @media (max-width: 600px) {{
            body {{ padding: 16px; }}
            .header h1 {{ font-size: 22px; }}
            .paper {{ padding: 18px; }}
            .paper .title {{ font-size: 17px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 AI 论文速递</h1>
        <div class="time">🕐 最后更新：{now}</div>
    </div>
'''
    
    if not papers:
        html += '<p style="text-align:center;color:#888;">📭 今日暂无新论文</p>'
    else:
        for paper in papers:
            html += f'''
    <div class="paper">
        <div class="title"><a href="{paper['pdf_url']}" target="_blank">{paper['title']}</a></div>
        <div class="meta">📅 {paper['published']}</div>
        <div class="summary">{paper['summary']}</div>
        <a class="link" href="{paper['pdf_url']}" target="_blank">📄 阅读原文</a>
    </div>
'''
    
    html += f'''
    <div class="footer">
        🤖 Powered by PhantomText · 每日自动更新
    </div>
</body>
</html>
'''
    return html

def push_to_serverchan(message):
    """推送到 Server酱（微信）"""
    if not SEND_KEY:
        print("⚠️ SEND_KEY 未设置，跳过微信推送")
        return
    
    try:
        url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
        data = {
            "title": "PhantomText 更新完成",
            "desp": message
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ 微信推送成功！")
        else:
            print(f"❌ 微信推送失败: {response.text}")
    except Exception as e:
        print(f"❌ 微信推送异常: {e}")

def main():
    print("🤖 PhantomText 启动...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 爬取论文
    print("📡 正在爬取 arXiv 论文...")
    papers = fetch_papers("cs.AI", 5)
    
    if not papers:
        print("❌ 未获取到论文")
        push_to_serverchan("今日无新论文")
        return
    
    print(f"✅ 获取到 {len(papers)} 篇论文")
    
    # 生成 HTML
    print("📝 生成网页...")
    html = generate_html(papers)
    
    # 写入文件
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ index.html 已保存")
    
    # 推送到微信
    repo = os.environ.get('GITHUB_REPOSITORY', '')
    username = repo.split('/')[0] if '/' in repo else ''
    msg = f"已更新 {len(papers)} 篇论文\nhttps://{username}.github.io/paper-daily/" if username else f"已更新 {len(papers)} 篇论文"
    push_to_serverchan(msg)
    
    print("🎉 所有任务完成！")

if __name__ == "__main__":
    main()
