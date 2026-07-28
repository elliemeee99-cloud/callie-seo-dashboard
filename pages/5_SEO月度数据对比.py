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
# ==========================================
# ==========================================
# 🎨 UI Refinements V2 - Enterprise SaaS Style
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:270px!important}
h1{font-size:30px!important;font-weight:700!important;color:#111827!important}
h2{font-size:24px!important;font-weight:700!important;color:#111827!important}
h3{font-size:20px!important;font-weight:700!important;color:#111827!important}
h4,h5,h6{font-size:18px!important;font-weight:700!important;color:#111827!important}
p{color:#6B7280!important;font-size:14px!important}
hr{border-color:#E5E7EB!important;margin:8px 0!important}
.stButton button{height:38px!important;border-radius:10px!important;font-size:14px!important;font-weight:600!important;padding:0 16px!important}
.stButton button[kind="primary"]{background:#EFF6FF!important;color:#1D4ED8!important;border:1px solid #BFDBFE!important}
.stButton button[kind="primary"]:hover{background:#DBEAFE!important;border-color:#93C5FD!important;color:#1E40AF!important}
.stButton button[kind="secondary"]{background:#FFFFFF!important;color:#374151!important;border:1px solid #D1D5DB!important}
.stButton button[kind="secondary"]:hover{background:#F9FAFB!important;border-color:#9CA3AF!important;color:#111827!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px!important;border:1px solid #E5E7EB!important;background-color:#FFFFFF;box-shadow:0 1px 3px rgba(0,0,0,.06)!important;padding:16px!important;margin-bottom:12px!important}
[data-testid="stExpander"]{border:1px solid #E5E7EB!important;border-radius:12px!important;background-color:#FFFFFF!important;margin-bottom:16px!important;overflow:hidden}
[data-testid="stExpander"] summary{padding:14px 20px!important;background-color:#FFFFFF!important}
[data-testid="stExpander"] summary p{font-size:16px!important;font-weight:700!important;color:#111827!important}
.country-nav{position:fixed!important;top:11rem!important;left:1.2rem!important;width:140px!important;max-height:calc(100vh - 10rem)!important;overflow-y:auto!important;z-index:9999!important;background:#FFFFFF!important;padding:10px!important;border-radius:10px!important;border:1px solid #E5E7EB!important}
.country-nav a{display:flex!important;align-items:center!important;gap:6px!important;padding:8px 8px!important;margin-bottom:2px!important;border-radius:6px!important;color:#374151!important;font-weight:500!important;font-size:13px!important;text-decoration:none!important;border-left:3px solid transparent!important;transition:all .12s!important}
.country-nav a:hover{background-color:#F1F5F9!important;color:#111827!important;border-left-color:#CBD5E1!important}
.country-nav a span{font-size:14px!important}
[data-testid="stPageLink-NavLink"]{background:transparent!important;border:none!important;border-radius:0!important;padding:8px 14px!important;border-bottom:2px solid transparent!important;margin-bottom:-1px}
[data-testid="stPageLink-NavLink"]:hover{background:#F1F5F9!important}
[data-testid="stPageLink-NavLink"] p{font-weight:600!important;color:#64748B!important;font-size:16px!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"]{border-bottom:2px solid #2563EB!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"] p{color:#2563EB!important;font-weight:600!important}
.stAlert{border-radius:10px!important;padding:10px 14px!important;margin-bottom:8px!important}
.back-to-top{position:fixed;bottom:32px;right:32px;background:#2563EB;color:#fff!important;width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;text-decoration:none!important;z-index:99999}
.back-to-top:hover{background:#1D4ED8}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
</style>""", unsafe_allow_html=True)

_nc = st.columns([0.1, 1, 1, 1, 1, 1, 1, 0.1])
with _nc[0]: pass
with _nc[1]: st.page_link("app.py", label="App 首页")
with _nc[2]: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览")
with _nc[3]: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细")
with _nc[4]: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理")
with _nc[5]: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录")
with _nc[6]: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比")
st.markdown("<div style='height:1px;background:#E2E8F0;margin:2px 0 14px 0;'></div>", unsafe_allow_html=True)
st.markdown("<a href='#top-anchor' class='back-to-top' title='\u56de\u5230\u9876\u90e8'>\u2191</a>", unsafe_allow_html=True)
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
def _parse_gsc_sheet(raw2, result):
    import pandas as _pd
    # GSC表纵向分区: 每段有自己的header行+数据行
    # 段1(行0): DE(col0-5) FR(col7-12) ES(col14-19) 行1-25
    # 段2(行28): IT(col0-5) NL(col7-12) 行29-53
    # 段3(行55): NO(col0-5) SE(col7-12) 行56-69
    # 段4(行71): FI(col0-5) PL(col7-12) 行72-85
    _segments = [
        (0, [('DE',0), ('FR',7), ('ES',14)]),
        (28, [('IT',0), ('NL',7)]),
        (55, [('NO',0), ('SE',7)]),
        (71, [('FI',0), ('PL',7)]),
    ]
    _gsc = {}
    for _hr, _sites in _segments:
        for _sc, _base in _sites:
            _m=[]; _tv=[]; _bv=[]; _lv=[]; _uv=[]; _ov=[]
            for _ri in range(_hr+1, len(raw2)):
                _v = raw2.iloc[_ri, _base]
                if not isinstance(_v, (int,float)) or _pd.isna(_v):
                    break
                _dt = _pd.to_datetime(_v, origin='1899-12-30', unit='D')
                _m.append(_dt.strftime('%Y-%m'))
                _tv.append(float(raw2.iloc[_ri,_base+1]) if _pd.notna(raw2.iloc[_ri,_base+1]) else 0.0)
                _bv.append(float(raw2.iloc[_ri,_base+2]) if _pd.notna(raw2.iloc[_ri,_base+2]) else 0.0)
                _lv.append(float(raw2.iloc[_ri,_base+3]) if _pd.notna(raw2.iloc[_ri,_base+3]) else 0.0)
                _uv.append(float(raw2.iloc[_ri,_base+4]) if _pd.notna(raw2.iloc[_ri,_base+4]) else 0.0)
                _ov.append(float(raw2.iloc[_ri,_base+5]) if _pd.notna(raw2.iloc[_ri,_base+5]) else 0.0)
            _gsc[_sc] = {'months':_m,'total':_tv,'brand':_bv,'blog':_lv,'utm':_uv,'onsite':_ov}
    result['gsc_data'] = _gsc


        

# ==========================================
# 🎯 页面头部与数据持久化上传
# ==========================================
col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>SEO 月度数据对比</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>掌握SEO核心指标与站点表现</div>", unsafe_allow_html=True)
with col_h_right:
    st.markdown(f"<div style='color:#9CA3AF;font-size:11px;text-align:right;margin-bottom:2px;line-height:1;'>更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns([1, 1, 1.8])
    with col_b1:
        if st.button("\u2726 \u6e05\u7a7a\u7f13\u5b58", use_container_width=False):
            if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
            if 'monthly_data' in st.session_state: del st.session_state['monthly_data']
            st.success("\u7f13\u5b58\u5df2\u6e05\u7a7a\uff01")
            st.rerun()
    with col_b2:
        if st.button("\u540c\u6b65\u6570\u636e", type="primary", use_container_width=False):
            pass
    with col_b3:
        uploaded_file = st.file_uploader("上传Excel", type=['xlsx', 'xls'], label_visibility="collapsed")
    msg_area = st.empty()
    
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
                # 直接按表单名读取流量数据
                if 'SEO月度流量数据汇总' in xls.sheet_names:
                    df_traffic_raw = pd.read_excel(xls, sheet_name='SEO月度流量数据汇总', header=None)
                    _parse_traffic_sheet(df_traffic_raw, data_dict)
                if 'SEO GSC月度点击数据汇总' in xls.sheet_names:
                    df_gsc_raw = pd.read_excel(xls, sheet_name='SEO GSC月度点击数据汇总', header=None)
                    _parse_gsc_sheet(df_gsc_raw, data_dict)
                pd.to_pickle(data_dict, CACHE_FILE)
                st.session_state['monthly_data'] = data_dict
                msg_area.success("✅ 数据解析成功！")
            else:
                msg_area.error("❌ 表格结构不匹配，请检查。")
                
        except Exception as e:
            msg_area.error(f"❌ 解析失败: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass
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
        col_ts1, col_ts2, col_ts3 = st.columns(3)
        with col_ts1:
            if st.button('销售额对比', key='tab_switch_sales', use_container_width=True,
                         type='primary' if tab_selected == 'sales' else 'secondary'):
                st.session_state.tab_selected = 'sales'
                st.rerun()
        with col_ts2:
            if st.button('流量数据对比', key='tab_switch_traffic', use_container_width=True,
                         type='primary' if tab_selected == 'traffic' else 'secondary'):
                st.session_state.tab_selected = 'traffic'
                st.rerun()
        with col_ts3:
            if st.button('GSC点击数据对比', key='tab_switch_gsc', use_container_width=True,
                         type='primary' if tab_selected == 'gsc' else 'secondary'):
                st.session_state.tab_selected = 'gsc'
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
            st.markdown('<style>.country-nav{position:fixed;top:11rem;left:1.2rem;width:140px;max-height:calc(100vh - 10rem);overflow-y:auto;z-index:9999;background:#ffffff;padding:10px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.04);border:1px solid #EEF2F6}.country-nav::-webkit-scrollbar{width:0;background:transparent}.block-container{padding-left:250px!important}[data-testid="stExpander"]{border:1px solid #EEF2F6!important;border-radius:16px!important;background-color:#ffffff!important;box-shadow:0 4px 20px rgba(0,0,0,0.02)!important;margin-bottom:24px!important;overflow:hidden}[data-testid="stExpander"]summary{padding:20px 24px!important;background-color:#ffffff!important}[data-testid="stExpander"]summary p{font-size:18px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.5px}</style>', unsafe_allow_html=True)

            _nav_html = """<div class="country-nav"><div style="font-size:15px;font-weight:800;color:#1e293b;margin-bottom:16px;display:flex;align-items:center;gap:8px;"><span style="font-size:18px;">\U0001f4cd</span> 快速定位</div><div style="display:flex;flex-direction:column;gap:8px;">
            <a href="#jump-DE" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1e9\U0001f1ea</span> DE</a>
            <a href="#jump-FR" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1f7</span> FR</a>
            <a href="#jump-ES" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ea\U0001f1f8</span> ES</a>
            <a href="#jump-IT" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ee\U0001f1f9</span> IT</a>
            <a href="#jump-NL" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f1</span> NL</a>
            <a href="#jump-NO" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f4</span> NO</a>
            <a href="#jump-SE" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f8\U0001f1ea</span> SE</a>
            <a href="#jump-FI" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1ee</span> FI</a>
            <a href="#jump-PL" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f5\U0001f1f1</span> PL</a>
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
            st.markdown('<style>.country-nav{position:fixed;top:11rem;left:1.2rem;width:140px;max-height:calc(100vh - 10rem);overflow-y:auto;z-index:9999;background:#ffffff;padding:10px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.04);border:1px solid #EEF2F6}.country-nav::-webkit-scrollbar{width:0;background:transparent}.block-container{padding-left:250px!important}[data-testid="stExpander"]{border:1px solid #EEF2F6!important;border-radius:16px!important;background-color:#ffffff!important;box-shadow:0 4px 20px rgba(0,0,0,0.02)!important;margin-bottom:24px!important;overflow:hidden}[data-testid="stExpander"]summary{padding:20px 24px!important;background-color:#ffffff!important}[data-testid="stExpander"]summary p{font-size:18px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.5px}</style>', unsafe_allow_html=True)
            # 流量看板内容
            traffic_months = st.session_state['monthly_data'].get('traffic_months', [])
            traffic_total = st.session_state['monthly_data'].get('traffic_total', {})
            traffic_onsite = st.session_state['monthly_data'].get('traffic_onsite', {})
            traffic_blog = st.session_state['monthly_data'].get('traffic_blog', {})

            if not traffic_months:
                st.warning("⚠️ 流量数据未找到。请检查Excel是否包含「SEO月度流量数据汇总」表单，或点击「清空本地缓存」后重新上传。")
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
                <a href="#tjump-DE" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1e9\U0001f1ea</span> DE</a>
                <a href="#tjump-FR" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1f7</span> FR</a>
                <a href="#tjump-ES" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ea\U0001f1f8</span> ES</a>
                <a href="#tjump-IT" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ee\U0001f1f9</span> IT</a>
                <a href="#tjump-NL" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f1</span> NL</a>
                <a href="#tjump-NO" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f4</span> NO</a>
                <a href="#tjump-SE" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f8\U0001f1ea</span> SE</a>
                <a href="#tjump-FI" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1ee</span> FI</a>
                <a href="#tjump-PL" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f5\U0001f1f1</span> PL</a>
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



        elif tab_selected == 'gsc':
            st.markdown('<style>.block-container{padding-left:250px!important}.country-nav{position:fixed;top:11rem;left:1.2rem;width:140px;max-height:calc(100vh - 10rem);overflow-y:auto;z-index:9999;background:#ffffff;padding:10px;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.04);border:1px solid #EEF2F6}[data-testid="stExpander"]{border:1px solid #EEF2F6!important;border-radius:16px!important;background-color:#ffffff!important;box-shadow:0 4px 20px rgba(0,0,0,0.02)!important;margin-bottom:24px!important;overflow:hidden}[data-testid="stExpander"] summary{padding:20px 24px!important;background-color:#ffffff!important}[data-testid="stExpander"] summary p{font-size:18px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.5px}</style>', unsafe_allow_html=True)
            gsc_data = st.session_state['monthly_data'].get('gsc_data', {})
            if not gsc_data:
                st.warning("⚠️ GSC 点击数据未找到，请确认Excel包含「SEO GSC月度点击数据汇总」表单。")
            else:
                st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 1. 各站点GSC总点击趋势 (2024.06 ~ 至今)")
                with st.container(border=True):
                    # Merge all sites by month for combined chart
                    _all_months = sorted(set().union(*[set(gsc_data[s]['months']) for s in ['DE','FR','ES','IT','NL','NO','SE','FI','PL']]))
                    f_g=go.Figure()
                    _gsc_colors = ['#3b82f6','#ef4444','#f59e0b','#22c55e','#06b6d4','#ec4899','#8b5cf6','#14b8a6','#f97316']
                    for _i,_s in enumerate(['DE','FR','ES','IT','NL','NO','SE','FI','PL']):
                        _gd = gsc_data[_s]
                        f_g.add_trace(go.Scatter(x=_gd['months'],y=_gd['total'],mode='lines+markers',name=f'{_s} 总点击',line=dict(width=2,color=_gsc_colors[_i]),marker=dict(size=5)))
                    f_g.update_layout(height=400,hovermode='x unified',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=20,r=20,t=20,b=20),
                        legend=dict(orientation='h',yanchor='top',y=-0.15,xanchor='center',x=0.5),
                        xaxis=dict(showgrid=True,gridcolor='#f1f5f9',type='category',tickangle=-45,nticks=18),
                        yaxis=dict(showgrid=True,gridcolor='#f1f5f9'))
                    st.plotly_chart(f_g,use_container_width=True)
                
                st.markdown("""<div class="country-nav">
    <div style="font-size:15px;font-weight:800;color:#1e293b;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
        <span style="font-size:18px;">\U0001f5b1</span> GSC\u7ad9\u70b9</div>
    <div style="display:flex;flex-direction:column;gap:8px;">
        <a href="#gjump-DE" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1e9\U0001f1ea</span> DE</a>
        <a href="#gjump-FR" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1f7</span> FR</a>
        <a href="#gjump-ES" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ea\U0001f1f8</span> ES</a>
        <a href="#gjump-IT" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1ee\U0001f1f9</span> IT</a>
        <a href="#gjump-NL" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f1</span> NL</a>
        <a href="#gjump-NO" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #EA4335;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f3\U0001f1f4</span> NO</a>
        <a href="#gjump-SE" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #FBBC05;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f8\U0001f1ea</span> SE</a>
        <a href="#gjump-FI" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #34A853;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1eb\U0001f1ee</span> FI</a>
        <a href="#gjump-PL" style="text-decoration:none;padding:8px 8px;background-color:#f8fafc;border-radius:6px;border-left:4px solid #4285F4;color:#1e293b;font-weight:600;display:flex;align-items:center;gap:10px;"><span>\U0001f1f5\U0001f1f1</span> PL</a>
    </div>
</div>""", unsafe_allow_html=True)
                st.markdown("### 各站点GSC点击详情")
                
                for _s2 in ['DE','FR','ES','IT','NL','NO','SE','FI','PL']:
                    _d2 = gsc_data[_s2]
                    st.markdown(f'<div id="gjump-{_s2}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                    with st.expander(f"GSC {_s2} 站点 — 点击详情", expanded=True):
                        x1,x2=st.columns(2)
                        with x1:
                            st.markdown(f"**① {_s2} 总点击趋势**")
                            f2=go.Figure()
                            f2.add_trace(go.Scatter(x=_d2['months'],y=_d2['total'],mode='lines+markers',name=f'{_s2} 总点击',line=dict(width=2,color='#3b82f6'),marker=dict(size=5)))
                            f2.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type='category',tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor='#f1f5f9'))
                            st.plotly_chart(f2,use_container_width=True)
                        with x2:
                            st.markdown(f"**② {_s2} 品牌词点击趋势**")
                            f2=go.Figure()
                            f2.add_trace(go.Scatter(x=_d2['months'],y=_d2['brand'],mode='lines+markers',name=f'{_s2} 品牌词',line=dict(width=2,color='#ef4444'),marker=dict(size=5)))
                            f2.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type='category',tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor='#f1f5f9'))
                            st.plotly_chart(f2,use_container_width=True)
                        x3,x4=st.columns(2)
                        with x3:
                            st.markdown(f"**③ {_s2} Blog点击趋势**")
                            f2=go.Figure()
                            f2.add_trace(go.Scatter(x=_d2['months'],y=_d2['blog'],mode='lines+markers',name=f'{_s2} Blog',line=dict(width=2,color='#f59e0b'),marker=dict(size=5)))
                            f2.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type='category',tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor='#f1f5f9'))
                            st.plotly_chart(f2,use_container_width=True)
                        with x4:
                            st.markdown(f"**④ {_s2} 站内点击趋势**")
                            f2=go.Figure()
                            f2.add_trace(go.Scatter(x=_d2['months'],y=_d2['onsite'],mode='lines+markers',name=f'{_s2} 站内',line=dict(width=2,color='#8b5cf6'),marker=dict(size=5)))
                            f2.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type='category',tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor='#f1f5f9'))
                            st.plotly_chart(f2,use_container_width=True)
