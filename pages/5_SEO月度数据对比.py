import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO月度数据对比", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🧭 极限压缩防乱码 CSS + 自定义 UI 组件
# ==========================================
compressed_css = """
<div id="top-anchor"></div>
<style>
[data-testid="stSidebar"]{display:none !important;}
[data-testid="collapsedControl"]{display:none !important;}
[data-testid="stHeader"]{display:none !important;}
.block-container{padding-top:2rem !important;max-width:95% !important;}
.stApp{background-color:#f8fafc !important;}

/* 导航栏样式 */
[data-testid="stPageLink-NavLink"]{background-color:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:12px !important;padding:12px 6px !important;text-align:center !important;display:flex !important;justify-content:center !important;align-items:center !important;transition:all 0.25s ease !important;box-shadow:0 2px 4px rgba(0,0,0,0.02) !important;text-decoration:none !important;white-space:nowrap;}
[data-testid="stPageLink-NavLink"]:hover{background-color:#ffffff !important;border-color:#3b82f6 !important;transform:translateY(-2px) !important;box-shadow:0 8px 16px rgba(37,99,235,0.1) !important;}
[data-testid="stPageLink-NavLink"] p{font-weight:800 !important;color:#1e293b !important;font-size:14px !important;margin:0 !important;}

/* 🍓 回到顶部按钮 */
.back-to-top{position:fixed;bottom:40px;right:40px;background-color:#FF8FAB;color:#ffffff !important;border:none;width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:24px;font-weight:800;box-shadow:0 4px 15px rgba(255,143,171,0.35);text-decoration:none !important;z-index:99999;transition:all 0.3s ease;}
.back-to-top:hover{background-color:#FF5D8F;transform:translateY(-5px);box-shadow:0 8px 20px rgba(255,143,171,0.55);color:#ffffff !important;}

/* 容器圆角 */
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;border:1px solid #e2e8f0 !important;background-color:#ffffff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);padding:20px;}

/* 🔥 多选框站点筛选 -> 统一淡蓝色圆角卡片 */
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] { background-color: #e0f2fe !important; color: #0369a1 !important; border-radius: 12px !important; padding: 6px 14px !important; font-weight: 700 !important; border: 1px solid #bae6fd !important; }
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] span { color: #0369a1 !important; }
div[data-testid="stMultiSelect"] span[data-baseweb="tag"] svg { fill: #0369a1 !important; }

/* 🔥 Radio 按钮美化 (用于日、周、月切换) */
div[data-testid="stRadio"] div[role="radiogroup"] { display: flex !important; flex-direction: row !important; gap: 10px !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: #f1f5f9 !important; padding: 6px 20px !important; border-radius: 10px !important; cursor: pointer !important; transition: all 0.2s; border: 1px solid #e2e8f0; }
div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child { display: none !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] p { color: #64748b !important; font-weight: 600 !important; margin: 0 !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"], div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background-color: #0ea5e9 !important; border-color: #0ea5e9 !important; box-shadow: 0 4px 10px rgba(14,165,233,0.2) !important;}
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p, div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color: #ffffff !important; }
</style>
<a href="#top-anchor" class="back-to-top" title="回到顶部">↑</a>
"""
st.markdown(compressed_css, unsafe_allow_html=True)

# 导航栏扩展为 6 个按钮
spacer_left, nav1, nav2, nav3, nav4, nav5, nav6, spacer_right = st.columns([0.1, 1, 1, 1, 1, 1, 1, 0.1])
with nav1: st.page_link("app.py", label="App 首页", icon="🏠")
with nav2: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with nav3: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with nav4: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with nav5: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
with nav6: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比", icon="📊")
st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

# ==========================================
# ⚙️ 核心配置与工具函数
# ==========================================
FIXED_SITES = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
EN_TO_CN = {"DE": "德国", "FR": "法国", "ES": "西班牙", "IT": "意大利", "NL": "荷兰", "NO": "挪威", "SE": "瑞典", "FI": "芬兰", "PL": "波兰"}
COLOR_PALETTE = ['#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452', '#9A60B4', '#EA7CCC']

def parse_excel_dates(date_series):
    """鲁棒性极强的时间解析器，处理 Excel 序列号及常规文本"""
    parsed_dates = []
    for val in date_series:
        try:
            if isinstance(val, (int, float)):
                parsed_dates.append(pd.to_datetime(val, origin='1899-12-30', unit='D'))
            else:
                parsed_dates.append(pd.to_datetime(str(val).replace('月', '')))
        except:
            parsed_dates.append(pd.NaT)
    return pd.Series(parsed_dates)

