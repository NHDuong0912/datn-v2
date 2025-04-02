// Xử lý form đăng nhập
document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => {
        if (!response.ok) {
            throw response;
        }
        return response.json();
    })
    .then(data => {
        // Store the JWT token
        localStorage.setItem('auth_token', data.access_token);
        
        // Redirect to dashboard
        window.location.href = '/dashboard/';
    })
    .catch(error => {
        if (error.json) {
            error.json().then(errorData => {
                const errorElement = document.getElementById('error-message');
                errorElement.textContent = errorData.msg || 'Login failed';
            });
        } else {
            console.error('Error:', error);
        }
    });
});
