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
.site-header {
    background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 12px 12px 0 0;
    font-size: 20px;
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
.section-title {
    font-size: 16px;
    font-weight: bold;
    color: #475569;
    margin-top: 15px;
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
# 📊 核心计算逻辑：提取并聚合 KPI (🔥终极修复版：原生 Lambda 防护)
# ==========================================
def extract_metric(df_data, metric_keywords, agg_type='sum'):
    # 模糊匹配指标名 (去除空格，转大写)
    clean_keywords = [k.replace(' ', '').upper() for k in metric_keywords]
    
    # 🔥 使用原生 apply lambda 替代 .str 引擎，100% 免疫 TypeError
    mask = df_data['Metric'].apply(lambda x: str(x).replace(' ', '').upper()).isin(clean_keywords)
    df_sub = df_data[mask]
    
    if df_sub.empty: 
        return 0.0
        
    # 🔥 清洗数值时同样使用 apply，规避潜在风险
    cleaned_vals = df_sub['Value'].apply(lambda x: re.sub(r'[^\d\.-]', '', str(x)))
    num_vals = pd.to_numeric(cleaned_vals, errors='coerce').fillna(0.0)
    
    if agg_type == 'sum':
        return num_vals.sum()
    elif agg_type == 'mean':
        return num_vals.mean()
    elif agg_type == 'latest':
        # 针对快照数据（如收录、外链），取所选时间范围内的最新一日数据
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
    
    # 顶部时间切换控件 (单选按钮)
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    time_view = st.radio("⏱️ 数据时间维度", ["昨日数据", "过去7天数据"], horizontal=True)
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    en_to_cn = {
        "DE": "🇩🇪 德国", "FR": "🇫🇷 法国", "ES": "🇪🇸 西班牙", 
        "IT": "🇮🇹 意大利", "NL": "🇳🇱 荷兰", "NO": "🇳🇴 挪威", 
        "SE": "🇸🇪 瑞典", "FI": "🇫🇮 芬兰", "PL": "🇵🇱 波兰"
    }

    # 按顺序遍历国家渲染瀑布流
    for site in fixed_sites_order:
        df_site = df_all[df_all['Site'] == site]
        if df_site.empty: continue
        
        # 计算该站点的日期基准
        max_date = df_site['Date'].max()
        if time_view == "昨日数据":
            target_dates = [max_date]
        else:
            # 过去 7 天
            target_dates = pd.date_range(end=max_date, periods=7).tolist()
            
        df_target = df_site[df_site['Date'].isin(target_dates)]
        if df_target.empty: continue

        # ==========================================
        # 🧮 获取各项 KPI 计算结果
        # ==========================================
        # 1. 销售额
        ss_seo_sales = extract_metric(['Superset SEO销售额', 'SupersetSEO销售额'], df_target, 'sum')
        ss_total_sales = extract_metric(['Superset 总销售额', 'Superset总销售额'], df_target, 'sum')
        ss_ratio = (ss_seo_sales / ss_total_sales * 100) if ss_total_sales > 0 else 0.0
        
        ga4_seo_sales = extract_metric(['GA4 SEO销售额', 'GA4SEO销售额'], df_target, 'sum')
        ga4_total_sales = extract_metric(['GA4 网站总销售额', 'GA4网站总销售额', 'GA4总销售额'], df_target, 'sum')
        ga4_ratio = (ga4_seo_sales / ga4_total_sales * 100) if ga4_total_sales > 0 else 0.0
        
        # 2. 流量
        seo_traffic = extract_metric(['SEO 总流量', 'SEO流量', 'SEO总流量'], df_target, 'sum')
        total_traffic = extract_metric(['网站总流量'], df_target, 'sum')
        bounce_rate = extract_metric(['跳出率'], df_target, 'mean') # 跳出率求均值
        
        # 3. AI
        ai_sales = extract_metric(['AI Assistant 销售额', 'AIAssistant销售额'], df_target, 'sum')
        ai_traffic = extract_metric(['AI Assistant 流量', 'AIAssistant流量'], df_target, 'sum')
        
        # 4. 快照指标 (仅取最新一日)
        index_count = extract_metric(['收录'], df_target, 'latest')
        backlink_count = extract_metric(['外链'], df_target, 'latest')
        backlink_domain = extract_metric(['外链域名广度'], df_target, 'latest')

        # ==========================================
        # 🎨 渲染站点卡片
        # ==========================================
        site_title = en_to_cn.get(site, f"🌍 {site}")
        st.markdown(f"<div class='site-header'>{site_title}</div>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='site-container'>", unsafe_allow_html=True)
            
            # --- 板块 1: 销售额数据 ---
            st.markdown("<div class='section-title'>💰 销售额数据</div>", unsafe_allow_html=True)
            cols1 = st.columns(6)
            with cols1[0]: render_kpi("Superset SEO销售额", f"${ss_seo_sales:,.2f}")
            with cols1[1]: render_kpi("Superset 总销售额", f"${ss_total_sales:,.2f}")
            with cols1[2]: render_kpi("Superset 占比情况", f"{ss_ratio:.2f}%")
            with cols1[3]: render_kpi("GA4 SEO销售额", f"${ga4_seo_sales:,.2f}")
            with cols1[4]: render_kpi("GA4 网站总销售额", f"${ga4_total_sales:,.2f}")
            with cols1[5]: render_kpi("GA4 占比情况", f"{ga4_ratio:.2f}%")
            
            # --- 板块 2: 流量数据 ---
            st.markdown("<div class='section-title'>🌊 流量数据</div>", unsafe_allow_html=True)
            cols2 = st.columns(3)
            with cols2[0]: render_kpi("SEO流量", f"{seo_traffic:,.0f}")
            with cols2[1]: render_kpi("网站总流量", f"{total_traffic:,.0f}")
            with cols2[2]: render_kpi("跳出率", f"{bounce_rate:.2f}%")
            
            cols_bottom1, cols_bottom2 = st.columns(2)
            
            # --- 板块 3: AI Assistant数据 ---
            with cols_bottom1:
                st.markdown("<div class='section-title'>🤖 AI Assistant 数据</div>", unsafe_allow_html=True)
                c_ai1, c_ai2 = st.columns(2)
                with c_ai1: render_kpi("AI Assistant 销售额", f"${ai_sales:,.2f}")
                with c_ai2: render_kpi("AI Assistant 流量", f"{ai_traffic:,.0f}")
                
            # --- 板块 4: Google 收录与外链 ---
            with cols_bottom2:
                st.markdown("<div class='section-title'>🔗 Google 收录与外链</div>", unsafe_allow_html=True)
                c_g1, c_g2, c_g3 = st.columns(3)
                with c_g1: render_kpi("收录", f"{index_count:,.0f}")
                with c_g2: render_kpi("外链", f"{backlink_count:,.0f}")
                with c_g3: render_kpi("外链域名广度", f"{backlink_domain:,.0f}")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- 底部扩展：全量原始数据对比表 ---
            with st.expander(f"👁️ 查看 {site} 底层原始数据表格 (按时间升序)"):
                df_pivot = df_target.pivot_table(
                    index='Metric', 
                    columns='Date', 
                    values='Value', 
                    aggfunc=lambda x: ' '.join(str(v) for v in x)
                )
                # 从左往右（时间递增排布）
                sorted_dates = sorted(df_pivot.columns, reverse=False)
                df_pivot = df_pivot[sorted_dates]
                df_pivot.columns = [d.strftime('%Y-%m-%d') for d in df_pivot.columns]
                
                st.dataframe(df_pivot, use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("尚未扫描到有效的站点数据，请检查网络连接或表单格式。")
