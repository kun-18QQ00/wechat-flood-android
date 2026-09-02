/* ==========================================
   消息助手 v6.0 - JavaScript交互逻辑
   ========================================== */

// ===== 全局状态 =====
const AppState = {
    isRunning: false,
    isPaused: false,
    sentCount: 0,
    currentIndex: 0,
    startTime: null,
    selectedApp: '微信',
    selectedMode: '顺序',
    messages: [],
    timer: null
};

// ===== 预设消息 =====
const Presets = {
    emoji: "😀\n😂\n🤣\n😍\n🥰\n😎\n🤩\n😘\n😋\n🤔\n👍\n❤️\n🔥\n✨\n🎉",
    num: Array.from({length: 20}, (_, i) => i + 1).join('\n'),
    greet: "你好\n早上好\n下午好\n晚上好\n在吗\n忙吗\n吃饭了吗\n晚安"
};

// ===== 应用包名映射 =====
const AppPackages = {
    '微信': 'com.tencent.mm',
    'QQ': 'com.tencent.mobileqq',
    '钉钉': 'com.alibaba.android.rimet',
    '飞书': 'com.ss.android.lark',
    'Telegram': 'org.telegram.messenger',
    'WhatsApp': 'com.whatsapp'
};

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
    // 隐藏启动画面
    setTimeout(() => {
        const splash = document.getElementById('splash');
        splash.style.opacity = '0';
        splash.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            splash.style.display = 'none';
            document.getElementById('app').style.display = 'block';
            addLog('应用已启动', 'info');
        }, 500);
    }, 1500);
    
    // 监听输入
    const msgInput = document.getElementById('msgInput');
    msgInput.addEventListener('input', () => {
        updateCharCount();
    });
});

// ===== 更新字符计数 =====
function updateCharCount() {
    const input = document.getElementById('msgInput');
    const count = document.getElementById('charCount');
    count.textContent = `${input.value.length} 字符`;
}

// ===== 加载预设 =====
function loadPreset(type) {
    const input = document.getElementById('msgInput');
    input.value = Presets[type] || '';
    updateCharCount();
    addLog(`已加载预设: ${type === 'emoji' ? '表情' : type === 'num' ? '数字' : '问候'}`, 'info');
    showToast('预设已加载');
}

// ===== 选择应用 =====
function selectApp(btn, appName) {
    // 移除其他按钮的active状态
    document.querySelectorAll('.app-btn').forEach(b => b.classList.remove('active'));
    
    // 设置当前按钮active
    btn.classList.add('active');
    
    // 更新状态
    AppState.selectedApp = appName;
    document.getElementById('selectedApp').textContent = `当前: ${appName}`;
    
    addLog(`已选择: ${appName}`, 'info');
}

// ===== 选择模式 =====
function selectMode(btn, mode) {
    // 移除其他按钮的active状态
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    
    // 设置当前按钮active
    btn.classList.add('active');
    
    // 更新状态
    AppState.selectedMode = mode;
    addLog(`模式: ${mode}`, 'info');
}

// ===== 更新速度 =====
function updateSpeed(value) {
    document.getElementById('speedValue').textContent = `${parseFloat(value).toFixed(1)} 秒`;
}

// ===== 开始发送 =====
function startSending() {
    if (AppState.isRunning) return;
    
    const input = document.getElementById('msgInput');
    const text = input.value.trim();
    
    if (!text) {
        showToast('请输入消息内容');
        addLog('错误: 消息内容为空', 'error');
        return;
    }
    
    // 解析消息
    AppState.messages = text.split('\n').filter(m => m.trim());
    
    if (AppState.messages.length === 0) {
        showToast('消息内容为空');
        addLog('错误: 无有效消息', 'error');
        return;
    }
    
    // 初始化状态
    AppState.isRunning = true;
    AppState.isPaused = false;
    AppState.sentCount = 0;
    AppState.currentIndex = 0;
    AppState.startTime = Date.now();
    
    // 更新UI
    updateUIState('running');
    
    addLog(`开始发送 ${AppState.messages.length} 条消息`, 'info');
    addLog(`目标: ${AppState.selectedApp} | 模式: ${AppState.selectedMode}`, 'info');
    
    // 调用Python后端
    callPythonBackend('start', {
        messages: AppState.messages,
        app: AppState.selectedApp,
        mode: AppState.selectedMode,
        interval: parseFloat(document.getElementById('speedSlider').value),
        batch: parseInt(document.getElementById('batchInput').value) || 0
    });
    
    // 开始发送循环
    sendNext();
}

// ===== 发送下一条 =====
function sendNext() {
    if (!AppState.isRunning || AppState.isPaused) return;
    
    const batch = parseInt(document.getElementById('batchInput').value) || 999999;
    
    if (AppState.sentCount >= batch) {
        completeSending();
        return;
    }
    
    // 选择消息
    let msg;
    if (AppState.selectedMode === '随机') {
        msg = AppState.messages[Math.floor(Math.random() * AppState.messages.length)];
    } else if (AppState.selectedMode === '单条') {
        msg = AppState.messages[0];
    } else {
        msg = AppState.messages[AppState.currentIndex % AppState.messages.length];
        AppState.currentIndex++;
    }
    
    // 发送消息
    sendMessage(msg);
    
    AppState.sentCount++;
    updateStatus();
    
    // 调用Python后端
    callPythonBackend('send', { message: msg });
    
    // 设置下一次发送
    const interval = parseFloat(document.getElementById('speedSlider').value) * 1000;
    AppState.timer = setTimeout(sendNext, interval);
}

