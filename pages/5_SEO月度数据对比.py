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
CACHE_FILE = "seo_monthly_sales_v9.pkl"

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
                # 解析流量数据表单 (SEO月度流量数据汇总)
                if 'SEO月度流量数据汇总' in xls.sheet_names:
                    try:
                        df_traffic_raw = pd.read_excel(xls, sheet_name='SEO月度流量数据汇总', header=None)
                        _parse_traffic_sheet(df_traffic_raw, data_dict)
                    except Exception as te:
                        st.warning(f"⚠️ 流量数据表解析异常（不影响销售额看板）: {te}")
                pd.to_pickle(data_dict, CACHE_FILE)
                st.session_state['monthly_data'] = data_dict
                st.success("✅ 数据报表完美解析！已识别销售额(3子表)与流量汇总表，含9站点逐月明细。")
            else:
                st.error("❌ 表格结构未能精准匹配！请确保三张表头分别带有'非品牌'、'ALL'与'网站总销售额'字样，并且包含'总计'列。")
                
        except Exception as e:
            st.error(f"❌ 解析失败，请检查文件格式。报错详情: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

# ==========================================
# 📂 本地文件自动加载（GitHub同步的Excel）
# ==========================================
st.markdown("<hr style='margin-top:8px;margin-bottom:12px;border-color:#e2e8f0;'/>", unsafe_allow_html=True)
col_path, col_load = st.columns([4, 1])
with col_path:
    local_path = st.text_input(
        "📁 本地Excel路径（GitHub同步文件，填写后自动加载）",
        value=st.session_state.get('local_excel_path', ''),
        placeholder="例如: /Users/elliekim/Documents/Codex/data/seo_data.xlsx",
        key='local_path_input'
    )
with col_load:
    st.write("")
    st.write("")
    if st.button("从路径加载", use_container_width=True):
        if local_path and os.path.exists(local_path):
            try:
                with open(local_path, 'rb') as f:
                    loaded = pd.ExcelFile(f)
                    target_sheet = 'SEO销售额汇总' if 'SEO销售额汇总' in loaded.sheet_names else loaded.sheet_names[0]
                    df_raw2 = pd.read_excel(loaded, sheet_name=target_sheet, header=None)
                    
                    nb_idx2=-1; all_idx2=-1; site_idx2=-1
                    for i2, row2 in df_raw2.iterrows():
                        rs2 = [str(x).replace(chr(10),'').strip().upper() for x in row2 if pd.notna(x)]
                        rj2 = "".join(rs2)
                        if '总计' in rj2 or '合计' in rj2:
                            if '非品牌' in rj2: nb_idx2 = i2
                            elif 'ALL' in rj2: all_idx2 = i2
                            elif '网站总销售额' in rj2: site_idx2 = i2
                    
                    if nb_idx2 != -1 and all_idx2 != -1 and site_idx2 != -1:
                        df_nb2, nb_d2 = extract_table(df_raw2, nb_idx2, all_idx2 if all_idx2 > nb_idx2 else len(df_raw2))
                        df_all2, all_d2 = extract_table(df_raw2, all_idx2, site_idx2 if site_idx2 > all_idx2 else len(df_raw2))
                        df_site2, site_d2 = extract_table(df_raw2, site_idx2, len(df_raw2))
                        
                        dd2 = {'nonbrand':df_nb2,'allseo':df_all2,'site':df_site2,
                               'nb_detail':nb_d2,'all_detail':all_d2,'site_detail':site_d2}
                        
                        if 'SEO月度流量数据汇总' in loaded.sheet_names:
                            try:
                                tf2 = pd.read_excel(loaded, sheet_name='SEO月度流量数据汇总', header=None)
                                _parse_traffic_sheet(tf2, dd2)
                            except Exception as te2:
                                st.warning(f"流量表解析异常: {te2}")
                        
                        st.session_state['monthly_data'] = dd2
                        pd.to_pickle(dd2, CACHE_FILE)
                        st.session_state['local_excel_path'] = local_path
                        st.success(f"✅ 已从本地文件加载数据: {os.path.basename(local_path)}")
                        st.rerun()
                    else:
                        st.error("表格结构不匹配，请检查文件。")
            except Exception as le:
                st.error(f"加载失败: {le}")
        else:
            st.error("文件路径不存在，请检查。")

# ==========================================
# 📈 深度对比图表渲染
# ==========================================
# 严格检验缓存数据是否合法，避免旧缓存造成 KeyError
if 'monthly_data' in st.session_state and isinstance(st.session_state['monthly_data'], dict) and 'nonbrand' in st.session_state['monthly_data'] and 'nb_detail' in st.session_state['monthly_data']:
    df_nb = st.session_state['monthly_data']['nonbrand']
    df_all = st.session_state['monthly_data']['allseo']
    df_site = st.session_state['monthly_data']['site']
    nb_detail = st.session_state['monthly_data']['nb_detail']
    all_detail = st.session_state['monthly_data']['all_detail']
    site_detail = st.session_state['monthly_data']['site_detail']
    
    if df_nb.empty or df_all.empty or df_site.empty:
        st.warning("⚠️ 提取到的核心数据为空（非品牌/ALL/网站总销售额至少一张表无数据），请检查报表内数据格式是否正确。")
    else:
        # 数据融合，计算涨降幅
        # ==========================================
        # 🎴 看板切换 (销售额 / 流量)
        # ==========================================
        tab_selected = st.session_state.get('tab_selected', 'sales')
        col_ts1, col_ts2 = st.columns(2)
        with col_ts1:
            if st.button('📊 销售额对比', key='tab_switch_sales', use_container_width=True,
                         type='primary' if tab_selected == 'sales' else 'secondary'):
                st.session_state.tab_selected = 'sales'
                st.rerun()
        with col_ts2:
            if st.button('📈 流量数据对比', key='tab_switch_traffic', use_container_width=True,
                         type='primary' if tab_selected == 'traffic' else 'secondary'):
                st.session_state.tab_selected = 'traffic'
                st.rerun()
        st.markdown('<hr style="margin-top:6px;margin-bottom:20px;border-color:#e2e8f0;"/>', unsafe_allow_html=True)

        # 销售额看板内容 (使用 div display 控制显隐)
        if tab_selected == 'sales':
            df_site_renamed = df_site.rename(columns={'Total': 'Total_Site'})
            df_merge = pd.merge(df_nb, df_all, on='Month', how='outer', suffixes=('_NB', '_All')).fillna(0)
            df_merge = pd.merge(df_merge, df_site_renamed, on='Month', how='left').fillna(0)
            df_merge = df_merge.sort_values('Month').reset_index(drop=True)
            df_merge['NB_Growth'] = df_merge['Total_NB'].pct_change() * 100
            df_merge['All_Growth'] = df_merge['Total_All'].pct_change() * 100
            df_merge['Site_Growth'] = df_merge['Total_Site'].pct_change() * 100

            # ------------------------------------------
            
# ⚡ 1. 销售额月度涨降幅对比
            # ------------------------------------------
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### ⚡ 1. 销售额月度涨降幅 (Growth Rate) 对比")
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
            
# 📉 2. 历年【非品牌词销售额】同比走势
            # ------------------------------------------
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 📉 2. 历年【非品牌词销售额总计】年度同环比走势")
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
            
# 📊 3. 非品牌词 vs ALL SEO 绝对值走势
            # ------------------------------------------
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 📊 3. 【非品牌词】与【ALL SEO】销售额总计综合对比")
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
            
# 🏪 4. 网站总销售额月度趋势
            # ------------------------------------------
            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🏪 4. 网站总销售额月度趋势")
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
            


            st.markdown("### \U0001f3ea 各站点详细数据")
            st.markdown('<style>.country-nav{position:fixed;top:5.5rem;left:1.5rem;width:200px;max-height:calc(100vh - 8rem);overflow-y:auto;z-index:9999;background:#ffffff;padding:16px;border-radius:16px;box-shadow:0 8px 24px rgba(0,0,0,0.04);border:1px solid #EEF2F6}.country-nav::-webkit-scrollbar{width:0;background:transparent}.block-container{padding-left:250px!important}[data-testid="stExpander"]{border:1px solid #EEF2F6!important;border-radius:16px!important;background-color:#ffffff!important;box-shadow:0 4px 20px rgba(0,0,0,0.02)!important;margin-bottom:24px!important;overflow:hidden}[data-testid="stExpander"]summary{padding:20px 24px!important;background-color:#ffffff!important}[data-testid="stExpander"]summary p{font-size:18px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.5px}</style>', unsafe_allow_html=True)

            _nav_html = """<div class="country-nav"><div style="font-size:15px;font-weight:800;color:#1e293b;margin-bottom:16px;display:flex;align-items:center;gap:8px;"><span style="font-size:18px;">\U0001f4cd</span> 快速定位</div><div style="display:flex;flex-direction:column;gap:8px;">
            <a href="#jump-DE" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1e9\U0001f1ea</span> DE 德国</a>
            <a href="#jump-FR" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1f7</span> FR 法国</a>
            <a href="#jump-ES" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ea\U0001f1f8</span> ES 西班牙</a>
            <a href="#jump-IT" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ee\U0001f1f9</span> IT 意大利</a>
            <a href="#jump-NL" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f1</span> NL 荷兰</a>
            <a href="#jump-NO" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f4</span> NO 挪威</a>
            <a href="#jump-SE" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f8\U0001f1ea</span> SE 瑞典</a>
            <a href="#jump-FI" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1ee</span> FI 芬兰</a>
            <a href="#jump-PL" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f5\U0001f1f1</span> PL 波兰</a>
            </div></div>"""
            st.markdown(_nav_html, unsafe_allow_html=True)

            st.markdown(f'<div id="jump-DE" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc DE \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 DE \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'DE NB',nb_detail['DE'],'#f43f5e'),(f'DE ALL',all_detail['DE'],'#10b981'),(f'DE Total',site_detail['DE'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 DE \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','DE']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['DE'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 DE \u975e\u54c1\u724c\u8bcd\u4e0eDE ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['DE'],mode='lines+markers',name=f'DE NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['DE'],mode='lines+markers',name=f'DE ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 DE \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['DE'],mode='lines+markers',name=f'DE Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-FR" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc FR \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 FR \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'FR NB',nb_detail['FR'],'#f43f5e'),(f'FR ALL',all_detail['FR'],'#10b981'),(f'FR Total',site_detail['FR'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 FR \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','FR']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['FR'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 FR \u975e\u54c1\u724c\u8bcd\u4e0eFR ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['FR'],mode='lines+markers',name=f'FR NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['FR'],mode='lines+markers',name=f'FR ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 FR \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['FR'],mode='lines+markers',name=f'FR Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-ES" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc ES \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 ES \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'ES NB',nb_detail['ES'],'#f43f5e'),(f'ES ALL',all_detail['ES'],'#10b981'),(f'ES Total',site_detail['ES'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 ES \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','ES']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['ES'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 ES \u975e\u54c1\u724c\u8bcd\u4e0eES ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['ES'],mode='lines+markers',name=f'ES NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['ES'],mode='lines+markers',name=f'ES ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 ES \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['ES'],mode='lines+markers',name=f'ES Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-IT" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc IT \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 IT \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'IT NB',nb_detail['IT'],'#f43f5e'),(f'IT ALL',all_detail['IT'],'#10b981'),(f'IT Total',site_detail['IT'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 IT \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','IT']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['IT'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 IT \u975e\u54c1\u724c\u8bcd\u4e0eIT ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['IT'],mode='lines+markers',name=f'IT NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['IT'],mode='lines+markers',name=f'IT ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 IT \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['IT'],mode='lines+markers',name=f'IT Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-NL" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc NL \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 NL \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'NL NB',nb_detail['NL'],'#f43f5e'),(f'NL ALL',all_detail['NL'],'#10b981'),(f'NL Total',site_detail['NL'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 NL \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','NL']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['NL'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 NL \u975e\u54c1\u724c\u8bcd\u4e0eNL ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['NL'],mode='lines+markers',name=f'NL NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['NL'],mode='lines+markers',name=f'NL ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 NL \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['NL'],mode='lines+markers',name=f'NL Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-NO" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc NO \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 NO \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'NO NB',nb_detail['NO'],'#f43f5e'),(f'NO ALL',all_detail['NO'],'#10b981'),(f'NO Total',site_detail['NO'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 NO \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','NO']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['NO'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 NO \u975e\u54c1\u724c\u8bcd\u4e0eNO ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['NO'],mode='lines+markers',name=f'NO NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['NO'],mode='lines+markers',name=f'NO ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 NO \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['NO'],mode='lines+markers',name=f'NO Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-SE" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc SE \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 SE \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'SE NB',nb_detail['SE'],'#f43f5e'),(f'SE ALL',all_detail['SE'],'#10b981'),(f'SE Total',site_detail['SE'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 SE \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','SE']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['SE'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 SE \u975e\u54c1\u724c\u8bcd\u4e0eSE ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['SE'],mode='lines+markers',name=f'SE NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['SE'],mode='lines+markers',name=f'SE ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 SE \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['SE'],mode='lines+markers',name=f'SE Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-FI" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc FI \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 FI \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'FI NB',nb_detail['FI'],'#f43f5e'),(f'FI ALL',all_detail['FI'],'#10b981'),(f'FI Total',site_detail['FI'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 FI \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','FI']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['FI'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 FI \u975e\u54c1\u724c\u8bcd\u4e0eFI ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['FI'],mode='lines+markers',name=f'FI NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['FI'],mode='lines+markers',name=f'FI ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 FI \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['FI'],mode='lines+markers',name=f'FI Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
            st.markdown(f'<div id="jump-PL" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"\U0001f4cc PL \u7ad9\u70b9 \u2014 4\u7ef4\u5ea6\u8be6\u60c5", expanded=True):
                x1,x2=st.columns(2)
                with x1:
                    st.markdown(f"**\u2460 PL \u9500\u552e\u989d\u6708\u5ea6\u6da8\u964d\u5e45\u5bf9\u6bd4**")
                    f=go.Figure()
                    for lb,src,cl in [(f'PL NB',nb_detail['PL'],'#f43f5e'),(f'PL ALL',all_detail['PL'],'#10b981'),(f'PL Total',site_detail['PL'],'#6366f1')]:
                        g=src.pct_change()*100
                        f.add_trace(go.Scatter(x=nb_detail['Month'],y=g,mode='lines+markers',name=lb,line=dict(width=2,color=cl),marker=dict(size=5)))
                    f.add_hline(y=0,line_dash="dash",line_color="#94a3b8")
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x2:
                    st.markdown(f"**\u2461 PL \u5386\u5e74\u975e\u54c1\u724c\u8bcd\u9500\u552e\u989d\u5e74\u5ea6\u540c\u6bd4\u8d70\u52bf**")
                    ds=nb_detail[['Month','PL']].copy(); ds['Date']=pd.to_datetime(ds['Month']+'-01'); ds['Year']=ds['Date'].dt.year.astype(str); ds['Mnum']=ds['Date'].dt.month
                    f=go.Figure(); cs=['#10b981','#3b82f6','#f59e0b','#8b5cf6']
                    for i,y in enumerate(sorted(ds['Year'].unique())):
                        dy=ds[ds['Year']==y].sort_values('Mnum')
                        f.add_trace(go.Scatter(x=dy['Mnum'],y=dy['PL'],mode='lines+markers',name=f'{y}\u5e74',line=dict(width=3,color=cs[i])))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                x3,x4=st.columns(2)
                with x3:
                    st.markdown(f"**\u2462 PL \u975e\u54c1\u724c\u8bcd\u4e0ePL ALL SEO\u9500\u552e\u989d\u7efc\u5408\u5bf9\u6bd4**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=nb_detail['Month'],y=nb_detail['PL'],mode='lines+markers',name=f'PL NB'))
                    f.add_trace(go.Scatter(x=all_detail['Month'],y=all_detail['PL'],mode='lines+markers',name=f'PL ALL'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)
                with x4:
                    st.markdown(f"**\u2463 PL \u7f51\u7ad9\u603b\u9500\u552e\u989d\u6708\u5ea6\u8d8b\u52bf**")
                    f=go.Figure()
                    f.add_trace(go.Scatter(x=site_detail['Month'],y=site_detail['PL'],mode='lines+markers',name=f'PL Total'))
                    f.update_layout(height=300,legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                    st.plotly_chart(f,use_container_width=True)


        elif tab_selected == 'traffic':
            # 流量看板内容
            traffic_months = st.session_state['monthly_data'].get('traffic_months', [])
            traffic_total = st.session_state['monthly_data'].get('traffic_total', {})
            traffic_onsite = st.session_state['monthly_data'].get('traffic_onsite', {})
            traffic_blog = st.session_state['monthly_data'].get('traffic_blog', {})

            if not traffic_months:
                st.warning("流量数据未找到，请重新上传包含「SEO月度流量数据汇总」表单的Excel文件。")
            else:
                st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 1. 各站点月度总流量趋势 (2025.01 ~ 至今)")
                with st.container(border=True):
                    f_t=go.Figure()
                    colors_t = ["#3b82f6","#ef4444","#f59e0b","#22c55e","#06b6d4","#ec4899","#8b5cf6","#14b8a6","#f97316"]
                    for i,sc in enumerate(["DE","FR","ES","IT","NL","NO","SE","FI","PL"]):
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total[sc],mode="lines+markers",name=sc,line=dict(width=2,color=colors_t[i]),marker=dict(size=5)))
                    f_t.update_layout(height=400,hovermode="x unified",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=20,r=20,t=20,b=20),
                        legend=dict(orientation="h",yanchor="top",y=-0.15,xanchor="center",x=0.5),
                        xaxis=dict(showgrid=True,gridcolor="#f1f5f9",type="category",tickangle=-45,nticks=18),
                        yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                    st.plotly_chart(f_t,use_container_width=True)

                st.markdown("#### 2. 全站总流量年度同比 (各月对比)")
                with st.container(border=True):
                    tf=pd.DataFrame(traffic_total)
                    tf["Month"]=traffic_months
                    tf["Total"]=tf[["DE","FR","ES","IT","NL","NO","SE","FI","PL"]].sum(axis=1)
                    tf["Date"]=pd.to_datetime(tf["Month"]+"-01")
                    tf["Year"]=tf["Date"].dt.year.astype(str)
                    tf["Mnum"]=tf["Date"].dt.month
                    f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                    for i,y in enumerate(sorted(tf["Year"].unique())):
                        dy=tf[tf["Year"]==y].sort_values("Mnum")
                        f_t.add_trace(go.Scatter(x=dy["Mnum"],y=dy["Total"],mode="lines+markers",name=f'{y}年',line=dict(width=3,color=cs_t[i])))
                    f_t.update_layout(height=400,hovermode="x unified",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=20,r=20,t=20,b=20),
                        legend=dict(orientation="h",yanchor="top",y=-0.15,xanchor="center",x=0.5),
                        xaxis=dict(showgrid=True,gridcolor="#f1f5f9",tickmode="array",tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)]),
                        yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                    st.plotly_chart(f_t,use_container_width=True)

                st.markdown(f"""<div class="country-nav">
                <div style="font-size:15px;font-weight:800;color:#1e293b;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
                    <span style="font-size:18px;">\U0001f4cd</span> 流量站点</div>
            <div style="display:flex;flex-direction:column;gap:8px;">
                <a href="#tjump-DE" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1e9\U0001f1ea</span> DE 德国</a>
                <a href="#tjump-FR" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1f7</span> FR 法国</a>
                <a href="#tjump-ES" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ea\U0001f1f8</span> ES 西班牙</a>
                <a href="#tjump-IT" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ee\U0001f1f9</span> IT 意大利</a>
                <a href="#tjump-NL" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f1</span> NL 荷兰</a>
                <a href="#tjump-NO" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f4</span> NO 挪威</a>
                <a href="#tjump-SE" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f8\U0001f1ea</span> SE 瑞典</a>
                <a href="#tjump-FI" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1ee</span> FI 芬兰</a>
                <a href="#tjump-PL" style="text-decoration:none;padding:10px 12px;background-color:#f8fafc;border-radius:8px;border-left:5px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f5\U0001f1f1</span> PL 波兰</a>
                </div>
                </div>""", unsafe_allow_html=True)

                st.markdown("### \U0001f4cc 各站点流量详情")
                st.markdown(f'<div id="tjump-DE" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 DE 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 DE 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["DE"],mode="lines+markers",name=f'DE 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 DE 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"DE":traffic_total["DE"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["DE"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 DE 站内流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_onsite["DE"],mode="lines+markers",name=f'DE 站内',line=dict(width=2,color="#f59e0b"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x4:
                        st.markdown(f"**\u2463 DE Blog流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_blog["DE"],mode="lines+markers",name=f'DE Blog',line=dict(width=2,color="#8b5cf6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                st.markdown(f'<div id="tjump-FR" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 FR 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 FR 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["FR"],mode="lines+markers",name=f'FR 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 FR 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"FR":traffic_total["FR"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["FR"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 FR 站内流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_onsite["FR"],mode="lines+markers",name=f'FR 站内',line=dict(width=2,color="#f59e0b"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x4:
                        st.markdown(f"**\u2463 FR Blog流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_blog["FR"],mode="lines+markers",name=f'FR Blog',line=dict(width=2,color="#8b5cf6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                st.markdown(f'<div id="tjump-ES" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 ES 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 ES 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["ES"],mode="lines+markers",name=f'ES 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 ES 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"ES":traffic_total["ES"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["ES"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 站内流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                    with x4:
                        st.markdown(f"**\u2463 Blog流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)
                st.markdown(f'<div id="tjump-IT" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 IT 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 IT 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["IT"],mode="lines+markers",name=f'IT 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 IT 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"IT":traffic_total["IT"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["IT"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 IT 站内流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_onsite["IT"],mode="lines+markers",name=f'IT 站内',line=dict(width=2,color="#f59e0b"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x4:
                        st.markdown(f"**\u2463 IT Blog流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_blog["IT"],mode="lines+markers",name=f'IT Blog',line=dict(width=2,color="#8b5cf6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                st.markdown(f'<div id="tjump-NL" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 NL 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 NL 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["NL"],mode="lines+markers",name=f'NL 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 NL 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"NL":traffic_total["NL"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["NL"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 站内流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                    with x4:
                        st.markdown(f"**\u2463 Blog流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)
                st.markdown(f'<div id="tjump-NO" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 NO 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 NO 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["NO"],mode="lines+markers",name=f'NO 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 NO 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"NO":traffic_total["NO"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["NO"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 站内流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                    with x4:
                        st.markdown(f"**\u2463 Blog流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)
                st.markdown(f'<div id="tjump-SE" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 SE 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 SE 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["SE"],mode="lines+markers",name=f'SE 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 SE 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"SE":traffic_total["SE"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["SE"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 站内流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                    with x4:
                        st.markdown(f"**\u2463 Blog流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)
                st.markdown(f'<div id="tjump-FI" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 FI 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 FI 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["FI"],mode="lines+markers",name=f'FI 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 FI 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"FI":traffic_total["FI"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["FI"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 站内流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                    with x4:
                        st.markdown(f"**\u2463 Blog流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)
                st.markdown(f'<div id="tjump-PL" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 PL 站点 — 流量详情", expanded=True):
                    x1,x2=st.columns(2)
                    with x1:
                        st.markdown(f"**\u2460 PL 月度总流量趋势**")
                        f_t=go.Figure()
                        f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total["PL"],mode="lines+markers",name=f'PL 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                        st.plotly_chart(f_t,use_container_width=True)
                    with x2:
                        st.markdown(f"**\u2461 PL 流量年度同比**")
                        tdf=pd.DataFrame({'Month':traffic_months,"PL":traffic_total["PL"]})
                        tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                        tdf['Year']=tdf['Date'].dt.year.astype(str)
                        tdf['Mnum']=tdf['Date'].dt.month
                        f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                        for i,y in enumerate(sorted(tdf['Year'].unique())):
                            dy=tdf[tdf['Year']==y].sort_values('Mnum')
                            f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy["PL"],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                        f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                        f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                        st.plotly_chart(f_t,use_container_width=True)
                    x3,x4=st.columns(2)
                    with x3:
                        st.markdown(f"**\u2462 站内流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                    with x4:
                        st.markdown(f"**\u2463 Blog流量数据**")
                        st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)

def _parse_traffic_sheet(raw2, result):
    import pandas as _pd

    _sites = ['DE','FR','ES','IT','NL','NO','SE','FI','PL']
    _months = []; _traffic_total = {s: [] for s in _sites}
    for ri in range(1, len(raw2)):
        d = raw2.iloc[ri, 0]
        if _pd.isna(d): continue
        dt = _pd.to_datetime(d, origin='1899-12-30', unit='D') if isinstance(d, (int,float)) else d
        _months.append(dt.strftime('%Y-%m'))
        for idx, s in enumerate(_sites):
            v = raw2.iloc[ri, 1+idx]
            _traffic_total[s].append(float(v) if _pd.notna(v) else 0.0)
    result['traffic_months'] = _months; result['traffic_total'] = _traffic_total
    _onsite = {'DE':[],'FR':[],'IT':[]}
    for ri in range(1, len(raw2)):
        d = raw2.iloc[ri, 11]
        if _pd.isna(d): continue
        for idx, s in enumerate(['DE','FR','IT']):
            v = raw2.iloc[ri, 12+idx]
            _onsite[s].append(float(v) if _pd.notna(v) else 0.0)
    result['traffic_onsite'] = _onsite
    _blog = {'DE':[],'FR':[],'IT':[]}
    for ri in range(1, len(raw2)):
        d = raw2.iloc[ri, 16]
        if _pd.isna(d): continue
        for idx, s in enumerate(['DE','FR','IT']):
            v = raw2.iloc[ri, 17+idx]
            _blog[s].append(float(v) if _pd.notna(v) else 0.0)
    result['traffic_blog'] = _blog

        
