// ==UserScript==
// @name         获取B站活动列表完整版
// @namespace    http://tampermonkey.net/
// @version      2.0
// @description  获取B站热门活动和指定话题/专题数据，智能合并活动与话题
// @author       You
// @match        https://www.bilibili.com/*
// @match        https://member.bilibili.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_cookie
// @connect      api.bilibili.com
// @connect      member.bilibili.com
// ==/UserScript==

(function() {
    'use strict';

    // --- 工具函数：从cookie中获取值 ---
    function getCookieValue(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        if (match) return match[2];
        return '';
    }

    // --- 获取CSRF (bili_jct) ---
    function getCsrf() {
        return getCookieValue('bili_jct');
    }

    // --- 通用请求函数 ---
    async function request(url, options = {}) {
        const csrf = getCsrf();
        let finalUrl = url;
        if (url.includes('?') && !url.includes('csrf=') && url.includes('hot_activity')) {
            finalUrl += `&csrf=${csrf}`;
        } else if (!url.includes('?') && url.includes('hot_activity')) {
            finalUrl += `?csrf=${csrf}`;
        }

        const response = await fetch(finalUrl, {
            ...options,
            credentials: 'include',
            headers: {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                ...options.headers,
            },
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return response.json();
    }

    // --- 获取接口1：热门活动 ---
    async function fetchHotActivity(pn, ps = 20) {
        const url = `https://api.bilibili.com/x/activity_components/video_activity/hot_activity?pn=${pn}&ps=${ps}&web_location=888.139379`;
        const data = await request(url);
        return data;
    }

    // --- 获取接口2：话题/专题数据 ---
    async function fetchTopics() {
        const url = `https://member.bilibili.com/x/vupre/web/topic/type/v2?pn=0&ps=400`;
        const data = await request(url);
        return data;
    }

    // --- 获取所有热门活动数据 ---
    async function getAllActivities() {
        let allItems = [];
        let page = 1;
        const pageSize = 20;
        let maxPages = 50;
        
        while (page <= maxPages) {
            console.log(`正在获取活动第 ${page} 页...`);
            try {
                const result = await fetchHotActivity(page, pageSize);
                await new Promise(resolve => setTimeout(resolve, 300));
                
                if (result.code === 0 && result.data && result.data.list) {
                    const list = result.data.list;
                    if (list.length === 0) break;
                    
                    allItems.push(...list);
                    console.log(`活动第 ${page} 页获取 ${list.length} 条，累计 ${allItems.length} 条`);
                    
                    if (list.length < pageSize) break;
                    page++;
                } else {
                    console.warn('活动接口异常:', result);
                    break;
                }
            } catch (error) {
                console.error(`活动第 ${page} 页请求失败:`, error);
                break;
            }
        }
        return allItems;
    }

    // --- 合并活动数据（处理活动与话题的合并逻辑）---
    function mergeActivitiesWithTopics(activities, topics) {
        // 创建一个Map用于快速查找活动（按名称去重）
        const activityMap = new Map();
        
        // 先添加原有的活动数据
        activities.forEach(activity => {
            const key = activity.name || activity.title || '';
            if (key) {
                activityMap.set(key, {
                    source: 'activity',
                    ...activity,
                    // 确保有标准字段
                    name: activity.name || activity.title,
                    id: activity.id,
                    isFromTopic: false,
                    show_activity_icon: true
                });
            }
        });
        
        // 处理话题数据中的活动项（show_activity_icon为true）
        let mergedCount = 0;
        let newActivityCount = 0;
        
        topics.forEach(topic => {
            const topicName = topic.topic_name || topic.name;
            if (!topicName) return;
            
            if (topic.show_activity_icon === true) {
                // 这是一个活动
                const existingActivity = activityMap.get(topicName);
                
                if (existingActivity) {
                    // 如果已存在活动，合并信息（保留活动信息，补充话题字段）
                    mergedCount++;
                    const merged = {
                        ...existingActivity,
                        ...topic, // 话题字段优先补充
                        source: 'merged',
                        name: topicName,
                        mergedFromTopic: true,
                        topic_id: topic.topic_id,
                        topic_description: topic.topic_description,
                        activity_text: topic.activity_text || existingActivity.activity_text,
                        activity_description: topic.activity_description || existingActivity.activity_description,
                        mission_id: topic.mission_id || existingActivity.mission_id,
                        arc_play_vv: topic.arc_play_vv || existingActivity.arc_play_vv,
                        final_score: topic.final_score || existingActivity.final_score,
                        similarity_score: topic.similarity_score || existingActivity.similarity_score
                    };
                    activityMap.set(topicName, merged);
                } else {
                    // 新活动，创建活动格式（补充默认值）
                    newActivityCount++;
                    const newActivity = {
                        source: 'topic_as_activity',
                        id: topic.topic_id,
                        name: topicName,
                        title: topicName,
                        // 话题特有字段
                        topic_id: topic.topic_id,
                        topic_name: topic.topic_name,
                        topic_description: topic.topic_description,
                        activity_description: topic.activity_description || '',
                        activity_text: topic.activity_text || '',
                        mission_id: topic.mission_id || 0,
                        arc_play_vv: topic.arc_play_vv || 0,
                        final_score: topic.final_score || 0,
                        similarity_score: topic.similarity_score || 0,
                        show_activity_icon: true,
                        // 补充默认的活动字段
                        act_url: topic.act_url || `https://www.bilibili.com/topic/${topic.topic_id}`,
                        cover: topic.cover || '',
                        hot_cover: topic.hot_cover || '',
                        stime: topic.stime || Math.floor(Date.now() / 1000),
                        etime: topic.etime || Math.floor(Date.now() / 1000) + 30 * 24 * 3600,
                        hot_labels: topic.hot_labels || [],
                        isFromTopic: true
                    };
                    activityMap.set(topicName, newActivity);
                }
            }
        });
        
        console.log(`活动合并统计: 原有活动 ${activities.length} 个`);
        console.log(`话题中的活动: 合并 ${mergedCount} 个, 新增 ${newActivityCount} 个`);
        
        // 返回合并后的活动列表和纯话题列表
        const mergedActivities = Array.from(activityMap.values());
        const pureTopics = topics.filter(topic => !topic.show_activity_icon);
        
        return {
            activities: mergedActivities,
            topics: pureTopics,
            stats: {
                originalActivities: activities.length,
                mergedFromTopics: mergedCount,
                newFromTopics: newActivityCount,
                totalActivities: mergedActivities.length,
                pureTopics: pureTopics.length
            }
        };
    }

    // --- 主函数：获取所有数据 ---
    async function getAllData() {
        console.log('=== 开始获取热门活动数据 ===');
        const activities = await getAllActivities();
        console.log(`热门活动获取完成，共 ${activities.length} 条`);
        
        console.log('=== 开始获取话题/专题数据 ===');
        let topicsData = [];
        try {
            const result = await fetchTopics();
            if (result.code === 0 && result.data) {
                // 解析 topics 数组
                if (result.data.topics && Array.isArray(result.data.topics)) {
                    topicsData = result.data.topics;
                    console.log(`话题数据获取成功，共 ${topicsData.length} 条`);
                    console.log(`其中 show_activity_icon=true 的数量: ${topicsData.filter(t => t.show_activity_icon === true).length}`);
                } else {
                    console.error('话题数据结构异常:', result.data);
                }
            } else if (result.code === -101) {
                console.error('账号未登录，无法获取话题数据');
            } else {
                console.error('话题接口异常:', result);
            }
        } catch (error) {
            console.error('获取话题数据失败:', error);
        }
        
        // 合并数据
        console.log('=== 开始合并活动与话题数据 ===');
        const merged = mergeActivitiesWithTopics(activities, topicsData);
        
        // 输出统计信息
        console.log('=== 获取完成 ===');
        console.log(`统计信息:`, merged.stats);
        console.log(`最终活动数量: ${merged.activities.length}`);
        console.log(`纯话题数量: ${merged.topics.length}`);
        console.log(`总计: ${merged.activities.length + merged.topics.length}`);
        
        return {
            activities: merged.activities,
            topics: merged.topics,
            stats: merged.stats,
            fetchTime: new Date().toISOString()
        };
    }

    // --- 导出JSON ---
    function exportJSON(data, filename) {
        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    // --- 创建UI按钮 ---
    function addButton() {
        const btn = document.createElement('button');
        btn.textContent = '📊 获取全部活动&话题数据';
        btn.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            padding: 12px 20px;
            background: linear-gradient(135deg, #00a1d6, #00c8ff);
            color: white;
            border: none;
            border-radius: 40px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: transform 0.2s;
            z-index: 10000;
        `;
        btn.onmouseenter = () => btn.style.transform = 'scale(1.02)';
        btn.onmouseleave = () => btn.style.transform = 'scale(1)';

        let isRunning = false;
        btn.onclick = async () => {
            if (isRunning) return;
            isRunning = true;
            const originalText = btn.textContent;
            btn.textContent = '⏳ 获取中，请稍候...';
            btn.disabled = true;

            try {
                const allData = await getAllData();
                const message = `获取完成！\n` +
                    `原有活动: ${allData.stats.originalActivities} 个\n` +
                    `话题中合并: ${allData.stats.mergedFromTopics} 个\n` +
                    `话题中新增: ${allData.stats.newFromTopics} 个\n` +
                    `最终活动: ${allData.activities.length} 个\n` +
                    `纯话题: ${allData.topics.length} 个\n` +
                    `总计: ${allData.activities.length + allData.topics.length} 个\n` +
                    `将导出为JSON文件。`;
                alert(message);
                exportJSON(allData, `bilibili_data_${new Date().toISOString().slice(0,19)}.json`);
            } catch (err) {
                console.error(err);
                alert('获取失败，请查看控制台(F12)了解详情');
            } finally {
                isRunning = false;
                btn.textContent = originalText;
                btn.disabled = false;
            }
        };
        document.body.appendChild(btn);
    }

    // 页面加载完成后添加按钮
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addButton);
    } else {
        addButton();
    }
})();
