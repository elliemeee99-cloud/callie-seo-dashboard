import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO月度数据对比", page_icon="📅", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🧭 极限压缩防乱码 CSS + 6 栏居中导航栏
# ==========================================
compressed_css = """
<div id="top-anchor"></div>
<style>[data-testid="stSidebar"]{display:none !important;}[data-testid="collapsedControl"]{display:none !important;}[data-testid="stHeader"]{display:none !important;}.block-container{padding-top:2rem !important;max-width:95% !important;}.stApp{background-color:#f8fafc !important;}[data-testid="stPageLink-NavLink"]{background-color:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:12px !important;padding:12px 6px !important;text-align:center !important;display:flex !important;justify-content:center !important;align-items:center !important;transition:all 0.25s ease !important;box-shadow:0 2px 4px rgba(0,0,0,0.02) !important;text-decoration:none !important;white-space:nowrap;}[data-testid="stPageLink-NavLink"]:hover{background-color:#ffffff !important;border-color:#3b82f6 !important;transform:translateY(-2px) !important;box-shadow:0 8px 16px rgba(37,99,235,0.1) !important;}[data-testid="stPageLink-NavLink"] p{font-weight:800 !important;color:#1e293b !important;font-size:14px !important;margin:0 !important;}.back-to-top{position:fixed;bottom:40px;right:40px;background-color:#FF8FAB;color:#ffffff !important;border:none;width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:24px;font-weight:800;box-shadow:0 4px 15px rgba(255,143,171,0.35);text-decoration:none !important;z-index:99999;transition:all 0.3s ease;}.back-to-top:hover{background-color:#FF5D8F;transform:translateY(-5px);box-shadow:0 8px 20px rgba(255,143,171,0.55);color:#ffffff !important;}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;border:1px solid #e2e8f0 !important;background-color:#ffffff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);padding:20px;}</style>
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

def parse_excel_dates(date_series):
    """鲁棒性极强的时间解析器，处理 Excel 序列号及常规文本"""
    parsed_dates = []
    for val in date_series:
        try:
            if isinstance(val, (int, float)):
                # 处理 45444 这种 Excel 序列时间
                parsed_dates.append(pd.to_datetime(val, origin='1899-12-30', unit='D'))
            else:
                parsed_dates.append(pd.to_datetime(str(val).replace('月', '')))
        except:
            parsed_dates.append(pd.NaT)
    return pd.Series(parsed_dates)

# ==========================================
# 🎯 页面头部与文件上传
# ==========================================
st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📊 SEO 月度数据深度对比</div>", unsafe_allow_html=True)
st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>支持跨站点、长周期的销售额、流量及点击数据同环比分析。</div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>📥 上传最新月度报表</div>", unsafe_allow_html=True)
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
                df_sales_raw['Month'] = df_sales_raw['Date'].dt.strftime('%Y-%m')
                
                # 提取对应站点的列做融合 (Melt)
                available_sites = [s for s in FIXED_SITES if s in df_sales_raw.columns]
                df_sales_clean = df_sales_raw[['Month'] + available_sites].copy()
                # 转换数据类型保证安全
                for col in available_sites: df_sales_clean[col] = pd.to_numeric(df_sales_clean[col], errors='coerce').fillna(0)
                
                st.session_state['monthly_sales'] = df_sales_clean
                
            st.success("✅ 月度数据报表解析成功！")
        except Exception as e:
            st.error(f"❌ 解析失败: {e}")

# ==========================================
# 📈 模块一：SEO非品牌词销售额月度对比
# ==========================================
if 'monthly_sales' in st.session_state and not st.session_state['monthly_sales'].empty:
    df_sales = st.session_state['monthly_sales']
    all_months = sorted(df_sales['Month'].unique())
    available_sites = [col for col in df_sales.columns if col != 'Month']
    
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    st.markdown("### 💰 SEO非品牌词销售额月度对比")
    
    with st.container(border=True):
        # 顶部控制器
        col_ctrl1, col_ctrl2 = st.columns([2, 1])
        with col_ctrl1:
            selected_sites = st.multiselect("🌍 选择要对比的站点", options=available_sites, default=available_sites, format_func=lambda x: f"{x} {EN_TO_CN.get(x, '')}")
        with col_ctrl2:
            start_month, end_month = st.select_slider("📅 选择时间范围", options=all_months, value=(all_months[0], all_months[-1]))
        
        if selected_sites:
            # 数据过滤
            mask = (df_sales['Month'] >= start_month) & (df_sales['Month'] <= end_month)
            df_filtered = df_sales[mask].copy()
            
            # --- 1. 同环比指标计算 ---
            # 计算选中时间段内“最新一个月”的总销售额
            df_trend = df_sales.groupby('Month')[selected_sites].sum().sum(axis=1).reset_index(name='Total_Sales')
            df_trend = df_trend.sort_values('Month').set_index('Month')
            
            target_month = end_month
            current_sales = df_trend.loc[target_month, 'Total_Sales'] if target_month in df_trend.index else 0
            
            # 环比 (上个月)
            target_dt = pd.to_datetime(target_month + '-01')
            prev_month_dt = target_dt - pd.DateOffset(months=1)
            prev_month = prev_month_dt.strftime('%Y-%m')
            prev_sales = df_trend.loc[prev_month, 'Total_Sales'] if prev_month in df_trend.index else None
            mom_str = f"{((current_sales - prev_sales)/prev_sales)*100:+.1f}%" if prev_sales else "无数据"
            
            # 同比 (去年同月)
            last_year_dt = target_dt - pd.DateOffset(years=1)
            last_year_month = last_year_dt.strftime('%Y-%m')
            yoy_sales = df_trend.loc[last_year_month, 'Total_Sales'] if last_year_month in df_trend.index else None
            yoy_str = f"{((current_sales - yoy_sales)/yoy_sales)*100:+.1f}%" if yoy_sales else "无数据"

            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            m1.metric(label=f"🌟 {target_month} 选中站点总销售额", value=f"${current_sales:,.2f}")
            m2.metric(label=f"📉 环比 (较 {prev_month})", value=f"${prev_sales:,.2f}" if prev_sales else "N/A", delta=mom_str)
            m3.metric(label=f"📅 同比 (较 {last_year_month})", value=f"${yoy_sales:,.2f}" if yoy_sales else "N/A", delta=yoy_str)
            
            st.markdown("<hr style='margin: 20px 0; border-color: #f1f5f9;'/>", unsafe_allow_html=True)
            
            # --- 2. 绘制多维度折线图 ---
            fig = go.Figure()
            color_palette = ['#4285F4', '#EA4335', '#FBBC05', '#34A853', '#9C27B0', '#00BCD4', '#FF9800', '#795548', '#607D8B']
            
            # 添加每个站点的折线
            for idx, site in enumerate(selected_sites):
                fig.add_trace(go.Scatter(
                    x=df_filtered['Month'], y=df_filtered[site],
                    mode='lines+markers',
                    name=site,
                    line=dict(width=3, color=color_palette[idx % len(color_palette)]),
                    marker=dict(size=8, symbol='circle', color='#ffffff', line=dict(color=color_palette[idx % len(color_palette)], width=2)),
                    hovertemplate=f'<b>{site}</b><br>日期: %{{x}}<br>销售额: $%%{{y:,.2f}}<extra></extra>'
                ))
            
            # 计算并添加一条隐形的加总辅助线，悬浮时可查看该月总计
            df_filtered['Total'] = df_filtered[selected_sites].sum(axis=1)
            fig.add_trace(go.Scatter(
                x=df_filtered['Month'], y=df_filtered['Total'],
                mode='lines', name='总计',
                line=dict(width=0), # 隐形线条，只为了悬浮提示
                hoverinfo='skip',
                hovertemplate='<b>选中站点总计</b>: $%{y:,.2f}<extra></extra>'
            ))

            fig.update_layout(
                title=dict(text="📈 非品牌词销售额趋势分析", font=dict(size=16, color='#1e293b', weight='bold')),
                height=400,
                hovermode='x unified',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- 3. 数据明细表 ---
            st.markdown("<div style='font-size: 13px; color:#64748b; margin-top: 10px; margin-bottom: 8px;'>👇 选定维度下的原始数据明细</div>", unsafe_allow_html=True)
            df_display = df_filtered[['Month'] + selected_sites + ['Total']].copy()
            df_display = df_display.rename(columns={'Total': '选中总计', 'Month': '月份'})
            # 倒序排列，最新月份在最上
            df_display = df_display.sort_values('月份', ascending=False).reset_index(drop=True)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
        else:
            st.warning("⚠️ 请至少选择一个站点进行对比。")
else:
    st.info("👈 请在上方上传《SEO 整体数据情况》台账激活月度对比看板。")
