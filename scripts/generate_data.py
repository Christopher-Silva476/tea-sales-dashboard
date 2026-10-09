# -*- coding: utf-8 -*-
"""
scripts/generate_data.py —— 生成模拟茶饮销售数据（原始脏数据）

作用：
  1. 定义 8 个品类、16 个商品（与 sql/insert_data.sql 保持一致）
  2. 生成 2023-01-01 ~ 2024-12-31 两年约 30000 条订单明细
  3. 人为注入「缺失值 + 异常值」以模拟真实脏数据场景，供 clean_data.py 清洗

输出：
  data/raw_tea_orders.csv  （原始数据，含脏数据）

运行：python scripts/generate_data.py
依赖：pandas, numpy, random
"""
import random
import datetime
import sys
import os

# 将项目根目录加入 sys.path，便于 import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from config import RAW_CSV

random.seed(2024)
np.random.seed(2024)

# ---------------------------------------------------------------
# ① 品类与商品（与 SQL 脚本保持一致）
# ---------------------------------------------------------------
CATEGORIES = {
    1: "奶茶", 2: "果茶", 3: "纯茶", 4: "咖啡",
    5: "冰淇淋", 6: "气泡水", 7: "酸奶昔", 8: "烘焙小食",
}

PRODUCTS = [
    (1, "波霸奶茶", 1, 16.0), (2, "黑糖珍奶", 1, 18.0),
    (3, "满杯百香果", 2, 15.0), (4, "满杯橙子", 2, 14.0),
    (5, "茉莉绿茶", 3, 12.0), (6, "冷萃乌龙", 3, 13.0),
    (7, "冰美式", 4, 18.0), (8, "生椰拿铁", 4, 20.0),
    (9, "抹茶冰淇淋", 5, 12.0), (10, "香草圣代", 5, 10.0),
    (11, "西柚气泡水", 6, 13.0), (12, "白桃气泡水", 6, 13.0),
    (13, "芒果酸奶昔", 7, 17.0), (14, "蓝莓酸奶昔", 7, 18.0),
    (15, "芝士蛋糕", 8, 15.0), (16, "可颂", 8, 11.0),
]

CITIES = ["重庆", "上海", "北京", "广州", "深圳", "成都", "杭州", "武汉"]


def season_of(month: int) -> str:
    """由月份映射季节：3-5 春 / 6-8 夏 / 9-11 秋 / 12-2 冬"""
    if month in (3, 4, 5):
        return "春"
    if month in (6, 7, 8):
        return "夏"
    if month in (9, 10, 11):
        return "秋"
    return "冬"


# ---------------------------------------------------------------
# ② 生成订单明细
# ---------------------------------------------------------------
def generate_raw_orders(n_orders: int = 12000) -> pd.DataFrame:
    """
    生成 n_orders 张订单对应的订单明细行（一张订单可能含 1~3 个商品）。
    返回 DataFrame，字段与 orders 表结构对应。
    """
    records = []
    order_id = 100000  # 订单号起点

    for _ in range(n_orders):
        order_id += 1
        # 随机下单日期：2023-01-01 ~ 2024-12-31
        days = random.randint(0, 365 * 2)
        order_date = datetime.date(2023, 1, 1) + datetime.timedelta(days=days)
        city = random.choice(CITIES)
        season = season_of(order_date.month)
        # 节假日概率 18%，节假日更可能触发折扣
        is_holiday = 1 if random.random() < 0.18 else 0
        discount = (
            random.choice([0.0, 0.0, 0.10, 0.15, 0.20, 0.30]) if is_holiday
            else random.choice([0.0, 0.0, 0.0, 0.05, 0.10])
        )

        # 每个订单 1~3 个商品 SKU
        for _ in range(random.randint(1, 3)):
            pid, pname, cat_id, base_price = random.choice(PRODUCTS)
            quantity = random.randint(1, 5)
            unit_price = round(base_price * (1 - discount), 2)
            amount = round(quantity * unit_price, 2)

            # ③ 人为注入脏数据
            # 缺失值：约 2% 的城市缺失、1% 的 quantity 缺失、1% 的 amount 缺失
            if random.random() < 0.02:
                city = np.nan
            if random.random() < 0.01:
                quantity = np.nan
            if random.random() < 0.01:
                amount = np.nan

            # 异常值：quantity 出现 0/负数；unit_price 出现负值；amount 异常偏大
            if random.random() < 0.015:
                quantity = random.choice([0, -1, -3])
            if random.random() < 0.01:
                unit_price = -unit_price
            if random.random() < 0.015:
                amount = round(quantity * unit_price * random.uniform(20, 50), 2)  # 放大异常

            records.append({
                "order_id": order_id,
                "order_date": order_date,
                "city": city,
                "season": season,
                "is_holiday": is_holiday,
                "discount_rate": discount,
                "product_id": pid,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            })

    return pd.DataFrame(records)


def main():
    print("[generate_data] 开始生成模拟数据 ...")
    df = generate_raw_orders(12000)
    df.to_csv(RAW_CSV, index=False, encoding="utf-8-sig")

    print(f"[generate_data] 已生成 {len(df)} 条订单明细，保存至: {RAW_CSV}")
    print("[generate_data] 脏数据概览（清洗前）：")
    print(f"  - city 缺失: {df['city'].isna().sum()} 条")
    print(f"  - quantity 缺失: {df['quantity'].isna().sum()} 条")
    print(f"  - amount 缺失: {df['amount'].isna().sum()} 条")
    print(f"  - quantity<=0 异常: {(df['quantity'].fillna(0) <= 0).sum()} 条")
    print(f"  - unit_price<0 异常: {(df['unit_price'] < 0).sum()} 条")


if __name__ == "__main__":
    main()
