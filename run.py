#!/usr/bin/env python
"""
Script khởi chạy ứng dụng Flask
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)