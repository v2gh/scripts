// ==UserScript==
// @name         deepseek回答完成时通知（仅从“正在回答” → “完成/空”时触发）
// @namespace    http://tampermonkey.net/
// @version      1.4
// @description  仅当从“正在回答”变成“回答完成或输入框为空”时，发出浏览器通知
// @author       You
// @match        https://chat.deepseek.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    const SELECTOR = 'input[type="file"][multiple] + div[role="button"]';

    // 预存关键 path 片段
    const SQUARE_PATH_SNIPPET = 'M2 4.88006C2 3.68015 2 3.08019 2.30557 2.6596C';
    const ARROW_PATH_SNIPPET = 'M8.3125 0.981648C8.66767 1.05456 8.97902 1.20565 9.2627 1.4338C';

    let lastState = null;

    function getButtonState() {
        const btn = document.querySelector(SELECTOR);
        if (!btn) return 'notfound';

        const svgPath = btn.querySelector('svg path')?.getAttribute('d');
        const isDisabled = btn.getAttribute('aria-disabled') === 'true';

        if (!svgPath) return 'unknown';

        const isSquare = svgPath.includes(SQUARE_PATH_SNIPPET);
        const isArrow = svgPath.includes(ARROW_PATH_SNIPPET);

        if (isSquare && !isDisabled) return 'thinking';
        if (isArrow && !isDisabled) return 'ready_to_send';
        if (isArrow && isDisabled) return 'completed_or_empty';

        return 'unknown';
    }

    function triggerNotification() {
        // 检查通知权限
        if (Notification.permission === "granted") {
            new Notification("🎉 回答已完成", {
                body: "点击查看结果或继续提问",
                icon: "https://example.com/icon.png", // 可选：替换成你喜欢的图标
                silent: false
            });
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(permission => {
                if (permission === "granted") {
                    new Notification("🎉 回答已完成", {
                        body: "点击查看结果或继续提问",
                        icon: "https://example.com/icon.png"
                    });
                }
            });
        }
    }

    function checkStatus() {
        const currentState = getButtonState();

        // 状态未变化，不处理
        if (currentState === lastState) return;

        console.log(`[${new Date().toLocaleTimeString()}] 🔄 状态更新: ${lastState} → ${currentState}`);

        // ✅ 核心逻辑：仅当从 thinking → completed_or_empty 时触发通知
        if (lastState === 'thinking' && currentState === 'completed_or_empty') {
            console.log("🔔 满足条件：正在回答 → 已完成/空，触发通知！");
            triggerNotification();
        }

        // 更新状态
        lastState = currentState;
    }

    // 初次检测（延迟1秒，确保页面加载）
    setTimeout(checkStatus, 1000);

    // 每 500ms 检测一次
    setInterval(checkStatus, 500);

    // 监听 DOM 变化（适合 SPA 页面）
    const observer = new MutationObserver(checkStatus);
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['aria-disabled']
    });

})();
