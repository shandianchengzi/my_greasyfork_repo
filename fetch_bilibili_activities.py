#!/usr/bin/env python3
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://api.bilibili.com/x/activity_components/video_activity/hot_activity"
PAGE_SIZE = 20
MAX_PAGES = 50
REQUEST_DELAY_SECONDS = 0.3


def request_json(params: dict) -> dict:
    url = f"{API_URL}?{urlencode(params)}"
    req = Request(
        url,
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (compatible; GitHubActionsBot/1.0)",
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"请求失败，HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"请求失败，网络错误: {exc.reason}") from exc


def fetch_all_data() -> list:
    page = 1
    all_items = []

    while page <= MAX_PAGES:
        print(f"正在获取第 {page} 页...")
        payload = request_json(
            {
                "pn": page,
                "ps": PAGE_SIZE,
                "web_location": "888.139379",
            }
        )

        if payload.get("code") != 0:
            raise RuntimeError(f"API 返回错误: {payload}")

        data = payload.get("data") or {}
        items = data.get("list") or []
        all_items.extend(items)
        print(f"第 {page} 页获取到 {len(items)} 条数据")

        if len(items) < PAGE_SIZE:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    # 去重（按 id）
    deduped = []
    seen_ids = set()
    seen_signatures = set()
    for item in all_items:
        item_id = item.get("id")
        if item_id is not None:
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)
        else:
            signature = (
                item.get("name"),
                item.get("act_url"),
                item.get("stime"),
                item.get("etime"),
            )
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
        deduped.append(item)

    return deduped


def main() -> None:
    result = fetch_all_data()
    timestamp_ms = int(time.time() * 1000)
    output = Path(f"bilibili_activities_{timestamp_ms}.json")
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已写入: {output}")
    print(f"总数: {len(result)}")


if __name__ == "__main__":
    main()
