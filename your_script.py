import json
from datetime import datetime
from pathlib import Path

# 输入文件
INPUT_FILE = "bilibili_activities_1779286294270.json"
OUTPUT_FILE = "bilibili_activities_view.html"

# 读取 JSON
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 时间格式化（中国时区 UTC+8）
def format_time(ts):
    dt = datetime.utcfromtimestamp(ts)  # 先按 UTC
    dt = dt.replace(hour=(dt.hour + 8) % 24)  # 转中国时区
    return dt.strftime("%Y-%m-%d %H:%M")

# 生成卡片 HTML
cards_html = []

for item in data:
    start_time = format_time(item.get("stime", 0))
    end_time = format_time(item.get("etime", 0))

    labels = "".join(
        f'<span class="tag">{label}</span>'
        for label in item.get("hot_labels", [])
    )

    card = f"""
    <div class="card">
        <div class="title">
            <a href="{item.get("act_url", "#")}" target="_blank">
                {item.get("name", "未知活动")}
            </a>
        </div>

        <div class="meta">
            <div><b>ID:</b> {item.get("id")}</div>
            <div><b>开始时间:</b> {start_time}</div>
            <div><b>结束时间:</b> {end_time}</div>
        </div>

        <div class="tags">
            {labels}
        </div>

        <div class="url">
            <a href="{item.get("act_url", "#")}" target="_blank">
                {item.get("act_url", "")}
            </a>
        </div>
    </div>
    """

    cards_html.append(card)

# 最终 HTML
html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>Bilibili 活动列表</title>

<style>
body {{
    margin: 0;
    padding: 20px;
    background: #f5f5f5;
    font-family: "Microsoft YaHei", sans-serif;
}}

h1 {{
    margin-bottom: 20px;
}}

.container {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 16px;
}}

.card {{
    background: white;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}}

.title {{
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 12px;
    line-height: 1.4;
}}

.title a {{
    color: #222;
    text-decoration: none;
}}

.title a:hover {{
    color: #00a1d6;
}}

.meta {{
    font-size: 14px;
    color: #666;
    line-height: 1.8;
}}

.tags {{
    margin-top: 12px;
}}

.tag {{
    display: inline-block;
    background: #e8f3ff;
    color: #0078d4;
    padding: 4px 10px;
    border-radius: 999px;
    margin-right: 8px;
    margin-bottom: 8px;
    font-size: 13px;
}}

.url {{
    margin-top: 12px;
    word-break: break-all;
}}

.url a {{
    color: #00a1d6;
    text-decoration: none;
}}

.url a:hover {{
    text-decoration: underline;
}}
</style>

</head>
<body>

<h1>Bilibili 活动列表</h1>

<div class="container">
{''.join(cards_html)}
</div>

</body>
</html>
"""

# 写入 HTML
Path(OUTPUT_FILE).write_text(html, encoding="utf-8")

print(f"已生成: {OUTPUT_FILE}")