# ==========================================
# 🎯 页面头部与文件上传
# ==========================================
st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📊 SEO 数据深度对比</div>", unsafe_allow_html=True)
st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>支持跨站点、长周期的销售额、流量及点击数据同环比分析。</div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>📥 上传数据报表</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请上传《SEO 整体数据情况》台账 (支持 Excel xlsx 格式)", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            
            # --- 模块 1: 解析非品牌词销售额 ---
            df_sales_raw = pd.read_excel(xls, sheet_name='SEO非品牌词销售额汇总') if 'SEO非品牌词销售额汇总' in xls.sheet_names else pd.DataFrame()
            
            if not df_sales_raw.empty:
                first_col = df_sales_raw.columns[0]
                df_sales_raw['Date'] = parse_excel_dates(df_sales_raw[first_col])
                df_sales_raw = df_sales_raw.dropna(subset=['Date'])
                
                # 提取可用站点
                available_sites = [s for s in FIXED_SITES if s in df_sales_raw.columns]
                df_sales_clean = df_sales_raw[['Date'] + available_sites].copy()
                for col in available_sites: df_sales_clean[col] = pd.to_numeric(df_sales_clean[col], errors='coerce').fillna(0)
                
                st.session_state['monthly_sales'] = df_sales_clean
                
            st.success("✅ 数据报表解析成功！")
        except Exception as e:
            st.error(f"❌ 解析失败: {e}")

