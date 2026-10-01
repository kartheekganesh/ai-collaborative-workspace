class WebSocketClient {
    constructor() {
        this.socket = null;
        this.currentDocId = null;
        this.token = null;
        this.callbacks = {};
        
        // Reconnection State
        this.reconnectTimer = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.baseReconnectDelay = 1000; // 1 second base delay
        this.isIntentionalDisconnect = false;
    }

    connect(documentId, token) {
        // Reset flag and state for new intentional connection
        this.isIntentionalDisconnect = false;
        
        // Close existing connection cleanly if switching documents
        if (this.socket) {
            this.disconnect();
        }

        this.currentDocId = documentId;
        this.token = token;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/documents/${documentId}?token=${token}`;

        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log(`[WS] Connected to document room: ${documentId}`);
            this.reconnectAttempts = 0; // Reset reconnection counter on success
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }
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

        this.socket.onclose = (event) => {
            console.log('[WS] Connection closed', event.code, event.reason);
            this.trigger('disconnect', null);

            // Attempt auto-reconnect only if disconnect wasn't explicit (e.g. clean user logout or document switch)
            if (!this.isIntentionalDisconnect) {
                this.scheduleReconnect();
            }
        };

        this.socket.onerror = (err) => {
            console.error('[WS] Error encountered:', err);
            // Browser handles socket closing automatically on error, triggering `onclose`
        };
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('[WS] Max reconnect attempts reached. Giving up.');
            this.trigger('reconnect_failed', null);
            return;
        }

        // Exponential backoff delay calculation: 1s, 2s, 4s, 8s, 16s...
        const delay = this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;

        console.log(`[WS] Attempting reconnect ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms...`);
        this.trigger('reconnecting', { attempt: this.reconnectAttempts, delay });

        this.reconnectTimer = setTimeout(() => {
            if (this.currentDocId && this.token) {
                this.connect(this.currentDocId, this.token);
            }
        }, delay);
    }

    sendContentChange(content) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'content_change',
                content: content
            }));
        } else {
            console.warn('[WS] Cannot send content change: Socket is not OPEN');
        }
    }

    sendCursorMove(position) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'cursor_move',
                position: position
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
        this.isIntentionalDisconnect = true;
        
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

const wsClient = new WebSocketClient();