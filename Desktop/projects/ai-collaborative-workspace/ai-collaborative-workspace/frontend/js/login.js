const authForm = document.getElementById('auth-form');
const authTitle = document.getElementById('auth-title');
const authDescription = document.getElementById('auth-description');
const nameField = document.getElementById('name-field');
const submitButton = document.getElementById('submit-button');
const toggleModeButton = document.getElementById('toggle-mode');
const errorMessage = document.getElementById('auth-error');
let isRegistering = false;

toggleModeButton.addEventListener('click', () => {
    isRegistering = !isRegistering;
    nameField.hidden = !isRegistering;
    nameField.querySelector('input').required = isRegistering;
    authTitle.textContent = isRegistering ? 'Create account' : 'Sign in';
    authDescription.textContent = isRegistering
        ? 'Create an account to start collaborating.'
        : 'Sign in to open your collaborative workspace.';
    submitButton.textContent = isRegistering ? 'Create account' : 'Sign in';
    toggleModeButton.textContent = isRegistering ? 'Already have an account? Sign in' : 'Create an account';
    errorMessage.textContent = '';
});

async function signIn(email, password) {
    const form = new URLSearchParams({ username: email, password });
    const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || 'Sign in failed.');
    }

    localStorage.setItem('access_token', data.access_token);
    window.location.assign('/');
}

authForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorMessage.textContent = '';
    submitButton.disabled = true;

    const formData = new FormData(authForm);
    const email = formData.get('email').trim();
    const password = formData.get('password');

    try {
        if (isRegistering) {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    full_name: formData.get('full_name').trim()
                })
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Account creation failed.');
            }
        }

        await signIn(email, password);
    } catch (error) {
        errorMessage.textContent = error.message || 'Unable to connect to the backend.';
    } finally {
        submitButton.disabled = false;
    }
});
