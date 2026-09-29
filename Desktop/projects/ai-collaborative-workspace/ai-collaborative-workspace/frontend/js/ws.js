class WebSocketClient {
    constructor() {
        this.socket = null;
        this.currentDocId = null;
        this.callbacks = {};
    }

    connect(documentId, token) {
        // Close existing connection if switching documents
        if (this.socket) {
            this.disconnect();
        }

        this.currentDocId = documentId;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/documents/${documentId}?token=${token}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log(`[WS] Connected to document room: ${documentId}`);
            this.trigger('connect', null);
        };

        this.socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.trigger(message.type, message);
            } catch (err) {
                console.error('[WS] Error parsing message:', err);
            }
        };

        this.socket.onclose = () => {
            console.log('[WS] Connection closed');
            this.trigger('disconnect', null);
        };

        this.socket.onerror = (err) => {
            console.error('[WS] Error:', err);
        };
    }

    sendContentChange(content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'content_change',
                content: content
            }));
        }
    }

    on(event, callback) {
        this.callbacks[event] = callback;
    }

    trigger(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event](data);
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

const wsClient = new WebSocketClient();