# ==========================================
# 📈 模块一：SEO非品牌词销售额深度对比
# ==========================================
if 'monthly_sales' in st.session_state and not st.session_state['monthly_sales'].empty:
    df_sales = st.session_state['monthly_sales']
    available_sites = [col for col in df_sales.columns if col != 'Date']
    
    min_date = df_sales['Date'].min().date()
    max_date = df_sales['Date'].max().date()
    
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    st.markdown("### 💰 SEO非品牌词销售额对比")
    
    with st.container(border=True):
        # 1. 顶部控制器
        col_ctrl1, col_ctrl2 = st.columns([1.5, 1])
        with col_ctrl1:
            st.markdown("<div style='font-size: 13px; color:#64748b; font-weight:600; margin-bottom:8px;'>🌍 筛选对比站点 (卡片可多选)</div>", unsafe_allow_html=True)
            selected_sites = st.multiselect("筛选对比站点", options=available_sites, default=available_sites, format_func=lambda x: f"{x} {EN_TO_CN.get(x, '')}", label_visibility="collapsed")
        with col_ctrl2:
            st.markdown("<div style='font-size: 13px; color:#64748b; font-weight:600; margin-bottom:8px;'>📅 筛选具体时间范围</div>", unsafe_allow_html=True)
            date_range = st.date_input("选择时间范围", value=(min_date, max_date), min_value=min_date, max_value=max_date, label_visibility="collapsed")
        
        # 处理时间选择器逻辑
        if isinstance(date_range, (tuple, list)):
            if len(date_range) == 2: start_date, end_date = date_range
            elif len(date_range) == 1: start_date = end_date = date_range[0]
            else: start_date, end_date = min_date, max_date
        else: start_date = end_date = date_range
        if start_date > end_date: start_date, end_date = end_date, start_date
        
        if selected_sites:
            # 数据过滤
            mask = (df_sales['Date'] >= pd.to_datetime(start_date)) & (df_sales['Date'] <= pd.to_datetime(end_date))
            df_filtered = df_sales[mask].copy()
            
            # --- 同环比指标计算 (按月逻辑处理) ---
            df_filtered['Month_Str'] = df_filtered['Date'].dt.strftime('%Y-%m')
            df_sales['Month_Str'] = df_sales['Date'].dt.strftime('%Y-%m')
            
            target_month = df_filtered['Month_Str'].max() if not df_filtered.empty else None
            df_trend = df_sales.groupby('Month_Str')[selected_sites].sum().sum(axis=1).reset_index(name='Total')
            df_trend = df_trend.set_index('Month_Str')
            
            current_sales = df_trend.loc[target_month, 'Total'] if target_month in df_trend.index else 0
            
            # 环比 (上个月)
            try:
                prev_month = (pd.to_datetime(target_month + '-01') - pd.DateOffset(months=1)).strftime('%Y-%m')
                prev_sales = df_trend.loc[prev_month, 'Total'] if prev_month in df_trend.index else None
                mom_str = f"{((current_sales - prev_sales)/prev_sales)*100:+.1f}%" if prev_sales else "无数据"
            except:
                prev_sales, mom_str = None, "N/A"
            
            # 同比 (去年同月)
            try:
                last_year_month = (pd.to_datetime(target_month + '-01') - pd.DateOffset(years=1)).strftime('%Y-%m')
                yoy_sales = df_trend.loc[last_year_month, 'Total'] if last_year_month in df_trend.index else None
                yoy_str = f"{((current_sales - yoy_sales)/yoy_sales)*100:+.1f}%" if yoy_sales else "无数据"
            except:
                last_year_month, yoy_sales, yoy_str = "去年同期", None, "N/A"

            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"🌟 {target_month} 最新总销售额 (选定站点)", value=f"${current_sales:,.2f}")
            m2.metric(label=f"📉 环比 (较 {prev_month if prev_sales else '上月'})", value=f"${prev_sales:,.2f}" if prev_sales else "N/A", delta=mom_str)
            m3.metric(label=f"📅 同比 (较 {last_year_month})", value=f"${yoy_sales:,.2f}" if yoy_sales else "N/A", delta=yoy_str)
            st.markdown("<hr style='margin: 20px 0; border-color: #f1f5f9;'/>", unsafe_allow_html=True)
            
            # ==========================================
            # 📉 折线图分析模块 (各站点拆分趋势)
            # ==========================================
            st.markdown("<div style='font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 16px;'>🔍 各站点非品牌词销售额趋势折线图</div>", unsafe_allow_html=True)
            
            fig_line = go.Figure()
            for idx, site in enumerate(selected_sites):
                fig_line.add_trace(go.Scatter(
                    x=df_filtered['Date'], y=df_filtered[site],
                    mode='lines+markers', name=site,
                    line=dict(width=3, color=COLOR_PALETTE[idx % len(COLOR_PALETTE)]),
                    marker=dict(size=8, symbol='circle', color='#ffffff', line=dict(color=COLOR_PALETTE[idx % len(COLOR_PALETTE)], width=2)),
                    hovertemplate=f'<b>{site}</b><br>日期: %{{x}}<br>销售额: $%%{{y:,.2f}}<extra></extra>'
                ))

            fig_line.update_layout(
                height=350, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=10, b=20), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickformat='%Y-%m-%d'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
            st.markdown("<hr style='margin: 30px 0; border-color: #f1f5f9;'/>", unsafe_allow_html=True)

            # ==========================================
            # 📊 柱线混合汇总模块 (支持 日/周/月 筛选)
            # ==========================================
            col_sum1, col_sum2 = st.columns([1, 1])
            with col_sum1:
                st.markdown("<div style='font-size: 15px; font-weight: 700; color: #1e293b; margin-top: 8px;'>📦 全局汇总分析 (堆叠柱状图 + 汇总折线)</div>", unsafe_allow_html=True)
            with col_sum2:
                time_grain = st.radio("时间粒度", ["日", "周", "月"], index=2, horizontal=True, label_visibility="collapsed")
            
            st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)
            
            # 重新进行时间聚合计算
            df_agg = df_filtered.copy()
            if time_grain == "周": df_agg['Date_Axis'] = df_agg['Date'].dt.to_period('W').dt.to_timestamp()
            elif time_grain == "月": df_agg['Date_Axis'] = df_agg['Date'].dt.to_period('M').dt.to_timestamp()
            else: df_agg['Date_Axis'] = df_agg['Date']
            
            df_grouped = df_agg.groupby('Date_Axis')[selected_sites].sum().reset_index()
            df_grouped['Total'] = df_grouped[selected_sites].sum(axis=1)
            
            fig_mix = go.Figure()
            # 1. 堆叠柱状图 (拆分各站点)
            for idx, site in enumerate(selected_sites):
                fig_mix.add_trace(go.Bar(
                    x=df_grouped['Date_Axis'], y=df_grouped[site], name=site,
                    marker_color=COLOR_PALETTE[idx % len(COLOR_PALETTE)],
                    hovertemplate=f'<b>{site}</b>: $%%{{y:,.2f}}<extra></extra>'
                ))
            # 2. 悬浮虚线 (总计辅助线)
            fig_mix.add_trace(go.Scatter(
                x=df_grouped['Date_Axis'], y=df_grouped['Total'],
                mode='lines+markers', name='选中汇总总计',
                line=dict(color='#0f172a', width=2, dash='dot'), marker=dict(size=6, color='#0f172a'),
                hovertemplate='<b>总计 (Total)</b>: $%{y:,.2f}<extra></extra>'
            ))
            
            fig_mix.update_layout(
                barmode='stack', height=400, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=10, b=20), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickformat='%Y-%m-%d' if time_grain == '日' else '%Y-%m'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig_mix, use_container_width=True)
            
        else:
            st.warning("⚠️ 请至少保留一个筛选站点。")
else:
    st.info("👈 请在上方上传《SEO 整体数据情况》台账激活月度对比看板。")
