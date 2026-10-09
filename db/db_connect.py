# -*- coding: utf-8 -*-
"""
db/db_connect.py —— 数据库连接管理

作用：提供统一的 MySQL 连接获取与关闭工具，供查询层复用。
"""
import pymysql
from config import DB_CONFIG


def get_connection() -> pymysql.connections.Connection:
    """建立并返回一个 MySQL 连接"""
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor,  # 返回字典，便于转 JSON
    )


def mysql_available() -> bool:
    """
    探测 MySQL 是否可用（连接 + 表是否存在）。
    用于决定走 MySQL 查询还是降级为 CSV 演示模式。
    """
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES LIKE 'orders'")
                return cur.fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False
