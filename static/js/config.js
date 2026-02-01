/**
 * 配置页面JavaScript
 */

// 全局状态
let currentData = null;
let apiConfigured = false;

// DOM元素
const elements = {
    topic: document.getElementById('topic'),
    exchanges: document.getElementById('exchanges'),
    voice: document.getElementById('voice'),
    generateBtn: document.getElementById('generateBtn'),
    previewBtn: document.getElementById('previewBtn'),
    saveBtn: document.getElementById('saveBtn'),
    status: document.getElementById('status'),
    previewContent: document.getElementById('previewContent'),
    keywordsPanel: document.getElementById('keywordsPanel'),
    keywordsList: document.getElementById('keywordsList'),
    apiStatus: document.getElementById('apiStatus')
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    bindEvents();
    checkApiConfig();
});

// 绑定事件
function bindEvents() {
    elements.generateBtn.addEventListener('click', handleGenerate);
    elements.previewBtn.addEventListener('click', handlePreview);
    elements.saveBtn.addEventListener('click', handleSave);
}

// 检查API配置
async function checkApiConfig() {
    try {
        const res = await fetch('/api/config');
        const data = await res.json();

        if (data.success && data.services_ready) {
            apiConfigured = true;
            elements.apiStatus.innerHTML = '✅ API 已配置，服务就绪';
            elements.apiStatus.style.background = '#d4edda';
            elements.apiStatus.style.color = '#155724';
            elements.generateBtn.disabled = false;
        } else {
            apiConfigured = false;
            elements.apiStatus.innerHTML = '❌ ' + data.message;
            elements.apiStatus.style.background = '#f8d7da';
            elements.apiStatus.style.color = '#721c24';
            elements.generateBtn.disabled = true;
        }
    } catch (error) {
        apiConfigured = false;
        elements.apiStatus.innerHTML = '❌ 无法连接到服务器';
        elements.apiStatus.style.background = '#f8d7da';
        elements.apiStatus.style.color = '#721c24';
        elements.generateBtn.disabled = true;
    }
}

// 显示状态
function showStatus(message, type) {
    elements.status.className = `status ${type}`;
    elements.status.innerHTML = message;
}

// 隐藏状态
function hideStatus() {
    elements.status.className = 'status';
    elements.status.textContent = '';
}

// 设置按钮状态
function setButtonsState(generating) {
    elements.generateBtn.disabled = generating;
    elements.previewBtn.disabled = !currentData || generating;
    elements.saveBtn.disabled = !currentData || generating;
}

// 生成内容
async function handleGenerate() {
    const topic = elements.topic.value.trim();
    const numExchanges = parseInt(elements.exchanges.value);

    if (!apiConfigured) {
        showStatus('❌ API 未配置，请在 .env 文件中设置 DASHSCOPE_API_KEY', 'error');
        return;
    }
    if (!topic) {
        showStatus('❌ 请输入学习话题', 'error');
        return;
    }

    setButtonsState(true);
    showStatus('⏳ 正在生成内容，请稍候...', 'loading');

    try {
        // 生成完整内容
        const generateRes = await fetch('/api/generate-full', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, num_exchanges: numExchanges })
        });

        const data = await generateRes.json();

        if (data.success) {
            currentData = data;
            showStatus('✅ 生成成功！', 'success');
            renderPreview(data);
            renderKeywords(data.keywords);
        } else {
            throw new Error(data.error || '生成失败');
        }
    } catch (error) {
        showStatus(`❌ ${error.message}`, 'error');
        console.error(error);
    } finally {
        setButtonsState(false);
    }
}

// 渲染预览
function renderPreview(data) {
    const dialogueHtml = data.dialogue.map((item, index) => `
        <div class="dialogue-row">
            <div class="col chinese">
                <span class="speaker speaker-${item.speaker.toLowerCase()}">${item.speaker}</span>
                ${item.chinese}
            </div>
            <div class="col english">${item.english}</div>
            <div class="col audio">
                ${item.audio_url ? `<audio controls src="${item.audio_url}"></audio>` : '无音频'}
            </div>
        </div>
    `).join('');

    elements.previewContent.innerHTML = `
        <div class="dialogue-table">
            <div class="dialogue-header">
                <div class="col">中文</div>
                <div class="col">英文</div>
                <div class="col">读音</div>
            </div>
            <div class="dialogue-body">
                ${dialogueHtml}
            </div>
        </div>
    `;
}

// 渲染关键词
function renderKeywords(keywords) {
    if (!keywords || keywords.length === 0) {
        elements.keywordsPanel.style.display = 'none';
        return;
    }

    elements.keywordsPanel.style.display = 'block';
    elements.keywordsList.innerHTML = keywords.map(kw => `
        <div class="keyword-item">
            <span class="word">${kw.word}</span>
            <span class="phonetic">${kw.phonetic || ''}</span>
            <span class="meaning">${kw.chinese}</span>
        </div>
    `).join('');
}

// 预览（在新窗口打开）
function handlePreview() {
    if (!currentData) return;

    const params = new URLSearchParams({
        topic: currentData.topic,
        dialogue: JSON.stringify(currentData.dialogue),
        keywords: JSON.stringify(currentData.keywords)
    });

    window.open(`/frontend/learn.html?${params.toString()}`, '_blank');
}

// 保存HTML
async function handleSave() {
    if (!currentData) return;

    setButtonsState(true);
    showStatus('⏳ 正在保存...', 'loading');

    try {
        const res = await fetch('/api/save-html', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: currentData.topic,
                dialogue: currentData.dialogue,
                keywords: currentData.keywords
            })
        });

        const data = await res.json();

        if (data.success) {
            showStatus(`✅ 已保存！<a href="${data.url}" target="_blank">点击打开</a>`, 'success');
        } else {
            throw new Error(data.error || '保存失败');
        }
    } catch (error) {
        showStatus(`❌ ${error.message}`, 'error');
    } finally {
        setButtonsState(false);
    }
}