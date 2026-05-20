# my_greasyfork_repo
some simple scripts in it.

## B站活动列表自动抓取

仓库已添加 GitHub Actions 工作流：

- 文件：`.github/workflows/fetch-bilibili-activities.yml`
- 触发方式：
  - 每天自动执行一次（UTC `01:00`）
  - 支持在 Actions 页面手动执行（`workflow_dispatch`）
- 执行脚本：`fetch_bilibili_activities.py`
- 输出结果：`bilibili_activities_*.json`

工作流会在抓取后自动提交新增/更新的 `bilibili_activities_*.json` 文件到当前分支。
