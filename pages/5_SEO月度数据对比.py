import streamlit as st
import pandas as pd
import datetime
import os
import plotly.graph_objects as go

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO月度数据对比", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

# 强制使用新缓存名称，避免旧的崩溃数据引发 KeyError
CACHE_FILE = "seo_monthly_sales_v8.pkl"

# ==========================================
# 🧭 极限防乱码单行 CSS + 6栏导航
# ==========================================
compressed_css = """<div id="top-anchor"></div><style>[data-testid="stSidebar"]{display:none !important;}[data-testid="collapsedControl"]{display:none !important;}[data-testid="stHeader"]{display:none !important;}.block-container{padding-top:2rem !important;max-width:95% !important;}.stApp{background-color:#f8fafc !important;}[data-testid="stPageLink-NavLink"]{background-color:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:12px !important;padding:12px 6px !important;text-align:center !important;display:flex !important;justify-content:center !important;align-items:center !important;transition:all 0.25s ease !important;box-shadow:0 2px 4px rgba(0,0,0,0.02) !important;text-decoration:none !important;white-space:nowrap;}[data-testid="stPageLink-NavLink"]:hover{background-color:#ffffff !important;border-color:#3b82f6 !important;transform:translateY(-2px) !important;box-shadow:0 8px 16px rgba(37,99,235,0.1) !important;}[data-testid="stPageLink-NavLink"] p{font-weight:800 !important;color:#1e293b !important;font-size:14px !important;margin:0 !important;}.back-to-top{position:fixed;bottom:40px;right:40px;background-color:#FF8FAB;color:#ffffff !important;border:none;width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:24px;font-weight:800;box-shadow:0 4px 15px rgba(255,143,171,0.35);text-decoration:none !important;z-index:99999;transition:all 0.3s ease;}.back-to-top:hover{background-color:#FF5D8F;transform:translateY(-5px);box-shadow:0 8px 20px rgba(255,143,171,0.55);color:#ffffff !important;}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;border:1px solid #e2e8f0 !important;background-color:#ffffff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);padding:20px;}</style><a href="#top-anchor" class="back-to-top" title="回到顶部">↑</a>"""
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
# ⚙️ 核心解析引擎 (彻底修复错位Bug)
# ==========================================
def parse_excel_dates(date_list):
    parsed_dates = []
    for val in date_list:
        if pd.isna(val) or str(val).strip() == '':
            parsed_dates.append(pd.NaT)
            continue
        if isinstance(val, datetime.datetime):
            parsed_dates.append(val)
            continue
        try:
            if isinstance(val, (int, float)):
                parsed_dates.append(pd.to_datetime(val, origin='1899-12-30', unit='D'))
            else:
                v_str = str(val).strip().replace('年', '-').replace('月', '-').replace('日', '')
                if v_str.endswith('-'): v_str = v_str[:-1]
                parsed_dates.append(pd.to_datetime(v_str))
        except:
            parsed_dates.append(pd.NaT)
    return pd.Series(parsed_dates)

def extract_table(df_raw, start_idx, end_idx):
    df = df_raw.iloc[start_idx:end_idx].copy().reset_index(drop=True)
    if df.empty: return pd.DataFrame(), pd.DataFrame()
    
    # 强制将第一行设为列名
    df.columns = [str(c).replace('\n', '').strip() for c in df.iloc[0]]
    df = df.iloc[1:].dropna(how='all')
    if len(df) == 0: return pd.DataFrame(), pd.DataFrame()
    
    cols = list(df.columns)
    cols[0] = 'RawDate'
    df.columns = cols
    
    # 剔除底部的多余汇总行
    df = df[~df['RawDate'].astype(str).str.contains('总计|合计', na=False, case=False)]
    
    # 🔥 核心修复：使用 .tolist().values，强制按行位置直接赋权，彻底消灭索引错位！
    df['Date'] = parse_excel_dates(df['RawDate'].tolist()).values
    df = df.dropna(subset=['Date'])
    
    total_col = next((c for c in df.columns if '总计' in str(c) or '合计' in str(c)), None)
    if total_col:
        s = df[total_col].copy()
        if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
        # 剥离金额符号
        s = s.astype(str).str.replace(r'[$,\s]', '', regex=True)
        df['Total'] = pd.to_numeric(s, errors='coerce').fillna(0)
    else:
        df['Total'] = 0.0
    
    # 解析各站点列（DE/FR/ES/IT/NL/NO/SE/FI/PL）
    country_keywords = ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']
    country_cols = [c for c in df.columns if c in country_keywords]
    for col in country_cols:
        s = df[col].copy()
        if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
        s = s.astype(str).str.replace(r'[$,\s]', '', regex=True)
        df[col] = pd.to_numeric(s, errors='coerce').fillna(0)
        
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    
    monthly_total = df.groupby('Month')['Total'].sum().reset_index()
    monthly_detail = df.groupby('Month')[country_cols].sum().reset_index() if country_cols else pd.DataFrame()
    return monthly_total, monthly_detail

