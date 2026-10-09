# -*- coding: utf-8 -*-
"""
scripts/clean_data.py —— 使用 pandas 对原始数据做清洗（缺失值 + 异常值）

清洗策略：
  1. 缺失值处理：
     - city 缺失：填充为 "未知"
     - quantity 缺失：填充为该商品类别的众数（取整）
     - amount 缺失：按 quantity * unit_price 重算
  2. 异常值处理：
     - quantity <= 0：视为异常，改为 1（最小合法购买量）
     - unit_price < 0：取绝对值
     - amount 与 quantity*unit_price 严重不符（IQR 判定）：重算为 quantity*unit_price
     - amount <= 0：重算
  3. 输出清洗后的数据，打印清洗报告（各步骤处理行数）

输出：
  data/cleaned_tea_orders.csv

运行：python scripts/clean_data.py
依赖：pandas, numpy
"""
import pandas as pd
import numpy as np
import sys
import os

# 将项目根目录加入 sys.path，便于 import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RAW_CSV, CLEANED_CSV


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """对原始订单数据执行清洗，返回清洗后的 DataFrame（复制）"""
    df = df.copy()
    report = []  # 记录清洗动作

    # =========================================================
    # ① 缺失值处理
    # =========================================================
    # city 缺失 → 填充 "未知"
    n_city = df["city"].isna().sum()
    df["city"] = df["city"].fillna("未知")
    report.append(("city 缺失填充为'未知'", n_city))

    # quantity 缺失 → 用众数（最常见购买量）填充，取整
    n_qty = df["quantity"].isna().sum()
    if n_qty > 0:
        mode_qty = int(df["quantity"].mode().iloc[0])
        df["quantity"] = df["quantity"].fillna(mode_qty)
        report.append((f"quantity 缺失填充为众数 {mode_qty}", n_qty))

    # amount 缺失 → 用 quantity * unit_price 重算
    n_amt_na = df["amount"].isna().sum()
    mask_amt_na = df["amount"].isna()
    df.loc[mask_amt_na, "amount"] = (
        df.loc[mask_amt_na, "quantity"] * df.loc[mask_amt_na, "unit_price"]
    ).round(2)
    report.append(("amount 缺失按 quantity*unit_price 重算", n_amt_na))

    # =========================================================
    # ② 异常值处理
    # =========================================================
    # quantity <= 0 → 改为 1
    n_qty_bad = (df["quantity"] <= 0).sum()
    df.loc[df["quantity"] <= 0, "quantity"] = 1
    report.append(("quantity<=0 异常改为 1", n_qty_bad))

    # unit_price < 0 → 取绝对值
    n_price_bad = (df["unit_price"] < 0).sum()
    df.loc[df["unit_price"] < 0, "unit_price"] = df.loc[
        df["unit_price"] < 0, "unit_price"
    ].abs()
    report.append(("unit_price<0 取绝对值", n_price_bad))

    # amount 与 quantity*unit_price 不符（IQR 判定严重偏离）→ 重算
    df["calc_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    diff = (df["amount"] - df["calc_amount"]).abs()
    q1, q3 = diff.quantile(0.25), diff.quantile(0.75)
    iqr = q3 - q1
    threshold = max(q3 + 1.5 * iqr, 1.0)
    mask_bad_amt = diff > threshold
    n_amt_bad = int(mask_bad_amt.sum())
    df.loc[mask_bad_amt, "amount"] = df.loc[mask_bad_amt, "calc_amount"]
    report.append((f"amount 与实算不符(>阈值{threshold:.2f})重算", n_amt_bad))

    # amount <= 0 → 重算（兜底）
    n_amt_le0 = (df["amount"] <= 0).sum()
    df.loc[df["amount"] <= 0, "amount"] = df.loc[
        df["amount"] <= 0, "calc_amount"
    ]
    report.append(("amount<=0 重算", n_amt_le0))

    # 删除 calc_amount 辅助列
    df = df.drop(columns=["calc_amount"])
    return df, report


def main():
    print("[clean_data] 读取原始数据 ...")
    df = pd.read_csv(RAW_CSV, encoding="utf-8-sig")
    print(f"[clean_data] 清洗前记录数: {len(df)}")

    cleaned, report = clean(df)

    print("\n[clean_data] 清洗报告：")
    for action, count in report:
        print(f"  - {action}: {count} 条")
    print(f"[clean_data] 清洗后记录数: {len(cleaned)}")

    cleaned.to_csv(CLEANED_CSV, index=False, encoding="utf-8-sig")
    print(f"[clean_data] 清洗后数据已保存: {CLEANED_CSV}")


if __name__ == "__main__":
    main()
