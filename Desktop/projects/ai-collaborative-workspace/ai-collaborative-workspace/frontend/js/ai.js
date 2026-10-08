const AIAssistant = {
    async askQuestion(documentId, question, token, onChunk) {
        const url = `/api/v1/ai/documents/${encodeURIComponent(documentId)}/ask/stream?prompt=${encodeURIComponent(question)}`;
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Unable to get an AI response.');
        }
        if (!response.body) {
            throw new Error('The browser does not support streamed responses.');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finished = false;

        const processEvent = (event) => {
            const data = event
                .split(/\r?\n/)
                .filter((line) => line.startsWith('data:'))
                .map((line) => line.slice(5).replace(/^ /, ''))
                .join('\n');
            if (!data) return;
            if (data === '[DONE]') {
                finished = true;
                return;
            }
            if (data.startsWith('[ERROR]')) {
                throw new Error(data.slice(7).trim() || 'The AI provider failed.');
            }
            onChunk(data);
        };

        while (!finished) {
            const { done, value } = await reader.read();
            buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

            const events = buffer.split(/\r?\n\r?\n/);
            buffer = events.pop() || '';
            events.forEach(processEvent);
            if (done) {
                if (buffer.trim()) processEvent(buffer);
                break;
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('ai-chat-form');
    const input = document.getElementById('ai-prompt-input');
    const history = document.getElementById('ai-chat-history');
    const sendButton = document.getElementById('ai-send-btn');
    const sidebar = document.getElementById('ai-sidebar');
    const toggleButton = document.getElementById('ai-sidebar-toggle');
    const clearButton = document.getElementById('clear-history-btn');

    if (!form || !input || !history || !sendButton) return;

    const appendMessage = (className, text = '') => {
        const message = document.createElement('div');
        message.className = `chat-message ${className}`;
        message.textContent = text;
        history.appendChild(message);
        history.scrollTop = history.scrollHeight;
        return message;
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const question = input.value.trim();
        const token = Auth.getToken();
        const documentId = window.currentDocumentId;
        if (!question || !token) return;
        if (!documentId) {
            appendMessage('assistant', 'Select a document before asking a question.');
            return;
        }

        appendMessage('user', question);
        const answer = appendMessage('assistant');
        input.value = '';
        sendButton.disabled = true;

        try {
            await AIAssistant.askQuestion(documentId, question, token, (chunk) => {
                answer.textContent += chunk;
                history.scrollTop = history.scrollHeight;
            });
        } catch (error) {
            answer.textContent = error.message || 'Unable to get an AI response.';
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    });

    toggleButton?.addEventListener('click', () => {
        sidebar?.classList.toggle('collapsed');
    });

    clearButton?.addEventListener('click', () => {
        history.replaceChildren();
    });
});
