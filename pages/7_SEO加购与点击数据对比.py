import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
import re

st.set_page_config(page_title="加购与点击数据对比", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 UI 样式与左侧悬浮导航
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:140px!important}
h1, h2, h3, h4, h5, h6 {color:#111827!important}
p {color:#6B7280!important;font-size:14px!important}
hr{border-color:#E5E7EB!important;margin:8px 0!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px!important;border:1px solid #E5E7EB!important;background-color:#FFFFFF;box-shadow:0 1px 3px rgba(0,0,0,.06)!important;padding:16px!important;margin-bottom:12px!important}

/* KPI 卡片 */
.kpi-card {background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align: center; height: 100%;}
.kpi-title {font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 8px;}
.kpi-value {font-size: 30px; font-weight: 700; color: #0F172A; margin: 0;}
.kpi-value.blue {color: #2563EB;}
.kpi-value.green {color: #10B981;}
.kpi-value.purple {color: #8B5CF6;}
.kpi-value.orange {color: #F59E0B;}

/* 左侧浮动导航菜单 */
.country-nav{position:fixed!important;top:11rem!important;left:1.2rem!important;width:100px!important;max-height:calc(100vh - 10rem)!important;overflow-y:auto!important;z-index:9999!important;background:#FFFFFF!important;padding:12px 10px!important;border-radius:12px!important;border:1px solid #EEF2F6!important;box-shadow:0 8px 24px rgba(0,0,0,0.04)!important}
.country-nav::-webkit-scrollbar{width:0;background:transparent}
.country-nav a{display:flex!important;align-items:center!important;gap:6px!important;padding:6px 6px!important;margin-bottom:6px!important;border-radius:6px!important;color:#1e293b!important;font-weight:600!important;text-decoration:none!important;transition:all .15s ease!important}
.country-nav a:hover{transform:translateX(2px)!important;background-color:#F1F5F9!important}
.c-flag { font-size: 16px; line-height: 1; }
.c-name { display:inline-block; color:#fff; font-size:11px; font-weight:700; border-radius:3px; padding:2px 4px; line-height:1.2; }

/* 顶部导航 Tabs */
[data-testid="stPageLink-NavLink"]{background:transparent!important;border:none!important;border-radius:0!important;padding:8px 14px!important;border-bottom:2px solid transparent!important;margin-bottom:-1px}
[data-testid="stPageLink-NavLink"]:hover{background:#F1F5F9!important}
[data-testid="stPageLink-NavLink"] p{font-weight:600!important;color:#64748B!important;font-size:14px!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"]{border-bottom:2px solid #2563EB!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"] p{color:#2563EB!important;font-weight:600!important}
.back-to-top{position:fixed;bottom:32px;right:32px;background:#2563EB;color:#fff!important;width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;text-decoration:none!important;z-index:99999}
.back-to-top:hover{background:#1D4ED8}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
</style>""", unsafe_allow_html=True)

# 导航辅助组件
def get_nav_html(prefix, icon, title):
    sites = [('DE', '🇩🇪', '#4285F4'), ('FR', '🇫🇷', '#EA4335'), ('ES', '🇪🇸', '#FBBC05'),
             ('IT', '🇮🇹', '#34A853'), ('NL', '🇳🇱', '#4285F4'), ('NO', '🇳🇴', '#EA4335'),
             ('SE', '🇸🇪', '#FBBC05'), ('FI', '🇫🇮', '#34A853'), ('PL', '🇵🇱', '#4285F4'),
             ('EN', '🇬🇧', '#111827')]
    links = ""
    for site, flag, color in sites:
        links += f'<a href="#{prefix}-{site}" style="border-left:4px solid {color};"><span class="c-flag">{flag}</span><span class="c-name" style="background:{color};">{site}</span></a>'
    return f'<div class="country-nav"><div style="font-size:12px;font-weight:800;color:#1e293b;margin-bottom:12px;display:flex;align-items:center;gap:4px;"><span style="font-size:14px;">{icon}</span> {title}</div><div style="display:flex;flex-direction:column;">{links}</div></div>'

# --- 顶部导航栏 ---
_nc = st.columns([0.1, 1, 1, 1, 1, 1, 1, 1, 1.2, 0.1])
with _nc[0]: pass
with _nc[1]: st.page_link("app.py", label="App 首页", icon="🏠")
with _nc[2]: st.page_link("pages/1_SEO目标概览.py", label="目标概览", icon="🎯")
with _nc[3]: st.page_link("pages/2_SEO站点明细.py", label="站点明细", icon="🗄️")
with _nc[4]: st.page_link("pages/3_SEO需求管理.py", label="需求管理", icon="📋")
with _nc[5]: st.page_link("pages/4_SEO重点事件记录.py", label="事件记录", icon="📅")
with _nc[6]: st.page_link("pages/5_SEO月度数据对比.py", label="月度对比", icon="📊")
with _nc[7]: st.page_link("pages/6_AI来源数据.py", label="AI 来源", icon="🤖")
with _nc[8]: st.page_link("pages/7_SEO加购与点击数据对比.py", label="加购与转化", icon="🛒")
st.markdown("<div style='height:1px;background:#E2E8F0;margin:2px 0 14px 0;'></div>", unsafe_allow_html=True)
st.markdown("<a href='#top-anchor' class='back-to-top' title='\u56de\u5230\u9876\u90e8'>\u2191</a>", unsafe_allow_html=True)

# --- 页面头部 ---
col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>🛒 SEO 加购与点击对比大盘</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>直连 Google Sheets，深度比对 2025 vs 2026 前端引流与后端转化 (加购/订单) 表现</div>", unsafe_allow_html=True)
with col_h_right:
    st.markdown(f"<div style='color:#9CA3AF;font-size:11px;text-align:right;margin-bottom:2px;line-height:1;'>最后同步：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    if st.button("🔄 从云端刷新数据", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# ⚙️ 核心解析引擎：全图雷达扫描
# ==========================================
def safe_parse_ym(val):
    if pd.isna(val) or str(val).strip() == '': return None
    if isinstance(val, datetime.datetime): return val.strftime('%Y-%m')
    if isinstance(val, (int, float)):
        try: return pd.to_datetime(val, origin='1899-12-30', unit='D').strftime('%Y-%m')
        except: return None
    v_str = str(val).strip()
    match = re.search(r'(202\d)[年\-/]\s*(\d{1,2})', v_str)
    if match: return f"{match.group(1)}-{int(match.group(2)):02d}"
    try: return pd.to_datetime(v_str).strftime('%Y-%m')
    except: return None

def clean_num(x):
    try:
        return float(str(x).replace('$', '').replace(',', '').strip())
    except:
        return 0.0

@st.cache_data(ttl=600)
def load_conversion_data():
    url = "https://docs.google.com/spreadsheets/d/1CUaU-_F7sz9OkqGSblVfjODihzMiKPVvEGNDZD6mKVA/export?format=xlsx"
    try:
        xls_dict = pd.read_excel(url, sheet_name=None, header=None)
    except Exception as e:
        raise RuntimeError(f"无法读取表格，请检查网络或分享权限(需知道链接的人可查看): {e}")

    # 模糊匹配表名
    cart_sheet_name = next((k for k in xls_dict.keys() if '加购' in k), list(xls_dict.keys())[0])
    click_sheet_name = next((k for k in xls_dict.keys() if '点击' in k), list(xls_dict.keys())[-1] if len(xls_dict)>1 else list(xls_dict.keys())[0])

    df_cart_raw = xls_dict[cart_sheet_name]
    df_click_raw = xls_dict[click_sheet_name]

    # --- 1. 解析加购数据 ---
    cart_records = []
    for r in range(len(df_cart_raw)):
        for c in range(len(df_cart_raw.columns)):
            val = str(df_cart_raw.iloc[r, c]).strip()
            if val == '加购数' and c > 0:
                site = str(df_cart_raw.iloc[r, c-1]).strip().upper()
                for row_idx in range(r+1, len(df_cart_raw)):
                    date_val = df_cart_raw.iloc[row_idx, c-1]
                    if pd.isna(date_val) or str(date_val).strip() == '': break
                    ym = safe_parse_ym(date_val)
                    if not ym: break
                    
                    cart_records.append({
                        'Site': site,
                        'Month': ym,
                        'Cart': clean_num(df_cart_raw.iloc[row_idx, c]),
                        'Order': clean_num(df_cart_raw.iloc[row_idx, c+1] if c+1 < len(df_cart_raw.columns) else 0)
                    })
    df_cart = pd.DataFrame(cart_records)

    # --- 2. 解析点击数据 ---
    click_records = []
    for r in range(len(df_click_raw)):
        for c in range(len(df_click_raw.columns)):
            val = str(df_click_raw.iloc[r, c]).strip()
            if val == '总点击' and c > 0:
                site = str(df_click_raw.iloc[r, c-1]).strip().upper()
                for row_idx in range(r+1, len(df_click_raw)):
                    date_val = df_click_raw.iloc[row_idx, c-1]
                    if pd.isna(date_val) or str(date_val).strip() == '': break
                    ym = safe_parse_ym(date_val)
                    if not ym: break
                    
                    click_records.append({
                        'Site': site,
                        'Month': ym,
                        'Total_Click': clean_num(df_click_raw.iloc[row_idx, c]),
                        'Brand_Click': clean_num(df_click_raw.iloc[row_idx, c+1] if c+1 < len(df_click_raw.columns) else 0),
                        'Blog_Click': clean_num(df_click_raw.iloc[row_idx, c+2] if c+2 < len(df_click_raw.columns) else 0),
                        'UTM_Click': clean_num(df_click_raw.iloc[row_idx, c+3] if c+3 < len(df_click_raw.columns) else 0),
                        'Onsite_Click': clean_num(df_click_raw.iloc[row_idx, c+4] if c+4 < len(df_click_raw.columns) else 0)
                    })
    df_click = pd.DataFrame(click_records)

    # --- 3. 合并大宽表 ---
    if df_cart.empty and df_click.empty: return pd.DataFrame()
    elif df_click.empty: return df_cart
    elif df_cart.empty: return df_click
        
    df_final = pd.merge(df_cart, df_click, on=['Site', 'Month'], how='outer').fillna(0)
    return df_final

# --- 通用 YoY 绘图函数 ---
def plot_yoy(df, metric, title):
    fig = go.Figure()
    cs = ['#10B981', '#3B82F6', '#F59E0B'] # 绿, 蓝, 橙
    for i, year in enumerate(sorted(df['Year'].unique())):
        dy = df[df['Year'] == year].sort_values('Mnum')
        fig.add_trace(go.Scatter(
            x=dy['Mnum'], y=dy[metric], mode='lines+markers', name=f'{year}年',
            line=dict(width=3, color=cs[i % len(cs)]), marker=dict(size=8)
        ))
    fig.update_layout(
        height=320, hovermode='x unified', margin=dict(l=10, r=10, t=40, b=10),
        title=dict(text=title, font=dict(size=14, color="#374151")),
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickmode='array', tickvals=list(range(1,13)), ticktext=[f'{i}月' for i in range(1,13)]),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    return fig

# ==========================================
# 📊 页面渲染与大盘展示
# ==========================================
try:
    with st.spinner("🚀 正在通过 API 直连 Google Sheets 解析矩阵数据..."):
        df_all = load_conversion_data()
        
    if df_all.empty:
        st.warning("⚠️ 表格连接成功，但未解析到有效数据。请检查表格结构是否符合规范。")
        st.stop()
        
    # 添加年份和月份列以供分析，并计算合并字段 UTM + 品牌词点击
    df_all['Date'] = pd.to_datetime(df_all['Month'] + '-01')
    df_all['Year'] = df_all['Date'].dt.year.astype(str)
    df_all['Mnum'] = df_all['Date'].dt.month
    df_all['UTM_Brand_Click'] = df_all['UTM_Click'] + df_all['Brand_Click']
    
    # ------------------------------------------
    # 模块 1：全站汇总 KPI (2026 YTD)
    # ------------------------------------------
    st.markdown("### 🏆 2026 vs 2025 同期转化对决 (全站大盘)")
    df_2026 = df_all[df_all['Month'] >= '2026-01']
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🛒 2026 全站累计加购数</div><div class="kpi-value blue">{df_2026["Cart"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">📦 2026 全站累计订单数</div><div class="kpi-value green">{df_2026["Order"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🖱️ 2026 全站累计总点击</div><div class="kpi-value purple">{df_2026["Total_Click"].sum():,.0f}</div></div>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    # ------------------------------------------
    # 模块 2：全站 YoY 同比折线图 (2x2 宫格)
    # ------------------------------------------
    df_global_yoy = df_all.groupby(['Year', 'Mnum'])[['Cart', 'Order', 'Onsite_Click', 'UTM_Brand_Click']].sum().reset_index()
    
    st.markdown("#### 📉 全站年度转化同比趋势 (2025 vs 2026)")
    with st.container(border=True):
        # 第一行：加购数 和 订单数
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1: st.plotly_chart(plot_yoy(df_global_yoy, 'Cart', "🛒 加购数 YoY"), use_container_width=True)
        with r1_c2: st.plotly_chart(plot_yoy(df_global_yoy, 'Order', "📦 订单数 YoY"), use_container_width=True)
        
        # 第二行：站内点击 和 UTM+品牌词点击
        r2_c1, r2_c2 = st.columns(2)
        with r2_c1: st.plotly_chart(plot_yoy(df_global_yoy, 'Onsite_Click', "🏠 SEO 站内点击 YoY"), use_container_width=True)
        with r2_c2: st.plotly_chart(plot_yoy(df_global_yoy, 'UTM_Brand_Click', "🏷️ UTM + 品牌词点击 YoY"), use_container_width=True)

    # 全站细分各项点击堆叠图
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("**🧩 全站各项点击流量结构趋势 (品牌词/Blog/UTM/站内)**")
        df_click_melt = df_all.melt(id_vars=['Month'], value_vars=['Brand_Click', 'Blog_Click', 'UTM_Click', 'Onsite_Click'], var_name='Click_Type', value_name='Clicks')
        df_click_agg = df_click_melt.groupby(['Month', 'Click_Type'])['Clicks'].sum().reset_index()
        
        fig_clicks = px.bar(
            df_click_agg, x='Month', y='Clicks', color='Click_Type', 
            template="plotly_white", color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_clicks.update_layout(height=380, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
        st.plotly_chart(fig_clicks, use_container_width=True)

    st.markdown("<hr style='margin:32px 0; border-color:#e2e8f0;'/>", unsafe_allow_html=True)
    
    # ------------------------------------------
    # 模块 3：各分站点独立看板 (带导航)
    # ------------------------------------------
    st.markdown("### 🏬 各分站点 YoY 同比下钻")
    st.markdown(get_nav_html('site', '📍', '分站导航'), unsafe_allow_html=True)
    
    sites_list = ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']
    
    for site in sites_list:
        df_site = df_all[df_all['Site'] == site].copy()
        if df_site.empty: continue
        
        st.markdown(f'<div id="site-{site}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
        with st.expander(f"📌 {site} 站点 — 加购与点击转化趋势", expanded=True):
            
            # 站点 2026 KPI
            df_site_2026 = df_site[df_site['Month'] >= '2026-01']
            sc1, sc2, sc3 = st.columns(3)
            with sc1: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 加购数 ({site})</div><div class="kpi-value blue" style="font-size:24px;">{df_site_2026["Cart"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with sc2: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 订单数 ({site})</div><div class="kpi-value green" style="font-size:24px;">{df_site_2026["Order"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            with sc3: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 总点击 ({site})</div><div class="kpi-value purple" style="font-size:24px;">{df_site_2026["Total_Click"].sum():,.0f}</div></div>', unsafe_allow_html=True)
            
            st.write("")
            
            # 站点 YoY 图 (2x2 宫格)
            st.markdown(f"**📉 {site} 年度转化同比趋势**")
            sy_r1_c1, sy_r1_c2 = st.columns(2)
            with sy_r1_c1: st.plotly_chart(plot_yoy(df_site, 'Cart', f"🛒 {site} 加购数 YoY"), use_container_width=True)
            with sy_r1_c2: st.plotly_chart(plot_yoy(df_site, 'Order', f"📦 {site} 订单数 YoY"), use_container_width=True)
            
            sy_r2_c1, sy_r2_c2 = st.columns(2)
            with sy_r2_c1: st.plotly_chart(plot_yoy(df_site, 'Onsite_Click', f"🏠 {site} 站内点击 YoY"), use_container_width=True)
            with sy_r2_c2: st.plotly_chart(plot_yoy(df_site, 'UTM_Brand_Click', f"🏷️ {site} UTM+品牌词点击 YoY"), use_container_width=True)
            
            # 站点各项点击结构走势
            st.markdown(f"**🧩 {site} 站点各项点击流量结构趋势**")
            df_s_click_melt = df_site.melt(id_vars=['Month'], value_vars=['Brand_Click', 'Blog_Click', 'UTM_Click', 'Onsite_Click'], var_name='Click_Type', value_name='Clicks')
            fig_s_clicks = px.bar(
                df_s_click_melt, x='Month', y='Clicks', color='Click_Type', 
                template="plotly_white", color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_s_clicks.update_layout(height=300, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
            st.plotly_chart(fig_s_clicks, use_container_width=True)

except Exception as e:
    st.error(f"❌ 读取异常：{e}")
