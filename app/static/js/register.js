// Xử lý form đăng ký
document.getElementById('register-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const errorElement = document.getElementById('register-error-message');
    errorElement.classList.add('d-none'); // Ẩn thông báo lỗi cũ
    
    // Lấy giá trị input và trim() để loại bỏ khoảng trắng
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm-password').value;
    
    // Kiểm tra các trường bắt buộc
    if (!username || !email || !password || !confirmPassword) {
        showError('Vui lòng điền đầy đủ thông tin');
        return;
    }

    // Kiểm tra định dạng email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('Email không hợp lệ');
        return;
    }

    // Kiểm tra độ dài mật khẩu
    if (password.length < 6) {
        showError('Mật khẩu phải có ít nhất 6 ký tự');
        return;
    }
    
    // Kiểm tra mật khẩu nhập lại
    if (password !== confirmPassword) {
        showError('Mật khẩu xác nhận không khớp');
        return;
    }
    
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username,
                email,
                password
            })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.msg || 'Đăng ký thất bại');
        }

        // Đăng ký thành công
        alert('Đăng ký thành công! Vui lòng đăng nhập.');
        window.location.href = '/auth/login';
        
    } catch (error) {
        showError(error.message || 'Đã có lỗi xảy ra. Vui lòng thử lại.');
    }
});

// Hàm hiển thị thông báo lỗi
function showError(message) {
    const errorElement = document.getElementById('register-error-message');
    errorElement.textContent = message;
}


