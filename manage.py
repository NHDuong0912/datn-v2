#!/usr/bin/env python
"""
Script quản lý các tác vụ chung của dự án
"""
import click
import sys
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
from flask.cli import FlaskGroup

app = create_app()
cli = FlaskGroup(app)

@cli.command("init-db")
def init_db():
    """Khởi tạo database"""
    from migrations.manage import init_db
    init_db()
    click.echo("Database đã được khởi tạo")

@cli.command("create-admin")
@click.argument("username")
@click.argument("password")
@click.argument("email")
def create_admin(username, password, email):
    """Tạo tài khoản admin"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            click.echo(f"Người dùng {username} đã tồn tại")
            return
        
        new_user = User(
            username=username,
            email=email,
            role="admin",
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        click.echo(f"Tài khoản admin {username} đã được tạo")

@cli.command("list-users")
def list_users():
    """Liệt kê tất cả người dùng"""
    with app.app_context():
        users = User.query.all()
        if not users:
            click.echo("Chưa có người dùng nào")
            return
        
        click.echo("Danh sách người dùng:")
        for user in users:
            click.echo(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}")

if __name__ == "__main__":
    cli() 