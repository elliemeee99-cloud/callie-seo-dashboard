import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="AI 来源数据监控", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 UI 样式与导航 (企业 SaaS 级风格)
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:140px!important}
h1, h2, h3, h4, h5, h6 {color:#111827!important}
p {color:#6B7280!important;font-size:14px!important}
hr{border-color:#E5E7EB!important;margin:8px 0!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px!important;border:1px solid #E5E7EB!important;background-color:#FFFFFF;box-shadow:0 1px 3px rgba(0,0,0,.06)!important;padding:16px!important;margin-bottom:12px!important}
.kpi-card {background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align: center;}
.kpi-title {font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 8px;}
.kpi-value {font-size: 32px; font-weight: 700; color: #0F172A; margin: 0;}
.kpi-value.blue {color: #2563EB;}
.kpi-value.green {color: #10B981;}
.kpi-value.purple {color: #8B5CF6;}

/* 顶部导航 Tabs */
[data-testid="stPageLink-NavLink"]{background:transparent!important;border:none!important;border-radius:0!important;padding:8px 14px!important;border-bottom:2px solid transparent!important;margin-bottom:-1px}
[data-testid="stPageLink-NavLink"]:hover{background:#F1F5F9!important}
[data-testid="stPageLink-NavLink"] p{font-weight:600!important;color:#64748B!important;font-size:16px!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"]{border-bottom:2px solid #2563EB!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"] p{color:#2563EB!important;font-weight:600!important}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
</style>""", unsafe_allow_html=True)

# --- 导航栏 ---
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

col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>🤖 AI 来源数据监控大盘</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>直连 Google Sheets，分析 ChatGPT、Gemini 等 AI 引流与转化效果</div>", unsafe_allow_html=True)
with col_h_right:
    st.markdown(f"<div style='color:#9CA3AF;font-size:11px;text-align:right;margin-bottom:2px;line-height:1;'>最后同步：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    if st.button("🔄 从云端刷新数据", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# ⚙️ 核心解析引擎：游标穿透提取法
# ==========================================
@st.cache_data(ttl=600)
def load_and_parse_ai_data():
    # 替换为 CSV 下载直链，无视权限弹窗
    url = "https://docs.google.com/spreadsheets/d/1cXuEZoa8o6fF3H9ycMIgvd3iKKY1tvmBrZHl7gnw2Gk/export?format=csv&gid=0"
    df_raw = pd.read_csv(url, header=None)
    
    records = []
    # 遍历行寻找站点块
    for i in range(len(df_raw)):
        val0 = str(df_raw.iloc[i, 0]).strip()
        if 'Session source / medium' in val0:
            # 提取站点名称，例如 "DE Session source / medium" -> "DE"
            site = val0.split(' ')[0]
            
            # 定位时间行 (上一行) 和 指标行 (当前行)
            month_row = df_raw.iloc[i-1].tolist() if i > 0 else []
            metric_row = df_raw.iloc[i].tolist()
            
            # 构建列索引映射：找出哪些列属于哪个月份、哪个指标
            col_map = {}
            current_month = None
            for col_idx in range(1, len(df_raw.columns)):
                m_val = str(month_row[col_idx]).strip()
                if '年' in m_val:
                    # 将 "2025年1月" 转换为标准 "2025-01"
                    m_str = m_val.replace('年', '-').replace('月', '')
                    parts = m_str.split('-')
                    if len(parts) == 2:
                        current_month = f"{parts[0]}-{int(parts[1]):02d}"
                
                metric_val = str(metric_row[col_idx]).strip().lower()
                if current_month and metric_val in ['sessions', 'pages', 'total revenue']:
                    col_map[col_idx] = (current_month, metric_val)
            
            # 往下读取 AI 渠道的具体数据，直到遇到空行
            for j in range(i+1, min(i+12, len(df_raw))):
                src_val = str(df_raw.iloc[j, 0]).strip()
                if not src_val or src_val == 'nan': break
                if 'Session source' in src_val: break
                
                # 读取该渠道下各个列的数据
                for col_idx, (m_str, metric) in col_map.items():
                    raw_val = str(df_raw.iloc[j, col_idx]).replace('$', '').replace(',', '').strip()
                    try:
                        val_num = float(raw_val)
                    except:
                        val_num = 0.0
                        
                    records.append({
                        'Site': site,
                        'Source': src_val,
                        'Month': m_str,
                        'Metric': metric,
                        'Value': val_num
                    })
                    
    df_flat = pd.DataFrame(records)
    if df_flat.empty: return pd.DataFrame()
    
    # 将长表透视为宽表 (Month, Source, Metric -> Columns)
    df_pivot = df_flat.pivot_table(index=['Site', 'Source', 'Month'], columns='Metric', values='Value', aggfunc='sum').reset_index()
    
    # 统一列名
    rename_dict = {}
    for c in df_pivot.columns:
        if c.lower() == 'sessions': rename_dict[c] = 'Sessions'
        elif c.lower() == 'pages': rename_dict[c] = 'Pages'
        elif c.lower() == 'total revenue': rename_dict[c] = 'Revenue'
    df_pivot = df_pivot.rename(columns=rename_dict)
    
    # 防止因源表无数据导致的列缺失
    for col in ['Sessions', 'Pages', 'Revenue']:
        if col not in df_pivot.columns: df_pivot[col] = 0.0
            
    return df_pivot

# ==========================================
# 📊 渲染图表大盘
# ==========================================
try:
    with st.spinner("🚀 正在通过 API 直连 Google Sheets 解析数据..."):
        df_ai = load_and_parse_ai_data()

    if df_ai.empty:
        st.warning("⚠️ 表格连接成功，但未解析到符合要求的数据块。请检查表格的第一列是否包含 'DE Session source / medium' 等标识。")
    else:
        # =========================================================
        # 模块 1：2026年至今的全局核心数据 (剔除 ai-assistant)
        # =========================================================
        st.markdown("### 🏆 2026年至今 AI 来源核心成果 (全站汇总)")
        st.markdown("<p style='font-size:12px; margin-top:-10px;'>*注：计算总和时已自动剔除 `ai-assistant` 数据，避免渠道数据重复计算。</p>", unsafe_allow_html=True)
        
        # 过滤 2026 年以后的数据，并去除 ai-assistant
        df_2026 = df_ai[(df_ai['Month'] >= '2026-01') & (df_ai['Source'] != 'ai-assistant')]
        
        if not df_2026.empty:
            total_rev = df_2026['Revenue'].sum()
            total_ses = df_2026['Sessions'].sum()
            total_pag = df_2026['Pages'].sum()
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">💰 2026 累计 AI 贡献销售额</div>
                    <div class="kpi-value blue">${total_rev:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">🚀 2026 累计 AI 来源流量 (Sessions)</div>
                    <div class="kpi-value green">{total_ses:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">📄 2026 累计 AI 页面浏览 (Pages)</div>
                    <div class="kpi-value purple">{total_pag:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("尚未发现 2026 年的数据记录。")

        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

        # =========================================================
        # 模块 2：站点细分维度 & 月度趋势图
        # =========================================================
        st.markdown("### 🏬 站点细分月度趋势图")
        
        # 提取全局去除 ai-assistant 的数据用于绘图
        df_clean = df_ai[df_ai['Source'] != 'ai-assistant'].copy()
        
        # 按月按站点汇总
        df_trend = df_clean.groupby(['Site', 'Month'])[['Revenue', 'Sessions', 'Pages']].sum().reset_index()
        df_trend = df_trend.sort_values('Month')

        # 站点选择器
        sites_available = sorted(df_trend['Site'].unique().tolist())
        sites_display = ['全部站点 (All)'] + sites_available
        
        selected_site = st.radio("请选择查看的站点维度：", options=sites_display, horizontal=True)
        
        if selected_site == '全部站点 (All)':
            # 如果选了全部站点，就在图里画出所有站点的线条对比
            plot_df = df_trend.copy()
            title_prefix = "全球各站点"
            color_col = 'Site'
        else:
            # 单独筛选某个站点
            plot_df = df_trend[df_trend['Site'] == selected_site].copy()
            title_prefix = f"{selected_site} 站点"
            color_col = None

        if not plot_df.empty:
            col_chart1, col_chart2 = st.columns(2)
            
            # 图1：流量与页面趋势
            with col_chart1:
                with st.container(border=True):
                    st.markdown(f"**📈 {title_prefix} 流量趋势 (Sessions)**")
                    fig_ses = px.line(
                        plot_df, x='Month', y='Sessions', color=color_col, 
                        markers=True, template="plotly_white",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_ses.update_layout(height=350, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10),
                                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                    st.plotly_chart(fig_ses, width="stretch")
            
            # 图2：销售额趋势
            with col_chart2:
                with st.container(border=True):
                    st.markdown(f"**💰 {title_prefix} 销售额趋势 (Revenue)**")
                    if color_col:
                        fig_rev = px.line(plot_df, x='Month', y='Revenue', color=color_col, markers=True, template="plotly_white")
                    else:
                        # 单站点用柱状图展示销售额更直观
                        fig_rev = px.bar(plot_df, x='Month', y='Revenue', text_auto='.2s', template="plotly_white")
                        fig_rev.update_traces(marker_color='#2563EB')
                        
                    fig_rev.update_layout(height=350, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10),
                                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(tickprefix="$", showgrid=True, gridcolor='#f1f5f9'))
                    st.plotly_chart(fig_rev, width="stretch")
            
            # 附加图：查看具体的 AI 工具来源拆解 (按月堆叠)
            st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"**🤖 {title_prefix} 各大 AI 引擎流量贡献占比 (Sessions)**")
                if selected_site == '全部站点 (All)':
                    df_source_trend = df_clean.groupby(['Month', 'Source'])['Sessions'].sum().reset_index()
                else:
                    df_source_trend = df_clean[df_clean['Site'] == selected_site].groupby(['Month', 'Source'])['Sessions'].sum().reset_index()
                
                fig_src = px.bar(
                    df_source_trend, x='Month', y='Sessions', color='Source', 
                    template="plotly_white", text_auto='.2s',
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                fig_src.update_layout(height=400, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10),
                                    xaxis=dict(showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                st.plotly_chart(fig_src, width="stretch")
        else:
            st.info(f"暂无 {selected_site} 的数据。")
            
except Exception as e:
    st.error(f"❌ 读取 Google Sheets 失败，请检查以下设置：")
    st.markdown("1. 确保该 Google Sheet 的分享权限已设置为**「知道链接的人均可查看 (Anyone with the link can view)」**。")
    st.markdown("2. 确认你是否在公司内网，是否存在网络拦截。")
    st.code(str(e))
