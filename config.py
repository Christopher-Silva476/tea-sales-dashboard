# -*- coding: utf-8 -*-
"""
config.py —— 全局配置
作用：集中管理 MySQL 连接参数与文件路径，供各脚本 / Flask 应用统一引用。
注意：请将 password 改为你本机 MySQL 的 root 密码。
"""
import os

# MySQL 连接配置
DB_CONFIG = {
    "host": "localhost",        # MySQL 主机
    "port": 3306,               # MySQL 端口
    "user": "root",             # 用户名
    "password": "your_password",  # TODO: 修改为你的 MySQL 密码
    "database": "tea_sales",    # 数据库名
    "charset": "utf8mb4",
}

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据文件路径
RAW_CSV = os.path.join(BASE_DIR, "data", "raw_tea_orders.csv")          # 原始脏数据
CLEANED_CSV = os.path.join(BASE_DIR, "data", "cleaned_tea_orders.csv")  # 清洗后数据
