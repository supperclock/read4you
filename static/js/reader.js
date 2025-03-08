document.addEventListener('DOMContentLoaded', function() {
    const bookId = document.getElementById('book-container').dataset.bookId;
    const progressPosition = parseFloat(document.getElementById('book-container').dataset.progress);
    const voiceSelector = document.getElementById('voice-selector');
    const playButton = document.getElementById('play-button');
    const pauseButton = document.getElementById('pause-button');
    const progressBar = document.getElementById('progress-bar');
    const textContainer = document.getElementById('text-container');
    
    // 添加分页控件
    const paginationContainer = document.createElement('div');
    paginationContainer.className = 'pagination-controls';
    
    const prevButton = document.createElement('button');
    prevButton.className = 'btn btn-outline-primary';
    prevButton.innerHTML = '&laquo; 上一页';
    prevButton.disabled = true;
    
    const pageInfo = document.createElement('span');
    pageInfo.className = 'page-info';
    pageInfo.textContent = '第 1 页，共 ? 页';
    
    const nextButton = document.createElement('button');
    nextButton.className = 'btn btn-outline-primary';
    nextButton.innerHTML = '下一页 &raquo;';
    
    paginationContainer.appendChild(prevButton);
    paginationContainer.appendChild(pageInfo);
    paginationContainer.appendChild(nextButton);
    
    // 插入分页控件到阅读器控件下方
    const readerControls = document.querySelector('.reader-controls');
    readerControls.parentNode.insertBefore(paginationContainer, readerControls.nextSibling);
    
    let bookPages = [];
    let currentPage = 0;
    let totalPages = 0;
    let bookText = '';
    let currentPosition = progressPosition || 0;
    let isPlaying = false;
    let currentChunk = 0;
    let textChunks = [];
    let currentSentence = null;
    
    // 语音合成相关变量
    let speechSynthesis = window.speechSynthesis;
    let speechUtterance = null;
    let availableVoices = [];
    
    // 添加语音设置控制
    const rateControl = document.getElementById('rate-control');
    const pitchControl = document.getElementById('pitch-control');
    const rateValue = document.getElementById('rate-value');
    const pitchValue = document.getElementById('pitch-value');
    
    // 更新语速显示
    rateControl.addEventListener('input', function() {
        rateValue.textContent = parseFloat(this.value).toFixed(1);
    });
    
    // 更新音调显示
    pitchControl.addEventListener('input', function() {
        pitchValue.textContent = parseFloat(this.value).toFixed(1);
    });
    
    // 初始化语音合成
    function initSpeechSynthesis() {
        // 检查浏览器是否支持语音合成
        if (!('speechSynthesis' in window)) {
            alert('您的浏览器不支持语音合成功能，请使用Chrome、Edge或Safari浏览器。');
            return false;
        }
        
        // 获取可用的语音
        function loadVoices() {
            availableVoices = speechSynthesis.getVoices();
            
            // 更新语音选择器
            voiceSelector.innerHTML = '';
            
            // 首先添加中文语音
            const chineseVoices = availableVoices.filter(voice => 
                voice.lang.includes('zh') || voice.name.includes('Chinese') || voice.name.includes('中文')
            );
            
            if (chineseVoices.length > 0) {
                const chineseOptgroup = document.createElement('optgroup');
                chineseOptgroup.label = '中文语音';
                
                chineseVoices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    chineseOptgroup.appendChild(option);
                });
                
                voiceSelector.appendChild(chineseOptgroup);
            }
            
            // 然后添加其他语音
            const otherVoices = availableVoices.filter(voice => 
                !voice.lang.includes('zh') && !voice.name.includes('Chinese') && !voice.name.includes('中文')
            );
            
            if (otherVoices.length > 0) {
                const otherOptgroup = document.createElement('optgroup');
                otherOptgroup.label = '其他语音';
                
                otherVoices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.name;
                    option.textContent = `${voice.name} (${voice.lang})`;
                    otherOptgroup.appendChild(option);
                });
                
                voiceSelector.appendChild(otherOptgroup);
            }
            
            // 如果没有语音可用，显示提示
            if (availableVoices.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = '没有可用的语音';
                voiceSelector.appendChild(option);
            }
            
            // 尝试恢复上次使用的语音
            const savedVoice = localStorage.getItem(`book_${bookId}_voice`);
            if (savedVoice && availableVoices.some(v => v.name === savedVoice)) {
                voiceSelector.value = savedVoice;
            } else if (chineseVoices.length > 0) {
                // 默认选择第一个中文语音
                voiceSelector.value = chineseVoices[0].name;
            }
        }
        
        // 在某些浏览器中，需要等待voiceschanged事件
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
        
        // 立即尝试加载语音
        loadVoices();
        
        return true;
    }
    
    // 播放语音
    function playSpeech(text) {
        if (!speechSynthesis) return;
        
        // 如果正在播放，先停止
        if (speechUtterance) {
            speechSynthesis.cancel();
        }
        
        // 创建新的语音实例
        speechUtterance = new SpeechSynthesisUtterance(text);
        
        // 设置语音
        const selectedVoice = availableVoices.find(voice => voice.name === voiceSelector.value);
        if (selectedVoice) {
            speechUtterance.voice = selectedVoice;
        }
        
        // 保存当前选择的语音
        localStorage.setItem(`book_${bookId}_voice`, voiceSelector.value);
        
        // 设置语速和音调
        speechUtterance.rate = parseFloat(rateControl.value);
        speechUtterance.pitch = parseFloat(pitchControl.value);
        
        // 设置语言
        if (selectedVoice) {
            speechUtterance.lang = selectedVoice.lang;
        } else {
            speechUtterance.lang = 'zh-CN';  // 默认使用中文
        }
        
        // 监听语音结束事件
        speechUtterance.onend = function() {
            // 播放下一个块
            playNextChunk();
        };
        
        // 监听错误事件
        speechUtterance.onerror = function(event) {
            console.error('语音合成错误:', event.error);
            // 尝试继续播放下一个块
            playNextChunk();
        };
        
        // 开始播放
        speechSynthesis.speak(speechUtterance);
    }
    
    // 暂停语音
    function pauseSpeech() {
        if (speechSynthesis) {
            speechSynthesis.cancel();
            speechUtterance = null;
        }
    }
    
    // 加载书籍文本
    function loadBookText() {
        fetch(`/book/api/text/${bookId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    textContainer.innerHTML = `<p class="error">${data.error}</p>`;
                    return;
                }
                
                if (!data.pages || data.pages.length === 0) {
                    textContainer.innerHTML = '<p class="info">此文档没有可读取的文本内容。</p>';
                    return;
                }
                
                bookPages = data.pages;
                totalPages = data.total_pages;
                
                // 更新页面信息
                pageInfo.textContent = `第 1 页，共 ${totalPages} 页`;
                
                // 显示第一页或上次阅读的页面
                const savedPage = parseInt(localStorage.getItem(`book_${bookId}_page`) || '0');
                displayPage(savedPage < totalPages ? savedPage : 0);
                
                // 初始化语音合成
                initSpeechSynthesis();
            })
            .catch(error => {
                console.error('加载文本失败:', error);
                textContainer.innerHTML = '<p class="error">加载文本失败，请重试。</p>';
            });
    }
    
    // 显示指定页面
    function displayPage(pageIndex) {
        if (pageIndex < 0 || pageIndex >= bookPages.length) return;
        
        // 保存当前页面
        currentPage = pageIndex;
        localStorage.setItem(`book_${bookId}_page`, currentPage);
        
        // 更新页面信息
        pageInfo.textContent = `第 ${currentPage + 1} 页，共 ${totalPages} 页`;
        
        // 更新按钮状态
        prevButton.disabled = currentPage === 0;
        nextButton.disabled = currentPage === totalPages - 1;
        
        // 显示页面内容
        textContainer.innerHTML = bookPages[currentPage];
        textContainer.scrollTop = 0;
        
        // 添加页面切换动画
        textContainer.classList.add('page-transition');
        setTimeout(() => {
            textContainer.classList.remove('page-transition');
        }, 300);
        
        // 如果页面包含HTML标记，使用句子模式
        if (textContainer.querySelector('.sentence')) {
            // 句子模式 - 为所有句子添加点击事件
            const sentences = textContainer.querySelectorAll('.sentence');
            if (sentences.length > 0) {
                // 高亮第一个句子
                currentSentence = sentences[0];
                currentSentence.classList.add('highlight');
                
                // 为每个句子添加点击事件
                sentences.forEach(sentence => {
                    sentence.addEventListener('click', function() {
                        // 停止当前播放
                        if (isPlaying) {
                            pauseSpeech();
                        }
                        
                        // 移除所有高亮
                        sentences.forEach(s => s.classList.remove('highlight'));
                        
                        // 设置当前句子并高亮
                        currentSentence = this;
                        currentSentence.classList.add('highlight');
                        
                        // 开始从当前句子朗读
                        isPlaying = true;
                        updatePlayButtons();
                        playSpeech(currentSentence.textContent);
                    });
                });
            }
        } else {
            // 段落模式
            bookText = textContainer.innerText;
            textChunks = bookText.split(/(?:\r\n|\r|\n){2,}/).filter(chunk => chunk.trim());
            currentChunk = 0;
            
            // 高亮第一个段落
            highlightCurrentChunk();
            
            // 为每个段落添加点击事件
            const paragraphs = textContainer.querySelectorAll('p');
            paragraphs.forEach((paragraph, index) => {
                paragraph.addEventListener('click', function() {
                    // 停止当前播放
                    if (isPlaying) {
                        pauseSpeech();
                    }
                    
                    // 设置当前段落索引
                    currentChunk = index;
                    
                    // 高亮当前段落
                    highlightCurrentChunk();
                    
                    // 开始从当前段落朗读
                    isPlaying = true;
                    updatePlayButtons();
                    playSpeech(textChunks[currentChunk]);
                });
            });
        }
        
        // 保存阅读进度
        saveProgress();
    }
    
    // 高亮当前段落
    function highlightCurrentChunk() {
        // 移除所有高亮
        const paragraphs = textContainer.querySelectorAll('p');
        paragraphs.forEach(p => p.classList.remove('highlight'));
        
        // 如果有段落，高亮当前段落
        if (paragraphs.length > currentChunk) {
            paragraphs[currentChunk].classList.add('highlight');
            
            // 滚动到当前段落
            paragraphs[currentChunk].scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    // 更新播放按钮状态
    function updatePlayButtons() {
        if (isPlaying) {
            playButton.style.display = 'none';
            pauseButton.style.display = 'inline-block';
        } else {
            playButton.style.display = 'inline-block';
            pauseButton.style.display = 'none';
        }
    }
    
    // 播放按钮点击事件
    playButton.addEventListener('click', function() {
        isPlaying = true;
        updatePlayButtons();
        
        // 检查是使用句子模式还是段落模式
        if (textContainer.querySelector('.sentence')) {
            // 句子模式
            const sentences = textContainer.querySelectorAll('.sentence');
            if (!currentSentence) {
                currentSentence = sentences[0];
            }
            
            // 高亮当前句子
            sentences.forEach(s => s.classList.remove('highlight'));
            currentSentence.classList.add('highlight');
            
            // 滚动到当前句子
            currentSentence.scrollIntoView({ behavior: 'smooth', block: 'center' });
            
            // 播放当前句子
            playSpeech(currentSentence.textContent);
        } else {
            // 段落模式
            highlightCurrentChunk();
            playSpeech(textChunks[currentChunk]);
        }
    });
    
    // 暂停按钮点击事件
    pauseButton.addEventListener('click', function() {
        isPlaying = false;
        updatePlayButtons();
        pauseSpeech();
    });
    
    // 播放下一个块
    function playNextChunk() {
        if (!isPlaying) return;
        
        // 检查是使用句子模式还是段落模式
        if (textContainer.querySelector('.sentence')) {
            // 句子模式
            const sentences = textContainer.querySelectorAll('.sentence');
            const currentIndex = Array.from(sentences).indexOf(currentSentence);
            
            if (currentIndex < sentences.length - 1) {
                // 移动到下一个句子
                currentSentence = sentences[currentIndex + 1];
                
                // 高亮当前句子
                sentences.forEach(s => s.classList.remove('highlight'));
                currentSentence.classList.add('highlight');
                
                // 滚动到当前句子
                currentSentence.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // 播放当前句子
                playSpeech(currentSentence.textContent);
            } else {
                // 如果当前页面已读完，自动翻到下一页
                if (currentPage < totalPages - 1) {
                    displayPage(currentPage + 1);
                    // 自动开始朗读下一页
                    setTimeout(() => {
                        const newSentences = textContainer.querySelectorAll('.sentence');
                        if (newSentences.length > 0) {
                            currentSentence = newSentences[0];
                            newSentences.forEach(s => s.classList.remove('highlight'));
                            currentSentence.classList.add('highlight');
                            currentSentence.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            playSpeech(currentSentence.textContent);
                        }
                    }, 500);
                } else {
                    // 已经是最后一页，停止播放
                    isPlaying = false;
                    updatePlayButtons();
                    currentSentence = null;
                }
            }
        } else {
            // 原来的段落播放逻辑
            currentChunk++;
            if (currentChunk < textChunks.length) {
                highlightCurrentChunk();
                playSpeech(textChunks[currentChunk]);
            } else {
                // 如果当前页面已读完，自动翻到下一页
                if (currentPage < totalPages - 1) {
                    displayPage(currentPage + 1);
                    // 自动开始朗读下一页
                    setTimeout(() => {
                        currentChunk = 0;
                        if (textChunks.length > 0) {
                            highlightCurrentChunk();
                            playSpeech(textChunks[currentChunk]);
                        }
                    }, 500);
                } else {
                    // 已经是最后一页，停止播放
                    isPlaying = false;
                    updatePlayButtons();
                    currentChunk = 0;
                }
            }
        }
    }
    
    // 保存阅读进度
    function saveProgress() {
        // 确保所有必要的参数都存在
        const data = {
            book_id: bookId,
            position: currentPage / Math.max(1, totalPages - 1),  // 避免除以零
            voice_name: voiceSelector.value || 'default',  // 提供默认值
            current_page: currentPage
        };
        
        console.log('保存进度数据:', data);  // 添加调试日志
        
        fetch('/book/api/save-progress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('进度已保存:', data);
        })
        .catch(error => {
            console.error('保存进度失败:', error);
        });
    }
    
    // 添加分页按钮事件监听
    prevButton.addEventListener('click', function() {
        if (currentPage > 0) {
            displayPage(currentPage - 1);
        }
    });
    
    nextButton.addEventListener('click', function() {
        if (currentPage < totalPages - 1) {
            displayPage(currentPage + 1);
        }
    });
    
    // 监听语音选择器变化
    voiceSelector.addEventListener('change', function() {
        saveProgress();
    });
    
    // 监听滚动事件，更新进度条
    textContainer.addEventListener('scroll', function() {
        const scrollPosition = textContainer.scrollTop / (textContainer.scrollHeight - textContainer.clientHeight);
        progressBar.value = scrollPosition * 100;
    });
    
    // 添加CSS样式使段落和句子可点击
    const style = document.createElement('style');
    style.textContent = `
        .text-content p, .sentence {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .text-content p:hover, .sentence:hover {
            background-color: rgba(0, 123, 255, 0.1);
        }
    `;
    document.head.appendChild(style);
    
    // 初始化
    loadBookText();
    
    // 初始化按钮状态
    updatePlayButtons();
    
    // 页面关闭前保存进度
    window.addEventListener('beforeunload', function() {
        saveProgress();
    });
}); 