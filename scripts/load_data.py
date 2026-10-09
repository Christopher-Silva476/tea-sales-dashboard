# -*- coding: utf-8 -*-
"""
scripts/load_data.py —— 将清洗后的订单数据批量导入 MySQL orders 表

作用：
  1. 读取 data/cleaned_tea_orders.csv
  2. 用 pymysql executemany 批量插入 orders 表（避免 LOAD DATA 的 secure_file_priv 权限限制）
  3. 跳过 product_id 不在 product 表中的记录（保证外键完整）

前置条件：
  - 已执行 create_tables.sql + insert_data.sql（确保 product 表有商品数据）
  - config.py 中已配置正确的 MySQL 密码

运行：python scripts/load_data.py
依赖：pymysql, pandas
"""
import pymysql
import pandas as pd
import sys
import os

# 将项目根目录加入 sys.path，便于 import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_CONFIG, CLEANED_CSV


def load_to_mysql():
    """批量导入订单数据到 MySQL orders 表"""
    df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
    print(f"[load_data] 读取清洗后数据 {len(df)} 条")

    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            # 校验 product 表是否已有商品（否则外键会失败）
            cursor.execute("SELECT COUNT(*) FROM product")
            n_prod = cursor.fetchone()[0]
            if n_prod == 0:
                print("[load_data] 错误：product 表为空，请先执行 insert_data.sql")
                return

            # 只保留 product_id 存在的行，避免外键冲突
            cursor.execute("SELECT product_id FROM product")
            valid_ids = {r[0] for r in cursor.fetchall()}
            df = df[df["product_id"].isin(valid_ids)]
            print(f"[load_data] 过滤无效 product_id 后剩余 {len(df)} 条")

            # 构造批量插入参数（字段顺序与表结构一致）
            rows = [
                (
                    int(r.order_id), str(r.order_date), str(r.city), str(r.season),
                    int(r.is_holiday), float(r.discount_rate),
                    int(r.product_id), int(r.quantity),
                    float(r.unit_price), float(r.amount),
                )
                for r in df.itertuples()
            ]

            insert_sql = """
                INSERT INTO orders
                (order_id, order_date, city, season, is_holiday,
                 discount_rate, product_id, quantity, unit_price, amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # 分批插入，每批 2000 条，兼顾效率与内存
            batch = 2000
            total = 0
            for i in range(0, len(rows), batch):
                chunk = rows[i:i + batch]
                cursor.executemany(insert_sql, chunk)
                conn.commit()
                total += len(chunk)
                print(f"[load_data] 已导入 {total}/{len(rows)} 条")

        print(f"[load_data] 导入完成，共 {total} 条订单明细")
    finally:
        conn.close()


if __name__ == "__main__":
    load_to_mysql()
