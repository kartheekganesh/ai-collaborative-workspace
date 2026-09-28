const Auth = {
    setToken(token) {
        localStorage.setItem('access_token', token);
    },
    getToken() {
        return localStorage.getItem('access_token');
    },
    logout() {
        localStorage.removeItem('access_token');
        window.location.reload();
    },
    isAuthenticated() {
        return !!this.getToken();
    }
};

