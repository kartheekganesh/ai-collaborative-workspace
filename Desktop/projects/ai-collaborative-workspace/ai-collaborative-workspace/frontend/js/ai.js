// frontend/js/ai.js
const AIAssistant = {
    async askQuestion(documentId, question, token) {
        const outputElement = document.getElementById('ai-response-content');
        outputElement.innerHTML = '<em>Thinking...</em>';

        const url = `/api/v1/ai/documents/${documentId}/ask/stream?prompt=${encodeURIComponent(question)}`;

        try {
            const response = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            outputElement.innerText = ''; // Clear loading text

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const tokenText = line.replace('data: ', '');
                        if (tokenText === '[DONE]') break;
                        outputElement.innerText += tokenText;
                    }
                }
            }
        } catch (err) {
            outputElement.innerText = 'Error streaming response from AI assistant.';
            console.error(err);
        }
    }
};