import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# =========================
# 配置
# =========================
INPUT_FILE = "bilibili_activities_1779286294270.json"
OUTPUT_FILE = "bilibili_activities_view.html"

# 中国时区
CN_TZ = timezone(timedelta(hours=8))

# 自定义关键词映射（标题关键词 -> 虚拟标签）
# 当活动标题包含这些关键词时，即使原始标签没有，也会被赋予对应的虚拟标签
KEYWORD_TAGS = {
    "AI": "AI",
    "人工智能": "AI",
    "动画": "动画",
    "绘画": "绘画",
    "创作": "创作",
    "挑战": "挑战",
    "比赛": "比赛",
    "大赛": "大赛",
    "投稿": "投稿",
    "直播": "直播",
    "游戏": "游戏",
    "音乐": "音乐",
    "舞蹈": "舞蹈",
    "美食": "美食",
    "科技": "科技",
    "生活": "生活",
    "知识": "知识",
    "影视": "影视",
    "综艺": "综艺",
    "鬼畜": "鬼畜",
    "时尚": "时尚",
    "数码": "数码",
    "健身": "健身",
    "旅行": "旅行"
}

# =========================
# 工具函数
# =========================
def format_time(ts):
    """格式化中国时间"""
    dt = datetime.fromtimestamp(ts, tz=CN_TZ)
    return dt.strftime("%Y-%m-%d %H:%M")


def get_remaining_days(end_ts):
    """距离结束还有多少天"""
    now = datetime.now(CN_TZ).timestamp()
    seconds = end_ts - now
    return seconds / 86400


def get_status_text(days):
    """活动状态文本"""
    if days < 0:
        return "已结束"
    elif days < 1:
        return "今天截止"
    elif days < 2:
        return "明天截止"
    elif days < 7:
        return "即将截止"
    else:
        return "进行中"


def add_keyword_tags(item):
    """根据标题关键词添加虚拟标签"""
    title = item.get("name", "")
    original_tags = set(item.get("hot_labels", []))
    
    # 添加基于关键词的虚拟标签
    for keyword, tag in KEYWORD_TAGS.items():
        if keyword in title:
            original_tags.add(tag)
    
    # 更新标签列表
    item["hot_labels"] = list(original_tags)
    return original_tags


# =========================
# 读取 JSON
# =========================
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# =========================
# 预处理数据
# =========================
all_tags = set()

for item in data:
    # 添加基于标题关键词的虚拟标签
    tags = add_keyword_tags(item)
    all_tags.update(tags)
    
    item["remaining_days"] = get_remaining_days(item.get("etime", 0))
    item["status_text"] = get_status_text(item["remaining_days"])

# 默认按截止时间排序（快结束的在前）
data.sort(key=lambda x: x.get("etime", 0))

# 统计每个标签出现的次数
tag_counts = {}
for item in data:
    for tag in item.get("hot_labels", []):
        tag_counts[tag] = tag_counts.get(tag, 0) + 1

# 按标签数量降序排序，数量相同则按字母顺序
sorted_tags = sorted(tag_counts.items(), key=lambda x: (-x[1], x[0]))

# 生成带计数的标签 HTML
tags_html_parts = []
for tag, count in sorted_tags:
    tags_html_parts.append(
        f'<button class="filter-tag" onclick="toggleTag(this, \'{tag}\')">'
        f'{tag} '
        f'<span style="opacity:0.7; font-size:0.9em;">+{count}</span>'
        f'</button>'
    )

tags_html = "".join(tags_html_parts)


# =========================
# 卡片 HTML
# =========================
cards_html = []

for item in data:
    start_time = format_time(item.get("stime", 0))
    end_time = format_time(item.get("etime", 0))

    labels = item.get("hot_labels", [])

    labels_html = "".join(
        f'<span class="tag">{label}</span>'
        for label in labels
    )

    remaining = item["remaining_days"]
    title = item.get("name", "未知活动")

    if remaining < 0:
        remain_text = "已结束"
        remain_class = "expired"
    elif remaining < 1:
        remain_text = "今天截止"
        remain_class = "danger"
    elif remaining < 2:
        remain_text = "明天截止"
        remain_class = "warning"
    else:
        remain_text = f"剩余 {int(remaining)} 天"
        remain_class = "normal"

    # 将标题也加入 data-tags，以便搜索
    data_tags = ' '.join(labels) + f' title:{title}'
    
    card = f"""
    <div class="card"
         data-tags="{' '.join(labels)}"
         data-title="{title}"
         data-status="{item['status_text']}"
         data-remaining="{remaining}">
         
        <div class="title">
            <a href="{item.get("act_url", "#")}" target="_blank">
                {title}
            </a>
        </div>

        <div class="deadline {remain_class}">
            {remain_text}
        </div>

        <div class="meta">
            <div><b>ID:</b> {item.get("id")}</div>
            <div><b>开始:</b> {start_time}</div>
            <div><b>结束:</b> {end_time}</div>
        </div>

        <div class="tags">
            {labels_html}
        </div>

        <div class="url">
            <a href="{item.get("act_url", "#")}" target="_blank">
                {item.get("act_url", "")}
            </a>
        </div>
    </div>
    """

    cards_html.append(card)

