# -*- coding: utf-8 -*-
"""
services/kpi_service.py —— KPI 总览服务（模块05）

作用：基于数据访问层返回的 KPI 原始值，用 pandas 做二次分析：
  - 汇总总销售额 / 订单量 / 客单价
  - 计算月度环比增长率（洞察文案用）
"""
import pandas as pd


def get_kpi(repo) -> dict:
    """
    返回 KPI 总览指标。
    repo: 数据访问层实例（Repository）
    """
    kpi = repo.kpi_overview()

    # 二次分析：基于月度趋势计算环比增长率
    trend = repo.monthly_trend()
    mom = None
    if len(trend) >= 2:
        # 最近两个月营收
        df = pd.DataFrame(trend)
        df["revenue"] = df["revenue"].astype(float)
        df = df.sort_values("month")
        last_rev = float(df["revenue"].iloc[-1])
        prev_rev = float(df["revenue"].iloc[-2])
        if prev_rev:
            mom = round((last_rev - prev_rev) / prev_rev * 100, 2)
    else:
        last_rev = kpi["total_revenue"]

    return {
        "total_revenue": kpi["total_revenue"],
        "total_orders": kpi["total_orders"],
        "avg_order_value": kpi["avg_order_value"],
        "mom_growth": mom,          # 月度营收环比增长率(%)，可能为 None
        "latest_month_revenue": last_rev,
    }
