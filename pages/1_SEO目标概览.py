import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import datetime
import calendar
import re
import gc

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO数据看板", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 🧭 顶部横向导航栏 & 隐藏原生侧边栏目录
# ==========================================
st.markdown("""
<style>
/* 1. 彻底隐藏 Streamlit 默认的侧边栏目录 */
[data-testid="stSidebarNav"] { display: none !important; }

/* 2. 美化横向导航按钮 */
[data-testid="stPageLink-NavLink"] { 
    background-color: #ffffff; 
    border: 1px solid #e2e8f0; 
    border-radius: 12px; 
    padding: 10px 16px; 
    text-align: center;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #f8fafc;
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
}
[data-testid="stPageLink-NavLink"] p {
    font-weight: 700 !important;
    color: #1e293b !important;
    font-size: 15px !important;
}
</style>
""", unsafe_allow_html=True)

# 使用 columns 横向排布导航按钮 (按需分配宽度)
col_nav1, col_nav2, col_nav3, _ = st.columns([1.2, 1.5, 1.5, 5])

with col_nav1:
    st.page_link("app.py", label="App 首页", icon="🏠")
with col_nav2:
    # 修复了路径：加上了 1_ 前缀
    st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with col_nav3:
    # 修复了路径：加上了 2_ 前缀
    st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")

st.markdown("<div style='margin-bottom: 24px; border-bottom: 1px solid #EEF2F6; padding-bottom: 10px;'></div>", unsafe_allow_html=True)

# ==========================================
# 🎨 定制 CSS (🚀 全新胶囊导航栏 & 卡片式筛选器)
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f8fafc !important; }
#MainMenu {visibility: hidden;}
/* 这里已经彻底清除了隐藏 Header 和侧边栏的代码 */
.block-container { padding-top: 3rem !important; max-width: 98% !important; }

/* 圆角分区容器 */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    padding: 10px;
}

/* 覆盖原生卡片字体 */
div[data-testid="stMetricValue"] > div { color: #0f172a !important; font-size: 26px !important; font-weight: 800 !important; }
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 14px !important; font-weight: 600 !important; }
div[data-testid="stMetricDelta"] > div { font-size: 14px !important; }

