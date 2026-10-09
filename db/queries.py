# -*- coding: utf-8 -*-
"""
db/queries.py —— SQL 查询定义

作用：集中存放看板各分析维度的 SQL（多表 JOIN / GROUP BY / 窗口函数），
     供 MySQL 模式下执行；同时为每个查询标注对应的可视化用途。
"""

# ---------------------------------------------------------------------------
# 01 KPI 总览：总销售额、订单量、客单价
# ---------------------------------------------------------------------------
KPI_OVERVIEW = """
SELECT
    ROUND(SUM(amount), 2)                       AS total_revenue,   -- 总销售额
    COUNT(DISTINCT order_id)                    AS total_orders,    -- 订单量(去重订单号)
    ROUND(SUM(amount) / COUNT(DISTINCT order_id), 2) AS avg_order_value -- 客单价
FROM orders;
"""

# ---------------------------------------------------------------------------
# 02 月度营收 / 销量趋势（折线图）
# ---------------------------------------------------------------------------
MONTHLY_TREND = """
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,       -- 月份
    ROUND(SUM(amount), 2)            AS revenue,     -- 月度营收
    SUM(quantity)                    AS volume       -- 月度销量
FROM orders
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY month;
"""

# ---------------------------------------------------------------------------
# 03 城市 × 季节 维度分析（分组柱状图）
# ---------------------------------------------------------------------------
CITY_SEASON = """
SELECT
    city,
    season,
    ROUND(SUM(amount), 2)  AS revenue,   -- 城市×季节营收
    SUM(quantity)          AS volume,    -- 销量
    COUNT(DISTINCT order_id) AS orders   -- 订单数
FROM orders
GROUP BY city, season
ORDER BY revenue DESC;
"""

# ---------------------------------------------------------------------------
# 04 品类营收排行（多表 JOIN + 窗口函数 RANK 排名）
# ---------------------------------------------------------------------------
CATEGORY_RANK = """
SELECT
    c.category_name,
    ROUND(SUM(o.amount), 2)                       AS revenue,
    RANK() OVER (ORDER BY SUM(o.amount) DESC)     AS rnk   -- 营收排名窗口函数
FROM orders o
JOIN product p ON o.product_id = p.product_id
JOIN category c ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY revenue DESC;
"""

# ---------------------------------------------------------------------------
# 05 节假日 × 折扣率 与销量关系（热力图基础数据）
# ---------------------------------------------------------------------------
HOLIDAY_DISCOUNT = """
SELECT
    is_holiday,
    discount_rate,
    SUM(quantity)          AS volume,   -- 销量
    ROUND(SUM(amount), 2)  AS revenue   -- 营收
FROM orders
GROUP BY is_holiday, discount_rate
ORDER BY is_holiday, discount_rate;
"""

# ---------------------------------------------------------------------------
# 06 城市营收对比（柱状图）
# ---------------------------------------------------------------------------
CITY_REVENUE = """
SELECT
    city,
    ROUND(SUM(amount), 2)  AS revenue,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(AVG(amount), 2)  AS avg_order
FROM orders
GROUP BY city
ORDER BY revenue DESC;
"""
