document.addEventListener('DOMContentLoaded', async () => {
    // Application State
    let currentWorkspace = null;
    let currentDocument = null;
    let saveTimeout = null;

    // DOM Elements
    const userNameEl = document.getElementById('user-name');
    const workspaceListEl = document.getElementById('workspace-list');
    const documentListEl = document.getElementById('document-list');
    const currentWorkspaceTitle = document.getElementById('current-workspace-title');
    const docTitleInput = document.getElementById('document-title-input');
    const docContentEditor = document.getElementById('document-content-editor');
    const saveStatusEl = document.getElementById('save-status');
    const btnCreateWorkspace = document.getElementById('btn-create-workspace');
    const btnCreateDoc = document.getElementById('btn-create-doc');

    // 1. Load Authenticated User Profile
    try {
        const user = await APIClient.getCurrentUser();
        userNameEl.textContent = user.full_name || user.email;
    } catch (err) {
        saveStatusEl.textContent = 'Failed to load user profile';
    }

    // 2. Render Workspaces
    async function loadWorkspaces() {
        workspaceListEl.innerHTML = '';
        try {
            const workspaces = await APIClient.getWorkspaces();
            workspaces.forEach(ws => {
                const li = document.createElement('li');
                li.textContent = ws.name;
                li.classList.toggle('active', currentWorkspace?.id === ws.id);
                li.addEventListener('click', () => selectWorkspace(ws));
                workspaceListEl.appendChild(li);
            });
        } catch (err) {
            console.error('Error fetching workspaces:', err);
        }
    }

    // 3. Select Workspace & Fetch Documents
    async function selectWorkspace(workspace) {
        if (currentWorkspace?.id !== workspace.id) {
            await flushPendingSave();
            currentDocument = null;
            window.currentDocumentId = null;
            docTitleInput.value = '';
            docTitleInput.readOnly = true;
            docContentEditor.value = '';
            docContentEditor.disabled = true;
            if (typeof wsClient !== 'undefined') {
                wsClient.disconnect();
            }
            activeCollaborators.clear();
            renderPresenceBar();
        }
        currentWorkspace = workspace;
        currentWorkspaceTitle.textContent = workspace.name;
        btnCreateDoc.disabled = false;
        await loadWorkspaces(); // Refresh active state
        await loadDocuments();
    }

    async function loadDocuments() {
        if (!currentWorkspace) return;
        documentListEl.innerHTML = '';
        try {
            const docs = await APIClient.getDocuments(currentWorkspace.id);
            docs.forEach(doc => {
                const li = document.createElement('li');
                li.textContent = doc.title;
                li.classList.toggle('active', currentDocument?.id === doc.id);
                li.addEventListener('click', () => selectDocument(doc));
                documentListEl.appendChild(li);
            });
        } catch (err) {
            console.error('Error fetching documents:', err);
        }
    }

    // 4. Select Document & Connect WebSocket
    async function selectDocument(doc) {
        await flushPendingSave();
        currentDocument = doc;
        window.currentDocumentId = doc.id;
        activeCollaborators.clear();
        renderPresenceBar();
        docTitleInput.value = doc.title;
        docTitleInput.readOnly = false;
        docContentEditor.value = doc.content || '';
        docContentEditor.disabled = false;
        saveStatusEl.textContent = 'Document loaded';

        // Establish WebSocket connection for live editing
        const token = Auth.getToken();
        if (token && typeof wsClient !== 'undefined') {
            wsClient.connect(doc.id, token);
        }
    }

    // 5. Listen for Live Content Updates from Connected Peers
    if (typeof wsClient !== 'undefined') {
        wsClient.on('content_change', (data) => {
            // Preserve user's local cursor position before updating text
            const selectionStart = docContentEditor.selectionStart;
            const selectionEnd = docContentEditor.selectionEnd;

            // Apply remote content update
            docContentEditor.value = data.content;

            // Restore cursor position
            docContentEditor.setSelectionRange(selectionStart, selectionEnd);
            saveStatusEl.textContent = 'Synced live edit';
        });

        wsClient.on('user_joined', (data) => {
            activeCollaborators.set(data.user_id, { email: data.email });
            renderPresenceBar();
            saveStatusEl.textContent = `${data.email} joined`;
        });

        wsClient.on('user_left', (data) => {
            activeCollaborators.delete(data.user_id);
            renderPresenceBar();
            saveStatusEl.textContent = `${data.email} left`;
        });
    }

    const activeCollaborators = new Map();
    const presenceBar = document.getElementById('presence-bar');

    function renderPresenceBar() {
        presenceBar.innerHTML = '';
        activeCollaborators.forEach((user) => {
            const badge = document.createElement('div');
            badge.className = 'presence-badge';
            badge.title = user.email;
            badge.textContent = user.email.charAt(0).toUpperCase();
            presenceBar.appendChild(badge);
        });
    }

    function queueDocumentSave() {
        if (!currentDocument || !currentWorkspace) return;

        saveStatusEl.textContent = 'Saving changes...';
        clearTimeout(saveTimeout);
        const workspaceId = currentWorkspace.id;
        const documentId = currentDocument.id;
        const content = docContentEditor.value;
        const title = docTitleInput.value;
        saveTimeout = setTimeout(async () => {
            saveTimeout = null;
            try {
                await APIClient.updateDocument(workspaceId, documentId, {
                    title,
                    content
                });
                if (currentDocument?.id === documentId) {
                    saveStatusEl.textContent = 'All changes saved to DB';
                }
            } catch (err) {
                if (currentDocument?.id === documentId) {
                    saveStatusEl.textContent = 'Error saving document';
                }
            }
        }, 1000); // Debounce for 1 second
    }

    async function flushPendingSave() {
        if (!saveTimeout || !currentDocument || !currentWorkspace) return;
        clearTimeout(saveTimeout);
        saveTimeout = null;
        try {
            await APIClient.updateDocument(currentWorkspace.id, currentDocument.id, {
                title: docTitleInput.value,
                content: docContentEditor.value
            });
        } catch (err) {
            saveStatusEl.textContent = 'Error saving document';
        }
    }

    // Broadcast content immediately and persist document edits after the user pauses.
    docContentEditor.addEventListener('input', () => {
        if (!currentDocument || !currentWorkspace) return;
        if (typeof wsClient !== 'undefined') {
            wsClient.sendContentChange(docContentEditor.value);
        }
        queueDocumentSave();
    });
    docTitleInput.addEventListener('input', queueDocumentSave);

    // 7. Action Handlers: Create Workspace & Document
    btnCreateWorkspace.addEventListener('click', async () => {
        const name = prompt('Enter Workspace Name:');
        if (!name?.trim()) return;

        try {
            const workspace = await APIClient.createWorkspace(name.trim());
            await selectWorkspace(workspace);
            saveStatusEl.textContent = 'Workspace created';
        } catch (err) {
            console.error('Error creating workspace:', err);
            saveStatusEl.textContent = `Unable to create workspace: ${err.message}`;
        }
    });

    btnCreateDoc.addEventListener('click', async () => {
        if (!currentWorkspace) return;
        const title = prompt('Enter Document Title:');
        if (!title?.trim()) return;

        try {
            const newDoc = await APIClient.createDocument(currentWorkspace.id, title.trim());
            await loadDocuments();
            await selectDocument(newDoc);
        } catch (err) {
            console.error('Error creating document:', err);
            saveStatusEl.textContent = `Unable to create document: ${err.message}`;
        }
    });

    function handleCursorUpdate() {
        if (!currentDocument || typeof wsClient === 'undefined') return;
        wsClient.sendCursorMove(docContentEditor.selectionStart);
    }

    docContentEditor.addEventListener('keyup', handleCursorUpdate);
    docContentEditor.addEventListener('click', handleCursorUpdate);

    // Initial Load
    await loadWorkspaces();
});