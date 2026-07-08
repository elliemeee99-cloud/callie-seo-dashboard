import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import datetime
import re

# 网页基础设置
st.set_page_config(page_title="小语种SEO日报", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 终极定制 CSS
# ==========================================
st.markdown("""
<style>
/* 整体页面背景底色 (极浅的灰蓝色) */
.stApp {
    background-color: #f4f7f9 !important;
}

/* 隐藏默认的顶部导航、汉堡菜单 */
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
@st.cache_data(ttl="1h") # 把缓存时间缩短为1小时，方便当天修改数据后快速生效
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
                        val_str = str(values[i]).strip()
                        
                        # 彻底忽略没填的格子
                        if not val_str or val_str == "-" or val_str.lower() in ["n/a", "null"]:
                            continue
                            
                        # 清理掉各种奇怪的符号
                        clean_str = val_str.replace("$", "").replace(",", "").replace("%", "").replace("€", "").replace("£", "")
                        clean_str = re.sub(r'[^\d\.-]', '', clean_str)
                        
                        try:
                            clean_val = float(clean_str) if clean_str else 0.0
                        except:
                            clean_val = 0.0
                            
                        clean_records.append({
                            "Date": date_str,
                            "Site": current_site,
                            "Metric": metric_name,
                            "Value": clean_val
                        })
                        
        df_long = pd.DataFrame(clean_records)
        # 将表格中抓出来的字符串转化为 Python 的时间戳格式 (去掉时分秒)
        df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce').dt.normalize()
        df_long = df_long.dropna(subset=['Date']) 
        return df_long
    except Exception as e:
        st.error(f"🔌 云端连接失败，详情: {e}")
        return pd.DataFrame()


# ==========================================
# 📐 UI 布局与渲染
# ==========================================

# --- 获取真实的物理“今天”和“昨天” ---
# 获取当前时间并标准化去掉时分秒，以此为基准进行计算
real_today = pd.Timestamp(datetime.datetime.now().date())
real_yesterday = real_today - pd.Timedelta(days=1)
real_day_before_yesterday = real_today - pd.Timedelta(days=2)

today_str = real_today.strftime("%Y年%m月%d日")

# --- 1. 主页面头部 ---
st.markdown(f"""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #2563eb; font-size: 38px; font-weight: bold; margin-bottom: 8px;">小语种SEO日报</h1>
    <div style="color: #64748b; font-size: 16px;">{today_str}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("🚀 正在从 Google Sheets 同步实时数据..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    
    # 建立国家站中英对照
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}
    
    raw_sites = sorted(df_master['Site'].unique().tolist())
    display_sites = ["全部站点"] + [en_to_cn.get(s, s) for s in raw_sites]
    
    # --- 2. 核心导航：站点切换 ---
    col_nav1, col_nav2, col_nav3 = st.columns([1, 6, 1])
    with col_nav2:
        selected_site_cn = st.pills("站点切换", display_sites, default="全部站点", label_visibility="collapsed")
    
    st.write("") 
    
    # --- 3. 核心导航：时间与指标筛选 ---
    col_filter1, col_filter2 = st.columns([1, 1])
    with col_filter1:
        times = ["过去1天", "过去7天", "过去14天", "全部数据"]
        selected_time = st.pills("时间选择", times, default="过去7天", label_visibility="collapsed")
    with col_filter2:
        all_metrics = sorted(df_master['Metric'].unique().tolist())
        default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
        if not default_metrics: default_metrics = [all_metrics[0]]
        selected_metrics = st.multiselect("📊 图表附加展示指标：", all_metrics, default=default_metrics, label_visibility="collapsed")

    st.write("---")

    # ==========================================
    # 📊 数据处理与展示
    # ==========================================
    
    # 根据站点过滤
    if selected_site_cn == "全部站点" or selected_site_cn is None:
        target_sites = raw_sites
    else:
        target_sites = [cn_to_en.get(selected_site_cn, selected_site_cn)]
        
    df_site = df_master[df_master['Site'].isin(target_sites)]
    
    if not df_site.empty:
        
        # 💡 以物理的“今天”为锚点往前推算过滤范围
        if selected_time == "过去1天":
            start_date = real_today - pd.Timedelta(days=1)
        elif selected_time == "过去7天":
            start_date = real_today - pd.Timedelta(days=7)
        elif selected_time == "过去14天":
            start_date = real_today - pd.Timedelta(days=14)
        else:
            start_date = df_site['Date'].min()
            
        # 注意：end_date 设定为 real_today 以确保能包容昨日的数据，即便今天没数据也无妨
        end_date = real_today 
            
        mask = (df_site['Date'] >= start_date) & (df_site['Date'] <= end_date)
        df_filtered = df_site[mask]
        
        # 💡 强制按照物理世界的“昨天”和“前天”进行聚合提取
        day_data = df_site[df_site['Date'] == real_yesterday].groupby('Metric')['Value'].sum()
        prev_day_data = df_site[df_site['Date'] == real_day_before_yesterday].groupby('Metric')['Value'].sum()
        
        # 优先级提取核心指标
        sales_metric_key = None
        for m in all_metrics:
            if "SEO销售" in m or "总销售" in m:
                sales_metric_key = m
                break
        if not sales_metric_key:
            for m in all_metrics:
                if any(kw in m for kw in ["销售额", "转化价值", "成交额", "Sales", "Revenue"]):
                    sales_metric_key = m
                    break
                    
        traffic_metric = None
        for m in all_metrics:
            if m in ["SEO流量", "网站总流量", "总流量"]:
                traffic_metric = m
                break
        if not traffic_metric:
            traffic_metric = next((m for m in all_metrics if "流量" in m or "Traffic" in m), all_metrics[0])
                
        # --- 渲染卡片 ---
        col_c1, col_c2, col_c3 = st.columns(3)
        
        # 卡片标签标明昨天的日期
        date_label = real_yesterday.strftime('%m/%d')
        
        with col_c1:
            title_text = f"[{date_label}] 昨日{sales_metric_key}" if sales_metric_key else f"[{date_label}] 昨日销售"
            current_sales = day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
            prev_sales = prev_day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
            
            if prev_sales > 0:
                sales_delta = ((current_sales - prev_sales) / prev_sales) * 100
                delta_str = f"{sales_delta:+.1f}% 对比前日"
            else:
                delta_str = "0.0% 对比前日"
                
            st.metric(label=title_text, value=f"${current_sales:,.2f}", delta=delta_str)
            
        with col_c2:
            t_val = day_data.get(traffic_metric, 0.0)
            p_val = prev_day_data.get(traffic_metric, 0.0)
            d_str = f"{((t_val-p_val)/p_val)*100:+.1f}% 对比前日" if p_val > 0 else "0%"
            st.metric(label=f"[{date_label}] 昨日{traffic_metric}", value=f"{t_val:,.0f}", delta=d_str)

        with col_c3:
            st.metric(label="当前分析视图", value=f"{selected_site_cn}", delta=f"昨日基准: {date_label}")
            
        # 如果当天发现数据是 0（极大可能是当天的数据还未录入完毕），给出醒目提示
        if day_data.empty or (current_sales == 0 and t_val == 0):
             st.info(f"⚠️ 注意: Google Sheets 中可能暂未录入昨天 ({date_label}) 完整的数据。")
            
        st.write("---")
        
        # --- 渲染图表 ---
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
            # 强行限定 x 轴范围至昨天，以免右侧留出大量空缺的未来空白区间
            fig.update_xaxes(range=[start_date, real_yesterday + pd.Timedelta(hours=12)])
            
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
            
        # --- 渲染表格 ---
        st.write("---")
        st.subheader("🗄️ 明细数据报表")
        if not df_chart.empty:
            df_pivot = df_chart.pivot_table(index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum').reset_index()
            df_pivot = df_pivot.sort_values(by="Date", ascending=False)
            df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
    else:
        st.warning(f"没有找到 {selected_site_cn} 的历史数据。")
else:
    st.info("👈 请先配置好 GCP 的 JSON 密钥，并在 Google Sheets 中开放访问权限。")
