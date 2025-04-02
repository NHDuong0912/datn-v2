from flask import request, jsonify, render_template, make_response, Blueprint
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_login import login_user, logout_user
from app.models import User
from app import db
from app.models.models import AccessLog
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        # Hiển thị trang đăng nhập
        return render_template('register.html')
    
    data = request.get_json()
    
    # Kiểm tra xem user đã tồn tại chưa
    user = User.query.filter_by(username=data.get('username')).first()
    if user:
        return jsonify({"msg": "Username already exists"}), 400
    
    # Tạo user mới
    new_user = User(
        username=data.get('username'),
        email=data.get('email'),
        role=data.get('role', 'user')
    )
    new_user.password = generate_password_hash(data.get('password'))
    
    # Lưu user vào database
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST request (login attempt)
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and user.check_password(data.get('password')):
        login_user(user)
        access_token = create_access_token(identity=user.id)
        
        # Log the login action
        try:
            AccessLog.log_access(user.id, "User logged in")
        except Exception as e:
            print(f"Failed to log access: {str(e)}")
        
        return jsonify({'access_token': access_token}), 200
    
    return jsonify({'msg': 'Invalid username or password'}), 401

@auth.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    # Lấy identity từ JWT
    current_user_id = get_jwt_identity()
    
    # Tìm user trong database
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Trả về thông tin user (không bao gồm password)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    }), 200

@auth.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    # Lấy identity từ JWT
    current_user_id = get_jwt_identity()
    
    # Tìm user trong database
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    # Cập nhật thông tin user
    data = request.get_json()
    if 'email' in data:
        user.email = data['email']
    if 'password' in data:
        user.password = generate_password_hash(data['password'])
    
    db.session.commit()
    
    return jsonify({"msg": "Profile updated successfully"}), 200

@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user_id = get_jwt_identity()
    
    # Log the logout action
    try:
        AccessLog.log_access(current_user_id, "User logged out")
    except Exception as e:
        print(f"Failed to log access: {str(e)}")
    
    logout_user()
    return jsonify({'msg': 'User logged out successfully'}), 200