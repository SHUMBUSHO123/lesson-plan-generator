// ============================================
// WHATSAPP CHAT BOT - Backend Connected Version
// ============================================

(function() {
    console.log('WhatsApp Chat Bot - Starting...');

    // Configuration
    const CHAT_STORAGE_KEY = 'isomoplus_ai_chat_history';
    const CONVERSATION_ID_KEY = 'isomoplus_conversation_id';
    
    let chatHistory = [];
    let conversationId = null;
    let isLoading = false;

    // DOM Elements
    const container = document.getElementById('whatsapp-chat-container');
    const chatBtn = document.getElementById('whatsapp-chat-btn');
    const chatWindow = document.getElementById('whatsapp-chat-window');
    const chatHeader = document.getElementById('whatsapp-chat-header');
    const closeBtn = document.getElementById('whatsapp-close');
    const closeTempBtn = document.getElementById('whatsapp-close-temp');
    const resetPosBtn = document.getElementById('whatsapp-reset-pos');
    const sendBtn = document.getElementById('whatsapp-send');
    const inputField = document.getElementById('whatsapp-input');
    const messagesContainer = document.getElementById('whatsapp-messages');
    const accountStatusText = document.getElementById('account-status-text');
    const accountActionLink = document.getElementById('account-action-link');

    // ========================================
    // HELPER FUNCTIONS
    // ========================================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function getConversationId() {
        let id = localStorage.getItem(CONVERSATION_ID_KEY);
        if (!id) {
            id = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem(CONVERSATION_ID_KEY, id);
        }
        return id;
    }

    // ========================================
    // BACKEND API CALL
    // ========================================
    async function callChatbotAPI(message) {
        try {
            const response = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: conversationId,
                    language: 'en'
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Chatbot API error:', error);
            return {
                success: false,
                response: "⚠️ Service temporarily unavailable. Please refresh and try again."
            };
        }
    }

    // ========================================
    // CHAT WINDOW POSITIONING
    // ========================================
    function positionChatWindow() {
        if (!chatWindow || !container) return;
        
        const btnRect = container.getBoundingClientRect();
        const winH = chatWindow.offsetHeight || 520;
        const winW = 450;
        const vpH = window.innerHeight;
        const vpW = window.innerWidth;
        
        let top = btnRect.top - winH - 15;
        let left = btnRect.left;
        
        if (top < 5) top = 5;
        if (top + winH > vpH - 10) top = vpH - winH - 10;
        if (left + winW > vpW - 10) left = vpW - winW - 10;
        if (left < 10) left = 10;
        
        chatWindow.style.top = top + 'px';
        chatWindow.style.left = left + 'px';
    }

    // ========================================
    // CHAT MANAGEMENT
    // ========================================
    function saveChat() {
        try {
            localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify({
                history: chatHistory,
                timestamp: Date.now()
            }));
        } catch(e) {}
    }

    function loadChat() {
        try {
            const saved = localStorage.getItem(CHAT_STORAGE_KEY);
            if (saved) {
                const data = JSON.parse(saved);
                chatHistory = data.history || [];
                renderMessages();
                return true;
            }
        } catch(e) {}
        return false;
    }

// Helper: convert URLs to clickable links
function urlify(text) {
    var urlRegex = /(https?:\/\/[^\s]+)/g;
    return text.replace(urlRegex, function(url) {
        return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + url + '</a>';
    });
}

function addMessage(type, content, isHtml = false) {
    if (!messagesContainer) return;
    
    const message = {
        id: Date.now() + '_' + Math.random().toString(36).substr(2, 6),
        type: type,
        content: content,
        timestamp: new Date().toISOString()
    };
    chatHistory.push(message);
    if (chatHistory.length > 200) chatHistory = chatHistory.slice(-200);
    saveChat();
    
    const messageDiv = document.createElement('div');
    messageDiv.style.marginBottom = '12px';
    messageDiv.style.display = 'flex';
    messageDiv.style.justifyContent = type === 'user' ? 'flex-end' : 'flex-start';
    
    const bubble = document.createElement('div');
    bubble.style.maxWidth = '85%';
    bubble.style.padding = '10px 14px';
    bubble.style.borderRadius = '12px';
    bubble.style.background = type === 'user' ? '#25D366' : 'white';
    bubble.style.color = type === 'user' ? 'white' : '#111';
    bubble.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
    bubble.style.fontSize = '13px';
    bubble.style.lineHeight = '1.5';
    bubble.style.whiteSpace = 'pre-line';
    
    let displayContent = content;
    if (type === 'bot' && !isHtml) {
        // Convert URLs to clickable links
        displayContent = urlify(content);
    }
    
    if (isHtml) {
        bubble.innerHTML = displayContent;
    } else {
        bubble.innerHTML = displayContent.replace(/\n/g, '<br>');
    }
    
    const timeSpan = document.createElement('div');
    timeSpan.style.fontSize = '10px';
    timeSpan.style.marginTop = '4px';
    timeSpan.style.opacity = '0.6';
    timeSpan.style.textAlign = type === 'user' ? 'right' : 'left';
    timeSpan.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    bubble.appendChild(timeSpan);
    
    messageDiv.appendChild(bubble);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return message;
}
    

