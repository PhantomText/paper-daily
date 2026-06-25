#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import subprocess
import os

SEND_KEY = "SCT369834TbsLvWr4OKy7yAcm583z4iXhd"

GITHUB_USER = "PhantomText"
GITHUB_REPO = "paper-daily"
GITHUB_TOKEN = "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"

# ==================== 功能函数 ====================

def fetch_papers(category="cs.AI", max_results=3):
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
                'summary': summary[:300] + "..." if len(summary) > 300 else summary,
                'published': published,
                'pdf_url': pdf_url
            })
        
        return papers
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        return []

def generate_html(papers):
    """生成 HTML 网页"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI论文速递 - PhantomText</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f7fa;
            color: #333;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .paper {{
            background: white;
            border-radius: 10px;
            padding: 20px 25px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: 0.3s;
        }}
        .paper:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        .paper h3 {{
            margin: 0 0 8px 0;
            color: #2c3e50;
        }}
        .paper .date {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .paper .summary {{
            color: #555;
            line-height: 1.6;
            margin: 10px 0;
        }}
        .paper .link {{
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 6px 16px;
            border-radius: 5px;
            text-decoration: none;
            font-size: 14px;
        }}
        .paper .link:hover {{
            background: #2980b9;
        }}
        .footer {{
            text-align: center;
            color: #95a5a6;
            font-size: 14px;
            margin-top: 30px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <h1>📚 AI论文速递</h1>
    <p style="text-align:center;color:#7f8c8d;">更新于：{now}</p>
"""
    
    for i, paper in enumerate(papers[:5], 1):
        html += f"""
    <div class="paper">
        <h3>🔬 {paper['title']}</h3>
        <div class="date">📅 {paper['published']}</div>
        <div class="summary">{paper['summary']}</div>
        <a class="link" href="{paper['pdf_url']}" target="_blank">📄 阅读原文</a>
    </div>
"""
    
    html += f"""
    <div class="footer">
        Powered by PhantomText 🤖 | 每日自动更新
    </div>
</body>
</html>
"""
    return html

def push_to_github(content):
    """推送到 GitHub"""
    try:
        # 克隆仓库
        os.system('rm -rf /tmp/paper-daily')
        os.system(f'git clone https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git /tmp/paper-daily')
        
        # 写入文件
        with open('/tmp/paper-daily/index.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 提交并推送
        os.chdir('/tmp/paper-daily')
        os.system('git config user.name "PhantomText"')
        os.system('git config user.email "phantomtext@bot.com"')
        os.system('git add index.html')
        os.system(f'git commit -m "自动更新: {datetime.now().strftime("%Y-%m-%d %H:%M")}"')
        os.system('git push origin main')
        
        print("✅ 已推送到 GitHub")
        return True
    except Exception as e:
        print(f"❌ GitHub 推送失败: {e}")
        return False

def push_to_serverchan(title, content):
    """推送到 Server酱（微信）"""
    try:
        url = f"https://sctapi.ftqq.com/{SEND_KEY}.send"
        data = {"title": title, "desp": content}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ 微信推送成功！")
            return True
        return False
    except Exception as e:
        print(f"❌ 微信推送失败: {e}")
        return False

def main():
    print("🤖 PhantomText 启动...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 爬取论文
    print("📡 正在爬取 arXiv 论文...")
    papers = fetch_papers("cs.AI", 5)
    
    if not papers:
        print("❌ 未获取到论文")
        push_to_serverchan("PhantomText 通知", "今日无新论文")
        return
    
    print(f"✅ 获取到 {len(papers)} 篇论文")
    
    # 生成 HTML
    print("📝 生成网页...")
    html = generate_html(papers)
    
    # 推送到 GitHub
    print("📤 推送到 GitHub...")
    success = push_to_github(html)
    
    # 推送到微信通知
    if success:
        msg = f"✅ 已更新 {len(papers)} 篇论文\n"
        msg += f"🔗 https://{GITHUB_USER}.github.io/{GITHUB_REPO}/"
        push_to_serverchan("PhantomText 更新完成", msg)
    
    print("✅ 所有任务完成！")

if __name__ == "__main__":
    main()
