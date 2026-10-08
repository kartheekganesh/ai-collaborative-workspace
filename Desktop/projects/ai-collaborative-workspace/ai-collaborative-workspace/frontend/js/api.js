const API_BASE_URL = '/api/v1';

class APIClient {
    static getAuthHeader() {
        const token = localStorage.getItem('access_token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    }

    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...this.getAuthHeader(),
            ...options.headers
        };

        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            // Handle expired or missing token
            if (!window.location.pathname.endsWith('/login.html')) {
                window.location.href = '/static/login.html';
            }
            return;
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'API Request Failed');
        }

        return response.json();
    }

    // Auth & User
    static getCurrentUser() { return this.request('/auth/me'); }

    // Workspaces
    static getWorkspaces() { return this.request('/workspaces'); }
    static createWorkspace(name) {
        return this.request('/workspaces', {
            method: 'POST',
            body: JSON.stringify({ name })
        });
    }

    // Documents
    static getDocuments(workspaceId) {
        return this.request(`/workspaces/${workspaceId}/documents`);
    }
    static createDocument(workspaceId, title) {
        return this.request(`/workspaces/${workspaceId}/documents`, {
            method: 'POST',
            body: JSON.stringify({ title, content: '' })
        });
    }
    static updateDocument(workspaceId, docId, data) {
        return this.request(`/workspaces/${workspaceId}/documents/${docId}`, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    }
}