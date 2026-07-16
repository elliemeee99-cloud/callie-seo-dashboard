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

/* 站点明细表格的样式 */
.site-header {
    background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 12px 12px 0 0;
    font-size: 18px;
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

/* 🎨 KPI 卡片样式 */
.overview-title {
    font-size: 22px;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 15px;
}
.section-title {
    font-size: 15px;
    font-weight: 700;
    color: #475569;
    margin-top: 20px;
    margin-bottom: 10px;
    border-bottom: 2px solid #f1f5f9;
    padding-bottom: 8px;
}
.kpi-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    transition: all 0.2s ease;
}
.kpi-card:hover {
    border-color: #2563eb;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1);
}
.kpi-title {
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
}
.kpi-value {
    color: #2563eb;
    font-size: 24px;
    font-weight: 800;
}

/* 🔥 让 Radio 按钮看起来像卡片标签 */
div[data-testid="stRadio"] div[role="radiogroup"] { display: flex !important; flex-direction: row !important; gap: 10px !important; flex-wrap: wrap; }
div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; padding: 8px 24px !important; border-radius: 8px !important; cursor: pointer !important; transition: all 0.2s; }
div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child { display: none !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] p { color: #64748b !important; font-weight: 600 !important; margin: 0 !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"], div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background-color: #2563eb !important; border-color: #2563eb !important;}
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p, div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

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
            
            # 捕捉时间轴
            if len(row) > 1:
                check_val = str(row[1]).strip()
                if not check_val and len(row) > 2: check_val = str(row[2]).strip()
                if "202" in check_val or ("月" in check_val and "日" in check_val) or re.match(r'^\d{1,2}[-/]\d{1,2}$', check_val):
                    dates_row = [str(x).strip() for x in row[1:]]
                
            # 捕捉国家区块
            if first_cell.startswith("Callie ") and len(first_cell) <= 15:
                current_site = first_cell.replace("Callie ", "").strip()
                if current_site in cn_to_en:
                    current_site = cn_to_en[current_site]
                continue
            
            # 动态抓取指标
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
        
        del raw_data
        gc.collect()
        
        return df
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None

# ==========================================
# 📊 核心计算逻辑：提取并聚合 KPI 
# ==========================================
def extract_metric(metric_keywords, df_data, agg_type='sum'):
    clean_keywords = [k.replace(' ', '').upper() for k in metric_keywords]
    mask = df_data['Metric'].apply(lambda x: str(x).replace(' ', '').upper()).isin(clean_keywords)
    df_sub = df_data[mask]
    
    if df_sub.empty: 
        return 0.0
        
    cleaned_vals = df_sub['Value'].apply(lambda x: re.sub(r'[^\d\.-]', '', str(x)))
    num_vals = pd.to_numeric(cleaned_vals, errors='coerce').fillna(0.0)
    
    if agg_type == 'sum':
        return num_vals.sum()
    elif agg_type == 'mean':
        return num_vals.mean()
    elif agg_type == 'latest':
        latest_date = df_sub['Date'].max()
        latest_val_str = df_sub[df_sub['Date'] == latest_date]['Value'].iloc[0]
        try: return float(re.sub(r'[^\d\.-]', '', str(latest_val_str)))
        except: return 0.0
    return 0.0

def render_kpi(title, value_str):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value_str}</div>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# 📐 页面布局与交互
# ==========================================
st.title("🌍 站点深度体检与明细数据")

with st.spinner("✨ 正在逐行扫描底层表单并聚合分析..."):
    df_all = load_site_full_details()

