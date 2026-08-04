import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
import re

st.set_page_config(page_title="AI 来源数据监控", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

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
[data-testid="stPageLink-NavLink"] p{font-weight:600!important;color:#64748B!important;font-size:16px!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"]{border-bottom:2px solid #2563EB!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"] p{color:#2563EB!important;font-weight:600!important}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
.back-to-top{position:fixed;bottom:32px;right:32px;background:#2563EB;color:#fff!important;width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;text-decoration:none!important;z-index:99999}
.back-to-top:hover{background:#1D4ED8}
</style>""", unsafe_allow_html=True)

# 导航辅助组件
def get_nav_html(prefix, icon, title):
    sites = [('DE', '🇩🇪', '#4285F4'), ('FR', '🇫🇷', '#EA4335'), ('ES', '🇪🇸', '#FBBC05'),
             ('IT', '🇮🇹', '#34A853'), ('NL', '🇳🇱', '#4285F4'), ('NO', '🇳🇴', '#EA4335'),
             ('SE', '🇸🇪', '#FBBC05'), ('FI', '🇫🇮', '#34A853'), ('PL', '🇵🇱', '#4285F4'),
             ('EN', '🇬🇧', '#111827')]  # 加入 EN 专属导航
    links = ""
    for site, flag, color in sites:
        links += f'<a href="#{prefix}-{site}" style="border-left:4px solid {color};"><span class="c-flag">{flag}</span><span class="c-name" style="background:{color};">{site}</span></a>'
    return f'<div class="country-nav"><div style="font-size:12px;font-weight:800;color:#1e293b;margin-bottom:12px;display:flex;align-items:center;gap:4px;"><span style="font-size:14px;">{icon}</span> {title}</div><div style="display:flex;flex-direction:column;">{links}</div></div>'

_nc = st.columns([0.1, 1, 1, 1, 1, 1, 1, 1, 0.1])
with _nc[0]: pass
with _nc[1]: st.page_link("app.py", label="App 首页", icon="🏠")
with _nc[2]: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with _nc[3]: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with _nc[4]: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with _nc[5]: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
with _nc[6]: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比", icon="📊")
with _nc[7]: st.page_link("pages/6_AI来源数据.py", label="AI 来源数据", icon="🤖")
st.markdown("<div style='height:1px;background:#E2E8F0;margin:2px 0 14px 0;'></div>", unsafe_allow_html=True)
st.markdown("<a href='#top-anchor' class='back-to-top' title='\u56de\u5230\u9876\u90e8'>\u2191</a>", unsafe_allow_html=True)

col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>🤖 AI 来源数据监控大盘</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>直连 Google Sheets，多维度分析 AI 渠道引流与转化效果</div>", unsafe_allow_html=True)
with col_h_right:
    st.markdown(f"<div style='color:#9CA3AF;font-size:11px;text-align:right;margin-bottom:2px;line-height:1;'>最后同步：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    if st.button("🔄 从云端刷新数据", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# ⚙️ 核心解析引擎
# ==========================================
def extract_ym(text):
    text = str(text).strip()
    match = re.search(r'(202\d)[年\-/]\s*(\d{1,2})', text)
    if match: return f"{match.group(1)}-{int(match.group(2)):02d}"
    return None

@st.cache_data(ttl=600)
def load_and_parse_ai_data():
    url = "https://docs.google.com/spreadsheets/d/1cXuEZoa8o6fF3H9ycMIgvd3iKKY1tvmBrZHl7gnw2Gk/export?format=csv&gid=0"
    try:
        df_raw = pd.read_csv(url, header=None)
    except Exception as e:
        raise RuntimeError(f"CSV read failed: {e}")
    
    records = []
    for i in range(len(df_raw)):
        val0 = str(df_raw.iloc[i, 0]).strip().lower()
        if 'session source' in val0:
            site = str(df_raw.iloc[i, 0]).strip().split(' ')[0].upper()
            month_row = df_raw.iloc[i].tolist()
            if i + 1 >= len(df_raw): break
            metric_row = df_raw.iloc[i+1].tolist()
            
            col_map = {}
            current_month = None
            for col_idx in range(1, len(df_raw.columns)):
                m_val = str(month_row[col_idx]).strip()
                ym = extract_ym(m_val)
                if ym: current_month = ym
                
                metric_val = str(metric_row[col_idx]).strip().lower()
                metric = None
                if 'session' in metric_val: metric = 'sessions'
                elif 'page' in metric_val: metric = 'pages'
                elif 'revenue' in metric_val: metric = 'total revenue'
                
                if current_month and metric:
                    col_map[col_idx] = (current_month, metric)
            
            for j in range(i+2, min(i+50, len(df_raw))):
                src_val = str(df_raw.iloc[j, 0]).strip()
                if not src_val or src_val.lower() in ['nan', 'none']: break
                if 'session source' in src_val.lower(): break
                
                for col_idx, (m_str, metric) in col_map.items():
                    if col_idx < len(df_raw.columns):
                        raw_val = str(df_raw.iloc[j, col_idx]).replace('$', '').replace(',', '').strip()
                        try: val_num = float(raw_val)
                        except: val_num = 0.0
                        records.append({'Site': site, 'Source': src_val, 'Month': m_str, 'Metric': metric, 'Value': val_num})
                        
    df_flat = pd.DataFrame(records)
    return df_flat, df_raw

def plot_yoy(df, metric, title, is_currency=False):
    fig = go.Figure()
    cs = ['#10B981', '#3B82F6', '#F59E0B']
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
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$" if is_currency else "")
    )
    return fig

# ==========================================
# 📊 渲染图表大盘
# ==========================================
try:
    with st.spinner("🚀 正在通过 API 直连 Google Sheets 解析数据..."):
        df_flat, df_raw = load_and_parse_ai_data()

    if df_flat.empty:
        st.warning("⚠️ 警告：表格成功连通，但未从内容中提取出有效数据。")
        st.dataframe(df_raw.head(20), width="stretch")
    else:
        df_ai = df_flat.pivot_table(index=['Site', 'Source', 'Month'], columns='Metric', values='Value', aggfunc='sum').reset_index()
        if 'total revenue' in df_ai.columns: df_ai = df_ai.rename(columns={'total revenue': 'Revenue'})
        df_ai.rename(columns={'sessions': 'Sessions', 'pages': 'Pages'}, inplace=True)
        for req_col in ['Sessions', 'Pages', 'Revenue']:
            if req_col not in df_ai.columns: df_ai[req_col] = 0.0
            
        # 插入左侧导航
        st.markdown(get_nav_html('site', '📍', '分站导航'), unsafe_allow_html=True)
        
        # 💥 核心修改：切分数据，顶部三大模块全部剔除 EN 站点
        df_main = df_ai[df_ai['Site'] != 'EN'].copy()
        
        # =========================================================
        # 模块 1：全局全站汇总 (剔除 ai-assistant & 剔除 EN)
        # =========================================================
        st.markdown("### 🏆 1. 全局 AI 来源成果 (全站汇总, 不含 EN 站 & ai-assistant)")
        
        df_global = df_main[df_main['Source'] != 'ai-assistant']
        df_2026_global = df_global[df_global['Month'] >= '2026-01']
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">💰 2026 累计 AI 贡献销售额</div><div class="kpi-value blue">${df_2026_global["Revenue"].sum():,.2f}</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">🚀 2026 累计 AI 来源流量</div><div class="kpi-value green">{df_2026_global["Sessions"].sum():,.0f}</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="kpi-card"><div class="kpi-title">📄 2026 累计 AI 引用页面</div><div class="kpi-value purple">{df_2026_global["Pages"].sum():,.0f}</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
        
        # 1.1 全站年度对比 (YoY)
        df_global_yoy = df_global.groupby('Month')[['Revenue', 'Sessions', 'Pages']].sum().reset_index()
        df_global_yoy['Year'] = df_global_yoy['Month'].str[:4]
        df_global_yoy['Mnum'] = df_global_yoy['Month'].str[5:].astype(int)
        
        with st.container(border=True):
            st.markdown("**📉 2025 vs 2026 全站年度对比 (YoY)**")
            yoy1, yoy2, yoy3 = st.columns(3)
            with yoy1: st.plotly_chart(plot_yoy(df_global_yoy, 'Revenue', "销售额同比对比", True), use_container_width=True)
            with yoy2: st.plotly_chart(plot_yoy(df_global_yoy, 'Sessions', "流量同比对比", False), use_container_width=True)
            with yoy3: st.plotly_chart(plot_yoy(df_global_yoy, 'Pages', "引用页面同比对比", False), use_container_width=True)

        st.markdown("<hr style='margin:32px 0;'/>", unsafe_allow_html=True)

        # =========================================================
        # 模块 2：AI-Assistant 单独大盘 (剔除 EN)
        # =========================================================
        st.markdown("### 🤖 2. ai-assistant 单独监控大盘 (不含 EN 站)")
        df_ast = df_main[df_main['Source'] == 'ai-assistant']
        
        if not df_ast.empty:
            with st.container(border=True):
                st.markdown("**📈 ai-assistant 历年月度发展总趋势图**")
                df_ast_trend = df_ast.groupby('Month')[['Revenue', 'Sessions', 'Pages']].sum().reset_index().sort_values('Month')
                fig_ast_trend = go.Figure()
                fig_ast_trend.add_trace(go.Scatter(x=df_ast_trend['Month'], y=df_ast_trend['Sessions'], name="流量", line=dict(color="#10B981", width=3), mode='lines+markers'))
                fig_ast_trend.add_trace(go.Scatter(x=df_ast_trend['Month'], y=df_ast_trend['Pages'], name="页面数", line=dict(color="#8B5CF6", width=3), mode='lines+markers'))
                fig_ast_trend.update_layout(height=350, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                st.plotly_chart(fig_ast_trend, use_container_width=True)

            df_ast_yoy = df_ast_trend.copy()
            df_ast_yoy['Year'] = df_ast_yoy['Month'].str[:4]
            df_ast_yoy['Mnum'] = df_ast_yoy['Month'].str[5:].astype(int)
            
            with st.container(border=True):
                st.markdown("**📉 ai-assistant 2025 vs 2026 年度对比 (YoY)**")
                ayoy1, ayoy2, ayoy3 = st.columns(3)
                with ayoy1: st.plotly_chart(plot_yoy(df_ast_yoy, 'Revenue', "销售额同比对比", True), use_container_width=True)
                with ayoy2: st.plotly_chart(plot_yoy(df_ast_yoy, 'Sessions', "流量同比对比", False), use_container_width=True)
                with ayoy3: st.plotly_chart(plot_yoy(df_ast_yoy, 'Pages', "引用页面同比对比", False), use_container_width=True)
        else:
            st.info("数据表中尚未检测到小语种站点的 'ai-assistant' 数据。")

        st.markdown("<hr style='margin:32px 0;'/>", unsafe_allow_html=True)

        # =========================================================
        # 模块 3：各大 AI 引擎流量贡献占比 (剔除 EN)
        # =========================================================
        st.markdown("### 🧩 3. 各大 AI 引擎引流贡献占比 (全站合并, 不含 EN 站)")
        with st.container(border=True):
            df_source_trend = df_global.groupby(['Month', 'Source'])['Sessions'].sum().reset_index()
            fig_src = px.bar(
                df_source_trend, x='Month', y='Sessions', color='Source', 
                template="plotly_white", text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_src.update_layout(height=400, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_src, use_container_width=True)

        st.markdown("<hr style='margin:32px 0;'/>", unsafe_allow_html=True)

        # =========================================================
        # 模块 4：各小语种分站点独立看板
        # =========================================================
        st.markdown("### 🏬 4. 小语种分站点详细数据 (不含 ai-assistant)")
        
        sites_list = ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']
        
        for site in sites_list:
            df_site = df_global[df_global['Site'] == site].copy()
            if df_site.empty: continue
            
            st.markdown(f'<div id="site-{site}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"📌 {site} 站点 — AI 来源详细大盘", expanded=True):
                
                df_site_2026 = df_site[df_site['Month'] >= '2026-01']
                s_rev = df_site_2026['Revenue'].sum()
                s_ses = df_site_2026['Sessions'].sum()
                s_pag = df_site_2026['Pages'].sum()
                
                sc1, sc2, sc3 = st.columns(3)
                with sc1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">2026 销售额</div><div class="kpi-value blue">${s_rev:,.2f}</div></div>', unsafe_allow_html=True)
                with sc2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">2026 流量</div><div class="kpi-value green">{s_ses:,.0f}</div></div>', unsafe_allow_html=True)
                with sc3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">2026 页面数</div><div class="kpi-value purple">{s_pag:,.0f}</div></div>', unsafe_allow_html=True)
                
                st.write("")
                
                df_site_trend = df_site.groupby('Month')[['Revenue', 'Sessions', 'Pages']].sum().reset_index().sort_values('Month')
                
                chart1, chart2, chart3 = st.columns(3)
                with chart1:
                    fig_s_rev = px.bar(df_site_trend, x='Month', y='Revenue', template="plotly_white", title="💰 销售额月度走势")
                    fig_s_rev.update_traces(marker_color='#2563EB')
                    fig_s_rev.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(tickprefix="$"))
                    st.plotly_chart(fig_s_rev, use_container_width=True)
                with chart2:
                    fig_s_ses = px.line(df_site_trend, x='Month', y='Sessions', markers=True, template="plotly_white", title="🚀 流量月度走势")
                    fig_s_ses.update_traces(line_color='#10B981', line_width=3)
                    fig_s_ses.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_s_ses, use_container_width=True)
                with chart3:
                    fig_s_pag = px.line(df_site_trend, x='Month', y='Pages', markers=True, template="plotly_white", title="📄 引用页面月度走势")
                    fig_s_pag.update_traces(line_color='#8B5CF6', line_width=3)
                    fig_s_pag.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_s_pag, use_container_width=True)

        st.markdown("<hr style='margin:32px 0;'/>", unsafe_allow_html=True)
        
        # =========================================================
        # 模块 5：EN 站点专属区域 (沉底展示)
        # =========================================================
        st.markdown("### 🇬🇧 5. EN 站点专属监控大盘 (不含 ai-assistant)")
        
        # 提取专属 EN 数据并排除 ai-assistant
        df_en = df_ai[(df_ai['Site'] == 'EN') & (df_ai['Source'] != 'ai-assistant')].copy()
        
        st.markdown(f'<div id="site-EN" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
        if not df_en.empty:
            with st.container(border=True):
                # <1> EN 站 2026 YTD KPI
                df_en_2026 = df_en[df_en['Month'] >= '2026-01']
                en_rev = df_en_2026['Revenue'].sum()
                en_ses = df_en_2026['Sessions'].sum()
                en_pag = df_en_2026['Pages'].sum()
                
                ec1, ec2, ec3 = st.columns(3)
                with ec1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">2026 销售额 (EN)</div><div class="kpi-value blue">${en_rev:,.2f}</div></div>', unsafe_allow_html=True)
                with ec2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">2026 流量 (EN)</div><div class="kpi-value green">{en_ses:,.0f}</div></div>', unsafe_allow_html=True)
                with ec3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">2026 页面数 (EN)</div><div class="kpi-value purple">{en_pag:,.0f}</div></div>', unsafe_allow_html=True)
                
                st.write("")
                
                # 计算月度趋势
                df_en_trend = df_en.groupby('Month')[['Revenue', 'Sessions', 'Pages']].sum().reset_index().sort_values('Month')
                
                en_chart1, en_chart2, en_chart3 = st.columns(3)
                with en_chart1:
                    fig_en_rev = px.bar(df_en_trend, x='Month', y='Revenue', template="plotly_white", title="💰 EN 销售额月度走势")
                    fig_en_rev.update_traces(marker_color='#111827')
                    fig_en_rev.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10), yaxis=dict(tickprefix="$"))
                    st.plotly_chart(fig_en_rev, use_container_width=True)
                with en_chart2:
                    fig_en_ses = px.line(df_en_trend, x='Month', y='Sessions', markers=True, template="plotly_white", title="🚀 EN 流量月度走势")
                    fig_en_ses.update_traces(line_color='#10B981', line_width=3)
                    fig_en_ses.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_en_ses, use_container_width=True)
                with en_chart3:
                    fig_en_pag = px.line(df_en_trend, x='Month', y='Pages', markers=True, template="plotly_white", title="📄 EN 引用页面月度走势")
                    fig_en_pag.update_traces(line_color='#8B5CF6', line_width=3)
                    fig_en_pag.update_layout(height=280, margin=dict(l=10, r=10, t=40, b=10))
                    st.plotly_chart(fig_en_pag, use_container_width=True)
        else:
            st.info("📊 数据表中尚未检测到 'EN' 站点的 AI 来源数据。")

except Exception as e:
    st.error(f"❌ 读取异常：{e}")
