import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import re

st.set_page_config(page_title="AI 来源数据监控", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 UI 样式与导航
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
# ⚙️ 核心解析引擎：精准多行游标 + 动态向前填充
# ==========================================
def extract_ym(text):
    """提取日期，兼容各种输入格式"""
    text = str(text).strip()
    match = re.search(r'(202\d)[年\-/]\s*(\d{1,2})', text)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}"
    return None

@st.cache_data(ttl=600)
def load_and_parse_ai_data():
    url = "https://docs.google.com/spreadsheets/d/1cXuEZoa8o6fF3H9ycMIgvd3iKKY1tvmBrZHl7gnw2Gk/export?format=csv&gid=0"
    try:
        df_raw = pd.read_csv(url, header=None)
    except Exception as e:
        raise RuntimeError(f"CSV read failed: {e}")
    
    records = []
    # 遍历行寻找站点块
    for i in range(len(df_raw)):
        val0 = str(df_raw.iloc[i, 0]).strip().lower()
        
        # 匹配 "DE Session source / medium" 这一行
        if 'session source' in val0:
            site = str(df_raw.iloc[i, 0]).strip().split(' ')[0].upper()
            
            # 依据截图，日期在第 i 行，指标在第 i+1 行，数据在 i+2 及其之后
            month_row = df_raw.iloc[i].tolist()
            
            # 防止索引越界
            if i + 1 >= len(df_raw): break
            metric_row = df_raw.iloc[i+1].tolist()
            
            col_map = {}
            current_month = None
            
            # 建立列映射表（自动向右填补由于合并单元格带来的空日期）
            for col_idx in range(1, len(df_raw.columns)):
                m_val = str(month_row[col_idx]).strip()
                ym = extract_ym(m_val)
                if ym:
                    current_month = ym
                
                metric_val = str(metric_row[col_idx]).strip().lower()
                metric = None
                if 'session' in metric_val: metric = 'sessions'
                elif 'page' in metric_val: metric = 'pages'
                elif 'revenue' in metric_val: metric = 'total revenue'
                
                if current_month and metric:
                    col_map[col_idx] = (current_month, metric)
            
            # 从第 i+2 行开始往下读取 AI 渠道的具体数据
            for j in range(i+2, min(i+50, len(df_raw))):
                src_val = str(df_raw.iloc[j, 0]).strip()
                
                # 撞到空行、"None" 或者进入下一个站点，停止当前站点的循环
                if not src_val or src_val.lower() == 'nan' or src_val.lower() == 'none': break
                if 'session source' in src_val.lower(): break
                
                for col_idx, (m_str, metric) in col_map.items():
                    if col_idx < len(df_raw.columns):
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
    return df_flat, df_raw

# ==========================================
# 📊 渲染图表大盘
# ==========================================
try:
    with st.spinner("🚀 正在通过 API 直连 Google Sheets 解析数据..."):
        df_flat, df_raw = load_and_parse_ai_data()

    if df_flat.empty:
        st.warning("⚠️ 警告：表格成功连通，但未从内容中提取出有效数据。")
        st.markdown("👇 **调试分析诊断器：** 这是系统抓取到的原始数据。")
        st.dataframe(df_raw.head(20), width="stretch")
    else:
        # 将长表转为宽表以便制图
        df_ai = df_flat.pivot_table(index=['Site', 'Source', 'Month'], columns='Metric', values='Value', aggfunc='sum').reset_index()
        
        # 统一规范列名
        rename_dict = {c: c.capitalize() for c in df_ai.columns}
        if 'total revenue' in df_ai.columns: df_ai = df_ai.rename(columns={'total revenue': 'Revenue'})
        df_ai.rename(columns={'sessions': 'Sessions', 'pages': 'Pages'}, inplace=True)
        
        # 补充防报错机制
        for req_col in ['Sessions', 'Pages', 'Revenue']:
            if req_col not in df_ai.columns: df_ai[req_col] = 0.0
        
        # =========================================================
        # 模块 1：2026年至今的全局核心数据 (剔除 ai-assistant)
        # =========================================================
        st.markdown("### 🏆 2026年至今 AI 来源核心成果 (全站汇总)")
        st.markdown("<p style='font-size:12px; margin-top:-10px;'>*注：计算总和时已自动剔除 `ai-assistant` 数据，避免与细分渠道数据发生重复计算。</p>", unsafe_allow_html=True)
        
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
        
        # 去除 ai-assistant 计算趋势图
        df_clean = df_ai[df_ai['Source'] != 'ai-assistant'].copy()
        
        df_trend = df_clean.groupby(['Site', 'Month'])[['Revenue', 'Sessions', 'Pages']].sum().reset_index()
        df_trend = df_trend.sort_values('Month')

        sites_available = sorted(df_trend['Site'].unique().tolist())
        sites_display = ['全部站点 (All)'] + sites_available
        
        selected_site = st.radio("请选择查看的站点维度：", options=sites_display, horizontal=True)
        
        if selected_site == '全部站点 (All)':
            plot_df = df_trend.copy()
            title_prefix = "全球各站点"
            color_col = 'Site'
        else:
            plot_df = df_trend[df_trend['Site'] == selected_site].copy()
            title_prefix = f"{selected_site} 站点"
            color_col = None

        if not plot_df.empty:
            col_chart1, col_chart2 = st.columns(2)
            
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
            
            with col_chart2:
                with st.container(border=True):
                    st.markdown(f"**💰 {title_prefix} 销售额趋势 (Revenue)**")
                    if color_col:
                        fig_rev = px.line(plot_df, x='Month', y='Revenue', color=color_col, markers=True, template="plotly_white")
                    else:
                        fig_rev = px.bar(plot_df, x='Month', y='Revenue', text_auto='.2s', template="plotly_white")
                        fig_rev.update_traces(marker_color='#2563EB')
                        
                    fig_rev.update_layout(height=350, hovermode='x unified', margin=dict(l=10, r=10, t=10, b=10),
                                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(tickprefix="$", showgrid=True, gridcolor='#f1f5f9'))
                    st.plotly_chart(fig_rev, width="stretch")
            
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
    st.error(f"❌ 读取异常：{e}")