# =========================
# HTML 页面
# =========================
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
    margin-bottom: 10px;
}}

.topbar {{
    background: white;
    padding: 16px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}}

.filter-group {{
    margin-bottom: 12px;
}}

.filter-tag {{
    margin: 4px;
    padding: 6px 12px;
    border: none;
    border-radius: 999px;
    cursor: pointer;
    background: #e8e8e8;
}}

.filter-tag.active {{
    background: #00a1d6;
    color: white;
}}

.search-box {{
    margin-bottom: 12px;
}}

.search-box input {{
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
}}

select {{
    padding: 8px;
    border-radius: 8px;
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
    margin-bottom: 10px;
}}

.title a {{
    color: #222;
    text-decoration: none;
}}

.title a:hover {{
    color: #00a1d6;
}}

.deadline {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 12px;
}}

.deadline.normal {{
    background: #e8f7e8;
    color: #0a7d22;
}}

.deadline.warning {{
    background: #fff3cd;
    color: #a36b00;
}}

.deadline.danger {{
    background: #ffe0e0;
    color: #cc0000;
}}

.deadline.expired {{
    background: #dddddd;
    color: #666;
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

.hidden {{
    display: none;
}}

</style>
</head>

<body>

<h1>Bilibili 活动列表</h1>

<div class="topbar">

    <div class="filter-group search-box">
        <b>标题搜索：</b><br>
        <input type="text" id="titleSearch" placeholder="输入标题关键词搜索..." oninput="applyFilters()">
    </div>

    <div class="filter-group">
        <b>标签筛选：</b><br>
        {tags_html}
    </div>

    <div class="filter-group">
        <b>活动周期：</b>
        <select id="statusFilter" onchange="applyFilters()">
            <option value="all">全部</option>
            <option value="进行中">进行中</option>
            <option value="即将截止">即将截止（7天内）</option>
            <option value="明天截止">明天截止</option>
            <option value="今天截止">今天截止</option>
            <option value="已结束">已结束</option>
        </select>
    </div>

</div>

<div class="container" id="container">
    {''.join(cards_html)}
</div>

<script>

let selectedTags = [];

function toggleTag(btn, tag) {{

    btn.classList.toggle("active");

    if (selectedTags.includes(tag)) {{
        selectedTags = selectedTags.filter(t => t !== tag);
    }} else {{
        selectedTags.push(tag);
    }}

    applyFilters();
}}

function applyFilters() {{

    const cards = document.querySelectorAll(".card");
    const statusFilter = document.getElementById("statusFilter").value;
    const searchText = document.getElementById("titleSearch").value.toLowerCase().trim();

    cards.forEach(card => {{

        const tags = card.dataset.tags;
        const status = card.dataset.status;
        const title = card.dataset.title.toLowerCase();

        let show = true;

        // 标题搜索筛选
        if (show && searchText !== "") {{
            show = title.includes(searchText);
        }}

        // 标签筛选
        if (show && selectedTags.length > 0) {{
            show = selectedTags.some(tag => tags.includes(tag));
        }}

        // 状态筛选
        if (show && statusFilter !== "all") {{
            show = status === statusFilter;
        }}

        if (show) {{
            card.classList.remove("hidden");
        }} else {{
            card.classList.add("hidden");
        }}
    }});
}}

</script>

</body>
</html>
"""

# =========================
# 输出 HTML
# =========================
Path(OUTPUT_FILE).write_text(html, encoding="utf-8")

print(f"已生成网页文件: {OUTPUT_FILE}")
print(f"共处理 {len(data)} 个活动")
print(f"自动生成标签: {', '.join(sorted(all_tags))}")