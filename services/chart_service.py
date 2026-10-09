# -*- coding: utf-8 -*-
"""
services/chart_service.py —— 图表数据服务（模块06/07/08）

作用：将数据访问层的原始查询结果，用 pandas 二次整理为前端 ECharts
     可直接消费的结构（折线 / 柱状 / 分组柱状 / 热力图矩阵）。
"""
import pandas as pd


# ---------------------------------------------------------------------------
# 06 月度营收 / 销量趋势（折线图）
# ---------------------------------------------------------------------------
def get_monthly_trend(repo) -> dict:
    rows = repo.monthly_trend()
    df = pd.DataFrame(rows).sort_values("month")
    return {
        "months": df["month"].tolist(),
        "revenue": df["revenue"].astype(float).round(2).tolist(),
        "volume": df["volume"].astype(int).tolist(),
    }


# ---------------------------------------------------------------------------
# 城市营收对比（柱状图）
# ---------------------------------------------------------------------------
def get_city_revenue(repo) -> dict:
    rows = repo.city_revenue()
    df = pd.DataFrame(rows)
    return {
        "cities": df["city"].tolist(),
        "revenue": df["revenue"].astype(float).round(2).tolist(),
        "orders": df["orders"].astype(int).tolist(),
        "avg_order": df["avg_order"].astype(float).round(2).tolist(),
    }


# ---------------------------------------------------------------------------
# 城市 × 季节（分组柱状图）
# ---------------------------------------------------------------------------
def get_city_season(repo) -> dict:
    rows = repo.city_season()
    df = pd.DataFrame(rows)
    # 透视：行=城市，列=季节，值为营收
    pivot = df.pivot_table(index="city", columns="season", values="revenue",
                           aggfunc="sum", fill_value=0)
    # 固定季节顺序
    season_order = [s for s in ["春", "夏", "秋", "冬"] if s in pivot.columns]
    pivot = pivot[season_order]
    cities = pivot.index.tolist()
    series = {season: pivot[season].round(2).tolist() for season in season_order}
    return {"cities": cities, "seasons": season_order, "series": series}


# ---------------------------------------------------------------------------
# 品类营收排名（柱状图，来自多表 JOIN + 窗口函数）
# ---------------------------------------------------------------------------
def get_category_rank(repo) -> dict:
    rows = repo.category_rank()
    df = pd.DataFrame(rows).sort_values("revenue", ascending=False)
    return {
        "names": df["category_name"].tolist(),
        "revenue": df["revenue"].astype(float).round(2).tolist(),
        "rnk": df["rnk"].astype(int).tolist(),
    }


# ---------------------------------------------------------------------------
# 节假日 × 折扣率 热力图（模块08）
# ---------------------------------------------------------------------------
def get_heatmap(repo) -> dict:
    """
    将 (is_holiday, discount_rate) 的销量统计转成 ECharts 热力图矩阵。
    返回：
      y_labels: ['非节假日','节假日']
      x_labels: 折扣率档次（去重升序）
      data: [[x_index, y_index, volume], ...]
    """
    rows = repo.holiday_discount()
    df = pd.DataFrame(rows)
    if df.empty:
        return {"x_labels": [], "y_labels": [], "data": []}

    # 折扣率分档排序
    x_labels = sorted(df["discount_rate"].unique().tolist())
    y_labels = ["非节假日", "节假日"]  # is_holiday 0 / 1

    pivot = df.pivot_table(index="is_holiday", columns="discount_rate",
                           values="volume", aggfunc="sum", fill_value=0)

    data = []
    for yi, holiday in enumerate([0, 1]):
        for xi, rate in enumerate(x_labels):
            val = int(pivot.loc[holiday, rate]) if holiday in pivot.index else 0
            data.append([xi, yi, val])
    return {"x_labels": x_labels, "y_labels": y_labels, "data": data}
