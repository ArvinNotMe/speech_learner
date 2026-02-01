/**
 * 学习页面JavaScript
 */

// 获取URL参数
function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        topic: params.get('topic') || '英语学习',
        dialogue: JSON.parse(params.get('dialogue') || '[]'),
        keywords: JSON.parse(params.get('keywords') || '[]')
    };
}

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    const data = getUrlParams();
    
    // 设置标题
    document.getElementById('topicTitle').textContent = `📚 ${data.topic}`;
    document.title = `${data.topic} - 英语口语练习`;
    
    // 渲染关键词
    renderKeywords(data.keywords);
    
    // 渲染对话
    renderDialogue(data.dialogue);
    
    // 绑定播放全部按钮
    document.getElementById('playAllBtn').addEventListener('click', playAllAudio);
});

// 渲染关键词
function renderKeywords(keywords) {
    const container = document.getElementById('keywordsList');
    
    if (!keywords || keywords.length === 0) {
        document.getElementById('keywordsSection').style.display = 'none';
        return;
    }
    
    container.innerHTML = keywords.map(kw => `
        <div class="keyword-item">
            <span class="word">${kw.word}</span>
            <span class="phonetic">${kw.phonetic || ''}</span>
            <span class="meaning">${kw.chinese}</span>
        </div>
    `).join('');
}

// 渲染对话
function renderDialogue(dialogue) {
    const container = document.getElementById('dialogueList');
    
    container.innerHTML = dialogue.map((item, index) => `
        <div class="dialogue-row" data-index="${index}">
            <div class="col chinese">
                <span class="speaker speaker-${item.speaker.toLowerCase()}">${item.speaker}</span>
                ${item.chinese}
            </div>
            <div class="col english">${item.english}</div>
            <div class="col audio">
                ${item.audio_url ? `
                    <audio controls src="${item.audio_url}" id="audio-${index}"></audio>
                ` : '<span class="no-audio">无音频</span>'}
            </div>
        </div>
    `).join('');
}

// 顺序播放所有音频
async function playAllAudio() {
    const audios = document.querySelectorAll('audio');
    const btn = document.getElementById('playAllBtn');
    
    if (audios.length === 0) {
        alert('没有可播放的音频');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = '<span class="icon">⏸️</span> 播放中...';
    
    for (let i = 0; i < audios.length; i++) {
        const audio = audios[i];
        const row = audio.closest('.dialogue-row');
        
        // 高亮当前行
        document.querySelectorAll('.dialogue-row').forEach(r => r.style.background = '');
        row.style.background = '#e3f2fd';
        
        // 播放音频
        try {
            await playAudio(audio);
        } catch (error) {
            console.error('播放失败:', error);
        }
        
        // 等待一下再播放下一个
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // 清除高亮
    document.querySelectorAll('.dialogue-row').forEach(r => r.style.background = '');
    
    btn.disabled = false;
    btn.innerHTML = '<span class="icon">▶️</span> 播放全部';
}

// 播放单个音频
function playAudio(audio) {
    return new Promise((resolve, reject) => {
        audio.onended = resolve;
        audio.onerror = reject;
        audio.play().catch(reject);
    });
}