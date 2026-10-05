// frontend/js/inline_ai.js
const InlineAIToolbar = {
    init() {
        this.toolbar = document.getElementById('inline-ai-toolbar');
        this.editor = document.getElementById('editor');

        if (!this.editor) return;

        // Listen for selection changes inside the document editor
        document.addEventListener('selectionchange', () => this.handleSelection());
    },

    handleSelection() {
        const selection = window.getSelection();
        const selectedText = selection.toString().trim();

        if (!selectedText || selectedText.length < 5) {
            this.hideToolbar();
            return;
        }

        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        // Position floating toolbar above the selected text
        this.toolbar.style.top = `${rect.top + window.scrollY - 45}px`;
        this.toolbar.style.left = `${rect.left + window.scrollX}px`;
        this.toolbar.classList.remove('hidden');
    },

    hideToolbar() {
        if (this.toolbar) {
            this.toolbar.classList.add('hidden');
        }
    },

    async executeAction(actionType) {
        const selectedText = window.getSelection().toString();
        if (!selectedText) return;

        // Route selection to backend inline AI endpoint
        const response = await fetch('/api/v1/ai/transform', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ action: actionType, text: selectedText })
        });

        const data = await response.json();
        if (data.transformed_text) {
            this.replaceSelectedText(data.transformed_text);
        }
        this.hideToolbar();
    },

    replaceSelectedText(newText) {
        const selection = window.getSelection();
        if (!selection.rangeCount) return;
        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(document.createTextNode(newText));
    }
};

document.addEventListener('DOMContentLoaded', () => InlineAIToolbar.init());