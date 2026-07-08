import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import datetime

# 网页基础设置 (宽屏模式，隐藏默认侧边栏)
st.set_page_config(page_title="小语种SEO日报", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 终极定制 CSS (无侧边栏纯净版)
# ==========================================
st.markdown("""
<style>
/* 整体页面背景底色 (极浅的灰蓝色) */
.stApp {
    background-color: #f4f7f9 !important;
}

/* 隐藏默认的顶部导航、汉堡菜单和可能存在的侧边栏呼出按钮 */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}
.block-container {
    padding-top: 2rem !important;
    max-width: 95% !important;
}

/* 横向标签 (Pills) 样式重构 */
button[data-testid="stPill"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    color: #64748b !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 8px 24px !important;
    margin-right: 8px !important;
    transition: all 0.2s;
}
/* 顶部标签激活样式 (深蓝色) */
button[data-testid="stPill"][aria-selected="true"] {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border-color: #2563eb !important;
    font-weight: 600 !important;
}

/* 数据卡片样式 (白色底，居中，亮蓝色大数字) */
div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    align-items: center;
}
div[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 15px !important;
}
div[data-testid="metric-container"] div[data-testid="stMetricValue"] > div {
    color: #2563eb !important;
    font-size: 34px !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取与清洗
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
        st.error(f"🔌 云端连接失败，请检查密钥配置。详情: {e}")
        return pd.DataFrame()


# ==========================================
# 📐 UI 布局与渲染
# ==========================================

# --- 1. 主页面头部 (大蓝字 + 日期) ---
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
st.markdown(f"""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #2563eb; font-size: 38px; font-weight: bold; margin-bottom: 8px;">小语种SEO日报</h1>
    <div style="color: #64748b; font-size: 16px;">{today_str}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("🚀 正在从 Google Sheets 同步实时数据..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    
    # 建立缩写与中文映射 (根据 Callie 常见国家站)
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}
    
    raw_sites = sorted(df_master['Site'].unique().tolist())
    display_sites = ["全部站点"] + [en_to_cn.get(s, s) for s in raw_sites]
    
    # --- 2. 核心导航：居中的站点切换 ---
    col_nav1, col_nav2, col_nav3 = st.columns([1, 6, 1])
    with col_nav2:
        selected_site_cn = st.pills("站点切换", display_sites, default="全部站点", label_visibility="collapsed")
    
    st.write("") # 间距
    
    # --- 3. 核心导航：时间与指标扩展筛选 ---
    col_filter1, col_filter2 = st.columns([1, 1])
    with col_filter1:
        # 默认选中“过去7天”，让图表立刻呈现出折线趋势
        times = ["过去1天", "过去7天", "过去14天", "全部数据"]
        selected_time = st.pills("时间选择", times, default="过去7天", label_visibility="collapsed")
    with col_filter2:
        # 用于下方图表和表格的指标多选
        all_metrics = sorted(df_master['Metric'].unique().tolist())
        default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
        if not default_metrics: default_metrics = [all_metrics[0]]
        selected_metrics = st.multiselect("📊 图表附加展示指标：", all_metrics, default=default_metrics, label_visibility="collapsed")

    st.write("---")

    # ==========================================
    # 📊 数据处理与核心板块展示
    # ==========================================
    
    # 1. 解析目标站点
    if selected_site_cn == "全部站点" or selected_site_cn is None:
        target_sites = raw_sites
    else:
        target_sites = [cn_to_en.get(selected_site_cn, selected_site_cn)]
        
    df_site = df_master[df_master['Site'].isin(target_sites)]
    
    if not df_site.empty:
        # 💡 智能寻日逻辑：寻找该站点真正在表格里填了数据的“最新一天”和“倒数第二天”
        available_dates = sorted(df_site['Date'].dropna().unique())
        
        if len(available_dates) > 0:
            latest_date = pd.Timestamp(available_dates[-1])
            # 如果只有一天的数据，那上一天就用同一天防止报错
            prev_date = pd.Timestamp(available_dates[-2]) if len(available_dates) >= 2 else latest_date
            
            # 2. 根据表格真实的最新日期往前推算筛选范围
            if selected_time == "过去1天":
                start_date = latest_date - pd.Timedelta(days=1)
            elif selected_time == "过去7天":
                start_date = latest_date - pd.Timedelta(days=7)
            elif selected_time == "过去14天":
                start_date = latest_date - pd.Timedelta(days=14)
            else:
                start_date = df_site['Date'].min()
                
            # 3. 过滤出图表和明细表使用的数据
            mask = (df_site['Date'] >= start_date) & (df_site['Date'] <= latest_date)
            df_filtered = df_site[mask]
            
            # 获取最新一天和上一天的聚合数据，用于顶部卡片计算环比
            day_data = df_site[df_site['Date'] == latest_date].groupby('Metric')['Value'].sum()
            prev_day_data = df_site[df_site['Date'] == prev_date].groupby('Metric')['Value'].sum()
            
            # 🤖 智能寻找代表“销售额”的指标
            sales_metric_key = None
            for m in all_metrics:
                if any(kw in m for kw in ["销售额", "转化价值", "成交额", "Sales", "Revenue"]):
                    sales_metric_key = m
                    break
                    
            # --- 渲染卡片区域 ---
            col_c1, col_c2, col_c3 = st.columns(3)
            
            # 为了让用户知道数据是哪天的，我们在标题加上日期的月/日
            date_label = latest_date.strftime('%m/%d')
            
            with col_c1:
                title_text = f"[{date_label}] {sales_metric_key}" if sales_metric_key else f"[{date_label}] SEO销售额"
                current_sales = day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
                prev_sales = prev_day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
                
                if prev_sales > 0:
                    sales_delta = ((current_sales - prev_sales) / prev_sales) * 100
                    delta_str = f"{sales_delta:+.1f}% 对比上一记录日"
                else:
                    delta_str = "0.0% 对比上一记录日"
                    
                st.metric(label=title_text, value=f"${current_sales:,.2f}", delta=delta_str)
                
            with col_c2:
                traffic_metric = next((m for m in all_metrics if "流量" in m or "Traffic" in m), all_metrics[0])
                t_val = day_data.get(traffic_metric, 0.0)
                p_val = prev_day_data.get(traffic_metric, 0.0)
                d_str = f"{((t_val-p_val)/p_val)*100:+.1f}% 对比上一记录日" if p_val > 0 else "0%"
                st.metric(label=f"[{date_label}] {traffic_metric}", value=f"{t_val:,.0f}", delta=d_str)

            with col_c3:
                st.metric(label="当前分析视图", value=f"{selected_site_cn}", delta=f"已更新至 {date_label}")
                
            st.write("---")
            
            # --- 渲染图表区域 ---
            st.subheader("📈 核心指标时序走势")
            
            df_chart = df_filtered[df_filtered['Metric'].isin(selected_metrics)].copy()
            if not df_chart.empty:
                df_chart['Legend'] = df_chart['Site'] + " - " + df_chart['Metric']
                fig = px.line(
                    df_chart, 
                    x="Date", y="Value", color="Legend",
                    markers=True,
                    template="plotly_white",
                    color_discrete_sequence=["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#0284c7", "#0ea5e9"]
                )
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="数值",
                    hovermode="x unified",
                    margin=dict(l=10, r=10, t=20, b=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    legend_title="指标"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            # --- 渲染表格区域 ---
            st.write("---")
            st.subheader("🗄️ 明细数据报表")
            df_pivot = df_chart.pivot_table(index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum').reset_index()
            df_pivot = df_pivot.sort_values(by="Date", ascending=False)
            df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        else:
            st.warning(f"在 {selected_site_cn} 站点中未解析到有效的日期格式数据。")
    else:
        st.warning(f"没有找到 {selected_site_cn} 的数据，请检查谷歌表格中是否填入了该站点。")
else:
    st.info("👈 请先配置好 GCP 的 JSON 密钥，并在 Google Sheets 中开放访问权限。")
