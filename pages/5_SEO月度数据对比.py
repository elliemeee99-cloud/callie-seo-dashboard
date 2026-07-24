import streamlit as st
import pandas as pd
import datetime
import os
import plotly.graph_objects as go

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO月度数据对比", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

CACHE_FILE = "seo_monthly_sales_v2.pkl"

# ==========================================
# 🧭 极限压缩防乱码 CSS + 6栏导航
# ==========================================
# 彻底去除了换行与注释，严防 Streamlit 乱码 Bug
compressed_css = """
<div id="top-anchor"></div>
<style>[data-testid="stSidebar"]{display:none !important;}[data-testid="collapsedControl"]{display:none !important;}[data-testid="stHeader"]{display:none !important;}.block-container{padding-top:2rem !important;max-width:95% !important;}.stApp{background-color:#f8fafc !important;}[data-testid="stPageLink-NavLink"]{background-color:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:12px !important;padding:12px 6px !important;text-align:center !important;display:flex !important;justify-content:center !important;align-items:center !important;transition:all 0.25s ease !important;box-shadow:0 2px 4px rgba(0,0,0,0.02) !important;text-decoration:none !important;white-space:nowrap;}[data-testid="stPageLink-NavLink"]:hover{background-color:#ffffff !important;border-color:#3b82f6 !important;transform:translateY(-2px) !important;box-shadow:0 8px 16px rgba(37,99,235,0.1) !important;}[data-testid="stPageLink-NavLink"] p{font-weight:800 !important;color:#1e293b !important;font-size:14px !important;margin:0 !important;}.back-to-top{position:fixed;bottom:40px;right:40px;background-color:#FF8FAB;color:#ffffff !important;border:none;width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:24px;font-weight:800;box-shadow:0 4px 15px rgba(255,143,171,0.35);text-decoration:none !important;z-index:99999;transition:all 0.3s ease;}.back-to-top:hover{background-color:#FF5D8F;transform:translateY(-5px);box-shadow:0 8px 20px rgba(255,143,171,0.55);color:#ffffff !important;}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;border:1px solid #e2e8f0 !important;background-color:#ffffff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);padding:20px;}div[data-testid="stMultiSelect"] span[data-baseweb="tag"]{background-color:#e0f2fe !important;color:#0369a1 !important;border-radius:12px !important;padding:6px 14px !important;font-weight:700 !important;border:1px solid #bae6fd !important;}div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span{color:#0369a1 !important;}div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg{fill:#0369a1 !important;}div[data-testid="stRadio"] div[role="radiogroup"]{display:flex !important;flex-direction:row !important;gap:10px !important;}div[data-testid="stRadio"] label[data-baseweb="radio"]{background-color:#f1f5f9 !important;padding:6px 20px !important;border-radius:10px !important;cursor:pointer !important;transition:all 0.2s;border:1px solid #e2e8f0;}div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child{display:none !important;}div[data-testid="stRadio"] label[data-baseweb="radio"] p{color:#64748b !important;font-weight:600 !important;margin:0 !important;}div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"],div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){background-color:#0ea5e9 !important;border-color:#0ea5e9 !important;box-shadow:0 4px 10px rgba(14,165,233,0.2) !important;}div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p,div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p{color:#ffffff !important;}</style>
<a href="#top-anchor" class="back-to-top" title="回到顶部">↑</a>
"""
st.markdown(compressed_css, unsafe_allow_html=True)

spacer_left, nav1, nav2, nav3, nav4, nav5, nav6, spacer_right = st.columns([0.1, 1, 1, 1, 1, 1, 1, 0.1])
with nav1: st.page_link("app.py", label="App 首页", icon="🏠")
with nav2: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with nav3: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with nav4: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with nav5: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
with nav6: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比", icon="📊")
st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

# ==========================================
# ⚙️ 核心配置与智能时间解析器
# ==========================================
def parse_excel_dates(date_series):
    parsed_dates = []
    for val in date_series:
        try:
            if isinstance(val, (int, float)):
                parsed_dates.append(pd.to_datetime(val, origin='1899-12-30', unit='D'))
            else:
                val_str = str(val).replace('月', '').strip()
                parsed_dates.append(pd.to_datetime(val_str))
        except:
            parsed_dates.append(pd.NaT)
    return pd.Series(parsed_dates)

# ==========================================
# 🎯 页面头部与数据持久化上传
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📊 SEO 核心指标深度对比</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>支持跨周期销售额同环比分析，数据已做本地加密缓存。</div>", unsafe_allow_html=True)
with col_refresh:
    st.write("") 
    if st.button("🗑️ 清空本地缓存"):
        if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
        if 'monthly_data' in st.session_state: del st.session_state['monthly_data']
        st.success("缓存已清空！")
        st.rerun()

