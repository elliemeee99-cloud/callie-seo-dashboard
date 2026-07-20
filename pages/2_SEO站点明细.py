import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import re
import gc
import plotly.graph_objects as go

# ==========================================
# 📍 全局变量与字典映射
# ==========================================
fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
en_to_cn = {v: k for k, v in cn_to_en.items()}
site_flags = {"DE": "🇩🇪", "FR": "🇫🇷", "ES": "🇪🇸", "IT": "🇮🇹", "NL": "🇳🇱", "NO": "🇳🇴", "SE": "🇸🇪", "FI": "🇫🇮", "PL": "🇵🇱"}

# Google 经典四色循环 (蓝, 红, 黄, 绿)
GOOGLE_COLORS = ['#4285F4', '#EA4335', '#FBBC05', '#34A853']

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO站点明细", page_icon="🌍", layout="wide")

# ==========================================
# 🎨 现代 SaaS 顶级视觉重构 
# ==========================================
st.markdown("""
<style>
/* 1. 整体极简浅灰背景 */
.stApp { 
    background-color: #F5F7FA !important; 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* 2. 增加顶部留白 */
.block-container { padding-top: 5rem !important; max-width: 96% !important; }

/* 3. 🔥 强力胶囊化单选框 */
div[role="radiogroup"] { gap: 12px !important; flex-wrap: wrap; }
div[role="radiogroup"] > label {
    background-color: #ffffff !important;
    border: 1px solid #E5E7EB !important;
    padding: 8px 24px !important;
    border-radius: 30px !important;
    cursor: pointer !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
div[role="radiogroup"] > label:hover { background-color: #F9FAFB !important; border-color: #D1D5DB !important; }
div[role="radiogroup"] > label > div:first-child { display: none !important; } 
div[role="radiogroup"] > label p, div[role="radiogroup"] > label div {
    margin: 0 !important; font-weight: 600 !important; color: #4B5563 !important; font-size: 14px !important;
}
div[role="radiogroup"] > label[aria-checked="true"], div[role="radiogroup"] > label:has(input:checked) {
    background-color: #2563EB !important; border-color: #2563EB !important; box-shadow: 0 4px 12px rgba(37,99,235,0.2) !important;
}
div[role="radiogroup"] > label[aria-checked="true"] p, div[role="radiogroup"] > label:has(input:checked) p,
div[role="radiogroup"] > label[aria-checked="true"] div, div[role="radiogroup"] > label:has(input:checked) div {
    color: #ffffff !important;
}

/* 4. 底层原始数据表格容器化 */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important; border: 1px solid #EEF2F6 !important;
    border-radius: 16px !important; box-shadow: 0 4px 20px rgba(0,0,0,0.02) !important; padding: 24px !important;
}

/* 5. 自定义大模块 Section */
.saas-section {
    background: #ffffff; border-radius: 16px; border: 1px solid #EEF2F6;
    box-shadow: 0 4px 20px rgba(0,0,0,0.02); padding: 32px; margin-bottom: 32px;
}
.saas-title {
    font-size: 20px; font-weight: 700; color: #111827; margin-bottom: 24px;
    display: flex; align-items: center; gap: 12px; letter-spacing: -0.5px;
}
.icon-box {
    width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px;
}

/* 6. 折叠面板高级化 */
[data-testid="stExpander"] {
    border: 1px solid #EEF2F6 !important; border-radius: 16px !important; background-color: #ffffff !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.02) !important; margin-bottom: 24px !important; overflow: hidden;
}
[data-testid="stExpander"] summary { padding: 20px 24px !important; background-color: #ffffff !important; }
[data-testid="stExpander"] summary:hover { background-color: #F9FAFB !important; }
[data-testid="stExpander"] summary p { font-size: 18px !important; font-weight: 800 !important; color: #111827 !important; letter-spacing: -0.5px; }

/* 7. 🔥 左侧悬浮电梯专属强制锁定 CSS */
div[data-testid="column"]:has(#nav-anchor) {
    position: -webkit-sticky !important;
    position: sticky !important;
    top: 6rem !important;
    align-self: flex-start !important;
    height: calc(100vh - 7rem) !important;
    overflow-y: auto !important;
    z-index: 1000 !important;
    padding-right: 15px !important;
}
div[data-testid="column"]:has(#nav-anchor)::-webkit-scrollbar {
    width: 0px;
    background: transparent;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 底层数据与清洗逻辑 
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
# 💎 纯原生 HTML 卡片与增强版图表渲染工厂
# ==========================================
def render_kpi_card(label, value, theme, highlight=False):
    themes = {
        "blue": {"dot": "#3B82F6", "bg": "#EFF6FF", "border": "#BFDBFE"},
        "cyan": {"dot": "#06B6D4", "bg": "#ECFEFF", "border": "#A5F3FC"},
        "purple": {"dot": "#8B5CF6", "bg": "#F5F3FF", "border": "#DDD6FE"},
        "green": {"dot": "#10B981", "bg": "#F0FDF4", "border": "#BBF7D0"},
        "default": {"bg": "#FAFBFC", "border": "transparent"}
    }
    bg = themes[theme]["bg"] if highlight else themes["default"]["bg"]
    border = themes[theme]["border"] if highlight else themes["default"]["border"]
    dot = themes[theme]["dot"]
    return f'<div style="background: {bg}; border: 1px solid {border}; border-radius: 16px; padding: 24px 20px; display: flex; flex-direction: column; justify-content: center; transition: 0.2s;"><div style="font-size: 14.5px; color: #6B7280; font-weight: 500; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;"><span style="color: {dot}; font-size: 12px;">●</span> {label}</div><div style="font-size: 40px; font-weight: 600; color: #2563EB; line-height: 1; letter-spacing: -0.5px;">{value}</div></div>'

def render_traffic_item(label, value, is_last=False):
    br = "border-right: 1px solid #EEF2F6;" if not is_last else ""
    return f'<div style="flex: 1; {br} padding: 0 24px;"><div style="font-size: 14.5px; color: #6B7280; font-weight: 500; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;"><span style="color: #06B6D4; font-size: 12px;">●</span> {label}</div><div style="font-size: 42px; font-weight: 600; color: #2563EB; line-height: 1; letter-spacing: -0.5px;">{value}</div></div>'

def render_comparison_chart(df_site, metric_names, title, p1_dates, p2_dates, prefix="", chart_key="", is_snapshot=False):
    clean_names = [m.replace(' ', '').upper() for m in metric_names]
    sub = df_site[df_site['Clean_Metric'].isin(clean_names)]

    p1_vals = [sub[sub['Date'].dt.date == d.date()]['Numeric_Value'].sum() for d in p1_dates]
    p2_vals = [sub[sub['Date'].dt.date == d.date()]['Numeric_Value'].sum() for d in p2_dates]

    if is_snapshot:
        def get_latest_valid(vals):
            for v in reversed(vals):
                if v > 0: return v
            return 0
        val1 = get_latest_valid(p1_vals)
        val2 = get_latest_valid(p2_vals)
        time_label_1, time_label_2 = "期末最新", "前期期末"
    else:
        val1, val2 = sum(p1_vals), sum(p2_vals)
        time_label_1, time_label_2 = "过去 7 天", "之前 7 天"

    if val2 > 0:
        delta_pct = (val1 - val2) / val2 * 100
        delta_str = f"↑ {delta_pct:.1f}%" if delta_pct >= 0 else f"↓ {abs(delta_pct):.1f}%"
        delta_color, bg_color = ("#10B981", "#F0FDF4") if delta_pct >= 0 else ("#EF4444", "#FEF2F2")
    else:
        delta_str, delta_color, bg_color = "一", "#9CA3AF", "#F3F4F6"

    val_str1 = f"{prefix}{val1:,.2f}" if prefix == "$" else f"{prefix}{val1:,.0f}"
    val_str2 = f"{prefix}{val2:,.2f}" if prefix == "$" else f"{prefix}{val2:,.0f}"

    x_labels = [d.strftime('%m-%d') for d in p1_dates] 
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(x=x_labels, y=p1_vals, mode='lines+markers', name='过去 7 天', line=dict(color='#4285F4', width=3), marker=dict(size=10, symbol='circle', color='#4285F4', line=dict(color='white', width=1.5)), hovertemplate='<b>%{x}</b><br>过去 7 天: ' + prefix + '%{y:,.2f}<extra></extra>' if prefix else '<b>%{x}</b><br>过去 7 天: %{y:,.0f}<extra></extra>'))
    fig.add_trace(go.Scatter(x=x_labels, y=p2_vals, mode='lines+markers', name='之前 7 天', line=dict(color='#EA4335', width=3), marker=dict(size=10, symbol='circle', color='#EA4335', line=dict(color='white', width=1.5)), hovertemplate='<b>%{x}</b><br>之前 7 天: ' + prefix + '%{y:,.2f}<extra></extra>' if prefix else '<b>%{x}</b><br>之前 7 天: %{y:,.0f}<extra></extra>'))

    fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified", xaxis=dict(type='category', showgrid=False, color='#6B7280'), yaxis=dict(showgrid=True, gridcolor='#E5E7EB', color='#6B7280', zeroline=False), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="#4B5563")), height=240, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

    with st.container(border=True):
        st.markdown(f'''<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;"><div style="font-weight:700; color:#374151; font-size:15px;">{title}</div><div style="font-size:13px; color:{delta_color}; font-weight:700; background:{bg_color}; padding:4px 10px; border-radius:12px;">{delta_str}</div></div><div style="font-size:13px; color:#6B7280; margin-bottom: 16px;">{time_label_1}: <b style="color:#111827;">{val_str1}</b> <span style="margin:0 6px;">|</span> {time_label_2}: {val_str2}</div>''', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=chart_key)

# ==========================================
# 📐 页面头部与同步按钮
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>🌍 Analytics Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 32px; font-size: 15px;'>全局站点全景与深度体检数据台。</div>", unsafe_allow_html=True)
with col_refresh:
    st.write("") 
    if st.button("🔄 同步最新数据"):
        load_site_full_details.clear()
        st.rerun()

with st.spinner("✨ 正在智能扫描最新数据..."):
    df_all = load_site_full_details()

if df_all is not None and not df_all.empty:

    mask_valid = (df_all['Clean_Metric'].isin(['网站总流量', 'SUPERSET总销售额'])) & (df_all['Numeric_Value'] > 0)
    valid_dates = df_all[mask_valid]['Date']
    actual_max_date = valid_dates.max() if not valid_dates.empty else df_all['Date'].max()

    # ==========================================
    # 🎛️ 顶部控制器
    # ==========================================
    site_options = ["全部站点"] + list(cn_to_en.keys())
    
    col_ctrl1, col_ctrl2 = st.columns([2.5, 1])
    with col_ctrl1:
        try:
            selected_site_cn = st.pills("站点切换", site_options, default="全部站点", label_visibility="collapsed")
            if not selected_site_cn: selected_site_cn = "全部站点"
        except AttributeError:
            selected_site_cn = st.radio("站点切换", site_options, horizontal=True, label_visibility="collapsed")
            
    with col_ctrl2:
        try:
            time_view = st.pills("时间切换", ["昨日数据", "过去7天数据"], default="昨日数据", label_visibility="collapsed")
            if not time_view: time_view = "昨日数据"
        except AttributeError:
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
    # 🏆 第一部分：四大指标区块展示
    # ==========================================
    if not df_target.empty:
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

        sales_cards = "".join([
            render_kpi_card('Superset SEO销售额', f"${ss_seo_sales:,.2f}", 'blue', highlight=True),
            render_kpi_card('Superset 总销售额', f"${ss_total_sales:,.2f}", 'blue'),
            render_kpi_card('Superset 占比情况', f"{ss_ratio:.2f}%", 'blue'),
            render_kpi_card('GA4 SEO销售额', f"${ga4_seo_sales:,.2f}", 'blue'),
            render_kpi_card('GA4 网站总销售额', f"${ga4_total_sales:,.2f}", 'blue'),
            render_kpi_card('GA4 占比情况', f"{ga4_ratio:.2f}%", 'blue')
        ])
        sales_html = f'<div class="saas-section"><div class="saas-title"><div class="icon-box" style="background:#EFF6FF; color:#3B82F6;">💰</div> 核心销售额追踪</div><div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 20px;">{sales_cards}</div></div>'
        st.markdown(sales_html, unsafe_allow_html=True)

        traffic_items = "".join([
            render_traffic_item('SEO 流量', f"{seo_traffic:,.0f}"),
            render_traffic_item('SEO Blog 流量', f"{seo_blog_traffic:,.0f}"),
            render_traffic_item('SEO 站内流量', f"{seo_onsite_traffic:,.0f}"),
            render_traffic_item('网站总流量', f"{total_traffic:,.0f}"),
            render_traffic_item('跳出率', f"{bounce_rate:.2f}%", is_last=True)
        ])
        traffic_html = f'<div class="saas-section"><div class="saas-title"><div class="icon-box" style="background:#ECFEFF; color:#06B6D4;">🌊</div> 流量漏斗健康度</div><div style="display: flex; align-items: center; margin: 20px -24px 0 -24px;">{traffic_items}</div><div style="margin-top: 32px; padding-top: 16px; border-top: 1px dashed #E5E7EB; font-size: 13px; color: #9CA3AF; display: flex; align-items: center; gap: 6px;"><span style="color: #06B6D4; font-size: 16px;">✦</span> 所有流量指标均已过滤异常抓取，建议结合跳出率动态评估渠道质量。</div></div>'
        st.markdown(traffic_html, unsafe_allow_html=True)

        ai_cards = "".join([
            render_kpi_card('AI 销售额', f"${ai_sales:,.2f}", 'purple', highlight=True),
            render_kpi_card('AI 流量获取', f"{ai_traffic:,.0f}", 'purple')
        ])
        google_cards = "".join([
            render_kpi_card('收录规模', f"{index_count:,.0f}", 'green', highlight=True),
            render_kpi_card('外链总数', f"{backlink_count:,.0f}", 'green'),
            render_kpi_card('域名广度', f"{backlink_domain:,.0f}", 'green')
        ])
        bottom_html = f'<div style="display: flex; gap: 32px; margin-bottom: 32px;"><div class="saas-section" style="flex: 1; margin-bottom: 0;"><div class="saas-title"><div class="icon-box" style="background:#F5F3FF; color:#8B5CF6;">🤖</div> AI Assistant 转化</div><div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">{ai_cards}</div><div style="margin-top: 24px; font-size: 13px; color: #9CA3AF;">监控大模型及助手带来的直接商业价值。</div></div><div class="saas-section" style="flex: 1; margin-bottom: 0;"><div class="saas-title"><div class="icon-box" style="background:#F0FDF4; color:#10B981;">🔗</div> Google 资产护城河</div><div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">{google_cards}</div><div style="margin-top: 24px; font-size: 13px; color: #9CA3AF;">反映网站在搜索引擎中的长期信誉积累。</div></div></div>'
        st.markdown(bottom_html, unsafe_allow_html=True)

    else:
        st.warning(f"⚠️ 在所选时间（{time_hint}）内暂无可用数据。")

    # ==========================================
    # 🗄️ 第二部分：各站点底层细分图表与全量明细表 
    # ==========================================
    st.markdown("<div style='font-size: 26px; font-weight: 800; color: #111827; margin: 64px 0 20px 0;'>🗄️ 各站点底层明细与趋势对比</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div style='font-weight:700; color:#334155; margin-bottom:8px;'>📅 全局时间范围筛选 (控制下方所有站点数据及图表)</div>", unsafe_allow_html=True)
        bottom_date_range = st.date_input("日期筛选", value=(actual_max_date - pd.Timedelta(days=14), actual_max_date), max_value=actual_max_date, label_visibility="collapsed")

    if isinstance(bottom_date_range, tuple):
        if len(bottom_date_range) == 2: s_date, e_date = bottom_date_range
        else: s_date = e_date = bottom_date_range[0]
    else: s_date = e_date = bottom_date_range

    s_date_ts = pd.Timestamp(s_date)
    e_date_ts = pd.Timestamp(e_date)

    p1_end = e_date_ts
    p1_start = p1_end - pd.Timedelta(days=6)
    p1_dates = pd.date_range(start=p1_start, end=p1_end).tolist()

    p2_end = p1_start - pd.Timedelta(days=1)
    p2_start = p2_end - pd.Timedelta(days=6)
    p2_dates = pd.date_range(start=p2_start, end=p2_end).tolist()

    st.markdown(f"""
    <div style='background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 16px; margin-bottom: 32px; margin-top: 16px;'>
        <div style='color: #1E3A8A; font-weight: 700; font-size: 15px; margin-bottom: 6px;'>📊 趋势对比说明</div>
        <div style='color: #2563EB; font-size: 13.5px; line-height: 1.6;'>
            趋势图动态锚定您在上方选择的结束日期（<b>{e_date_ts.strftime('%Y-%m-%d')}</b>）。<br>
            图表中的 <b style="color:#4285F4;">Google 蓝线</b> 代表 <b>过去 7 天（{p1_start.strftime('%m-%d')} 至 {p1_end.strftime('%m-%d')}）</b>；<b style="color:#EA4335;">Google 红线</b> 代表 <b>之前 7 天（{p2_start.strftime('%m-%d')} 至 {p2_end.strftime('%m-%d')}）</b>。<br>
            数据表格则展示您所选完整区间的全量明细。
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_raw_tables = df_all[(df_all['Date'].dt.date >= s_date_ts.date()) & (df_all['Date'].dt.date <= e_date_ts.date())]

    # 🔥 构建页面内非对称分栏：左边是悬浮导航，右侧是国家报表列表
    col_nav, col_charts = st.columns([1.5, 8.5])

    with col_nav:
        # 🔥 插入唯一靶向锚点，配合顶层 :has() CSS 实现侧边栏真·悬浮
        st.markdown("<span id='nav-anchor'></span>", unsafe_allow_html=True)
        
        # 🔥 彻底压缩的单行 HTML，防止 Markdown 解析器干扰产生乱码
        nav_html = "<div class='sticky-nav'><div style='font-size: 16px; font-weight: 800; color: #1e293b; margin-bottom: 16px;'>📍 站点快捷定位</div><div style='display:flex; flex-direction:column; gap:8px;'>"
        for idx, site in enumerate(fixed_sites_order):
            g_color = GOOGLE_COLORS[idx % 4]
            flag = site_flags.get(site, '🌍')
            cn_name = en_to_cn.get(site, site)
            nav_html += f"<a href='#jump-{site}' target='_self' style='text-decoration: none; padding: 10px 12px; background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {g_color}; border-radius: 6px; color: #1e293b; font-weight: 600; display: flex; align-items: center; gap: 8px; transition: all 0.2s;' onmouseover=\"this.style.backgroundColor='#f8fafc';\" onmouseout=\"this.style.backgroundColor='#ffffff';\"><span style='font-size: 16px;'>{flag}</span><span style='font-size: 13px;'>{site} {cn_name}</span></a>"
        nav_html += "</div></div>"
        st.markdown(nav_html, unsafe_allow_html=True)

    with col_charts:
        # --- 开始遍历渲染分站点数据 ---
        for site in fixed_sites_order:
            df_site_raw = df_all[df_all['Site'] == site]
            if not df_site_raw.empty:
                
                # HTML 锚点：与左侧导航栏跳转一一对应
                st.markdown(f"<div id='jump-{site}' style='position: relative; top: -100px;'></div>", unsafe_allow_html=True)
                
                site_flag = site_flags.get(site, "🌍")
                site_name_cn = en_to_cn.get(site, site)
                expander_title = f"{site_flag} {site_name_cn} (Callie {site}) 数据中心"
                
                with st.expander(expander_title, expanded=True):
                    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

                    r1c1, r1c2 = st.columns(2)
                    with r1c1: render_comparison_chart(df_site_raw, ['Superset SEO销售额', 'SupersetSEO销售额'], '💰 Superset SEO 销售额对比', p1_dates, p2_dates, prefix="$", chart_key=f"{site}_ss_seo_sales")
                    with r1c2: render_comparison_chart(df_site_raw, ['GA4 SEO销售额', 'GA4SEO销售额'], '💰 GA4 SEO 销售额对比', p1_dates, p2_dates, prefix="$", chart_key=f"{site}_ga4_seo_sales")

                    r2c1, r2c2 = st.columns(2)
                    with r2c1: render_comparison_chart(df_site_raw, ['SEO 总流量', 'SEO流量', 'SEO总流量'], '🌊 GA4 SEO 流量对比', p1_dates, p2_dates, prefix="", chart_key=f"{site}_ga4_seo_traffic")
                    with r2c2: render_comparison_chart(df_site_raw, ['SEO Blog流量', 'SEOBlog流量'], '🌊 GA4 SEO Blog 流量对比', p1_dates, p2_dates, prefix="", chart_key=f"{site}_ga4_blog_traffic")

                    r3c1, r3c2 = st.columns(2)
                    with r3c1: render_comparison_chart(df_site_raw, ['SEO 站内流量', 'SEO站内流量'], '🌊 GA4 SEO 站内流量对比', p1_dates, p2_dates, prefix="", chart_key=f"{site}_ga4_onsite_traffic")
                    with r3c2: render_comparison_chart(df_site_raw, ['收录'], '🔗 Google 收录规模对比', p1_dates, p2_dates, prefix="", chart_key=f"{site}_google_index", is_snapshot=True)

                    r4c1, r4c2 = st.columns(2)
                    with r4c1: render_comparison_chart(df_site_raw, ['AI Assistant 销售额', 'AIAssistant销售额', 'AI销售额'], '🤖 AI Assistant 销售额对比', p1_dates, p2_dates, prefix="$", chart_key=f"{site}_ai_sales")
                    with r4c2: render_comparison_chart(df_site_raw, ['AI Assistant 流量', 'AIAssistant流量', 'AI流量'], '🤖 AI Assistant 流量对比', p1_dates, p2_dates, prefix="", chart_key=f"{site}_ai_traffic")

                    df_table_site = df_raw_tables[df_raw_tables['Site'] == site]
                    if not df_table_site.empty:
                        st.markdown("<div style='font-weight: 600; font-size: 14px; color:#6B7280; margin: 16px 0 8px 0;'>👉 原始指标明细表 (受全局时间范围约束)</div>", unsafe_allow_html=True)
                        with st.container(border=True):
                            df_pivot = df_table_site.pivot_table(index='Metric', columns='Date', values='Value', aggfunc=lambda x: ' '.join(str(v) for v in x))
                            sorted_dates = sorted(df_pivot.columns, reverse=False)
                            df_pivot = df_pivot[sorted_dates]
                            df_pivot.columns = [d.strftime('%m-%d') for d in df_pivot.columns]
                            
                            try:
                                st.dataframe(df_pivot, use_container_width=True)
                            except Exception:
                                st.dataframe(df_pivot)

else:
    st.info("尚未扫描到有效的站点数据，请检查网络连接或表单格式。")