if df_all is not None and not df_all.empty:
    
    # 字典配置
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}

    # ==========================================
    # 🏆 第一部分：全局 / 单站 核心指标总览
    # ==========================================
    with st.container(border=True):
        st.markdown("<div class='overview-title'>📊 核心指标总览</div>", unsafe_allow_html=True)
        
        # 1. 站点控制器
        site_options = ["全部站点", "德国", "法国", "西班牙", "意大利", "荷兰", "挪威", "瑞典", "芬兰", "波兰"]
        selected_site_cn = st.radio("切换站点", site_options, horizontal=True, label_visibility="collapsed")
        
        st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
        
        # 2. 时间控制器
        time_view = st.radio("时间维度", ["昨日数据", "过去7天数据"], horizontal=True, label_visibility="collapsed")
        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        # --- 数据过滤 (仅针对上面的 KPI 卡片) ---
        max_date = df_all['Date'].max()
        if time_view == "昨日数据":
            target_dates = [max_date]
        else:
            target_dates = pd.date_range(end=max_date, periods=7).tolist()
            
        if selected_site_cn == "全部站点":
            df_overview = df_all[df_all['Date'].isin(target_dates)]
        else:
            site_code = cn_to_en[selected_site_cn]
            df_overview = df_all[(df_all['Site'] == site_code) & (df_all['Date'].isin(target_dates))]
        
        # --- 计算 KPI ---
        if not df_overview.empty:
            ss_seo_sales = extract_metric(['Superset SEO销售额', 'SupersetSEO销售额'], df_overview, 'sum')
            ss_total_sales = extract_metric(['Superset 总销售额', 'Superset总销售额'], df_overview, 'sum')
            ss_ratio = (ss_seo_sales / ss_total_sales * 100) if ss_total_sales > 0 else 0.0
            
            ga4_seo_sales = extract_metric(['GA4 SEO销售额', 'GA4SEO销售额'], df_overview, 'sum')
            ga4_total_sales = extract_metric(['GA4 网站总销售额', 'GA4网站总销售额', 'GA4总销售额'], df_overview, 'sum')
            ga4_ratio = (ga4_seo_sales / ga4_total_sales * 100) if ga4_total_sales > 0 else 0.0
            
            seo_traffic = extract_metric(['SEO 总流量', 'SEO流量', 'SEO总流量'], df_overview, 'sum')
            total_traffic = extract_metric(['网站总流量'], df_overview, 'sum')
            bounce_rate = extract_metric(['跳出率'], df_overview, 'mean')
            
            ai_sales = extract_metric(['AI Assistant 销售额', 'AIAssistant销售额'], df_overview, 'sum')
            ai_traffic = extract_metric(['AI Assistant 流量', 'AIAssistant流量'], df_overview, 'sum')
            
            index_count = extract_metric(['收录'], df_overview, 'latest')
            backlink_count = extract_metric(['外链'], df_overview, 'latest')
            backlink_domain = extract_metric(['外链域名广度'], df_overview, 'latest')

            # --- 渲染卡片 ---
            st.markdown("<div class='section-title'>💰 销售额数据</div>", unsafe_allow_html=True)
            cols1 = st.columns(6)
            with cols1[0]: render_kpi("Superset SEO销售额", f"${ss_seo_sales:,.2f}")
            with cols1[1]: render_kpi("Superset 总销售额", f"${ss_total_sales:,.2f}")
            with cols1[2]: render_kpi("Superset 占比情况", f"{ss_ratio:.2f}%")
            with cols1[3]: render_kpi("GA4 SEO销售额", f"${ga4_seo_sales:,.2f}")
            with cols1[4]: render_kpi("GA4 网站总销售额", f"${ga4_total_sales:,.2f}")
            with cols1[5]: render_kpi("GA4 占比情况", f"{ga4_ratio:.2f}%")
            
            st.markdown("<div class='section-title'>🌊 流量数据</div>", unsafe_allow_html=True)
            cols2 = st.columns(3)
            with cols2[0]: render_kpi("SEO流量", f"{seo_traffic:,.0f}")
            with cols2[1]: render_kpi("网站总流量", f"{total_traffic:,.0f}")
            with cols2[2]: render_kpi("跳出率", f"{bounce_rate:.2f}%")
            
            cols_bottom1, cols_bottom2 = st.columns(2)
            with cols_bottom1:
                st.markdown("<div class='section-title'>🤖 AI Assistant 数据</div>", unsafe_allow_html=True)
                c_ai1, c_ai2 = st.columns(2)
                with c_ai1: render_kpi("AI Assistant 销售额", f"${ai_sales:,.2f}")
                with c_ai2: render_kpi("AI Assistant 流量", f"{ai_traffic:,.0f}")
                
            with cols_bottom2:
                st.markdown("<div class='section-title'>🔗 Google 收录与外链</div>", unsafe_allow_html=True)
                c_g1, c_g2, c_g3 = st.columns(3)
                with c_g1: render_kpi("收录", f"{index_count:,.0f}")
                with c_g2: render_kpi("外链", f"{backlink_count:,.0f}")
                with c_g3: render_kpi("外链域名广度", f"{backlink_domain:,.0f}")
        else:
            st.warning("所选站点或时间段内暂无可用数据。")

    st.write("---")

    # ==========================================
    # 🗄️ 第二部分：各站点原始明细数据表 (独立底层数据)
    # ==========================================
    st.markdown("<div class='overview-title'>🗄️ 各站点底层原始数据明细</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #64748b; margin-bottom: 20px;'>下方表格自动提取展示最近 15 天的全量底层指标，时间按从左向右（升序）排列。</div>", unsafe_allow_html=True)

    # 提取最近 15 天的日期作为底部表格的默认展示范围，防止表格过长
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
                
                # 🔥 时间顺序修改：从左往右（升序）
                sorted_dates = sorted(df_pivot.columns, reverse=False)
                df_pivot = df_pivot[sorted_dates]
                df_pivot.columns = [d.strftime('%m-%d') for d in df_pivot.columns] # 底部表格用 11-01 短格式更清爽
                
                st.dataframe(df_pivot, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("尚未扫描到有效的站点数据，请检查网络连接或表单格式。")
