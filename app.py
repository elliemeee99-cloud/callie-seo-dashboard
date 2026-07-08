import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import time

# 网页基础设置 (修改网页标题为 SEO日报数据)
st.set_page_config(page_title="SEO日报数据", page_icon="📈", layout="wide")

# ==========================================
# 🎨 自定义 CSS 样式注入 (参考广告看板 UI 进行美化)
# ==========================================
st.markdown("""
<style>
/* 整体应用背景色偏浅灰，突出白色卡片 */
.stApp {
    background-color: #f8fafc;
}
/* 核心指标卡片样式优化 */
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    display: flex;
    flex-direction: column;
    align-items: center; /* 文本居中 */
    justify-content: center;
}
/* 指标卡片 - 标题颜色 */
div[data-testid="metric-container"] label {
    font-size: 15px !important;
    color: #475569 !important;
    font-weight: 600;
}
/* 指标卡片 - 主体大数字颜色 (调整为截图中亮眼的蓝色) */
div[data-testid="metric-container"] div[data-testid="stMetricValue"] > div {
    font-size: 34px !important;
    font-weight: 700 !important;
    color: #1a56db !important; 
}
/* 隐藏原生 Streamlit UI 顶部空白和汉堡菜单 */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取与清洗引擎
# ==========================================

# 魔法缓存：每天自动刷新一次，避免超额调用 API
@st.cache_data(ttl="1d")
def load_and_transform_google_sheet():
    try:
        # 1. 读取谷歌授权秘钥
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        
        # 2. 连接到谷歌账号并打开表格
        client = gspread.authorize(creds)
        # 表格的 URL ID
        sheet_url = "https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit"
        sheet = client.open_by_url(sheet_url).sheet1
        
        # 3. 提取所有原始数据
        raw_data = sheet.get_all_values()
        
        # 4. 🔥 数据翻转与清洗引擎
        clean_records = []
        current_site = None
        dates_row = []
        
        for row_idx, row in enumerate(raw_data):
            if not row or not row[0]:
                continue
                
            first_cell = str(row[0]).strip()
            
            # 探测是不是国家站的开始行
            if first_cell.startswith("Callie ") and len(first_cell) <= 10:
                current_site = first_cell.replace("Callie ", "").strip()
                dates_row = row[1:]
                continue
                
            # 探测指标行
            if current_site and first_cell not in ["星期五", "星期六", "星期日", "星期一", "星期二", "星期三", "星期四", "网站要事记", "TDK优化记录表"]:
                metric_name = first_cell
                values = row[1:]
                
                # 开始执行数据翻转
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i].strip() != "":
                        date_str = dates_row[i]
                        val_str = values[i]
                        
                        # 清洗数值
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
                        
        # 5. 转化为标准长表 DataFrame
        df_long = pd.DataFrame(clean_records)
        df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce')
        df_long = df_long.dropna(subset=['Date']) 
        
        return df_long
    except Exception as e:
        st.error(f"🔌 连接云端数据湖失败，请检查 GCP 密钥配置是否正确。错误详情：{e}")
        return pd.DataFrame()

# ==========================================
# 📊 前端交互面板与可视化
# ==========================================

st.title("📊 SEO日报数据")
st.markdown("数据源: `Google Sheets (自动同步与转置)`")
st.write("---")

with st.spinner("🚀 正在抽取并清洗数据，请稍候..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    
    # --- 过滤器设计 ---
    st.subheader("📌 数据看板选项")
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1.5, 1])
    
    all_sites = sorted(df_master['Site'].unique().tolist())
    all_metrics = sorted(df_master['Metric'].unique().tolist())
    
    with col_filter1:
        selected_sites = st.multiselect("🌍 目标站点：", all_sites, default=all_sites)
    with col_filter2:
        default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
        if not default_metrics: default_metrics = [all_metrics[0]]
        selected_metrics = st.multiselect("📈 对比指标：", all_metrics, default=default_metrics)
    with col_filter3:
        min_date = df_master['Date'].min()
        max_date = df_master['Date'].max()
        selected_dates = st.date_input("📅 筛选日期范围：", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(selected_dates) == 2 and selected_sites and selected_metrics:
        start_date, end_date = selected_dates
        
        # 过滤主数据
        mask = (df_master['Site'].isin(selected_sites)) & \
               (df_master['Metric'].isin(selected_metrics)) & \
               (df_master['Date'] >= pd.to_datetime(start_date)) & \
               (df_master['Date'] <= pd.to_datetime(end_date))
        df_filtered = df_master[mask]
        
        if not df_filtered.empty:
            
            # ==========================================
            # 💡 核心数据卡片面板 (仿照广告后台大数字卡片)
            # ==========================================
            st.write("")
            st.subheader("🗓️ 核心指标概览 (选定周期内最新数据)")
            
            # 获取选定时间范围内的最后一天数据
            latest_date_in_range = df_filtered['Date'].max()
            previous_date = latest_date_in_range - pd.Timedelta(days=1)
            
            latest_data = df_filtered[df_filtered['Date'] == latest_date_in_range].groupby('Metric')['Value'].sum()
            prev_data = df_filtered[df_filtered['Date'] == previous_date].groupby('Metric')['Value'].sum()
            
            display_metrics = selected_metrics[:5]
            metric_cols = st.columns(len(display_metrics))
            
            for i, metric in enumerate(display_metrics):
                current_val = latest_data.get(metric, 0)
                previous_val = prev_data.get(metric, 0)
                
                # 计算环比涨跌幅
                delta_val = current_val - previous_val
                if previous_val != 0:
                    delta_pct = (delta_val / previous_val) * 100
                    delta_str = f"{delta_pct:+.1f}% 比前日"
                else:
                    delta_str = "0% 比前日"
                    
                with metric_cols[i]:
                    st.metric(
                        label=metric, 
                        value=f"{current_val:,.0f}", 
                        delta=delta_str
                    )
            
            st.write("---")
            
            # ==========================================
            # 📈 折线图表
            # ==========================================
            st.subheader("📈 时序对比走势")
            
            df_filtered['Legend'] = df_filtered['Site'] + " - " + df_filtered['Metric']
            
            fig = px.line(
                df_filtered, 
                x="Date", y="Value", color="Legend",
                markers=True,
                template="plotly_white"
            )
            
            fig.update_layout(
                xaxis_title="日期",
                yaxis_title="数值",
                legend_title="图例",
                hovermode="x unified",
                margin=dict(l=0, r=0, t=30, b=0),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # ==========================================
            # 🗄️ 数据明细表格
            # ==========================================
            st.write("---")
            st.subheader("🗄️ 明细数据报表")
            df_pivot = df_filtered.pivot_table(index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum').reset_index()
            df_pivot = df_pivot.sort_values(by="Date", ascending=False)
            df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        else:
            st.warning("所选区间或条件下无数据，请调整筛选器。")
else:
    st.info("👈 请先配置好 GCP 的 JSON 密钥，并在 Google Sheets 中开放访问权限。")
