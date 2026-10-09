/* ==========================================================================
   kpi.js —— 拉取 /api/kpi 并渲染 KPI 卡片（模块05）
   ========================================================================== */

async function loadKpi() {
    try {
        const res = await fetch('/api/kpi');
        const data = await res.json();

        // 总销售额（千分位格式化）
        document.getElementById('kpiRevenue').textContent =
            '¥ ' + Number(data.total_revenue).toLocaleString('zh-CN', {minimumFractionDigits: 2});

        // 订单量
        document.getElementById('kpiOrders').textContent =
            Number(data.total_orders).toLocaleString('zh-CN');

        // 客单价
        document.getElementById('kpiAvgOrder').textContent =
            '¥ ' + Number(data.avg_order_value).toFixed(2);

        // 月度营收环比（带涨跌颜色与箭头）
        const momEl = document.getElementById('kpiMom');
        if (data.mom_growth == null) {
            momEl.textContent = '--';
        } else {
            const v = Number(data.mom_growth);
            momEl.textContent = (v >= 0 ? '▲ ' : '▼ ') + v.toFixed(2) + '%';
            momEl.classList.add(v >= 0 ? 'up' : 'down');
        }
    } catch (e) {
        console.error('KPI 加载失败:', e);
    }
}

// 页面加载即渲染
loadKpi();
