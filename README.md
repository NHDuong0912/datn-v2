# Flask Project Template

Đây là một template dự án Flask với cấu trúc tối ưu cho các dự án vừa và nhỏ.

## Cấu trúc thư mục

```
├── app/
│   ├── api/            # API endpoints
│   ├── auth/           # Xác thực và phân quyền
│   ├── dashboard/      # Dashboard UI và routes
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── utils/          # Utility functions
│   ├── templates/      # HTML templates
│   └── static/         # Static files
├── config/             # Configuration files
├── migrations/         # Database migrations
├── tests/              # Test files
├── .env                # Environment variables
├── manage.py           # Script quản lý dự án
├── requirements.txt    # Project dependencies
└── run.py              # Application entry point
```

## Cài đặt

1. Tạo môi trường ảo:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Tạo file .env và cập nhật các biến môi trường:
```bash
cp .env.example .env
```

4. Khởi tạo database:
```bash
python manage.py init-db
```

5. Tạo tài khoản admin (tùy chọn):
```bash
python manage.py create-admin <username> <password> <email>
```

## Chạy ứng dụng

```bash
python run.py
```

Ứng dụng sẽ chạy tại http://localhost:5000

## Quản lý dự án

Dự án sử dụng file `manage.py` để quản lý các tác vụ thường xuyên:

```bash
# Khởi tạo database
python manage.py init-db

# Tạo tài khoản admin
python manage.py create-admin <username> <password> <email>

# Liệt kê tất cả người dùng
python manage.py list-users
```

## API Endpoints

- `GET /api/health`: Kiểm tra trạng thái API
- `GET /api/nodes`: Lấy danh sách các nodes
- `POST /api/nodes`: Tạo node mới
- `GET /api/nodes/<id>`: Lấy thông tin chi tiết của một node
- `PUT /api/nodes/<id>`: Cập nhật thông tin node
- `DELETE /api/nodes/<id>`: Xoá node

## Auth Endpoints

- `GET /auth/login`: Hiển thị form đăng nhập
- `POST /auth/login`: Xử lý đăng nhập
- `POST /auth/register`: Đăng ký tài khoản mới
- `GET /auth/profile`: Xem thông tin tài khoản
- `PUT /auth/profile`: Cập nhật thông tin tài khoản

## Testing

```bash
pytest
```

## Cấu trúc dự án

Dự án sử dụng:
- Factory Pattern cho việc khởi tạo ứng dụng
- Blueprint cho việc tổ chức routes
- SQLAlchemy cho ORM
- Flask-JWT-Extended cho authentication
- Flask-Migrate cho database migrations 