// ===== 发送消息（复制到剪贴板） =====
function sendMessage(msg) {
    // 复制到剪贴板
    if (navigator.clipboard) {
        navigator.clipboard.writeText(msg).then(() => {
            const displayMsg = msg.length > 15 ? msg.substring(0, 15) + '...' : msg;
            addLog(`#${AppState.sentCount + 1} 已复制: ${displayMsg}`);
        }).catch(err => {
            addLog(`复制失败: ${err.message}`, 'error');
        });
    } else {
        // 降级方案
        const textarea = document.createElement('textarea');
        textarea.value = msg;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        
        const displayMsg = msg.length > 15 ? msg.substring(0, 15) + '...' : msg;
        addLog(`#${AppState.sentCount + 1} 已复制: ${displayMsg}`);
    }
}

// ===== 暂停发送 =====
function pauseSending() {
    if (!AppState.isRunning) return;
    
    AppState.isPaused = !AppState.isPaused;
    
    if (AppState.isPaused) {
        clearTimeout(AppState.timer);
        updateUIState('paused');
        addLog('已暂停');
    } else {
        updateUIState('running');
        addLog('已继续');
        sendNext();
    }
}

// ===== 停止发送 =====
function stopSending() {
    if (!AppState.isRunning) return;
    
    AppState.isRunning = false;
    AppState.isPaused = false;
    clearTimeout(AppState.timer);
    
    updateUIState('stopped');
    addLog('正在停止...');
    
    // 调用Python后端
    callPythonBackend('stop', {});
}

// ===== 完成发送 =====
function completeSending() {
    AppState.isRunning = false;
    AppState.isPaused = false;
    
    updateUIState('stopped');
    addLog(`完成! 共发送 ${AppState.sentCount} 条`);
    updateStats();
    
    // 调用Python后端
    callPythonBackend('complete', { count: AppState.sentCount });
}

// ===== 更新UI状态 =====
function updateUIState(state) {
    const btnStart = document.getElementById('btnStart');
    const btnPause = document.getElementById('btnPause');
    const btnStop = document.getElementById('btnStop');
    const statusLabel = document.getElementById('statusLabel');
    
    switch (state) {
        case 'running':
            btnStart.disabled = true;
            btnPause.disabled = false;
            btnStop.disabled = false;
            btnPause.querySelector('.ctrl-text').textContent = '暂停';
            statusLabel.textContent = '运行中...';
            statusLabel.className = 'status-label running';
            break;
            
        case 'paused':
            btnPause.querySelector('.ctrl-text').textContent = '继续';
            statusLabel.textContent = '已暂停';
            statusLabel.className = 'status-label paused';
            break;
            
        case 'stopped':
            btnStart.disabled = false;
            btnPause.disabled = true;
            btnStop.disabled = true;
            btnPause.querySelector('.ctrl-text').textContent = '暂停';
            statusLabel.textContent = '已停止';
            statusLabel.className = 'status-label';
            break;
    }
}

// ===== 更新状态显示 =====
function updateStatus() {
    document.getElementById('countLabel').textContent = AppState.sentCount;
    updateStats();
    updateProgress();
}

// ===== 更新统计信息 =====
function updateStats() {
    if (AppState.startTime) {
        const elapsed = (Date.now() - AppState.startTime) / 1000;
        const speed = AppState.sentCount / elapsed;
        document.getElementById('statsLabel').textContent = 
            `速度: ${speed.toFixed(1)} 条/秒 | 耗时: ${elapsed.toFixed(0)} 秒`;
    }
}

// ===== 更新进度条 =====
function updateProgress() {
    const batch = parseInt(document.getElementById('batchInput').value) || 0;
    if (batch > 0) {
        const progress = (AppState.sentCount / batch) * 100;
        document.getElementById('progressFill').style.width = `${Math.min(progress, 100)}%`;
    }
}

// ===== 添加日志 =====
function addLog(message, type = '') {
    const logContainer = document.getElementById('logContainer');
    const time = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    
    const logItem = document.createElement('div');
    logItem.className = 'log-item';
    logItem.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-msg ${type}">${message}</span>
    `;
    
    logContainer.appendChild(logItem);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // 调用Python后端
    callPythonBackend('log', { message, type });
}

// ===== 清空日志 =====
function clearLog() {
    const logContainer = document.getElementById('logContainer');
    logContainer.innerHTML = '';
    addLog('日志已清空', 'info');
}

// ===== 显示Toast提示 =====
function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// ===== 调用Python后端 =====
function callPythonBackend(action, data) {
    // 通过URL scheme或postMessage与Python通信
    if (window.pywebview) {
        window.pywebview.api.handle_action(action, JSON.stringify(data));
    } else if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.python) {
        window.webkit.messageHandlers.python.postMessage({ action, data });
    } else {
        // 开发环境模拟
        console.log(`Python Backend: ${action}`, data);
    }
}

// ===== Python调用的接口 =====
window.updateFromPython = function(action, data) {
    switch (action) {
        case 'on_sent':
            AppState.sentCount = data.count;
            updateStatus();
            break;
            
        case 'on_complete':
            completeSending();
            break;
            
        case 'on_error':
            addLog(`错误: ${data.message}`, 'error');
            break;
            
        case 'update_clipboard':
            // 剪贴板已更新
            break;
    }
};
