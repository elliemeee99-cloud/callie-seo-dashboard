import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import re
import gc

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO站点明细", page_icon="🌍", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f8fafc !important; }

/* 站点明细表格的底色样式 */
.site-header {
    background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 12px 12px 0 0;
    font-size: 16px;
    font-weight: 700;
    margin-top: 30px;
}
.site-container {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 0 0 12px 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
.overview-title {
    font-size: 24px;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 5px;
}

/* 🔥 终极 Radio 按钮卡片化 CSS (作为兜底方案) */
div[role="radiogroup"] {
    gap: 0.8rem !important;
    flex-wrap: wrap;
}
div[role="radiogroup"] label {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    padding: 8px 20px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s;
}
div[role="radiogroup"] label:hover {
    border-color: #94a3b8 !important;
    background-color: #f1f5f9 !important;
}
div[role="radiogroup"] label div:first-child {
    display: none !important; /* 彻底隐藏原生小圆圈 */
}
div[role="radiogroup"] label[aria-checked="true"],
div[role="radiogroup"] label:has(input:checked) {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
}
div[role="radiogroup"] label p {
    margin: 0 !important;
    font-weight: 600 !important;
    color: #475569 !important;
    font-size: 14px !important;
}
div[role="radiogroup"] label[aria-checked="true"] p,
div[role="radiogroup"] label:has(input:checked) p {
    color: #ffffff !important;
}

/* 美化原生 metric 组件的字体颜色 */
[data-testid="stMetricValue"] {
    color: #2563eb !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"] {
    color: #64748b !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 安全数值转换函数
# ==========================================
def safe_to_float(val):
    try:
        clean_str = re.sub(r'[^\d\.-]', '', str(val))
        if not clean_str or clean_str in ['-', '.', '-.']:
            return 0.0
        return float(clean_str)
    except Exception:
        return 0.0

# ==========================================
# ⚙️ 站点全量明细数据引擎
# ==========================================
@st.cache_data(ttl=3600)
def load_site_full_details():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit")
        
        cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
        default_year = str(datetime.datetime.now().year)
        
        ws_all = spreadsheet.worksheet("All")
        raw_data = ws_all.get_all_values()
        
        records = []
        dates_row = []
        current_site = None
        
        for row in raw_data:
            if not row: continue
            first_cell = str(row[0]).strip()
            
            if len(row) > 1:
                check_val = str(row[1]).strip()
                if not check_val and len(row) > 2: check_val = str(row[2]).strip()
                if "202" in check_val or ("月" in check_val and "日" in check_val) or re.match(r'^\d{1,2}[-/]\d{1,2}$', check_val):
                    dates_row = [str(x).strip() for x in row[1:]]
                
            if first_cell.startswith("Callie ") and len(first_cell) <= 15:
                current_site = first_cell.replace("Callie ", "").strip()
                if current_site in cn_to_en:
                    current_site = cn_to_en[current_site]
                continue
            
            if current_site and first_cell and first_cell not in ["", "总计"]:
                metric_name = first_cell
                if metric_name in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]:
                    continue
                    
                values = row[1:]
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i] != "":
                        raw_val = str(values[i]).strip()
                        if raw_val:
                            d_str = dates_row[i]
                            if "月" in d_str and "日" in d_str:
                                try:
                                    m = d_str.split('月')[0].strip()
                                    d = d_str.split('月')[1].replace('日', '').strip()
                                    d_str = f"{default_year}-{m}-{d}"
                                except: pass
                            
                            records.append({
                                "Site": current_site,
                                "Metric": metric_name,
                                "Date_str": d_str,
                                "Value": raw_val
                            })
                            
        df = pd.DataFrame(records)
        
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date_str'], errors='coerce')
            df = df.dropna(subset=['Date'])
            df['Numeric_Value'] = df['Value'].apply(safe_to_float)
            df['Clean_Metric'] = df['Metric'].apply(lambda x: str(x).replace(' ', '').upper())
        
        del raw_data
        gc.collect()
        
        return df
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None

# ==========================================
# 📊 核心计算逻辑
# ==========================================
def get_metric(metric_name, df_data, agg_type='sum'):
    sub = df_data[df_data['Clean_Metric'] == metric_name.replace(' ', '').upper()]
    if sub.empty: return 0.0
    if agg_type == 'sum': return sub['Numeric_Value'].sum()
    if agg_type == 'mean': return sub['Numeric_Value'].mean()
    if agg_type == 'latest': 
        sub = sub.sort_values('Date')
        return sub['Numeric_Value'].iloc[-1]
    return 0.0

