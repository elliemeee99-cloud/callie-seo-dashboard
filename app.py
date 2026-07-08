import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# 网页基础设置 (宽屏模式)
st.set_page_config(page_title="小语种营销日报", page_icon="📈", layout="wide")

# ==========================================
# 🎨 1:1 深度复刻截图 UI (终极定制 CSS)
# ==========================================
st.markdown("""
<style>
/* 1. 整体页面背景底色 (极浅的灰蓝色，衬托白色组件) */
.stApp {
    background-color: #f4f7f9 !important;
}

/* 2. 隐藏默认的顶部导航和汉堡菜单 */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
.block-container {
    padding-top: 2rem !important;
}

/* 3. 左侧边栏重构 (纯白背景，灰色边框) */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0;
}
/* 隐藏侧边栏 Radio 的原生圆圈 */
[data-testid="stSidebar"] [role="radiogroup"] label div:first-of-type { 
    display: none; 
}
/* 侧边栏按钮基础样式 (对齐截图的垂直药丸) */
[data-testid="stSidebar"] [role="radiogroup"] label {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 15px;
    margin-bottom: 8px;
    background-color: #ffffff;
    color: #64748b;
    font-weight: 600;
    display: flex;
    justify-content: center;
    transition: all 0.2s;
}
/* 侧边栏按钮激活样式 (纯正深蓝色) */
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
    background-color: #2563eb !important; 
    color: #ffffff !important;
    border-color: #2563eb !important;
}

/* 4. 顶部横向标签 (Pills) 样式重构 */
button[data-testid="stPill"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    color: #64748b !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 8px 24px !important;
    margin-right: 8px !important;
}
/* 顶部标签激活样式 */
button[data-testid="stPill"][aria-selected="true"] {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border-color: #2563eb !important;
}

/* 5. 数据卡片样式 (白色底，居中，亮蓝色大数字) */
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
# ⚙️ 核心数据获取
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
            
            # 探测国家站缩写 (假设表格写的是 Callie DE, Callie FR)
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
        st.error(f"🔌 云端连接失败: {e}")
        return pd.DataFrame()


# ==========================================
# 📐 UI 布局与渲染
# ==========================================

# --- 1. 左侧边栏 (完美复刻垂直按钮切换) ---
site_map = {
    "全部站点": "ALL", "德国": "DE", "法国": "FR", 
    "西班牙": "ES", "意大利": "IT", "荷兰": "NL", 
    "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"
}

with st.sidebar:
    st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 13px; margin-bottom: 12px; writing-mode: vertical-lr; margin: 0 auto; letter-spacing: 5px;'>站点切换</div>", unsafe_allow_html=True)
    st.write("") # 占位
    selected_site_cn = st.radio("站点切换", list(site_map.keys()), label_visibility="collapsed")


# --- 2. 主页面头部 (大蓝字 + 日期) ---
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
st.markdown(f"""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #2563eb; font-size: 38px; font-weight: bold; margin-bottom: 8px;">小语种营销日报</h1>
    <div style="color: #64748b; font-size: 16px;">{today_str}</div>
</div>
""", unsafe_allow_html=True)


# --- 3. 横向导航菜单 (复刻截图) ---
tabs = ["目标管理看板", "每日数据看板", "各站数据看板", "SEO数据看板", "谷歌购物看板", "归因数据看板", "商品数据看板"]
selected_tab = st.pills("板块选择", tabs, default="SEO数据看板", label_visibility="collapsed")

st.write("") # 增加间距

# --- 4. 时间筛选器 (复刻截图) ---
times = ["过去1天", "过去7天", "过去14天", "按月份", "自定义"]
selected_time = st.pills("时间选择", times, default="过去1天", label_visibility="collapsed")

st.write("---")

# ==========================================
# 📊 数据处理与核心板块展示
# ==========================================

with st.spinner("🚀 同步数据中..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty and selected_tab == "SEO数据看板":
    
    # 获取数据源中的最新一天作为“昨天”
    max_date = df_master['Date'].max()
    prev_date = max_date - pd.Timedelta(days=1)
    
    # 根据侧边栏过滤站点
    target_site_code = site_map[selected_site_cn]
    if target_site_code != "ALL":
        df_filtered = df_master[df_master['Site'] == target_site_code]
    else:
        df_filtered = df_master
        
    # 如果数据没空
    if not df_filtered.empty:
        # 获取昨天和前天的聚合数据
        day_data = df_filtered[df_filtered['Date'] == max_date].groupby('Metric')['Value'].sum()
        prev_day_data = df_filtered[df_filtered['Date'] == prev_date].groupby('Metric')['Value'].sum()
        
        # 🤖 智能寻找代表“销售额”的指标
        sales_metric_key = None
        all_metrics = df_filtered['Metric'].unique()
        for m in all_metrics:
            if any(kw in m for kw in ["销售额", "转化价值", "成交额", "Sales", "Revenue"]):
                sales_metric_key = m
                break
                
        # 渲染卡片区域 (目前先放3个卡片看看效果)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 第一板块：精准展示昨日SEO销售额
            title_text = f"昨日 {sales_metric_key}" if sales_metric_key else "昨日SEO销售额"
            current_sales = day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
            prev_sales = prev_day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
            
            if prev_sales > 0:
                sales_delta = ((current_sales - prev_sales) / prev_sales) * 100
                delta_str = f"{sales_delta:+.1f}% 对比前日"
            else:
                delta_str = "0.0% 对比前日"
                
            st.metric(label=title_text, value=f"${current_sales:,.2f}", delta=delta_str)
            
        with col2:
            # 自动找一个流量指标填充占位
            traffic_metric = next((m for m in all_metrics if "流量" in m or "Traffic" in m), all_metrics[0])
            t_val = day_data.get(traffic_metric, 0.0)
            p_val = prev_day_data.get(traffic_metric, 0.0)
            d_str = f"{((t_val-p_val)/p_val)*100:+.1f}%" if p_val > 0 else "0%"
            st.metric(label=f"昨日 {traffic_metric}", value=f"{t_val:,.0f}", delta=d_str)

        with col3:
            # 占位卡片，后续可按需扩展
            st.metric(label="当前选中站点", value=selected_site_cn, delta="状态正常")
            
    else:
        st.warning(f"没有找到 {selected_site_cn} 的数据。")
