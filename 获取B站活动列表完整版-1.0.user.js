// ==UserScript==
// @name         获取B站活动列表完整版
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  获取所有活动列表
// @author       You
// @match        https://www.bilibili.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_cookie
// @connect      api.bilibili.com
// ==/UserScript==

(function() {
    'use strict';

    // 获取 CSRF token 的多种方式
    function getCsrfToken() {
        // 从 cookie 中获取
        const cookieMatch = document.cookie.match(/bili_jct=([^;]+)/);
        if (cookieMatch) return cookieMatch[1];

        // 从页面元素中获取（如果有）
        const metaToken = document.querySelector('meta[name="csrf"]');
        if (metaToken) return metaToken.getAttribute('content');

        console.warn('无法获取 CSRF token');
        return '';
    }

    // 封装请求函数
    function request(url) {
        return new Promise((resolve, reject) => {
            const csrf = getCsrfToken();
            const fullUrl = url.includes('csrf=') ? url : `${url}&csrf=${csrf}`;

            GM_xmlhttpRequest({
                method: 'GET',
                url: fullUrl,
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                credentials: 'include',
                onload: function(response) {
                    if (response.status === 200) {
                        try {
                            const data = JSON.parse(response.responseText);
                            resolve(data);
                        } catch (e) {
                            reject(e);
                        }
                    } else {
                        reject(new Error(`HTTP ${response.status}`));
                    }
                },
                onerror: reject
            });
        });
    }

    // 获取所有数据
    async function fetchAllData() {
        let page = 1;
        let allItems = [];
        let maxPages = 50; // 最大页数限制，防止无限循环
        const pageSize = 20;

        while (page <= maxPages) {
            console.log(`正在获取第 ${page} 页...`);

            const url = `https://api.bilibili.com/x/activity_components/video_activity/hot_activity?pn=${page}&ps=${pageSize}&web_location=888.139379`;

            try {
                const result = await request(url);

                if (result.code === 0 && result.data && result.data.list) {
                    const list = result.data.list;
                    allItems.push(...list);

                    console.log(`第 ${page} 页获取到 ${list.length} 条数据`);

                    // 如果返回的数据少于 pageSize，说明是最后一页
                    if (list.length < pageSize) {
                        break;
                    }

                    page++;

                    // 添加延迟，避免请求过快
                    await new Promise(resolve => setTimeout(resolve, 300));
                } else {
                    console.error('API 返回错误:', result);
                    break;
                }
            } catch (error) {
                console.error(`第 ${page} 页请求失败:`, error);
                break;
            }
        }

        return allItems;
    }

    // 显示数据统计
    function displayStats(data) {
        console.table({
            '总数据量': data.length,
            '活动列表': data.map(item => item.title || item.name || '未知标题')
        });
    }

    // 导出数据为 JSON
    function exportToJSON(data) {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bilibili_activities_${new Date().getTime()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // 创建 UI 按钮
    function addUIButton() {
        const button = document.createElement('button');
        button.textContent = '获取所有活动数据';
        button.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            padding: 10px 20px;
            background: #00a1d6;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        `;

        button.onclick = async () => {
            button.disabled = true;
            button.textContent = '获取中...';

            try {
                const data = await fetchAllData();
                console.log('获取完成！总数据量:', data.length);
                displayStats(data);

                // 询问是否导出
                if (data.length > 0 && confirm(`获取到 ${data.length} 条数据，是否导出为 JSON？`)) {
                    exportToJSON(data);
                }
            } catch (error) {
                console.error('获取失败:', error);
                alert('获取失败，请查看控制台');
            } finally {
                button.disabled = false;
                button.textContent = '获取所有活动数据';
            }
        };

        document.body.appendChild(button);
    }

    // 页面加载完成后添加按钮
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addUIButton);
    } else {
        addUIButton();
    }
})();