# ==========================================
# 🎯 页面头部与数据持久化上传
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📊 SEO 核心指标深度对比</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>取消繁琐确认，AI 自动提取非品牌词与整体销售额的同环比走势。</div>", unsafe_allow_html=True)
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
            target_sheet = 'SEO销售额汇总' if 'SEO销售额汇总' in xls.sheet_names else xls.sheet_names[0]
            df_raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
            
            # 智能切割上下表
            nb_idx = -1
            all_idx = -1
            site_idx = -1
            for i, row in df_raw.iterrows():
                row_strs = [str(x).replace('\n', '').strip().upper() for x in row if pd.notna(x)]
                row_joined = "".join(row_strs)
                if '总计' in row_joined or '合计' in row_joined:
                    if '非品牌' in row_joined: nb_idx = i
                    elif 'ALL' in row_joined: all_idx = i
                    elif '网站总销售额' in row_joined: site_idx = i
            
            if nb_idx != -1 and all_idx != -1 and site_idx != -1:
                df_nb, nb_detail = extract_table(df_raw, nb_idx, all_idx if all_idx > nb_idx else len(df_raw))
                df_all, all_detail = extract_table(df_raw, all_idx, site_idx if site_idx > all_idx else len(df_raw))
                df_site, site_detail = extract_table(df_raw, site_idx, len(df_raw))
                
                data_dict = {'nonbrand': df_nb, 'allseo': df_all, 'site': df_site,
                             'nb_detail': nb_detail, 'all_detail': all_detail, 'site_detail': site_detail}
                pd.to_pickle(data_dict, CACHE_FILE)
                st.session_state['monthly_data'] = data_dict
                st.success("✅ 数据报表完美解析！已识别三张子表，含9站点逐月明细。")
            else:
                st.error("❌ 表格结构未能精准匹配！请确保三张表头分别带有'非品牌'、'ALL'与'网站总销售额'字样，并且包含'总计'列。")
                
        except Exception as e:
            st.error(f"❌ 解析失败，请检查文件格式。报错详情: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

# ==========================================
# 📈 深度对比图表渲染
# ==========================================
# 严格检验缓存数据是否合法，避免旧缓存造成 KeyError
if 'monthly_data' in st.session_state and isinstance(st.session_state['monthly_data'], dict) and 'nonbrand' in st.session_state['monthly_data']:
    df_nb = st.session_state['monthly_data']['nonbrand']
    df_all = st.session_state['monthly_data']['allseo']
    df_site = st.session_state['monthly_data']['site']
    
    if df_nb.empty or df_all.empty or df_site.empty:
        st.warning("⚠️ 提取到的核心数据为空（非品牌/ALL/网站总销售额至少一张表无数据），请检查报表内数据格式是否正确。")
    else:
        # 数据融合，计算涨降幅
        df_site_renamed = df_site.rename(columns={'Total': 'Total_Site'})
        df_merge = pd.merge(df_nb, df_all, on='Month', how='outer', suffixes=('_NB', '_All')).fillna(0)
        df_merge = pd.merge(df_merge, df_site_renamed, on='Month', how='left').fillna(0)
        df_merge = df_merge.sort_values('Month').reset_index(drop=True)
        df_merge['NB_Growth'] = df_merge['Total_NB'].pct_change() * 100
        df_merge['All_Growth'] = df_merge['Total_All'].pct_change() * 100
        df_merge['Site_Growth'] = df_merge['Total_Site'].pct_change() * 100

        # ------------------------------------------
        # 📉 1. 历年【非品牌词销售额】同比走势
        # ------------------------------------------
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📉 1. 历年【非品牌词销售额总计】年度同环比走势")
        with st.container(border=True):
            df_yoy = df_nb.copy()
            df_yoy['Date'] = pd.to_datetime(df_yoy['Month'] + '-01')
            df_yoy['Year'] = df_yoy['Date'].dt.year.astype(str)
            df_yoy['Month_Num'] = df_yoy['Date'].dt.month
            
            fig1 = go.Figure()
            colors = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']
            for i, year in enumerate(sorted(df_yoy['Year'].unique())):
                df_year = df_yoy[df_yoy['Year'] == year].sort_values('Month_Num')
                fig1.add_trace(go.Scatter(
                    x=df_year['Month_Num'], y=df_year['Total'],
                    mode='lines+markers', name=f'{year}年',
                    line=dict(width=3, color=colors[i % len(colors)]),
                    marker=dict(size=8, color='#ffffff', line=dict(color=colors[i % len(colors)], width=2)),
                    # 🔥 修复完毕：干净的文字，纯正的美元符，绝无额外的百分号或“月”字
                    hovertemplate='<b>%{data.name} %{x}</b><br>非品牌词总计: $%{y:,.2f}<extra></extra>'
                ))
                
            fig1.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickmode='array', tickvals=list(range(1, 13)), ticktext=[f"{i}月" for i in range(1, 13)]),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig1, use_container_width=True)

        # ------------------------------------------
        # 📊 2. 非品牌词 vs ALL SEO 绝对值走势
        # ------------------------------------------
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📊 2. 【非品牌词】与【ALL SEO】销售额总计综合对比")
        with st.container(border=True):
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['Total_NB'],
                mode='lines+markers', name='非品牌词销售额总计',
                line=dict(width=3, color='#0ea5e9'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>非品牌词: $%{y:,.2f}<extra></extra>'
            ))
            fig2.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['Total_All'],
                mode='lines+markers', name='ALL SEO销售额总计',
                line=dict(width=3, color='#8b5cf6'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>ALL SEO: $%{y:,.2f}<extra></extra>'
            ))
            fig2.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig2, use_container_width=True)

        # ------------------------------------------
        # 🏪 3. 网站总销售额月度趋势
        # ------------------------------------------
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🏪 3. 网站总销售额月度趋势")
        with st.container(border=True):
            fig_site = go.Figure()
            fig_site.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['Total_Site'],
                mode='lines+markers', name='网站总销售额',
                line=dict(width=3, color='#f59e0b'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>网站总销售额: $%{y:,.2f}<extra></extra>'
            ))
            fig_site.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig_site, use_container_width=True)
        
        # ------------------------------------------
        # ⚡ 4. 销售额月度涨降幅对比
        # ------------------------------------------
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### ⚡ 4. 销售额月度涨降幅 (Growth Rate) 对比")
        with st.container(border=True):
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['NB_Growth'],
                mode='lines+markers', name='非品牌词涨跌幅(%)',
                line=dict(width=3, color='#f43f5e'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>非品牌词涨跌: %{y:+.2f}%<extra></extra>'
            ))
            fig3.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['All_Growth'],
                mode='lines+markers', name='ALL SEO涨跌幅(%)',
                line=dict(width=3, color='#10b981'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>ALL SEO涨跌: %{y:+.2f}%<extra></extra>'
            ))
            fig3.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['Site_Growth'],
                mode='lines+markers', name='网站总销售额涨跌幅(%)',
                line=dict(width=3, color='#6366f1'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>网站总销售额涨跌: %{y:+.2f}%<extra></extra>'
            ))
            
            fig3.add_hline(y=0, line_dash="dash", line_color="#94a3b8", annotation_text="0% 基准线")
            fig3.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', ticksuffix="%", tickformat='.2f')
            )
            st.plotly_chart(fig3, use_container_width=True)
        # ==========================================
        # 🏪 5. 各站点详细数据（可折叠）
        # ==========================================
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        with st.expander("🏪 各站点详细数据（含9站点逐月明细）", expanded=False):
            all_sites = ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']
            selected_sites = st.multiselect("选择要查看的站点", options=all_sites, default=['DE', 'FR', 'ES', 'IT', 'NL'])
            
            if not selected_sites:
                st.info("👆 请至少选择一个站点")
            else:
                colors_site = ['#0ea5e9', '#f43f5e', '#10b981', '#f59e0b', '#8b5cf6', '#6366f1', '#ec4899', '#14b8a6', '#f97316']
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**非品牌词销售额 - 各站点**")
                    fig_nb_site = go.Figure()
                    for i, s in enumerate(selected_sites):
                        fig_nb_site.add_trace(go.Scatter(x=nb_detail['Month'], y=nb_detail[s],
                            mode='lines+markers', name=s, line=dict(width=2, color=colors_site[i]), marker=dict(size=5),
                            hovertemplate=f'<b>%{{x}}</b><br>{s}: $%{{y:,.2f}}<extra></extra>'))
                    fig_nb_site.update_layout(height=300, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10,r=10,t=5,b=10), legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$"))
                    st.plotly_chart(fig_nb_site, use_container_width=True)
                    st.dataframe(nb_detail[['Month'] + selected_sites].round(2), use_container_width=True, hide_index=True)
                
                with c2:
                    st.markdown("**ALL SEO销售额 - 各站点**")
                    fig_all_site = go.Figure()
                    for i, s in enumerate(selected_sites):
                        fig_all_site.add_trace(go.Scatter(x=all_detail['Month'], y=all_detail[s],
                            mode='lines+markers', name=s, line=dict(width=2, color=colors_site[i]), marker=dict(size=5),
                            hovertemplate=f'<b>%{{x}}</b><br>{s}: $%{{y:,.2f}}<extra></extra>'))
                    fig_all_site.update_layout(height=300, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10,r=10,t=5,b=10), legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$"))
                    st.plotly_chart(fig_all_site, use_container_width=True)
                    st.dataframe(all_detail[['Month'] + selected_sites].round(2), use_container_width=True, hide_index=True)
                
                c3, c4 = st.columns(2)
                with c3:
                    st.markdown("**网站总销售额 - 各站点**")
                    fig_site_d = go.Figure()
                    for i, s in enumerate(selected_sites):
                        fig_site_d.add_trace(go.Scatter(x=site_detail['Month'], y=site_detail[s],
                            mode='lines+markers', name=s, line=dict(width=2, color=colors_site[i]), marker=dict(size=5),
                            hovertemplate=f'<b>%{{x}}</b><br>{s}: $%{{y:,.2f}}<extra></extra>'))
                    fig_site_d.update_layout(height=300, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10,r=10,t=5,b=10), legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$"))
                    st.plotly_chart(fig_site_d, use_container_width=True)
                    st.dataframe(site_detail[['Month'] + selected_sites].round(2), use_container_width=True, hide_index=True)
                
                with c4:
                    st.markdown("**月度涨跌幅 - 各站点 (%)**")
                    fig_growth_site = go.Figure()
                    for i, s in enumerate(selected_sites):
                        growth = nb_detail[s].pct_change() * 100
                        fig_growth_site.add_trace(go.Scatter(x=nb_detail['Month'], y=growth,
                            mode='lines+markers', name=s, line=dict(width=2, color=colors_site[i]), marker=dict(size=5),
                            hovertemplate=f'<b>%{{x}}</b><br>{s}: %{{y:+.2f}}%<extra></extra>'))
                    fig_growth_site.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
                    fig_growth_site.update_layout(height=300, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=10,r=10,t=5,b=10), legend=dict(orientation="h", yanchor="top", y=-0.25, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                        yaxis=dict(showgrid=True, gridcolor='#f1f5f9', ticksuffix="%", tickformat='.2f'))
                    st.plotly_chart(fig_growth_site, use_container_width=True)
                    growth_tb = nb_detail[['Month'] + selected_sites].pct_change().mul(100).round(2)
                    st.dataframe(growth_tb, use_container_width=True, hide_index=True)
else:
    st.info("👈 您的缓存池为空。请在上方上传最新整理好的《SEO 整体数据情况》台账以激活对比引擎。")
        