# ==========================================
# 📐 页面布局与交互
# ==========================================
st.markdown("<div class='overview-title'>🌍 站点深度体检中心</div>", unsafe_allow_html=True)
st.markdown("<div style='color: #64748b; margin-bottom: 20px;'>全局数据控制台：在此切换站点与时间，快速洞察核心指标波动。底层全量明细表请向下滚动查看。</div>", unsafe_allow_html=True)

with st.spinner("✨ 正在智能扫描最新数据..."):
    df_all = load_site_full_details()

if df_all is not None and not df_all.empty:
    
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}

    mask_valid = (df_all['Clean_Metric'].isin(['网站总流量', 'SUPERSET总销售额'])) & (df_all['Numeric_Value'] > 0)
    valid_dates = df_all[mask_valid]['Date']
    actual_max_date = valid_dates.max() if not valid_dates.empty else df_all['Date'].max()

    # ==========================================
    # 🎛️ 顶部控制器 (完美包裹在卡片中)
    # ==========================================
    site_options = ["全部站点"] + list(cn_to_en.keys())
    
    with st.container(border=True):
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        
        with col_ctrl1:
            st.markdown("<div style='font-weight:700; color:#334155; margin-bottom:8px;'>🌍 选择分析站点</div>", unsafe_allow_html=True)
            # 智能调用最新组件，老版本自动降级并应用 CSS
            try:
                selected_site_cn = st.pills("站点", site_options, default="全部站点", label_visibility="collapsed")
                if not selected_site_cn: selected_site_cn = "全部站点"
            except AttributeError:
                try:
                    selected_site_cn = st.segmented_control("站点", site_options, default="全部站点", label_visibility="collapsed")
                    if not selected_site_cn: selected_site_cn = "全部站点"
                except AttributeError:
                    selected_site_cn = st.radio("站点", site_options, horizontal=True, label_visibility="collapsed")
                    
        with col_ctrl2:
            st.markdown("<div style='font-weight:700; color:#334155; margin-bottom:8px;'>⏱️ 时间维度</div>", unsafe_allow_html=True)
            try:
                time_view = st.pills("时间", ["昨日数据", "过去7天数据"], default="昨日数据", label_visibility="collapsed")
                if not time_view: time_view = "昨日数据"
            except AttributeError:
                try:
                    time_view = st.segmented_control("时间", ["昨日数据", "过去7天数据"], default="昨日数据", label_visibility="collapsed")
                    if not time_view: time_view = "昨日数据"
                except AttributeError:
                    time_view = st.radio("时间", ["昨日数据", "过去7天数据"], horizontal=True, label_visibility="collapsed")

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # --- 数据过滤 ---
    if time_view == "昨日数据":
        target_dates = [actual_max_date]
        time_hint = actual_max_date.strftime('%Y-%m-%d')
    else:
        target_dates = pd.date_range(end=actual_max_date, periods=7).tolist()
        time_hint = f"{target_dates[0].strftime('%Y-%m-%d')} 至 {actual_max_date.strftime('%Y-%m-%d')}"
        
    if selected_site_cn == "全部站点":
        df_target = df_all[df_all['Date'].isin(target_dates)]
    else:
        site_code = cn_to_en[selected_site_cn]
        df_target = df_all[(df_all['Site'] == site_code) & (df_all['Date'].isin(target_dates))]
    
    # ==========================================
    # 🏆 四大指标区块展示 (原生 Container 完美排版)
    # ==========================================
    if not df_target.empty:
        ss_seo_sales = get_metric('Superset SEO销售额', df_target, 'sum')
        ss_total_sales = get_metric('Superset 总销售额', df_target, 'sum')
        ss_ratio = (ss_seo_sales / ss_total_sales * 100) if ss_total_sales > 0 else 0.0
        
        ga4_seo_sales = get_metric('GA4 SEO销售额', df_target, 'sum')
        ga4_total_sales = get_metric('GA4 网站总销售额', df_target, 'sum')
        ga4_ratio = (ga4_seo_sales / ga4_total_sales * 100) if ga4_total_sales > 0 else 0.0
        
        seo_traffic = get_metric('SEO 总流量', df_target, 'sum')
        total_traffic = get_metric('网站总流量', df_target, 'sum')
        bounce_rate = get_metric('跳出率', df_target, 'mean')
        
        ai_sales = get_metric('AI Assistant 销售额', df_target, 'sum')
        ai_traffic = get_metric('AI Assistant 流量', df_target, 'sum')
        
        index_count = get_metric('收录', df_target, 'latest')
        backlink_count = get_metric('外链', df_target, 'latest')
        backlink_domain = get_metric('外链域名广度', df_target, 'latest')

        # --- 区块 1: 销售额数据 (占满全宽的独立卡片) ---
        with st.container(border=True):
            st.markdown("<h4 style='color:#334155; margin-bottom: 20px;'>💰 销售额数据</h4>", unsafe_allow_html=True)
            cols1 = st.columns(6)
            cols1[0].metric("Superset SEO销售额", f"${ss_seo_sales:,.2f}")
            cols1[1].metric("Superset 总销售额", f"${ss_total_sales:,.2f}")
            cols1[2].metric("Superset 占比", f"{ss_ratio:.2f}%")
            cols1[3].metric("GA4 SEO销售额", f"${ga4_seo_sales:,.2f}")
            cols1[4].metric("GA4 网站总销售额", f"${ga4_total_sales:,.2f}")
            cols1[5].metric("GA4 占比", f"{ga4_ratio:.2f}%")
        
        # --- 区块 2、3、4: 三区并排 (每块都有独立的边框卡片) ---
        col_flow, col_ai, col_google = st.columns([2, 1.5, 2])
        
        with col_flow:
            with st.container(border=True):
                st.markdown("<h4 style='color:#334155; margin-bottom: 20px;'>🌊 流量数据</h4>", unsafe_allow_html=True)
                rt1, rt2, rt3 = st.columns(3)
                rt1.metric("SEO流量", f"{seo_traffic:,.0f}")
                rt2.metric("网站总流量", f"{total_traffic:,.0f}")
                rt3.metric("跳出率", f"{bounce_rate:.2f}%")

        with col_ai:
            with st.container(border=True):
                st.markdown("<h4 style='color:#334155; margin-bottom: 20px;'>🤖 AI Assistant</h4>", unsafe_allow_html=True)
                ra1, ra2 = st.columns(2)
                ra1.metric("AI销售额", f"${ai_sales:,.2f}")
                ra2.metric("AI流量", f"{ai_traffic:,.0f}")

        with col_google:
            with st.container(border=True):
                st.markdown("<h4 style='color:#334155; margin-bottom: 20px;'>🔗 Google 收录与外链</h4>", unsafe_allow_html=True)
                rg1, rg2, rg3 = st.columns(3)
                rg1.metric("收录", f"{index_count:,.0f}")
                rg2.metric("外链", f"{backlink_count:,.0f}")
                rg3.metric("域名广度", f"{backlink_domain:,.0f}")
    else:
        st.warning(f"⚠️ 在所选时间（{time_hint}）内暂无可用数据。")

    st.write("---")

    # ==========================================
    # 🗄️ 底部区域：各站点底层全量明细表
    # ==========================================
    st.markdown("<div class='overview-title' style='margin-top:20px;'>🗄️ 分站点底层原始数据明细</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #64748b; margin-bottom: 20px;'>下方表格展示最近 15 天的全量底层指标，时间按从左向右（升序）排列。</div>", unsafe_allow_html=True)

    recent_dates = sorted(df_all['Date'].unique())[-15:]
    df_raw_tables = df_all[df_all['Date'].isin(recent_dates)]

    for site in fixed_sites_order:
        df_site_raw = df_raw_tables[df_raw_tables['Site'] == site]
        if not df_site_raw.empty:
            
            site_title = f"{en_to_cn.get(site, site)} (Callie {site})"
            st.markdown(f"<div class='site-header'>🌍 {site_title}</div>", unsafe_allow_html=True)
            
            with st.container():
                st.markdown("<div class='site-container'>", unsafe_allow_html=True)
                
                df_pivot = df_site_raw.pivot_table(
                    index='Metric', 
                    columns='Date', 
                    values='Value', 
                    aggfunc=lambda x: ' '.join(str(v) for v in x)
                )
                
                sorted_dates = sorted(df_pivot.columns, reverse=False)
                df_pivot = df_pivot[sorted_dates]
                df_pivot.columns = [d.strftime('%m-%d') for d in df_pivot.columns] 
                
                st.dataframe(df_pivot, width='stretch')
                st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("尚未扫描到有效的站点数据，请检查网络连接或表单格式。")