function renderMessages() {
    if (!messagesContainer) return;
    messagesContainer.innerHTML = '';
    
    chatHistory.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.style.marginBottom = '12px';
        messageDiv.style.display = 'flex';
        messageDiv.style.justifyContent = msg.type === 'user' ? 'flex-end' : 'flex-start';
        
        const bubble = document.createElement('div');
        bubble.style.maxWidth = '85%';
        bubble.style.padding = '10px 14px';
        bubble.style.borderRadius = '12px';
        bubble.style.background = msg.type === 'user' ? '#25D366' : 'white';
        bubble.style.color = msg.type === 'user' ? 'white' : '#111';
        bubble.style.boxShadow = '0 1px 2px rgba(0,0,0,0.1)';
        bubble.style.fontSize = '13px';
        bubble.style.lineHeight = '1.5';
        bubble.style.whiteSpace = 'pre-line';
        
        let displayContent = msg.content;
        if (msg.type === 'bot') {
            displayContent = urlify(msg.content);
        }
        bubble.innerHTML = displayContent.replace(/\n/g, '<br>');
        
        const timeSpan = document.createElement('div');
        timeSpan.style.fontSize = '10px';
        timeSpan.style.marginTop = '4px';
        timeSpan.style.opacity = '0.6';
        timeSpan.style.textAlign = msg.type === 'user' ? 'right' : 'left';
        timeSpan.textContent = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        bubble.appendChild(timeSpan);
        
        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
    });
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
    
    function showTyping() {
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.style.marginBottom = '12px';
        indicator.style.display = 'flex';
        indicator.style.justifyContent = 'flex-start';
        indicator.innerHTML = `<div style="background: white; padding: 10px 16px; border-radius: 12px; display: flex; gap: 4px;">
            <span style="animation: typing 1.4s infinite">●</span>
            <span style="animation: typing 1.4s infinite 0.2s">●</span>
            <span style="animation: typing 1.4s infinite 0.4s">●</span>
        </div>`;
        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function hideTyping() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }

    // ========================================
    // PROCESS MESSAGE - CALLS BACKEND
    // ========================================
    async function processMessage(message) {
        if (!message || isLoading) return;
        
        addMessage('user', message);
        inputField.value = '';
        
        isLoading = true;
        showTyping();
        
        try {
            const data = await callChatbotAPI(message);
            hideTyping();
            
            if (data.success) {
                addMessage('bot', data.response);
            } else {
                addMessage('bot', data.response || "Sorry, I'm having trouble connecting. Please try again later.");
            }
        } catch (error) {
            console.error('Chat error:', error);
            hideTyping();
            addMessage('bot', "⚠️ Service temporarily unavailable. Please refresh and try again.");
        } finally {
            isLoading = false;
        }
    }

    // ========================================
    // LOAD QUICK REPLIES FROM BACKEND
    // ========================================
    async function loadQuickReplies() {
        try {
            console.log('Loading quick replies from backend...');
            const response = await fetch('/api/quick-replies/');
            
            if (!response.ok) {
                console.error('Failed to load quick replies:', response.status);
                return;
            }
            
            const data = await response.json();
            console.log('Quick replies loaded:', data);
            
            const row1 = document.getElementById('quick-reply-row-1');
            const row2 = document.getElementById('quick-reply-row-2');
            
            if (!row1 || !row2) {
                console.error('Quick reply containers not found!');
                return;
            }
            
            row1.innerHTML = '';
            row2.innerHTML = '';
            
            const row1Replies = data.quick_replies.filter(r => r.row === 1);
            const row2Replies = data.quick_replies.filter(r => r.row === 2);
            
            row1Replies.forEach(reply => {
                const button = document.createElement('button');
                button.className = 'whatsapp-quick-reply';
                button.innerHTML = `${reply.icon} ${reply.text}`;
                button.onclick = () => {
                    if (inputField) {
                        inputField.value = reply.message;
                        processMessage(reply.message);
                    }
                };
                row1.appendChild(button);
                console.log('Added button to row 1:', reply.text);
            });
            
            row2Replies.forEach(reply => {
                const button = document.createElement('button');
                button.className = 'whatsapp-quick-reply';
                button.innerHTML = `${reply.icon} ${reply.text}`;
                button.onclick = () => {
                    if (inputField) {
                        inputField.value = reply.message;
                        processMessage(reply.message);
                    }
                };
                row2.appendChild(button);
                console.log('Added button to row 2:', reply.text);
            });
            
            console.log(`Loaded ${row1Replies.length} quick replies for row 1, ${row2Replies.length} for row 2`);
        } catch (error) {
            console.error('Failed to load quick replies:', error);
        }
    }

    // ========================================
    // UI FUNCTIONS
    // ========================================
    function toggleChat() {
        if (!chatWindow) return;
        
        if (chatWindow.style.display === 'flex' || chatWindow.style.display === 'block') {
            chatWindow.style.display = 'none';
        } else {
            positionChatWindow();
            chatWindow.style.display = 'flex';
            setTimeout(() => {
                if (messagesContainer) {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
            }, 50);
        }
    }

    function hideChat() {
        if (chatWindow) chatWindow.style.display = 'none';
    }

    // ========================================
    // CHECK ACCOUNT STATUS
    // ========================================
    async function checkAccountStatus() {
        try {
            const response = await fetch('/api/user/status/', {
                credentials: 'include',
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (accountStatusText) {
                    if (data.is_premium) {
                        accountStatusText.innerHTML = `✅ Premium Active • ${data.username || 'User'}`;
                        accountStatusText.style.color = '#4CAF50';
                        if (accountActionLink) {
                            accountActionLink.textContent = 'My Dashboard';
                            accountActionLink.href = '/dashboard/';
                        }
                    } else if (data.is_authenticated) {
                        accountStatusText.innerHTML = `🆓 Free Plan • ${data.username || 'User'}`;
                        accountStatusText.style.color = '#ff9800';
                        if (accountActionLink) {
                            accountActionLink.textContent = 'Upgrade Now';
                            accountActionLink.href = '/pricing/';
                        }
                    }
                }
            } else {
                if (accountStatusText) {
                    accountStatusText.innerHTML = '🔓 Not Registered • Create free account';
                    accountStatusText.style.color = '#f44336';
                    if (accountActionLink) {
                        accountActionLink.textContent = 'Sign Up Free →';
                        accountActionLink.href = '/register/';
                    }
                }
            }
        } catch (err) {
            console.warn('Account check failed:', err);
            if (accountStatusText && window.isAuthenticated !== true) {
                accountStatusText.innerHTML = '🔓 Not Registered • Create free account';
                accountStatusText.style.color = '#f44336';
                if (accountActionLink) {
                    accountActionLink.textContent = 'Sign Up Free →';
                    accountActionLink.href = '/register/';
                }
            }
        }
    }

    // ========================================
    // EVENT LISTENERS
    // ========================================
    function setup() {
        conversationId = getConversationId();
        
        // Load chat history or add welcome message
        if (!loadChat() || chatHistory.length === 0) {
            addMessage('bot', "👋 Hi! I'm IsomoPlus AI Assistant!\n\nI can help you generate CBC lesson plans, answer questions about pricing, guide you through features, and troubleshoot issues.\n\nWhat would you like to know?");
        }
        
        // Button click
        if (chatBtn) {
            chatBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                toggleChat();
            });
        }
        
        // Close buttons
        if (closeBtn) closeBtn.addEventListener('click', hideChat);
        if (closeTempBtn) closeTempBtn.addEventListener('click', hideChat);
        
        // Send message
        if (sendBtn && inputField) {
            sendBtn.addEventListener('click', function() {
                const msg = inputField.value.trim();
                if (msg) processMessage(msg);
            });
            
            inputField.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const msg = inputField.value.trim();
                    if (msg) processMessage(msg);
                }
            });
        }
        
        // Reset position
        if (resetPosBtn) {
            resetPosBtn.addEventListener('click', function() {
                if (container) {
                    container.style.left = '20px';
                    container.style.bottom = '20px';
                    showToast('Position reset!', 2000);
                }
            });
        }
        
        // Check account status
        checkAccountStatus();
        
        // Load quick replies from backend
        loadQuickReplies();
        
        // Reposition on resize
        window.addEventListener('resize', () => {
            if (chatWindow && chatWindow.style.display !== 'none') {
                positionChatWindow();
            }
        });
    }
    
    function showToast(message, duration) {
        let toast = document.getElementById('whatsapp-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'whatsapp-toast';
            toast.style.cssText = 'position:fixed; bottom:100px; left:90px; background:#333; color:white; padding:8px 16px; border-radius:8px; font-size:12px; z-index:100002; opacity:0; transition:opacity 0.3s ease;';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.style.opacity = '1';
        setTimeout(() => toast.style.opacity = '0', duration);
    }

    // Start
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setup);
    } else {
        setup();
    }

})();