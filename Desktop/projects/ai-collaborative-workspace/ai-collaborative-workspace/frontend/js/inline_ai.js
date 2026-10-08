const InlineAIToolbar = {
    init() {
        this.editor = document.getElementById('document-content-editor');
        if (!this.editor) return;

        this.toolbar = document.createElement('div');
        this.toolbar.className = 'inline-ai-toolbar hidden';
        this.toolbar.style.position = 'fixed';
        this.toolbar.setAttribute('role', 'toolbar');
        this.toolbar.setAttribute('aria-label', 'AI text tools');

        [
            ['rephrase', 'Rephrase'],
            ['summarize', 'Summarize'],
            ['fix_grammar', 'Fix grammar']
        ].forEach(([action, label]) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = label;
            button.addEventListener('mousedown', (event) => event.preventDefault());
            button.addEventListener('click', () => this.executeAction(action));
            this.toolbar.appendChild(button);
        });

        document.body.appendChild(this.toolbar);
        this.editor.addEventListener('select', () => this.handleSelection());
        this.editor.addEventListener('mouseup', () => this.handleSelection());
        this.editor.addEventListener('keyup', () => this.handleSelection());
        document.addEventListener('mousedown', (event) => {
            if (!this.toolbar.contains(event.target) && event.target !== this.editor) {
                this.hideToolbar();
            }
        });
    },

    handleSelection() {
        const start = this.editor.selectionStart;
        const end = this.editor.selectionEnd;
        if (end - start < 5 || !this.editor.value.slice(start, end).trim()) {
            this.hideToolbar();
            return;
        }

        const bounds = this.editor.getBoundingClientRect();
        this.toolbar.style.top = `${Math.max(8, bounds.top - 44)}px`;
        this.toolbar.style.left = `${bounds.left + Math.min(bounds.width - 240, 12)}px`;
        this.toolbar.classList.remove('hidden');
    },

    hideToolbar() {
        this.toolbar?.classList.add('hidden');
    },

    async executeAction(action) {
        const start = this.editor.selectionStart;
        const end = this.editor.selectionEnd;
        const selectedText = this.editor.value.slice(start, end);
        if (!selectedText.trim()) return;

        try {
            const response = await fetch('/api/v1/ai/transform', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...APIClient.getAuthHeader()
                },
                body: JSON.stringify({ action, text: selectedText })
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.detail || 'Unable to transform the selected text.');
            }

            const before = this.editor.value.slice(0, start);
            const after = this.editor.value.slice(end);
            this.editor.value = `${before}${data.transformed_text}${after}`;
            this.editor.focus();
            this.editor.setSelectionRange(
                start,
                start + data.transformed_text.length
            );
            this.editor.dispatchEvent(new Event('input', { bubbles: true }));
            this.hideToolbar();
        } catch (error) {
            const saveStatus = document.getElementById('save-status');
            if (saveStatus) saveStatus.textContent = error.message;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => InlineAIToolbar.init());
