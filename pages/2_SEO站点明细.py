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

# ==========================================
# 🎨 现代 SaaS 顶级视觉重构 (Stripe / Vercel 风格)
# ==========================================
st.markdown("""
<style>
/* 1. 整体极简浅灰背景 */
.stApp { 
    background-color: #F5F7FA !important; 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* 2. 隐藏原生顶部的多余留白 */
.block-container { padding-top: 2rem !important; max-width: 96% !important; }

/* 3. Vercel 风格的极简控制器 (药丸按钮) */
div[role="radiogroup"] { gap: 12px !important; flex-wrap: wrap; }
div[role="radiogroup"] label {
    background-color: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    padding: 8px 20px !important;
    border-radius: 30px !important; /* 圆润的胶囊形 */
    cursor: pointer !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
div[role="radiogroup"] label:hover { background-color: #F9FAFB !important; border-color: #D1D5DB !important; }
/* 🔥 修复文字消失问题：严格限制只隐藏作为直接子元素的第一个 div (即小圆圈) */
div[role="radiogroup"] label > div:first-child { display: none !important; } 

div[role="radiogroup"] label p, div[role="radiogroup"] label div {
    margin: 0 !important;
    font-weight: 600 !important;
    color: #4B5563 !important;
    font-size: 14px !important;
}
/* 选中态：Linear 风格的高级深邃黑 */
div[role="radiogroup"] label[aria-checked="true"], 
div[role="radiogroup"] label:has(input:checked) {
    background-color: #111827 !important;
    border-color: #111827 !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important;
}
div[role="radiogroup"] label[aria-checked="true"] p, 
div[role="radiogroup"] label:has(input:checked) p,
div[role="radiogroup"] label[aria-checked="true"] div, 
div[role="radiogroup"] label:has(input:checked) div {
    color: #ffffff !important;
}

/* 4. 底层原始数据表格的 SaaS 容器化 */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 1px solid #EEF2F6 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.02) !important;
    padding: 24px !important;
}

/* 自定义大模块 Section */
.saas-section {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #EEF2F6;
    box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    padding: 32px;
    margin-bottom: 32px;
}
.saas-title {
    font-size: 20px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    letter-spacing: -0.5px;
}
.icon-box {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 底层数据与清洗逻辑 (保持稳定)
# ==========================================
def safe_to_float(val):
    try:
        clean_str = re.sub(r'[^\d\.-]', '', str(val))
        if not clean_str or clean_str in ['-', '.', '-.']: return 0.0
        return float(clean_str)
    except: return 0.0

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
                if metric_name in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]: continue
                    
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
                            records.append({"Site": current_site, "Metric": metric_name, "Date_str": d_str, "Value": raw_val})
                            
        df = pd.DataFrame(records)
        
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date_str'], errors='coerce')
            df = df.dropna(subset=['Date'])
            df['Numeric_Value'] = df['Value'].apply(safe_to_float)
            df['Clean_Metric'] = df['Metric'].apply(lambda x: str(x).replace(' ', '').upper())
        
        del raw_data; gc.collect()
        return df
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None

def get_metric(metric_names, df_data, agg_type='sum'):
    if isinstance(metric_names, str): metric_names = [metric_names]
    clean_names = [m.replace(' ', '').upper() for m in metric_names]
    sub = df_data[df_data['Clean_Metric'].isin(clean_names)]
    if sub.empty: return 0.0
    if agg_type == 'sum': return sub['Numeric_Value'].sum()
    if agg_type == 'mean': return sub['Numeric_Value'].mean()
    if agg_type == 'latest': return sub.sort_values('Date')['Numeric_Value'].iloc[-1]
    return 0.0

# ==========================================
# 💎 纯原生 HTML 卡片渲染工厂 (实现顶级 UI 的核心)
# ==========================================
def render_kpi_card(label, value, theme, highlight=False):
    # 主题字典：精准控制 点缀色 / 高亮背景色 / 弱边框色
    themes = {
        "blue": {"dot": "#3B82F6", "bg": "#EFF6FF", "border": "#BFDBFE"},
        "cyan": {"dot": "#06B6D4", "bg": "#ECFEFF", "border": "#A5F3FC"},
        "purple": {"dot": "#8B5CF6", "bg": "#F5F3FF", "border": "#DDD6FE"},
        "green": {"dot": "#10B981", "bg": "#F0FDF4", "border": "#BBF7D0"},
        "default": {"bg": "#FAFBFC", "border": "transparent"} # 默认采用纯净浅灰无边框
    }
    bg = themes[theme]["bg"] if highlight else themes["default"]["bg"]
    border = themes[theme]["border"] if highlight else themes["default"]["border"]
    dot = themes[theme]["dot"]
    
    return f"""
    <div style="background: {bg}; border: 1px solid {border}; border-radius: 16px; padding: 24px 20px; display: flex; flex-direction: column; justify-content: center; transition: 0.2s;">
        <div style="font-size: 14.5px; color: #6B7280; font-weight: 500; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span style="color: {dot}; font-size: 12px;">●</span> {label}
        </div>
        <div style="font-size: 40px; font-weight: 600; color: #2563EB; line-height: 1; letter-spacing: -0.5px;">
            {value}
        </div>
    </div>
    """

def render_traffic_item(label, value, is_last=False):
    # 横向弱分割线设计
    br = "border-right: 1px solid #EEF2F6;" if not is_last else ""
    return f"""
    <div style="flex: 1; {br} padding: 0 24px;">
        <div style="font-size: 14.5px; color: #6B7280; font-weight: 500; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span style="color: #06B6D4; font-size: 12px;">●</span> {label}
        </div>
        <div style="font-size: 42px; font-weight: 600; color: #2563EB; line-height: 1; letter-spacing: -0.5px;">
            {value}
        </div>
    </div>
    """

# ==========================================
# 📐 全局交互层
# ==========================================
st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px;'>🌍 Analytics Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div style='color: #6B7280; margin-bottom: 32px; font-size: 15px;'>全局站点全景与深度体检数据台。</div>", unsafe_allow_html=True)

with st.spinner("✨ 正在同步最新数据仓库..."):
    df_all = load_site_full_details()

if df_all is not None and not df_all.empty:
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}

    mask_valid = (df_all['Clean_Metric'].isin(['网站总流量', 'SUPERSET总销售额'])) & (df_all['Numeric_Value'] > 0)
    valid_dates = df_all[mask_valid]['Date']
    actual_max_date = valid_dates.max() if not valid_dates.empty else df_all['Date'].max()

    # --- 高级控制器 ---
    site_options = ["全部站点"] + list(cn_to_en.keys())
    
    col_c1, col_c2 = st.columns([2.5, 1])
    with col_c1:
        # 🔥 直接赋值，坚决不取巧报错
        selected_site_cn = st.radio("站点切换", site_options, horizontal=True, label_visibility="collapsed")
    with col_c2:
        # 🔥 直接赋值
        time_view = st.radio("时间切换", ["昨日数据", "过去7天数据"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<div style='margin-bottom: 36px;'></div>", unsafe_allow_html=True)

    if time_view == "昨日数据":
        target_dates = [actual_max_date]
        time_hint = actual_max_date.strftime('%Y-%m-%d')
    else:
        target_dates = pd.date_range(end=actual_max_date, periods=7).tolist()
        time_hint = f"{target_dates[0].strftime('%Y-%m-%d')} 至 {actual_max_date.strftime('%Y-%m-%d')}"
        
    if selected_site_cn == "全部站点":
        df_target = df_all[df_all['Date'].isin(target_dates)]
    else:
        site_code = cn_to_en.get(selected_site_cn, "DE")
        df_target = df_all[(df_all['Site'] == site_code) & (df_all['Date'].isin(target_dates))]
    
    # ==========================================
    # 🏆 四大独立模块渲染 (完全 HTML/CSS 构建)
    # ==========================================
    if not df_target.empty:
        
        # 1. 核心计算
        ss_seo_sales = get_metric(['Superset SEO销售额', 'SupersetSEO销售额'], df_target, 'sum')
        ss_total_sales = get_metric(['Superset 总销售额', 'Superset总销售额'], df_target, 'sum')
        ss_ratio = (ss_seo_sales / ss_total_sales * 100) if ss_total_sales > 0 else 0.0
        ga4_seo_sales = get_metric(['GA4 SEO销售额', 'GA4SEO销售额'], df_target, 'sum')
        ga4_total_sales = get_metric(['GA4 网站总销售额', 'GA4网站总销售额', 'GA4总销售额'], df_target, 'sum')
        ga4_ratio = (ga4_seo_sales / ga4_total_sales * 100) if ga4_total_sales > 0 else 0.0
        
        seo_traffic = get_metric(['SEO 总流量', 'SEO流量', 'SEO总流量'], df_target, 'sum')
        seo_blog_traffic = get_metric(['SEO Blog流量', 'SEOBlog流量'], df_target, 'sum')
        seo_onsite_traffic = get_metric(['SEO 站内流量', 'SEO站内流量'], df_target, 'sum')
        total_traffic = get_metric(['网站总流量', '网站流量'], df_target, 'sum')
        bounce_rate = get_metric(['跳出率'], df_target, 'mean')
        
        ai_sales = get_metric(['AI Assistant 销售额', 'AIAssistant销售额', 'AI销售额'], df_target, 'sum')
        ai_traffic = get_metric(['AI Assistant 流量', 'AIAssistant流量', 'AI流量'], df_target, 'sum')
        
        index_count = get_metric(['收录'], df_target, 'latest')
        backlink_count = get_metric(['外链'], df_target, 'latest')
        backlink_domain = get_metric(['外链域名广度'], df_target, 'latest')

        # [区块 1] 销售额数据 (高亮 Superset SEO)
        sales_html = f"""
        <div class="saas-section">
            <div class="saas-title">
                <div class="icon-box" style="background:#EFF6FF; color:#3B82F6;">💰</div> 核心销售额追踪
            </div>
            <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 20px;">
                {render_kpi_card('Superset SEO销售额', f"${ss_seo_sales:,.2f}", 'blue', highlight=True)}
                {render_kpi_card('Superset 总销售额', f"${ss_total_sales:,.2f}", 'blue')}
                {render_kpi_card('Superset 占比情况', f"{ss_ratio:.2f}%", 'blue')}
                {render_kpi_card('GA4 SEO销售额', f"${ga4_seo_sales:,.2f}", 'blue')}
                {render_kpi_card('GA4 网站总销售额', f"${ga4_total_sales:,.2f}", 'blue')}
                {render_kpi_card('GA4 占比情况', f"{ga4_ratio:.2f}%", 'blue')}
            </div>
        </div>
        """
        st.markdown(sales_html, unsafe_allow_html=True)

        # [区块 2] 流量漏斗 (弱分割线 + 底部描述)
        traffic_html = f"""
        <div class="saas-section">
            <div class="saas-title">
                <div class="icon-box" style="background:#ECFEFF; color:#06B6D4;">🌊</div> 流量漏斗健康度
            </div>
            <div style="display: flex; align-items: center; margin: 20px -24px 0 -24px;">
                {render_traffic_item('SEO 流量', f"{seo_traffic:,.0f}")}
                {render_traffic_item('SEO Blog 流量', f"{seo_blog_traffic:,.0f}")}
                {render_traffic_item('SEO 站内流量', f"{seo_onsite_traffic:,.0f}")}
                {render_traffic_item('网站总流量', f"{total_traffic:,.0f}")}
                {render_traffic_item('跳出率', f"{bounce_rate:.2f}%", is_last=True)}
            </div>
            <div style="margin-top: 32px; padding-top: 16px; border-top: 1px dashed #E5E7EB; font-size: 13px; color: #9CA3AF; display: flex; align-items: center; gap: 6px;">
                <span style="color: #06B6D4; font-size: 16px;">✦</span> 所有流量指标均已过滤异常抓取，建议结合跳出率动态评估渠道质量。
            </div>
        </div>
        """
        st.markdown(traffic_html, unsafe_allow_html=True)

        # [区块 3 & 4] AI 数据与 Google 外链 (50/50 完美对齐分布)
        bottom_html = f"""
        <div style="display: flex; gap: 32px; margin-bottom: 32px;">
            <div class="saas-section" style="flex: 1; margin-bottom: 0;">
                <div class="saas-title">
                    <div class="icon-box" style="background:#F5F3FF; color:#8B5CF6;">🤖</div> AI Assistant 转化
                </div>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    {render_kpi_card('AI 销售额', f"${ai_sales:,.2f}", 'purple', highlight=True)}
                    {render_kpi_card('AI 流量获取', f"{ai_traffic:,.0f}", 'purple')}
                </div>
                <div style="margin-top: 24px; font-size: 13px; color: #9CA3AF;">监控大模型及助手带来的直接商业价值。</div>
            </div>
            
            <div class="saas-section" style="flex: 1; margin-bottom: 0;">
                <div class="saas-title">
                    <div class="icon-box" style="background:#F0FDF4; color:#10B981;">🔗</div> Google 资产护城河
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                    {render_kpi_card('收录规模', f"{index_count:,.0f}", 'green', highlight=True)}
                    {render_kpi_card('外链总数', f"{backlink_count:,.0f}", 'green')}
                    {render_kpi_card('域名广度', f"{backlink_domain:,.0f}", 'green')}
                </div>
                <div style="margin-top: 24px; font-size: 13px; color: #9CA3AF;">反映网站在搜索引擎中的长期信誉积累。</div>
            </div>
        </div>
        """
        st.markdown(bottom_html, unsafe_allow_html=True)

    else:
        st.warning(f"⚠️ 在所选时间（{time_hint}）内暂无可用数据。")

    # ==========================================
    # 🗄️ 底部区域：各站点底层全量明细表 (兼容 SaaS 风格容器)
    # ==========================================
    st.markdown("<div style='font-size: 20px; font-weight: 700; color: #111827; margin: 40px 0 10px 0;'>🗄️ 各站点底层原始数据明细</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 14px;'>以下表格自动提取展示最近 15 天的全量底层指标，时间按升序排布以供追溯。</div>", unsafe_allow_html=True)

    recent_dates = sorted(df_all['Date'].unique())[-15:]
    df_raw_tables = df_all[df_all['Date'].isin(recent_dates)]

    for site in fixed_sites_order:
        df_site_raw = df_raw_tables[df_raw_tables['Site'] == site]
        if not df_site_raw.empty:
            st.markdown(f"<div style='font-weight: 600; font-size: 16px; color:#374151; margin-bottom: 12px;'>🌍 {en_to_cn.get(site, site)} (Callie {site})</div>", unsafe_allow_html=True)
            with st.container(border=True):
                df_pivot = df_site_raw.pivot_table(index='Metric', columns='Date', values='Value', aggfunc=lambda x: ' '.join(str(v) for v in x))
                sorted_dates = sorted(df_pivot.columns, reverse=False)
                df_pivot = df_pivot[sorted_dates]
                df_pivot.columns = [d.strftime('%m-%d') for d in df_pivot.columns] 
                st.dataframe(df_pivot, width='stretch')

else:
    st.info("尚未扫描到有效的站点数据，请检查网络连接或表单格式。")
