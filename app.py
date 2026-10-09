# -*- coding: utf-8 -*-
"""
app.py —— Flask 主应用（模块04/05/06/07/08 的 Web 层）

作用：
  1. 提供看板页面路由  /
  2. 提供 6 个 JSON 数据接口，供前端 ECharts 渲染：
       /api/kpi             -> KPI 卡片（总销售额/订单量/客单价/环比）
       /api/monthly_trend   -> 月度营收·销量折线
       /api/city_revenue    -> 城市营收柱状
       /api/city_season     -> 城市×季节分组柱状
       /api/category_rank   -> 品类营收排行（多表JOIN+窗口函数）
       /api/heatmap         -> 节假日×折扣率 热力图
  3. 启动时构建数据访问层单例 Repository（MySQL 优先，CSV 降级演示）

运行：
  .venv\\Scripts\\python.exe app.py
  浏览器访问 http://127.0.0.1:5000
"""
from flask import Flask, render_template, jsonify
from data.repository import Repository
from services import kpi_service, chart_service

app = Flask(__name__)

# 数据访问层单例（启动时探测 MySQL；不可用则自动降级为 CSV 演示）
repo = Repository()


# ---------------------------------------------------------------------------
# 页面路由
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """看板主页"""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# JSON 数据接口
# ---------------------------------------------------------------------------
@app.route("/api/kpi")
def api_kpi():
    """KPI 总览"""
    return jsonify(kpi_service.get_kpi(repo))


@app.route("/api/monthly_trend")
def api_monthly_trend():
    """月度营收 / 销量趋势"""
    return jsonify(chart_service.get_monthly_trend(repo))


@app.route("/api/city_revenue")
def api_city_revenue():
    """城市营收对比"""
    return jsonify(chart_service.get_city_revenue(repo))


@app.route("/api/city_season")
def api_city_season():
    """城市 × 季节"""
    return jsonify(chart_service.get_city_season(repo))


@app.route("/api/category_rank")
def api_category_rank():
    """品类营收排名"""
    return jsonify(chart_service.get_category_rank(repo))


@app.route("/api/heatmap")
def api_heatmap():
    """节假日 × 折扣率 热力图"""
    return jsonify(chart_service.get_heatmap(repo))


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("茶饮销售数据分析看板已启动")
    print("请访问: http://127.0.0.1:5000")
    print("=" * 60)
    # debug=True 便于开发调试；生产环境请关闭
    app.run(host="0.0.0.0", port=5000, debug=True)
