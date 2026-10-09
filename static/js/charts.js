/* ==========================================================================
   charts.js —— 使用 ECharts 渲染核心图表（模块06/07/08）
   依赖: ECharts 5.x
   ========================================================================== */

// 统一的深色主题工具
function baseTooltip() {
    return {
        trigger: 'axis',
        backgroundColor: 'rgba(15,23,42,0.9)',
        borderColor: '#334155',
        textStyle: { color: '#e2e8f0' }
    };
}

const AXIS = {
    axisLine: { lineStyle: { color: '#334155' } },
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: '#1e293b' } }
};

// --------------------------------------------------------------------------
// 06 月度营收 / 销量趋势 —— 双轴折线图
// --------------------------------------------------------------------------
async function loadTrend() {
    const res = await fetch('/api/monthly_trend');
    const data = await res.json();
    const chart = echarts.init(document.getElementById('chartTrend'));

    chart.setOption({
        tooltip: baseTooltip(),
        legend: { data: ['营收(元)', '销量(杯)'], textStyle: { color: '#94a3b8' }, top: 0 },
        grid: { left: 70, right: 70, top: 40, bottom: 40 },
        xAxis: {
            type: 'category',
            data: data.months,
            axisLabel: { color: '#94a3b8', interval: 2 }
        },
        yAxis: [
            { type: 'value', name: '营收(元)', ...AXIS },
            { type: 'value', name: '销量(杯)', ...AXIS, splitLine: { show: false } }
        ],
        series: [
            {
                name: '营收(元)', type: 'line', smooth: true,
                data: data.revenue, yAxisIndex: 0,
                itemStyle: { color: '#38bdf8' },
                areaStyle: { color: 'rgba(56,189,248,0.15)' }
            },
            {
                name: '销量(杯)', type: 'line', smooth: true,
                data: data.volume, yAxisIndex: 1,
                itemStyle: { color: '#a78bfa' }
            }
        ]
    });
    window.addEventListener('resize', () => chart.resize());
}

// --------------------------------------------------------------------------
// 品类营收排行 —— 横向柱状图（多表JOIN+窗口函数）
// --------------------------------------------------------------------------
async function loadCategory() {
    const res = await fetch('/api/category_rank');
    const data = await res.json();
    const chart = echarts.init(document.getElementById('chartCategory'));

    chart.setOption({
        tooltip: { trigger: 'axis', ...baseTooltip() },
        grid: { left: 80, right: 40, top: 20, bottom: 40 },
        xAxis: { type: 'value', name: '营收(元)', ...AXIS },
        yAxis: {
            type: 'category',
            data: data.names.slice().reverse(),   // 反转为升序排列
            axisLabel: { color: '#94a3b8' }
        },
        series: [{
            type: 'bar',
            data: data.revenue.slice().reverse(),
            itemStyle: {
                borderRadius: [0, 6, 6, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                    { offset: 0, color: '#0ea5e9' },
                    { offset: 1, color: '#38bdf8' }
                ])
            },
            label: { show: true, position: 'right', color: '#e2e8f0', fontSize: 11 }
        }]
    });
    window.addEventListener('resize', () => chart.resize());
}

// --------------------------------------------------------------------------
// 城市营收对比 —— 柱状图
// --------------------------------------------------------------------------
async function loadCity() {
    const res = await fetch('/api/city_revenue');
    const data = await res.json();
    const chart = echarts.init(document.getElementById('chartCity'));

    chart.setOption({
        tooltip: { trigger: 'axis', ...baseTooltip() },
        grid: { left: 50, right: 40, top: 20, bottom: 60 },
        xAxis: {
            type: 'category', data: data.cities,
            axisLabel: { color: '#94a3b8', rotate: 30 }
        },
        yAxis: { type: 'value', name: '营收(元)', ...AXIS },
        series: [{
            type: 'bar',
            data: data.revenue,
            barMaxWidth: 40,
            itemStyle: {
                borderRadius: [6, 6, 0, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#34d399' },
                    { offset: 1, color: '#0f766e' }
                ])
            }
        }]
    });
    window.addEventListener('resize', () => chart.resize());
}

// --------------------------------------------------------------------------
// 07 城市 × 季节 —— 分组柱状图
// --------------------------------------------------------------------------
async function loadSeason() {
    const res = await fetch('/api/city_season');
    const data = await res.json();
    const chart = echarts.init(document.getElementById('chartSeason'));

    const palette = { '春': '#38bdf8', '夏': '#f87171', '秋': '#fbbf24', '冬': '#a78bfa' };
    const series = data.seasons.map(season => ({
        name: season,
        type: 'bar',
        data: data.series[season],
        itemStyle: { color: palette[season] || '#38bdf8' }
    }));

    chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...baseTooltip() },
        legend: { data: data.seasons, textStyle: { color: '#94a3b8' }, top: 0 },
        grid: { left: 60, right: 30, top: 40, bottom: 60 },
        xAxis: {
            type: 'category', data: data.cities,
            axisLabel: { color: '#94a3b8', rotate: 30 }
        },
        yAxis: { type: 'value', name: '营收(元)', ...AXIS },
        series
    });
    window.addEventListener('resize', () => chart.resize());
}

// --------------------------------------------------------------------------
// 08 节假日 × 折扣率 —— 热力图
// --------------------------------------------------------------------------
async function loadHeatmap() {
    const res = await fetch('/api/heatmap');
    const data = await res.json();
    const chart = echarts.init(document.getElementById('chartHeatmap'));

    // 将销量映射为 0~100 的色阶，便于热力图区分
    const volumes = data.data.map(d => d[2]);
    const maxV = Math.max(...volumes, 1);

    chart.setOption({
        tooltip: {
            formatter: p => `${data.y_labels[p.value[1]]} × 折扣${p.value[0] === 0 ? '0%' : (data.x_labels[p.value[0]] * 100) + '%'}<br/>销量: ${p.value[2]}杯`,
            ...baseTooltip()
        },
        grid: { left: 70, right: 30, top: 40, bottom: 50 },
        xAxis: {
            type: 'category', data: data.x_labels.map(r => r === 0 ? '0%' : (r * 100) + '%'),
            axisLabel: { color: '#94a3b8' }
        },
        yAxis: { type: 'category', data: data.y_labels, axisLabel: { color: '#94a3b8' } },
        visualMap: {
            min: 0, max: maxV, calculable: true, orient: 'horizontal',
            left: 'center', bottom: 0,
            textStyle: { color: '#94a3b8' },
            inRange: { color: ['#0f172a', '#38bdf8', '#fbbf24', '#f87171'] }
        },
        series: [{
            type: 'heatmap',
            data: data.data,
            label: { show: true, color: '#fff', fontSize: 11 },
            itemStyle: { borderColor: '#0f172a', borderWidth: 2 }
        }]
    });
    window.addEventListener('resize', () => chart.resize());
}

// --------------------------------------------------------------------------
// 入口：并行加载全部图表
// --------------------------------------------------------------------------
async function initAllCharts() {
    try {
        await Promise.all([
            loadTrend(), loadCategory(), loadCity(), loadSeason(), loadHeatmap()
        ]);
        document.getElementById('mode-tag').textContent = '看板已加载 ✓';
    } catch (e) {
        console.error('图表加载失败:', e);
        document.getElementById('mode-tag').textContent = '数据加载失败';
    }
}

document.addEventListener('DOMContentLoaded', initAllCharts);
