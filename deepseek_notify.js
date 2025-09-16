// ==UserScript==
// @name         回答完成时通知（仅从“正在回答” → “完成/空”时触发）
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
    // 1. 检查浏览器是否支持 Notification API
    if (!("Notification" in window)) {
        console.warn("当前浏览器不支持桌面通知。");
        return;
    }

    // 2. 检查是否在安全上下文（HTTPS 或 localhost）
    if (!window.isSecureContext && window.location.hostname !== "localhost") {
        console.warn("通知 API 仅在 HTTPS 或 localhost 环境下可用。");
        return;
    }

    // 3. 检查权限状态
    if (Notification.permission === "granted") {
        showNotification();
    } else if (Notification.permission === "denied") {
        console.warn("用户已拒绝通知权限。请在浏览器设置中手动开启。");
        // 可选：引导用户去设置
        alert("通知被禁用，请在浏览器设置中允许本站通知。");
    } else {
        // 请求权限（必须由用户手势触发，比如点击按钮）
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                showNotification();
            } else {
                console.warn("用户未授予通知权限。");
            }
        }).catch(err => {
            console.error("请求通知权限时出错：", err);
        });
    }
}

function showNotification() {
    const duration = 8000; // ms
    const notification = new Notification("🎉 回答已完成", {
        body: "点击查看结果或继续提问",
        icon: "https://example.com/icon.png", // 替换为你自己的图标
        silent: false,
        requireInteraction: true // 可选：通知不会自动消失
    });

   // ⏱️ 设置 N 毫秒后自动关闭
    setTimeout(() => {
        notification.close(); // 👈 手动关闭通知
    }, duration);

    // 可选：点击通知后跳转或执行操作
    notification.onclick = function() {
        window.focus(); // 聚焦窗口
        // window.open("https://example.com/result", "_blank");
        this.close(); // 关闭通知
    };
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


})();