# -*- coding: utf-8 -*-
"""
data/repository.py —— 数据访问层（MySQL 优先，CSV 降级演示）

作用：
  1. 启动时探测 MySQL 是否可用：
     - 可用 → mode="mysql"，执行 db/queries.py 中的真实 SQL（JOIN/GROUP BY/窗口函数）
     - 不可用 → mode="csv"，用 pandas 从 data/cleaned_tea_orders.csv 复现同等分析，
       便于在没有 MySQL 的环境下演示看板
  2. 对外暴露统一的查询方法，上层 services 无需关心数据来源。

用法：
    repo = Repository()
    repo.kpi_overview()          # -> {total_revenue, total_orders, avg_order_value}
    repo.monthly_trend()         # -> [{month, revenue, volume}]
    repo.city_season()           # -> [{city, season, revenue, volume, orders}]
    repo.category_rank()         # -> [{category_name, revenue, rnk}]
    repo.holiday_discount()      # -> [{is_holiday, discount_rate, volume, revenue}]
    repo.city_revenue()          # -> [{city, revenue, orders, avg_order}]
"""
import pandas as pd
from db.db_connect import mysql_available, get_connection
from config import CLEANED_CSV
from db import queries as SQL


class Repository:
    """统一数据访问层"""

    def __init__(self):
        self.mode = "mysql" if mysql_available() else "csv"
        print(f"[Repository] 数据源模式: {self.mode}")
        if self.mode == "csv":
            # 演示模式：读取清洗后的 CSV
            self.df = pd.read_csv(CLEANED_CSV, encoding="utf-8-sig")
            # 补齐商品/品类映射（与 SQL 种子数据一致）
            self._load_dim()

    # ------------------------------------------------------------------
    # 维度补充（CSV 模式用）
    # ------------------------------------------------------------------
    def _load_dim(self):
        """CSV 模式下加载 product/category 映射，用于品类维度计算"""
        # 从 insert_data.sql 的种子数据硬编码映射（保持一致性）
        self.cat_of_product = {
            1: "奶茶", 2: "奶茶", 3: "果茶", 4: "果茶",
            5: "纯茶", 6: "纯茶", 7: "咖啡", 8: "咖啡",
            9: "冰淇淋", 10: "冰淇淋", 11: "气泡水", 12: "气泡水",
            13: "酸奶昔", 14: "酸奶昔", 15: "烘焙小食", 16: "烘焙小食",
        }

    # ------------------------------------------------------------------
    # 通用 MySQL 查询执行
    # ------------------------------------------------------------------
    def _query_mysql(self, sql: str) -> list:
        """在 MySQL 模式下执行 SQL，返回 dict 列表"""
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                return cur.fetchall()
        finally:
            conn.close()

    # ==================================================================
    # 01 KPI 总览
    # ==================================================================
    def kpi_overview(self) -> dict:
        if self.mode == "mysql":
            row = self._query_mysql(SQL.KPI_OVERVIEW)[0]
            return {
                "total_revenue": float(row["total_revenue"]),
                "total_orders": int(row["total_orders"]),
                "avg_order_value": float(row["avg_order_value"]),
            }
        # CSV 模式复现
        df = self.df
        total_revenue = float(df["amount"].sum())
        total_orders = int(df["order_id"].nunique())
        avg_order = round(total_revenue / total_orders, 2)
        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "avg_order_value": avg_order,
        }

    # ==================================================================
    # 02 月度营收/销量趋势
    # ==================================================================
    def monthly_trend(self) -> list:
        if self.mode == "mysql":
            return [
                {"month": r["month"], "revenue": float(r["revenue"]),
                 "volume": int(r["volume"])}
                for r in self._query_mysql(SQL.MONTHLY_TREND)
            ]
        df = self.df.copy()
        df["month"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y-%m")
        g = df.groupby("month", as_index=False).agg(
            revenue=("amount", "sum"), volume=("quantity", "sum")
        ).sort_values("month")
        return [
            {"month": r["month"], "revenue": round(float(r["revenue"]), 2),
             "volume": int(r["volume"])}
            for r in g.to_dict("records")
        ]

    # ==================================================================
    # 03 城市 × 季节
    # ==================================================================
    def city_season(self) -> list:
        if self.mode == "mysql":
            return [
                {"city": r["city"], "season": r["season"],
                 "revenue": float(r["revenue"]), "volume": int(r["volume"]),
                 "orders": int(r["orders"])}
                for r in self._query_mysql(SQL.CITY_SEASON)
            ]
        df = self.df.copy()
        g = df.groupby(["city", "season"], as_index=False).agg(
            revenue=("amount", "sum"), volume=("quantity", "sum"),
            orders=("order_id", "nunique")
        ).sort_values("revenue", ascending=False)
        return [
            {"city": r["city"], "season": r["season"],
             "revenue": round(float(r["revenue"]), 2), "volume": int(r["volume"]),
             "orders": int(r["orders"])}
            for r in g.to_dict("records")
        ]

    # ==================================================================
    # 04 品类营收排名（窗口函数）
    # ==================================================================
    def category_rank(self) -> list:
        if self.mode == "mysql":
            return [
                {"category_name": r["category_name"], "revenue": float(r["revenue"]),
                 "rnk": int(r["rnk"])}
                for r in self._query_mysql(SQL.CATEGORY_RANK)
            ]
        df = self.df.copy()
        df["category_name"] = df["product_id"].map(self.cat_of_product)
        g = df.groupby("category_name", as_index=False)["amount"].sum()
        g = g.sort_values("amount", ascending=False).reset_index(drop=True)
        g["rnk"] = range(1, len(g) + 1)
        return [
            {"category_name": r["category_name"], "revenue": round(float(r["amount"]), 2),
             "rnk": int(r["rnk"])}
            for r in g.to_dict("records")
        ]

    # ==================================================================
    # 05 节假日 × 折扣率（热力图）
    # ==================================================================
    def holiday_discount(self) -> list:
        if self.mode == "mysql":
            return [
                {"is_holiday": int(r["is_holiday"]), "discount_rate": float(r["discount_rate"]),
                 "volume": int(r["volume"]), "revenue": float(r["revenue"])}
                for r in self._query_mysql(SQL.HOLIDAY_DISCOUNT)
            ]
        df = self.df.copy()
        g = df.groupby(["is_holiday", "discount_rate"], as_index=False).agg(
            volume=("quantity", "sum"), revenue=("amount", "sum")
        )
        return [
            {"is_holiday": int(r["is_holiday"]), "discount_rate": float(r["discount_rate"]),
             "volume": int(r["volume"]), "revenue": round(float(r["revenue"]), 2)}
            for r in g.to_dict("records")
        ]

    # ==================================================================
    # 06 城市营收对比
    # ==================================================================
    def city_revenue(self) -> list:
        if self.mode == "mysql":
            return [
                {"city": r["city"], "revenue": float(r["revenue"]),
                 "orders": int(r["orders"]), "avg_order": float(r["avg_order"])}
                for r in self._query_mysql(SQL.CITY_REVENUE)
            ]
        df = self.df.copy()
        g = df.groupby("city", as_index=False).agg(
            revenue=("amount", "sum"), orders=("order_id", "nunique"),
            avg_order=("amount", "mean")
        ).sort_values("revenue", ascending=False)
        return [
            {"city": r["city"], "revenue": round(float(r["revenue"]), 2),
             "orders": int(r["orders"]), "avg_order": round(float(r["avg_order"]), 2)}
            for r in g.to_dict("records")
        ]
