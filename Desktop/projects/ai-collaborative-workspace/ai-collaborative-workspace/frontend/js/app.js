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
    function selectDocument(doc) {
        currentDocument = doc;
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
    }

    // 6. Unified Input Event Listener (Broadcast via WS + Debounced Persistence to DB)
    docContentEditor.addEventListener('input', () => {
        if (!currentDocument || !currentWorkspace) return;

        // Broadcast immediate live update over WebSocket
        if (typeof wsClient !== 'undefined') {
            wsClient.sendContentChange(docContentEditor.value);
        }

        // Debounce persistent REST API update to PostgreSQL database
        saveStatusEl.textContent = 'Saving changes...';
        clearTimeout(saveTimeout);
        saveTimeout = setTimeout(async () => {
            try {
                await APIClient.updateDocument(currentWorkspace.id, currentDocument.id, {
                    content: docContentEditor.value
                });
                saveStatusEl.textContent = 'All changes saved to DB';
            } catch (err) {
                saveStatusEl.textContent = 'Error saving document';
            }
        }, 1000); // Debounce for 1 second
    });

    // 7. Action Handlers: Create Workspace & Document
    btnCreateWorkspace.addEventListener('click', async () => {
        const name = prompt('Enter Workspace Name:');
        if (name) {
            await APIClient.createWorkspace(name);
            await loadWorkspaces();
        }
    });

    btnCreateDoc.addEventListener('click', async () => {
        if (!currentWorkspace) return;
        const title = prompt('Enter Document Title:');
        if (title) {
            const newDoc = await APIClient.createDocument(currentWorkspace.id, title);
            await loadDocuments();
            selectDocument(newDoc);
        }
    });

    // Initial Load
    await loadWorkspaces();
});