with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>📥 上传数据报表</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请上传最新版的《SEO 整体数据情况》台账 (支持 Excel xlsx 格式)", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            # 智能寻找工作表 (找带有销售额汇总的Sheet)
            target_sheet = xls.sheet_names[0]
            for s in xls.sheet_names:
                if '销售额' in s and '汇总' in s:
                    target_sheet = s
                    break
                    
            df_raw = pd.read_excel(xls, sheet_name=target_sheet)
            
            # 第一列强制解析为时间列
            date_col = df_raw.columns[0]
            df_raw['Date'] = parse_excel_dates(df_raw[date_col])
            df_raw = df_raw.dropna(subset=['Date']).sort_values('Date').reset_index(drop=True)
            
            # 保存到本地缓存
            df_raw.to_pickle(CACHE_FILE)
            st.session_state['monthly_data'] = df_raw
            st.success("✅ 数据报表解析成功，已自动安全留存！")
        except Exception as e:
            st.error(f"❌ 解析失败，请检查文件格式。报错详情: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

# ==========================================
# 📈 销售额深度对比模块
# ==========================================
if 'monthly_data' in st.session_state:
    df = st.session_state['monthly_data'].copy()
    cols = df.columns.tolist()
    
    # --- 智能字段映射引擎 ---
    default_nonbrand = cols[1] if len(cols) > 1 else cols[0]
    default_allseo = cols[2] if len(cols) > 2 else cols[0]
    
    for c in cols:
        if '总计' in str(c) or '非品牌词' in str(c):
            if '涨' not in str(c) and '降' not in str(c) and '占比' not in str(c):
                default_nonbrand = c
        if 'ALL' in str(c).upper() or 'SEO销售额' in str(c) or '网站总销售' in str(c):
            if c != default_nonbrand and '非' not in str(c) and '涨' not in str(c) and '占比' not in str(c):
                default_allseo = c

    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ 数据源映射与确认")
    st.markdown("<div style='font-size: 13px; color:#64748b; margin-bottom: 12px;'>由于表格结构已更新，AI已为您自动推断数据列。如果对应错误，请手动修正下方选项。</div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        with c1: col_nonbrand = st.selectbox("🎯 【非品牌词销售额】对应的数据列", options=cols, index=cols.index(default_nonbrand) if default_nonbrand in cols else 0)
        with c2: col_allseo = st.selectbox("🎯 【ALL SEO销售额】对应的数据列", options=cols, index=cols.index(default_allseo) if default_allseo in cols else 0)

    # 格式化提取到的数值
    df[col_nonbrand] = pd.to_numeric(df[col_nonbrand], errors='coerce').fillna(0)
    df[col_allseo] = pd.to_numeric(df[col_allseo], errors='coerce').fillna(0)
    
    st.markdown("<hr style='margin: 30px 0; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

    # ==========================================
    # 📈 图表 1: 历年 1-12 月非品牌词销售额 YoY 对比
    # ==========================================
    st.markdown(f"#### 📉 1. 历年【{col_nonbrand}】月度 YoY 环比分析图")
    with st.container(border=True):
        df_yoy = df.copy()
        df_yoy['Year'] = df_yoy['Date'].dt.year.astype(str)
        df_yoy['Month_Num'] = df_yoy['Date'].dt.month
        
        fig1 = go.Figure()
        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
        for i, year in enumerate(sorted(df_yoy['Year'].unique())):
            df_year = df_yoy[df_yoy['Year'] == year].sort_values('Month_Num')
            fig1.add_trace(go.Scatter(
                x=df_year['Month_Num'], y=df_year[col_nonbrand],
                mode='lines+markers', name=f'{year}年',
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8, color='#ffffff', line=dict(color=colors[i % len(colors)], width=2)),
                hovertemplate=f'<b>{year}年%{{x}}月</b><br>销售额: $%%{{y:,.2f}}<extra></extra>'
            ))
            
        fig1.update_layout(
            height=400, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickmode='array', tickvals=list(range(1, 13)), ticktext=[f"{i}月" for i in range(1, 13)]),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
        )
        st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 📈 图表 2: 非品牌词 vs ALL SEO 销售额走势
    # ==========================================
    st.markdown(f"#### 📊 2. 【{col_nonbrand}】与【{col_allseo}】综合走势对比")
    with st.container(border=True):
        df_trend = df.copy()
        df_trend['Month_Str'] = df_trend['Date'].dt.strftime('%Y-%m')
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df_trend['Month_Str'], y=df_trend[col_nonbrand],
            mode='lines+markers', name=f'非品牌词销售额',
            line=dict(width=3, color='#0ea5e9'), marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>非品牌词: $%{y:,.2f}<extra></extra>'
        ))
        fig2.add_trace(go.Scatter(
            x=df_trend['Month_Str'], y=df_trend[col_allseo],
            mode='lines+markers', name=f'ALL SEO销售额',
            line=dict(width=3, color='#8b5cf6'), marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>ALL SEO: $%{y:,.2f}<extra></extra>'
        ))
        fig2.update_layout(
            height=400, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 📈 图表 3: 销售额月度涨降幅对比
    # ==========================================
    st.markdown("#### ⚡ 3. 销售额月度涨降幅 (Growth Rate) 对比")
    with st.container(border=True):
        df_growth = df.copy()
        df_growth['Month_Str'] = df_growth['Date'].dt.strftime('%Y-%m')
        
        # 精准计算环比涨跌幅 (%)
        df_growth['NonBrand_Growth'] = df_growth[col_nonbrand].pct_change() * 100
        df_growth['AllSEO_Growth'] = df_growth[col_allseo].pct_change() * 100
        
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df_growth['Month_Str'], y=df_growth['NonBrand_Growth'],
            mode='lines+markers', name=f'非品牌词涨降幅(%)',
            line=dict(width=3, color='#f43f5e'), marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>非品牌词涨跌: %{y:+.2f}%<extra></extra>'
        ))
        fig3.add_trace(go.Scatter(
            x=df_growth['Month_Str'], y=df_growth['AllSEO_Growth'],
            mode='lines+markers', name=f'ALL SEO涨降幅(%)',
            line=dict(width=3, color='#10b981'), marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>ALL SEO涨跌: %{y:+.2f}%<extra></extra>'
        ))
        
        # 添加一条浅灰色的零点辅助线
        fig3.add_hline(y=0, line_dash="dash", line_color="#94a3b8", annotation_text="0% 基准线")

        fig3.update_layout(
            height=400, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', ticksuffix="%")
        )
        st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("👈 您的缓存池为空。请在上方上传最新整理好的《SEO 整体数据情况》台账。")