/* 自定义精美 HTML 表格悬浮效果 */
.custom-table-row:hover { background-color: #f1f5f9 !important; }

/* 🔥 顶部 Tab 看板切换 -> 蓝底胶囊风格 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] { gap: 12px !important; border-bottom: none !important; }
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { display: none !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"] { background-color: #f1f5f9 !important; border-radius: 8px !important; padding: 12px 28px !important; border: none !important; box-shadow: none !important; transition: all 0.3s ease; }
div[data-testid="stTabs"] button[data-baseweb="tab"] p { color: #64748b !important; font-weight: 700 !important; font-size: 17px !important; margin: 0 !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] { background-color: #2563eb !important; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3) !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p { color: #ffffff !important; }

/* 🔥 Radio 日期聚合切换 -> 卡片式按钮 */
div[data-testid="stRadio"] div[role="radiogroup"] { display: flex !important; flex-direction: row !important; gap: 10px !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: #f1f5f9 !important; padding: 8px 24px !important; border-radius: 8px !important; cursor: pointer !important; transition: all 0.2s; }
div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child { display: none !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] p { color: #64748b !important; font-weight: 600 !important; margin: 0 !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"], div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background-color: #2563eb !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p, div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color: #ffffff !important; }

/* 🔥 多选框站点筛选 -> 统一蓝色实心胶囊 */
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] { background-color: #2563eb !important; color: #ffffff !important; border-radius: 8px !important; padding: 6px 14px !important; font-weight: 600 !important; border: none !important; }
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span { color: #ffffff !important; }
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg { fill: #ffffff !important; }

/* 🔥 同步数据按钮样式优化 */
div[data-testid="stButton"] button { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; color: #1e293b !important; font-weight: 600 !important; border-radius: 8px !important; padding: 10px 16px !important; transition: all 0.2s ease !important; }
div[data-testid="stButton"] button:hover { border-color: #2563eb !important; color: #2563eb !important; background-color: #f8fafc !important; box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取引擎 
# ==========================================
@st.cache_data(ttl=3600)
def load_and_transform_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit")
        
        cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
        fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
        
        sales_data = {}
        target_sales_data = {}
        target_traffic_data = {}
        historical_records = []
        traffic_records = []
        
        default_year = str(datetime.datetime.now().year)

        # --- 1. 读取 SEO销售额目标完成情况 ---
        try:
            sheet2 = spreadsheet.worksheet("SEO销售额目标完成情况")
            raw_data_2 = sheet2.get_all_values()
            if raw_data_2:
                headers_2 = []
                for row in raw_data_2:
                    row_strs = [str(x).strip() for x in row]
                    if any(k in row_strs for k in ["DE", "FR", "德国", "法国", "Callie DE"]):
                        headers_2 = row_strs
                        break
                
                if not headers_2:
                    headers_2 = raw_data_2[0] 
                
                for row in raw_data_2:
                    if not row or not row[0]: continue
                    first_col = str(row[0]).strip()
                    
                    if first_col == "总计":
                        for i in range(1, min(len(headers_2), len(row))):
                            raw_site = headers_2[i].strip()
                            clean_site = raw_site.replace("Callie ", "").strip()
                            if clean_site in cn_to_en: clean_site = cn_to_en[clean_site]
                            if clean_site not in fixed_sites_order: continue
                            
                            val_str = row[i].strip()
                            clean_str = re.sub(r'[^\d\.-]', '', val_str)
                            sales_data[clean_site] = float(clean_str) if clean_str else 0.0
                            
                    elif first_col == "分站点目标": 
                        for i in range(1, min(len(headers_2), len(row))):
                            raw_site = headers_2[i].strip()
                            clean_site = raw_site.replace("Callie ", "").strip()
                            if clean_site in cn_to_en: clean_site = cn_to_en[clean_site]
                            if clean_site not in fixed_sites_order: continue
                            
                            val_str = row[i].strip()
                            clean_str = re.sub(r'[^\d\.-]', '', val_str)
                            target_sales_data[clean_site] = float(clean_str) if clean_str else 0.0
                            
                    elif re.search(r'\d', first_col): 
                        try:
                            if "月" in first_col and "日" in first_col:
                                month = first_col.split('月')[0].strip()
                                day = first_col.split('月')[1].replace('日', '').strip()
                                date_str = f"{default_year}-{month}-{day}"
                            else:
                                date_str = first_col
                                
                            for i in range(1, min(len(headers_2), len(row))):
                                raw_site = headers_2[i].strip()
                                clean_site = raw_site.replace("Callie ", "").strip()
                                if clean_site in cn_to_en: clean_site = cn_to_en[clean_site]
                                if clean_site not in fixed_sites_order: continue
                                
                                val_str = row[i].strip()
                                clean_str = re.sub(r'[^\d\.-]', '', val_str)
                                val = float(clean_str) if clean_str else 0.0
                                historical_records.append({"Date": date_str, "Site": clean_site, "Value": val})
                        except:
                            continue
        except Exception as e:
            print(f"SEO销售额目标完成情况 读取失败: {e}")

        # --- 2. 读取 SEO月度流量目标 ---
        try:
            sheet3 = spreadsheet.worksheet("SEO月度流量目标")
            raw_data_3 = sheet3.get_all_values()
            if raw_data_3:
                headers_3 = []
                for row in raw_data_3:
                    row_strs = [str(x).strip() for x in row]
                    if any(k in row_strs for k in ["DE", "FR", "德国", "法国", "Callie DE"]):
                        headers_3 = row_strs
                        break
                
                if headers_3:
                    for row in raw_data_3:
                        if not row or not row[0]: continue
                        first_col = str(row[0]).strip()
                        if "目标" in first_col or "Target" in first_col: 
                            for i in range(1, min(len(headers_3), len(row))):
                                raw_site = headers_3[i].strip()
                                if not raw_site: continue
                                clean_site = raw_site.replace("Callie ", "").strip()
                                if clean_site in cn_to_en:
                                    clean_site = cn_to_en[clean_site]
                                if clean_site in fixed_sites_order:
                                    val_str = str(row[i]).strip()
                                    clean_str = re.sub(r'[^\d\.-]', '', val_str)
                                    target_traffic_data[clean_site] = float(clean_str) if clean_str else 0.0
        except Exception as e:
            print(f"SEO月度流量目标 读取失败: {e}")

        # --- 3. 读取 All ---
        try:
            sheet1 = spreadsheet.worksheet("All")
            raw_data_1 = sheet1.get_all_values()
            
            dates_row = []
            current_site = None
            captured_traffic = False
            
            for row in raw_data_1:
                if not row: continue
                first_cell = str(row[0]).strip()
                
                if len(row) > 1:
                    check_val = str(row[1]).strip()
                    if "202" in check_val or ("月" in check_val and "日" in check_val) or re.match(r'^\d{1,2}[-/]\d{1,2}$', check_val):
                        dates_row = [str(x).strip() for x in row[1:]]
                    
                if first_cell.startswith("Callie ") and len(first_cell) <= 15:
                    current_site = first_cell.replace("Callie ", "").strip()
                    if current_site in cn_to_en:
                        current_site = cn_to_en[current_site]
                    captured_traffic = False 
                    continue
                
                clean_metric_name = re.sub(r'\s+', '', first_cell).upper()
                if current_site and clean_metric_name in ["SEO总流量", "SEO流量"] and not captured_traffic:
                    values = row[1:]
                    for i in range(len(values)):
                        if i < len(dates_row) and dates_row[i] != "":
                            v_str = str(values[i]).strip()
                            if v_str:
                                clean_str = re.sub(r'[^\d\.-]', '', v_str)
                                try:
                                    val = float(clean_str) if clean_str else 0.0
                                except ValueError:
                                    val = 0.0
                                
                                d_str = dates_row[i]
                                if "月" in d_str and "日" in d_str:
                                    try:
                                        m = d_str.split('月')[0].strip()
                                        d = d_str.split('月')[1].replace('日', '').strip()
                                        d_str = f"{default_year}-{m}-{d}"
                                    except:
                                        pass
                                        
                                traffic_records.append({"Date": d_str, "Site": current_site, "Value": val})
                    captured_traffic = True 
        except Exception as e:
            print(f"All 读取失败: {e}")
                        
        df_hist = pd.DataFrame(historical_records)
        if not df_hist.empty:
            df_hist['Date'] = pd.to_datetime(df_hist['Date'], errors='coerce')
            df_hist = df_hist.dropna(subset=['Date'])
            df_hist['Date'] = df_hist['Date'].dt.normalize()
            
        df_traffic = pd.DataFrame(traffic_records)
        if not df_traffic.empty:
            df_traffic['Date'] = pd.to_datetime(df_traffic['Date'], errors='coerce')
            df_traffic = df_traffic.dropna(subset=['Date'])
            df_traffic['Date'] = df_traffic['Date'].dt.normalize()
            
        del raw_data_1
        gc.collect()
            
        return {"sales": sales_data, "targets_sales": target_sales_data, "targets_traffic": target_traffic_data, "historical_df": df_hist, "traffic_df": df_traffic}
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None


# ==========================================
# 📐 数据流初始化与时间基准锁定
# ==========================================
real_today = pd.Timestamp(datetime.datetime.now().date())
latest_date = real_today - pd.Timedelta(days=1)  
start_of_current_month = latest_date.replace(day=1)

with st.spinner("✨ 正在深度清洗多表数据资产..."):
    data_dict = load_and_transform_google_sheet()

if data_dict:
    sales_data = data_dict["sales"]
    target_sales_data = data_dict["targets_sales"]
    target_traffic_data = data_dict["targets_traffic"]
    df_hist = data_dict["historical_df"]
    df_traffic = data_dict["traffic_df"]
    
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    en_to_cn = {
        "DE": "🇩🇪 德国", "FR": "🇫🇷 法国", "ES": "🇪🇸 西班牙", "IT": "🇮🇹 意大利", 
        "NL": "🇳🇱 荷兰", "NO": "🇳🇴 挪威", "SE": "🇸🇪 瑞典", "FI": "🇫🇮 芬兰", "PL": "🇵🇱 波兰"
    }

    col_header, col_refresh = st.columns([5, 1])
    with col_header:
        st.markdown(f"""
        <div style="margin-bottom: 25px;">
            <h1 style="color: #1e293b; font-size: 32px; font-weight: 800; margin-bottom: 4px;">🚀 SEO数据全局看板</h1>
            <div style="color: #64748b; font-size: 14px;">报表同步基准日：{latest_date.strftime('%Y-%m-%d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_refresh:
        st.write("") 
        if st.button("🔄 同步最新数据"):
            load_and_transform_google_sheet.clear() 
            st.rerun()

    # ==========================================
    # 🎛️ 顶层双大盘看板导航切换系统
    # ==========================================
    tab_dashboard, tab_details = st.tabs(["📊 SEO月度目标完成情况", "🗄️ 数据明细分析"])

    # ------------------------------------------
    # 🏆 第一大看板：SEO月度目标完成情况
    # ------------------------------------------
    with tab_dashboard:
        days_in_month = calendar.monthrange(latest_date.year, latest_date.month)[1]
        current_day = latest_date.day
        time_progress_rate = (current_day / days_in_month) * 100

        # 🔥 核心：计算本月剩余天数（包含真实今天）
        days_in_current_month = calendar.monthrange(real_today.year, real_today.month)[1]
        remaining_days = days_in_current_month - real_today.day + 1
        if remaining_days <= 0:
            remaining_days = 1  # 兜底避免除0报错

        total_sales_actual = sales_data.get("总计", sum([sales_data.get(s, 0) for s in fixed_sites_order]))
        total_sales_target = sum([target_sales_data.get(s, 0) for s in fixed_sites_order])
        s_total_rate = (total_sales_actual / total_sales_target * 100) if total_sales_target > 0 else 0
        capped_s_rate = min(s_total_rate, 100) 

        actual_traffic_map = {}
        if not df_traffic.empty:
            mask_mtd_traffic = (df_traffic['Date'] >= pd.to_datetime(start_of_current_month)) & (df_traffic['Date'] <= pd.to_datetime(latest_date))
            mtd_traffic_df = df_traffic[mask_mtd_traffic]
            for s in fixed_sites_order:
                actual_traffic_map[s] = mtd_traffic_df[mtd_traffic_df['Site'] == s]['Value'].sum()
        else:
            for s in fixed_sites_order: actual_traffic_map[s] = 0.0
            
        total_traffic_actual = sum(actual_traffic_map.values())
        total_traffic_target = sum([target_traffic_data.get(s, 0) for s in fixed_sites_order])
        t_total_rate = (total_traffic_actual / total_traffic_target * 100) if total_traffic_target > 0 else 0
        capped_t_rate = min(t_total_rate, 100)

        # 销售额目标进度
        st.markdown("### 💰 销售额目标进度")
        s_cheer = "🎉 完美达标！" if s_total_rate >= 100 else ("🔥 销售额超前！" if s_total_rate >= time_progress_rate else "✨ 销售额加速中！")
        with st.container(border=True):
            col_s1, col_s2 = st.columns([1, 2.5])
            with col_s1:
                st.write("")
                st.metric("🎯 本月销售总目标", f"${total_sales_target:,.2f}")
                st.metric("💰 累计实际完成", f"${total_sales_actual:,.2f}", f"进度 {s_total_rate:.1f}%")
            with col_s2:
                st.write("")
                s_html = (
                    f'<div style="padding: 0px 20px;">'
                    f'<div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #475569; font-weight: 600; font-size: 15px;">'
                    f'<span>{s_cheer}</span><span style="color: #f43f5e; font-size: 18px;">{s_total_rate:.1f}%</span>'
                    f'</div>'
                    f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 28px; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 22px;">'
                    f'<div style="background: linear-gradient(90deg, #fbcfe8 0%, #f43f5e 100%); border-radius: 30px; width: {capped_s_rate}%; height: 100%;"></div>'
                    f'<div style="position: absolute; top: -12px; left: calc({capped_s_rate}% - 20px); font-size: 32px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1));">🚀</div>'
                    f'<div style="position: absolute; top: 0px; right: 10px; line-height: 28px; font-size: 18px;">🏁</div>'
                    f'</div>'
                    f'<div style="display: flex; justify-content: space-between; margin-bottom: 6px; color: #64748b; font-weight: 500; font-size: 13px;">'
                    f'<span>⏳ 时间进度 ({current_day} / {days_in_month} 天)</span><span>{time_progress_rate:.1f}%</span>'
                    f'</div>'
                    f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 10px; position: relative; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">'
                    f'<div style="background: linear-gradient(90deg, #bae6fd 0%, #3b82f6 100%); border-radius: 30px; width: {time_progress_rate}%; height: 100%;"></div>'
                    f'</div></div>'
                )
                st.markdown(s_html, unsafe_allow_html=True)

        with st.container(border=True):
            cols = st.columns(9)
            for i, site in enumerate(fixed_sites_order):
                with cols[i]:
                    s_actual = sales_data.get(site, 0)
                    s_target = target_sales_data.get(site, 0)
                    s_rate = (s_actual / s_target * 100) if s_target > 0 else 0
                    color = "normal" if s_rate >= time_progress_rate else "off"
                    
                    # 🔥 替换为：剩余日均算法
                    sales_diff = s_target - s_actual
                    if sales_diff > 0:
                        daily_sales_needed = sales_diff / remaining_days
                        delta_str = f"剩余日均 ${daily_sales_needed:,.0f}"
                    else:
                        delta_str = "已达标"
                        
                    st.metric(label=f"{en_to_cn[site]} (🎯${s_target:,.0f})", value=f"${s_actual:,.0f}", delta=delta_str, delta_color=color)
                    
                    bar_color = '#10b981' if s_rate >= time_progress_rate else '#f43f5e'
                    site_html = (
                        f'<div style="margin-top: 5px;">'
                        f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">'
                        f'<span>业绩</span><span style="font-weight: 600; color: {bar_color};">{s_rate:.1f}%</span>'
                        f'</div><div style="background-color: #f1f5f9; border-radius: 10px; width: 100%; height: 6px; margin-bottom: 10px;">'
                        f'<div style="background-color: {bar_color}; border-radius: 10px; width: {min(s_rate, 100)}%; height: 100%;"></div></div>'
                        f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">'
                        f'<span>时间</span><span>{time_progress_rate:.1f}%</span>'
                        f'</div><div style="background-color: #f1f5f9; border-radius: 10px; width: 100%; height: 6px;">'
                        f'<div style="background-color: #3b82f6; border-radius: 10px; width: {time_progress_rate}%; height: 100%;"></div></div></div>'
                    )
                    st.markdown(site_html, unsafe_allow_html=True)

        st.markdown("### 📈 全局 MTD 销售同环比")
        with st.container(border=True):
            if not df_hist.empty:
                try:
                    start_of_last_month = (start_of_current_month - pd.Timedelta(days=1)).replace(day=1)
                    end_of_last_month_mtd = start_of_last_month + pd.Timedelta(days=current_day - 1)
                except:
                    start_of_last_month = start_of_current_month - pd.DateOffset(months=1)
                    end_of_last_month_mtd = start_of_last_month + pd.DateOffset(days=current_day - 1)
                start_of_last_year_month = start_of_current_month - pd.DateOffset(years=1)
                end_of_last_year_mtd = start_of_last_year_month + pd.DateOffset(days=current_day - 1)
                
                mask_mom = (df_hist['Date'] >= pd.to_datetime(start_of_last_month)) & (df_hist['Date'] <= pd.to_datetime(end_of_last_month_mtd))
                total_mom_historical = df_hist[mask_mom]['Value'].sum()
                mask_yoy = (df_hist['Date'] >= pd.to_datetime(start_of_last_year_month)) & (df_hist['Date'] <= pd.to_datetime(end_of_last_year_mtd))
                total_yoy_historical = df_hist[mask_yoy]['Value'].sum()
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1: st.metric(label=f"当前本月累计 (1日-{current_day}日)", value=f"${total_sales_actual:,.2f}")
                with col_m2: st.metric(label=f"上月同期 ({start_of_last_month.strftime('%m/%d')}-{end_of_last_month_mtd.strftime('%m/%d')})", value=f"${total_mom_historical:,.2f}", delta=f"{((total_sales_actual - total_mom_historical) / total_mom_historical) * 100:+.1f}% (环比)" if total_mom_historical > 0 else "0.0% (无历史)")
                with col_m3: st.metric(label=f"去年同期 ({start_of_last_year_month.strftime('%Y/%m/%d')}-{end_of_last_year_mtd.strftime('%m/%d')})", value=f"${total_yoy_historical:,.2f}", delta=f"{((total_sales_actual - total_yoy_historical) / total_yoy_historical) * 100:+.1f}% (同比)" if total_yoy_historical > 0 else "0.0% (无历史)")
            else:
                st.info("尚未在表单中抓取到有效的历史同环比数据。")

        st.markdown("### 🗄️ 本月各站点每日销售明细")
        with st.container(border=True):
            if not df_hist.empty:
                mask_mtd = (df_hist['Date'] >= pd.to_datetime(start_of_current_month)) & (df_hist['Date'] <= pd.to_datetime(latest_date))
                df_mtd_daily = df_hist[mask_mtd]
                
                if not df_mtd_daily.empty:
                    df_pivot = df_mtd_daily.pivot_table(index='Date', columns='Site', values='Value', aggfunc='sum').reset_index()
                    if "总计" not in df_pivot.columns: df_pivot['总计'] = df_pivot[[s for s in fixed_sites_order if s in df_pivot.columns]].sum(axis=1)
                    display_cols = ['Date'] + [s for s in fixed_sites_order if s in df_pivot.columns] + ['总计']
                    df_pivot = df_pivot[display_cols].sort_values('Date', ascending=False)
                    df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
                    rename_dict = {s: en_to_cn.get(s, s) for s in fixed_sites_order}
                    rename_dict["Date"] = "日期"
                    df_pivot = df_pivot.rename(columns=rename_dict)

                    html_table = '<div style="overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px;"><table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: center;"><thead><tr style="background-color: #ffffff;">'
                    for col in df_pivot.columns: html_table += f'<th style="color: #2563eb; font-weight: 600; padding: 14px 10px; border-bottom: 2px solid #e2e8f0;">{col}</th>'
                    html_table += '</tr></thead><tbody>'
                    for idx, row in df_pivot.iterrows():
                        bg_color = "#ffffff" if idx % 2 == 0 else "#f8fafc"
                        html_table += f'<tr class="custom-table-row" style="background-color: {bg_color}; border-bottom: 1px solid #f1f5f9;">'
                        for col in df_pivot.columns:
                            val = row[col]
                            display_val = f"${val:,.2f}" if isinstance(val, (int, float)) else str(val)
                            cell_style = "padding: 12px 10px; color: #334155;"
                            if col == "总计": cell_style += " background-color: #ecfdf5; font-weight: 700; color: #065f46; border-left: 1px solid #d1fae5;"
                            elif col == "日期": cell_style += " font-weight: 500; color: #475569;"
                            html_table += f'<td style="{cell_style}">{display_val}</td>'
                        html_table += '</tr>'
                    st.markdown(html_table + '</tbody></table></div>', unsafe_allow_html=True)
                else:
                    st.info("💡 当前月份暂无每日销售明细数据。")
            else:
                st.info("💡 尚未抓取到任何历史销售数据。")

        st.write("---")
        st.markdown("### 📊 SEO流量目标进度")
        t_cheer = "🎉 流量完美达标！" if t_total_rate >= 100 else ("🌊 流量超前涌入！" if t_total_rate >= time_progress_rate else "✨ 流量蓄力中，冲鸭！")
        with st.container(border=True):
            col_t1, col_t2 = st.columns([1, 2.5])
            with col_t1:
                st.write("")
                st.metric("🎯 本月流量总目标", f"{total_traffic_target:,.0f}")
                st.metric("🌊 累计实际流量", f"{total_traffic_actual:,.0f}", f"进度 {t_total_rate:.1f}%")
            with col_t2:
                st.write("")
                t_html = (
                    f'<div style="padding: 0px 20px;">'
                    f'<div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #475569; font-weight: 600; font-size: 15px;">'
                    f'<span>{t_cheer}</span><span style="color: #0284c7; font-size: 18px;">{t_total_rate:.1f}%</span>'
                    f'</div>'
                    f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 28px; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 22px;">'
                    f'<div style="background: linear-gradient(90deg, #bae6fd 0%, #0284c7 100%); border-radius: 30px; width: {capped_t_rate}%; height: 100%;"></div>'
                    f'<div style="position: absolute; top: -12px; left: calc({capped_t_rate}% - 20px); font-size: 32px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1));">🚀</div>'
                    f'<div style="position: absolute; top: 0px; right: 10px; line-height: 28px; font-size: 18px;">🏁</div>'
                    f'</div>'
                    f'<div style="display: flex; justify-content: space-between; margin-bottom: 6px; color: #64748b; font-weight: 500; font-size: 13px;">'
                    f'<span>⏳ 时间进度 ({current_day} / {days_in_month} 天)</span><span>{time_progress_rate:.1f}%</span>'
                    f'</div>'
                    f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 10px; position: relative; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">'
                    f'<div style="background: linear-gradient(90deg, #cbd5e1 0%, #64748b 100%); border-radius: 30px; width: {time_progress_rate}%; height: 100%;"></div>'
                    f'</div></div>'
                )
                st.markdown(t_html, unsafe_allow_html=True)

        with st.container(border=True):
            cols = st.columns(9)
            for i, site in enumerate(fixed_sites_order):
                with cols[i]:
                    t_actual = actual_traffic_map.get(site, 0)
                    t_target = target_traffic_data.get(site, 0)
                    t_rate = (t_actual / t_target * 100) if t_target > 0 else 0
                    color = "normal" if t_rate >= time_progress_rate else "off"
                    
                    # 🔥 替换为：剩余日均算法
                    traffic_diff = t_target - t_actual
                    if traffic_diff > 0:
                        daily_traffic_needed = traffic_diff / remaining_days
                        delta_str = f"剩余日均 {daily_traffic_needed:,.0f}"
                    else:
                        delta_str = "已达标"
                        
                    st.metric(label=f"{en_to_cn[site]} (🎯{t_target:,.0f})", value=f"{t_actual:,.0f}", delta=delta_str, delta_color=color)
                    
                    bar_color = '#10b981' if t_rate >= time_progress_rate else '#f43f5e'
                    site_html = (
                        f'<div style="margin-top: 5px;">'
                        f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">'
                        f'<span>流量</span><span style="font-weight: 600; color: {bar_color};">{t_rate:.1f}%</span>'
                        f'</div><div style="background-color: #f1f5f9; border-radius: 10px; width: 100%; height: 6px; margin-bottom: 10px;">'
                        f'<div style="background-color: {bar_color}; border-radius: 10px; width: {min(t_rate, 100)}%; height: 100%;"></div></div>'
                        f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">'
                        f'<span>时间</span><span>{time_progress_rate:.1f}%</span>'
                        f'</div><div style="background-color: #f1f5f9; border-radius: 10px; width: 100%; height: 6px;">'
                        f'<div style="background-color: #cbd5e1; border-radius: 10px; width: {time_progress_rate}%; height: 100%;"></div></div></div>'
                    )
                    st.markdown(site_html, unsafe_allow_html=True)

        st.markdown("### 🗄️ 本月各站点每日SEO流量明细")
        with st.container(border=True):
            if not df_traffic.empty:
                mask_traffic = (df_traffic['Date'] >= pd.to_datetime(start_of_current_month)) & (df_traffic['Date'] <= pd.to_datetime(latest_date))
                df_t_daily = df_traffic[mask_traffic]
                
                if not df_t_daily.empty:
                    df_t_pivot = df_t_daily.pivot_table(index='Date', columns='Site', values='Value', aggfunc='sum').reset_index()
                    if "总计" not in df_t_pivot.columns: df_t_pivot['总计'] = df_t_pivot[[s for s in fixed_sites_order if s in df_t_pivot.columns]].sum(axis=1)
                    df_t_pivot = df_t_pivot[['Date'] + [s for s in fixed_sites_order if s in df_t_pivot.columns] + ['总计']].sort_values('Date', ascending=False)
                    df_t_pivot['Date'] = df_t_pivot['Date'].dt.strftime('%Y-%m-%d')
                    df_t_pivot = df_t_pivot.rename(columns=rename_dict)

                    html_t_table = '<div style="overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px;"><table style="width: 100%; border-collapse: collapse; font-size: 14px; text-align: center;"><thead><tr style="background-color: #ffffff;">'
                    for col in df_t_pivot.columns: html_t_table += f'<th style="color: #2563eb; font-weight: 600; padding: 14px 10px; border-bottom: 2px solid #e2e8f0;">{col}</th>'
                    html_t_table += '</tr></thead><tbody>'
                    for idx, row in df_t_pivot.iterrows():
                        bg_color = "#ffffff" if idx % 2 == 0 else "#f8fafc"
                        html_t_table += f'<tr class="custom-table-row" style="background-color: {bg_color}; border-bottom: 1px solid #f1f5f9;">'
                        for col in df_t_pivot.columns:
                            val = row[col]
                            display_val = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                            cell_style = "padding: 12px 10px; color: #334155;"
                            if col == "总计": cell_style += " background-color: #f0f9ff; font-weight: 700; color: #0369a1; border-left: 1px solid #bae6fd;"
                            elif col == "日期": cell_style += " font-weight: 500; color: #475569;"
                            html_t_table += f'<td style="{cell_style}">{display_val}</td>'
                        html_t_table += '</tr>'
                    st.markdown(html_t_table + '</tbody></table></div>', unsafe_allow_html=True)
                else:
                    st.info("💡 当前月份暂无每日SEO流量明细数据被记录。")
            else:
                st.info("💡 尚未抓取到任何每日流量历史数据。")


    # ------------------------------------------
    # 🗄️ 第二大看板：数据明细分析 (🔥 全新联动体系)
    # ------------------------------------------
    with tab_details:
        # --- 统一控制中枢 ---
        with st.container(border=True):
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1.2, 2.5])
            with col_ctrl1:
                time_grain = st.radio("⏱️ 时间聚合粒度", ["日", "周", "月"], index=0, horizontal=True)
            with col_ctrl2:
                # 智能推断日期筛选器的默认起止范围
                min_date = start_of_current_month.date()
                max_date = latest_date.date()
                if not df_hist.empty:
                    min_date = min(min_date, df_hist['Date'].min().date())
                
                date_range = st.date_input(
                    "📅 自定义日期范围", 
                    value=(start_of_current_month.date(), latest_date.date()),
                    max_value=latest_date.date()
                )
            with col_ctrl3:
                selected_sites = st.multiselect(
                    "🌍 筛选站点",
                    options=fixed_sites_order,
                    default=fixed_sites_order,
                    format_func=lambda x: en_to_cn.get(x, x)
                )

        if selected_sites:
            # 安全解析日期
            if isinstance(date_range, (tuple, list)):
                if len(date_range) == 2:
                    start_date, end_date = date_range
                elif len(date_range) == 1:
                    start_date = end_date = date_range[0]
                else:
                    start_date, end_date = start_of_current_month.date(), latest_date.date()
            else:
                start_date = end_date = date_range
            
            if start_date > end_date:
                start_date, end_date = end_date, start_date
            
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            # ECharts 经典清新高饱和配色
            color_palette = ['#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']

            # ==========================================
            # 📈 销售额趋势部分
            # ==========================================
            st.markdown("## 📈 SEO历史销售额趋势")
            if not df_hist.empty:
                mask_s_date = (df_hist['Date'] >= start_dt) & (df_hist['Date'] <= end_dt)
                df_s_filtered = df_hist[mask_s_date & df_hist['Site'].isin(selected_sites)].copy()
                
                if not df_s_filtered.empty:
                    if time_grain == "周": df_s_filtered['Date_Axis'] = df_s_filtered['Date'].dt.to_period('W').dt.to_timestamp()
                    elif time_grain == "月": df_s_filtered['Date_Axis'] = df_s_filtered['Date'].dt.to_period('M').dt.to_timestamp()
                    else: df_s_filtered['Date_Axis'] = df_s_filtered['Date']

                    # --- 销售额：总趋势曲线 ---
                    df_s_total_trend = df_s_filtered.groupby('Date_Axis')['Value'].sum().reset_index()
                    fig_s_total = go.Figure()
                    fig_s_total.add_trace(go.Scatter(
                        x=df_s_total_trend['Date_Axis'], y=df_s_total_trend['Value'],
                        mode='lines+markers', line=dict(color='#2563eb', width=3.5),
                        marker=dict(size=6, color='#ffffff', line=dict(color='#2563eb', width=2)), 
                        name='总销售额', hovertemplate='<b>日期</b>: %{x}<br><b>总销售额</b>: $%{y:,.2f}<extra></extra>'
                    ))
                    fig_s_total.update_layout(
                        title=dict(text="📊 选定站点 SEO 总销售额趋势", font=dict(size=16, color='#1e293b', weight='bold')),
                        height=350, plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified', margin=dict(l=20, r=20, t=50, b=20),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickformat='%Y-%m-%d' if time_grain=='日' else '%Y-%m'),
                        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
                    )
                    
                    st.write("")
                    with st.container(border=True):
                        st.plotly_chart(fig_s_total, use_container_width=True)

                    # --- 销售额：混合柱状图 ---
                    df_s_site_trend = df_s_filtered.groupby(['Date_Axis', 'Site'])['Value'].sum().reset_index()
                    fig_s_sites = go.Figure()
                    
                    for idx, site in enumerate(fixed_sites_order):
                        if site in selected_sites:
                            df_s_single = df_s_site_trend[df_s_site_trend['Site'] == site]
                            site_label = en_to_cn.get(site, site)
                            fig_s_sites.add_trace(go.Bar(
                                x=df_s_single['Date_Axis'], y=df_s_single['Value'],
                                name=site_label, marker_color=color_palette[idx % len(color_palette)],
                                hovertemplate=f'<b>{site_label}</b>: $%%{{y:,.2f}}<extra></extra>'
                            ))
                    
                    fig_s_sites.add_trace(go.Scatter(
                        x=df_s_total_trend['Date_Axis'], y=df_s_total_trend['Value'],
                        mode='lines+markers', line=dict(color='#1e293b', width=2, dash='dot'),
                        marker=dict(size=5, color='#1e293b'),
                        name='选定站点总计', hovertemplate='<b>总计</b>: $%{y:,.2f}<extra></extra>'
                    ))
                            
                    fig_s_sites.update_layout(
                        title=dict(text="🌍 各站点 SEO 销售额成分对比 (柱线混合图)", font=dict(size=16, color='#1e293b', weight='bold')),
                        height=450, plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified', barmode='stack', 
                        margin=dict(l=20, r=20, t=50, b=80), 
                        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=12)),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickformat='%Y-%m-%d' if time_grain=='日' else '%Y-%m'),
                        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
                    )
                    with st.container(border=True):
                        st.plotly_chart(fig_s_sites, use_container_width=True)
                else:
                    st.info("💡 当前选定的日期范围内，尚未抓取到有效【销售数据】。")
            else:
                st.info("💡 底表中缺乏历史【销售明细数据】。")

            st.write("---")

            # ==========================================
            # 🌊 流量趋势部分
            # ==========================================
            st.markdown("## 🌊 SEO历史流量趋势")
            if not df_traffic.empty:
                mask_t_date = (df_traffic['Date'] >= start_dt) & (df_traffic['Date'] <= end_dt)
                df_t_filtered = df_traffic[mask_t_date & df_traffic['Site'].isin(selected_sites)].copy()
                
                # 若所选时间超出了底层数据的最大时间范围，给与友好提示
                if not df_t_filtered.empty:
                    if time_grain == "周": df_t_filtered['Date_Axis'] = df_t_filtered['Date'].dt.to_period('W').dt.to_timestamp()
                    elif time_grain == "月": df_t_filtered['Date_Axis'] = df_t_filtered['Date'].dt.to_period('M').dt.to_timestamp()
                    else: df_t_filtered['Date_Axis'] = df_t_filtered['Date']

                    # --- 流量：总趋势曲线 ---
                    df_t_total_trend = df_t_filtered.groupby('Date_Axis')['Value'].sum().reset_index()
                    fig_t_total = go.Figure()
                    fig_t_total.add_trace(go.Scatter(
                        x=df_t_total_trend['Date_Axis'], y=df_t_total_trend['Value'],
                        mode='lines+markers', line=dict(color='#0284c7', width=3.5), # 使用湖蓝色区分销售额
                        marker=dict(size=6, color='#ffffff', line=dict(color='#0284c7', width=2)), 
                        name='总流量', hovertemplate='<b>日期</b>: %{x}<br><b>总流量</b>: %{y:,.0f}<extra></extra>'
                    ))
                    fig_t_total.update_layout(
                        title=dict(text="📊 选定站点 SEO 总流量趋势", font=dict(size=16, color='#1e293b', weight='bold')),
                        height=350, plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified', margin=dict(l=20, r=20, t=50, b=20),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickformat='%Y-%m-%d' if time_grain=='日' else '%Y-%m'),
                        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
                    )
                    
                    st.write("")
                    with st.container(border=True):
                        st.plotly_chart(fig_t_total, use_container_width=True)

                    # --- 流量：混合柱状图 ---
                    df_t_site_trend = df_t_filtered.groupby(['Date_Axis', 'Site'])['Value'].sum().reset_index()
                    fig_t_sites = go.Figure()
                    
                    for idx, site in enumerate(fixed_sites_order):
                        if site in selected_sites:
                            df_t_single = df_t_site_trend[df_t_site_trend['Site'] == site]
                            site_label = en_to_cn.get(site, site)
                            fig_t_sites.add_trace(go.Bar(
                                x=df_t_single['Date_Axis'], y=df_t_single['Value'],
                                name=site_label, marker_color=color_palette[idx % len(color_palette)],
                                hovertemplate=f'<b>{site_label}</b>: %{{y:,.0f}}<extra></extra>'
                            ))
                    
                    fig_t_sites.add_trace(go.Scatter(
                        x=df_t_total_trend['Date_Axis'], y=df_t_total_trend['Value'],
                        mode='lines+markers', line=dict(color='#1e293b', width=2, dash='dot'),
                        marker=dict(size=5, color='#1e293b'),
                        name='选定站点总计', hovertemplate='<b>总计</b>: %{y:,.0f}<extra></extra>'
                    ))
                            
                    fig_t_sites.update_layout(
                        title=dict(text="🌍 各站点 SEO 流量成分对比 (柱线混合图)", font=dict(size=16, color='#1e293b', weight='bold')),
                        height=450, plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified', barmode='stack', 
                        margin=dict(l=20, r=20, t=50, b=80), 
                        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, font=dict(size=12)),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickformat='%Y-%m-%d' if time_grain=='日' else '%Y-%m'),
                        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
                    )
                    with st.container(border=True):
                        st.plotly_chart(fig_t_sites, use_container_width=True)
                else:
                    st.info(f"💡 当前选定的日期范围（{start_date} 至 {end_date}）内，尚未抓取到有效【流量数据】。请尝试将起止日期往前调整。")
            else:
                st.info("💡 底表中缺乏历史【流量明细数据】。")

        else:
            st.warning("⚠️ 请至少选择一个国家站点进行数据趋势观察。")

else:
    st.info("👈 请配置 GCP JSON 密钥以接入数据。")
