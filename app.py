import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go

# 网页基础设置
st.set_page_config(page_title="SEO日报数据", page_icon="📈", layout="wide")

# ==========================================
# 🎨 蓝色科技感 UI 视觉重构 (完全对齐参考截图)
# ==========================================
st.markdown("""
<style>
/* 全局背景底色偏浅灰蓝，衬托白色卡片 */
.stApp {
    background-color: #f4f6f9;
}

/* 顶部标题与副标题样式 */
h1 {
    color: #1e293b !important;
    font-weight: 700 !important;
    font-size: 28px !important;
}

/* 核心指标卡片样式 - 纯白圆角轻量阴影 */
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 24px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    transition: transform 0.2s;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
}

/* 指标卡片 - 标题颜色（暗灰） */
div[data-testid="metric-container"] label {
    font-size: 14px !important;
    color: #64748b !important;
    font-weight: 600 !important;
}

/* 指标卡片 - 核心大数字颜色（改为标准的广告后台深蓝色） */
div[data-testid="metric-container"] div[data-testid="stMetricValue"] > div {
    font-size: 32px !important;
    font-weight: 700 !important;
    color: #1a56db !important; 
    letter-spacing: -0.5px;
}

/* 横向药丸标签 (st.pills) 样式深度定制 - 匹配蓝色主题 */
button[data-testid="stPill"] {
    background-color: #ffffff !important;
    color: #475569 !important;
    border: 1px solid #cbd5e1 !important;
    padding: 6px 16px !important;
    border-radius: 6px !important;
    font-size: 14px !important;
}
/* 选中状态的药丸标签 */
button[data-testid="stPill"][aria-selected="true"] {
    background-color: #1a56db !important;
    color: #ffffff !important;
    border-color: #1a56db !important;
    font-weight: 600 !important;
}

/* 隐藏 Streamlit 原生页眉 */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取与清洗引擎
# ==========================================

@st.cache_data(ttl="1d")
def load_and_transform_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit"
        sheet = client.open_by_url(sheet_url).sheet1
        
        raw_data = sheet.get_all_values()
        
        clean_records = []
        current_site = None
        dates_row = []
        
        for row_idx, row in enumerate(raw_data):
            if not row or not row[0]:
                continue
                
            first_cell = str(row[0]).strip()
            
            if first_cell.startswith("Callie ") and len(first_cell) <= 10:
                current_site = first_cell.replace("Callie ", "").strip()
                dates_row = row[1:]
                continue
                
            if current_site and first_cell not in ["星期五", "星期六", "星期日", "星期一", "星期二", "星期三", "星期四", "网站要事记", "TDK优化记录表"]:
                metric_name = first_cell
                values = row[1:]
                
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i].strip() != "":
                        date_str = dates_row[i]
                        val_str = values[i]
                        
                        clean_val = 0.0
                        if val_str:
                            val_str = str(val_str).replace("$", "").replace(",", "").replace("%", "").strip()
                            try:
                                clean_val = float(val_str)
                            except:
                                clean_val = 0.0
                                
                        clean_records.append({
                            "Date": date_str,
                            "Site": current_site,
                            "Metric": metric_name,
                            "Value": clean_val
                        })
                        
        df_long = pd.DataFrame(clean_records)
        df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce')
        df_long = df_long.dropna(subset=['Date']) 
        
        return df_long
    except Exception as e:
        st.error(f"🔌 云端数据湖连接失败，错误详情：{e}")
        return pd.DataFrame()


# ==========================================
# 📊 页面渲染与交互逻辑
# ==========================================

st.title("📊 SEO日报数据")
st.write("")

with st.spinner("🚀 正在实时同步云端数据，请稍候..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    
    # 获取动态列表
    all_sites = sorted(df_master['Site'].unique().tolist())
    all_metrics = sorted(df_master['Metric'].unique().tolist())
    
    # ------------------------------------------
    # 🌍 站点选择栏 (完美对齐截图的横向 Pills 标签)
    # ------------------------------------------
    site_options = ["全部站点"] + all_sites
    selected_pill = st.pills("🌍 目标站点：", site_options, default="全部站点")
    
    if selected_pill == "全部站点" or selected_pill is None:
        selected_sites = all_sites
    else:
        selected_sites = [selected_pill]
        
    st.write("")
    
    # ------------------------------------------
    # 📅 其余筛选器栏 (放在次要位置)
    # ------------------------------------------
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
        if not default_metrics: default_metrics = [all_metrics[0]]
        selected_metrics = st.multiselect("📈 附加对比指标：", all_metrics, default=default_metrics)
    with col_f2:
        min_date = df_master['Date'].min()
        max_date = df_master['Date'].max()
        selected_dates = st.date_input("📅 日期范围：", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        
        # 过滤全局数据
        mask = (df_master['Site'].isin(selected_sites)) & \
               (df_master['Date'] >= pd.to_datetime(start_date)) & \
               (df_master['Date'] <= pd.to_datetime(end_date))
        df_filtered = df_master[mask]
        
        if not df_filtered.empty:
            
            # ==========================================
            # 💡 数据分析第一个板块：昨日数据概览
            # ==========================================
            st.write("---")
            st.subheader("📊 数据分析")
            
            # 锁定日期：找到数据流中的最新一天（昨日）和前一天
            latest_date = df_filtered['Date'].max()
            prev_date = latest_date - pd.Timedelta(days=1)
            
            # 聚合当天和前天的数据
            day_data = df_filtered[df_filtered['Date'] == latest_date].groupby('Metric')['Value'].sum()
            prev_day_data = df_filtered[df_filtered['Date'] == prev_date].groupby('Metric')['Value'].sum()
            
            # 动态寻找代表“销售额”或“转化价值”的指标
            sales_metric_key = None
            for m in all_metrics:
                if any(x in m for x in ["销售额", "转化价值", "成交额", "Sales", "Revenue"]):
                    sales_metric_key = m
                    break
            
            # 排版：创建指标卡片列
            # 我们强制让第一个板块展示销售额，右侧展示选中的其他核心流量指标
            extra_display_metrics = [m for m in selected_metrics if m != sales_metric_key][:3]
            total_cols = 1 + len(extra_display_metrics)
            metric_cols = st.columns(total_cols)
            
            # 1. 🎯 核心固定板块：昨日 SEO 销售额
            with metric_cols[0]:
                title_text = f"昨日{sales_metric_key}" if sales_metric_key else "昨日SEO销售额"
                current_sales = day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
                prev_sales = prev_day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
                
                # 计算销售环比
                if prev_sales > 0:
                    sales_delta = ((current_sales - prev_sales) / prev_sales) * 100
                    delta_str = f"{sales_delta:+.1f}% 前日"
                else:
                    delta_str = "0.0% 前日"
                    
                st.metric(label=title_text, value=f"${current_sales:,.2f}", delta=delta_str)
                
            # 2. ⚡ 动态板块：其余选中的指标
            for idx, metric in enumerate(extra_display_metrics):
                with metric_cols[idx + 1]:
                    c_val = day_data.get(metric, 0.0)
                    p_val = prev_day_data.get(metric, 0.0)
                    if p_val > 0:
                        d_pct = ((c_val - p_val) / p_val) * 100
                        d_str = f"{d_pct:+.1f}% 前日"
                    else:
                        d_str = "0.0% 前日"
                    st.metric(label=f"昨日{metric}", value=f"{c_val:,.0f}", delta=d_str)
            
            # ==========================================
            # 📈 蓝色系折线走势图
            # ==========================================
            st.write("")
            df_chart = df_filtered[df_filtered['Metric'].isin(selected_metrics)].copy()
            if not df_chart.empty:
                df_chart['Legend'] = df_chart['Site'] + " - " + df_chart['Metric']
                
                # 选用经典的科技蓝调配色模板
                fig = px.line(
                    df_chart, 
                    x="Date", y="Value", color="Legend",
                    markers=True,
                    template="plotly_white",
                    color_discrete_sequence=["#1a56db", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"]
                )
                
                fig.update_layout(
                    xaxis_title="日期",
                    yaxis_title="数值",
                    hovermode="x unified",
                    margin=dict(l=10, r=10, t=20, b=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # ==========================================
            # 🗄️ 明细数据报表
            # ==========================================
            st.write("---")
            st.subheader("🗄️ 明细数据报表")
            df_pivot = df_filtered[df_filtered['Metric'].isin(selected_metrics)].pivot_table(
                index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum'
            ).reset_index()
            df_pivot = df_pivot.sort_values(by="Date", ascending=False)
            df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        else:
            st.warning("所选区间或条件下无数据，请调整筛选器。")
else:
    st.info("👈 请先配置好 GCP 的 JSON 密钥，并在 Google Sheets 中开放访问权限。")
