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
CACHE_FILE = "seo_monthly_sales_v11.pkl"

# ==========================================
# 🎨 UI Refinements V3 - Enterprise SaaS Style
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:140px!important}
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

/* KPI 卡片样式 */
.kpi-card {background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align: center; height: 100%;}
.kpi-title {font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 8px;}
.kpi-value {font-size: 30px; font-weight: 700; color: #0F172A; margin: 0;}
.kpi-value.blue {color: #2563EB;}
.kpi-value.green {color: #10B981;}
.kpi-value.purple {color: #8B5CF6;}
.kpi-value.orange {color: #F59E0B;}

/* Expander (下拉面板) 样式 */
[data-testid="stExpander"]{border:1px solid #EEF2F6!important;border-radius:16px!important;background-color:#ffffff!important;box-shadow:0 4px 20px rgba(0,0,0,0.02)!important;margin-bottom:24px!important;overflow:hidden}
[data-testid="stExpander"] summary{padding:20px 24px!important;background-color:#ffffff!important}
[data-testid="stExpander"] summary p{font-size:18px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.5px}

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
.stAlert{border-radius:10px!important;padding:10px 14px!important;margin-bottom:8px!important}
.back-to-top{position:fixed;bottom:32px;right:32px;background:#2563EB;color:#fff!important;width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;text-decoration:none!important;z-index:99999}
.back-to-top:hover{background:#1D4ED8}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
</style>""", unsafe_allow_html=True)

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

# ==========================================
# ⚙️ 辅助模块：左侧挂件生成器
# ==========================================
def get_nav_html(prefix, icon, title):
    sites = [('DE', '🇩🇪', '#4285F4'), ('FR', '🇫🇷', '#EA4335'), ('ES', '🇪🇸', '#FBBC05'),
             ('IT', '🇮🇹', '#34A853'), ('NL', '🇳🇱', '#4285F4'), ('NO', '🇳🇴', '#EA4335'),
             ('SE', '🇸🇪', '#FBBC05'), ('FI', '🇫🇮', '#34A853'), ('PL', '🇵🇱', '#4285F4')]
    links = ""
    for site, flag, color in sites:
        links += f'<a href="#{prefix}-{site}" style="border-left:4px solid {color};"><span class="c-flag">{flag}</span><span class="c-name" style="background:{color};">{site}</span></a>'
        
    return f'<div class="country-nav"><div style="font-size:12px;font-weight:800;color:#1e293b;margin-bottom:12px;display:flex;align-items:center;gap:4px;"><span style="font-size:14px;">{icon}</span> {title}</div><div style="display:flex;flex-direction:column;">{links}</div></div>'

# ==========================================
# ⚙️ 核心解析引擎
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
    
    df.columns = [str(c).replace('\n', '').strip() for c in df.iloc[0]]
    df = df.iloc[1:].dropna(how='all')
    if len(df) == 0: return pd.DataFrame(), pd.DataFrame()
    
    cols = list(df.columns)
    cols[0] = 'RawDate'
    df.columns = cols
    
    df = df[~df['RawDate'].astype(str).str.contains('总计|合计', na=False, case=False)]
    
    df['Date'] = parse_excel_dates(df['RawDate'].tolist()).values
    df = df.dropna(subset=['Date'])
    
    total_col = next((c for c in df.columns if '总计' in str(c) or '合计' in str(c)), None)
    if total_col:
        s = df[total_col].copy()
        if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
        s = s.astype(str).str.replace(r'[$,\s]', '', regex=True)
        df['Total'] = pd.to_numeric(s, errors='coerce').fillna(0)
    else:
        df['Total'] = 0.0
    
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
        if isinstance(d, str) and ('合计' in d or '总计' in d): continue
        try:
            dt = _pd.to_datetime(d, origin='1899-12-30', unit='D') if isinstance(d, (int,float)) else _pd.to_datetime(d)
            _months.append(dt.strftime('%Y-%m'))
            for idx, s in enumerate(_sites):
                v = raw2.iloc[ri, 1+idx]
                _traffic_total[s].append(float(v) if _pd.notna(v) else 0.0)
        except: pass
    result['traffic_months'] = _months; result['traffic_total'] = _traffic_total
    
    _onsite = {'DE':[],'FR':[],'IT':[]}
    for ri in range(1, len(raw2)):
        d = raw2.iloc[ri, 11]
        if _pd.isna(d): continue
        if isinstance(d, str) and ('合计' in d or '总计' in d): continue
        try:
            for idx, s in enumerate(['DE','FR','IT']):
                v = raw2.iloc[ri, 12+idx]
                _onsite[s].append(float(v) if _pd.notna(v) else 0.0)
        except: pass
    result['traffic_onsite'] = _onsite
    
    _blog = {'DE':[],'FR':[],'IT':[]}
    for ri in range(1, len(raw2)):
        d = raw2.iloc[ri, 16]
        if _pd.isna(d): continue
        if isinstance(d, str) and ('合计' in d or '总计' in d): continue
        try:
            for idx, s in enumerate(['DE','FR','IT']):
                v = raw2.iloc[ri, 17+idx]
                _blog[s].append(float(v) if _pd.notna(v) else 0.0)
        except: pass
    result['traffic_blog'] = _blog

def _parse_gsc_sheet(raw2, result):
    import pandas as _pd
    _gsc = {}
    
    _col0_targets = {
        'DE': [('DE', 0), ('FR', 7), ('ES', 14)],
        'IT': [('IT', 0), ('NL', 7)],
        'NO': [('NO', 0), ('SE', 7)],
        'FI': [('FI', 0), ('PL', 7)]
    }
    
    for _ri in range(len(raw2)):
        val0 = raw2.iloc[_ri, 0]
        if isinstance(val0, str) and val0.strip() in _col0_targets:
            _hr = _ri
            _sites = _col0_targets[val0.strip()]
            
            for _sc, _base in _sites:
                _m=[]; _tv=[]; _bv=[]; _lv=[]; _uv=[]; _ov=[]
                for _r_data in range(_hr+1, len(raw2)):
                    _v = raw2.iloc[_r_data, _base]
                    
                    if _pd.isna(_v) or (isinstance(_v, str) and ('总计' in _v or '非品牌' in _v or '品牌' in _v)):
                        break
                        
                    try:
                        if isinstance(_v, (int, float)):
                            _dt = _pd.to_datetime(_v, origin='1899-12-30', unit='D')
                        else:
                            _dt = _pd.to_datetime(_v)
                        _m.append(_dt.strftime('%Y-%m'))
                    except:
                        break
                    
                    def _safe_float(v):
                        try: return float(v) if _pd.notna(v) else 0.0
                        except: return 0.0
                    
                    _tv.append(_safe_float(raw2.iloc[_r_data, _base+1]))
                    _bv.append(_safe_float(raw2.iloc[_r_data, _base+2]))
                    _lv.append(_safe_float(raw2.iloc[_r_data, _base+3]))
                    _uv.append(_safe_float(raw2.iloc[_r_data, _base+4]))
                    _ov.append(_safe_float(raw2.iloc[_r_data, _base+5]))
                    
                _gsc[_sc] = {'months':_m,'total':_tv,'brand':_bv,'blog':_lv,'utm':_uv,'onsite':_ov}

    result['gsc_data'] = _gsc


# ==========================================
# 🎯 页面头部与数据持久化上传
# ==========================================
col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>SEO 月度数据对比</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>掌握SEO核心指标与各站点年度/月度表现</div>", unsafe_allow_html=True)
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
                
                if 'SEO月度流量数据汇总' in xls.sheet_names:
                    df_traffic_raw = pd.read_excel(xls, sheet_name='SEO月度流量数据汇总', header=None)
                    _parse_traffic_sheet(df_traffic_raw, data_dict)
                if 'SEO GSC月度点击数据汇总' in xls.sheet_names:
                    df_gsc_raw = pd.read_excel(xls, sheet_name='SEO GSC月度点击数据汇总', header=None)
                    _parse_gsc_sheet(df_gsc_raw, data_dict)
                pd.to_pickle(data_dict, CACHE_FILE)
                st.session_state['monthly_data'] = data_dict
                msg_area.success("✅ 数据解析成功！所有站点数据均已重新装载！")
            else:
                msg_area.error("❌ 表格结构不匹配，请检查。")
                
        except Exception as e:
            msg_area.error(f"❌ 解析失败: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

# ==========================================
# 📈 深度对比图表渲染
# ==========================================
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
        # 🎴 看板切换 (销售额 / 流量 / GSC)
        tab_selected = st.session_state.get('tab_selected', 'sales')
        col_ts1, col_ts2, col_ts3 = st.columns(3)
        with col_ts1:
            if st.button('销售额对比', key='tab_switch_sales', use_container_width=True, type='primary' if tab_selected == 'sales' else 'secondary'):
                st.session_state.tab_selected = 'sales'
                st.rerun()
        with col_ts2:
            if st.button('流量数据对比', key='tab_switch_traffic', use_container_width=True, type='primary' if tab_selected == 'traffic' else 'secondary'):
                st.session_state.tab_selected = 'traffic'
                st.rerun()
        with col_ts3:
            if st.button('GSC点击数据对比', key='tab_switch_gsc', use_container_width=True, type='primary' if tab_selected == 'gsc' else 'secondary'):
                st.session_state.tab_selected = 'gsc'
                st.rerun()
        st.markdown('<hr style="margin-top:6px;margin-bottom:20px;border-color:#e2e8f0;"/>', unsafe_allow_html=True)

        # ==========================================
        # 💰 销售额看板内容
        # ==========================================
        if tab_selected == 'sales':
            df_site_renamed = df_site.rename(columns={'Total': 'Total_Site'})
            df_merge = pd.merge(df_nb, df_all, on='Month', how='outer', suffixes=('_NB', '_All')).fillna(0)
            df_merge = pd.merge(df_merge, df_site_renamed, on='Month', how='left').fillna(0)
            df_merge = df_merge.sort_values('Month').reset_index(drop=True)
            df_merge['NB_Growth'] = df_merge['Total_NB'].pct_change() * 100
            df_merge['All_Growth'] = df_merge['Total_All'].pct_change() * 100
            df_merge['Site_Growth'] = df_merge['Total_Site'].pct_change() * 100

            # --- 🔥 新增：全站 2026 累计 KPI ---
            df_2026_sales = df_merge[df_merge['Month'] >= '2026-01']
            st.markdown("### 🏆 2026年累计核心指标 (全站大盘)")
            k1, k2, k3 = st.columns(3)
            with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">💰 2026 非品牌词总销售额</div><div class="kpi-value blue">${df_2026_sales["Total_NB"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🌐 2026 ALL SEO总销售额</div><div class="kpi-value purple">${df_2026_sales["Total_All"].sum():,.2f}</div></div>', unsafe_allow_html=True)
            with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🏪 2026 网站总销售额</div><div class="kpi-value orange">${df_2026_sales["Total_Site"].sum():,.2f}</div></div>', unsafe_allow_html=True)

            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
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
                fig3.update_layout(height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', ticksuffix="%", tickformat='.2f'))
                st.plotly_chart(fig3, use_container_width=True)

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
                        hovertemplate='<b>%{data.name} %{x}</b><br>非品牌词总计: $%{y:,.2f}<extra></extra>'
                    ))
                    
                fig1.update_layout(height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickmode='array', tickvals=list(range(1, 13)), ticktext=[f"{i}月" for i in range(1, 13)]), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$"))
                st.plotly_chart(fig1, use_container_width=True)

            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 📊 3. 【非品牌词】与【ALL SEO】销售额总计综合对比")
            with st.container(border=True):
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df_merge['Month'], y=df_merge['Total_NB'], mode='lines+markers', name='非品牌词销售额总计', line=dict(width=3, color='#0ea5e9'), marker=dict(size=8), hovertemplate='<b>%{x}</b><br>非品牌词: $%{y:,.2f}<extra></extra>'))
                fig2.add_trace(go.Scatter(x=df_merge['Month'], y=df_merge['Total_All'], mode='lines+markers', name='ALL SEO销售额总计', line=dict(width=3, color='#8b5cf6'), marker=dict(size=8), hovertemplate='<b>%{x}</b><br>ALL SEO: $%{y:,.2f}<extra></extra>'))
                fig2.update_layout(height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$"))
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🏪 4. 网站总销售额月度趋势")
            with st.container(border=True):
                fig_site = go.Figure()
                fig_site.add_trace(go.Scatter(x=df_merge['Month'], y=df_merge['Total_Site'], mode='lines+markers', name='网站总销售额', line=dict(width=3, color='#f59e0b'), marker=dict(size=8), hovertemplate='<b>%{x}</b><br>网站总销售额: $%{y:,.2f}<extra></extra>'))
                fig_site.update_layout(height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$"))
                st.plotly_chart(fig_site, use_container_width=True)
            
            st.markdown("<hr style='margin:32px 0;'/>", unsafe_allow_html=True)
            st.markdown("### 🏬 各站点详细销售额数据")
            st.markdown(get_nav_html('jump', '📍', '快速定位'), unsafe_allow_html=True)

            for target_site in ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']:
                st.markdown(f'<div id="jump-{target_site}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                with st.expander(f"📌 {target_site} 站点 — 销售详情", expanded=True):
                    
                    # --- 🔥 新增：分站点 2026 累计 KPI ---
                    nb_2026 = nb_detail[nb_detail['Month'] >= '2026-01'][target_site].sum()
                    all_2026 = all_detail[all_detail['Month'] >= '2026-01'][target_site].sum()
                    site_2026 = site_detail[site_detail['Month'] >= '2026-01'][target_site].sum()
                    
                    sc1, sc2, sc3 = st.columns(3)
                    with sc1: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 非品牌词 ({target_site})</div><div class="kpi-value blue" style="font-size:24px;">${nb_2026:,.2f}</div></div>', unsafe_allow_html=True)
                    with sc2: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 ALL SEO ({target_site})</div><div class="kpi-value purple" style="font-size:24px;">${all_2026:,.2f}</div></div>', unsafe_allow_html=True)
                    with sc3: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 总销售额 ({target_site})</div><div class="kpi-value orange" style="font-size:24px;">${site_2026:,.2f}</div></div>', unsafe_allow_html=True)
                    st.write("")
                    
                    x1, x2 = st.columns(2)
                    with x1:
                        st.markdown(f"**① {target_site} 销售额月度涨降幅对比**")
                        f = go.Figure()
                        for lb, src, cl in [(f'{target_site} NB', nb_detail[target_site], '#f43f5e'), 
                                            (f'{target_site} ALL', all_detail[target_site], '#10b981'), 
                                            (f'{target_site} Total', site_detail[target_site], '#6366f1')]:
                            g = src.pct_change() * 100
                            f.add_trace(go.Scatter(x=nb_detail['Month'], y=g, mode='lines+markers', name=lb, line=dict(width=2, color=cl), marker=dict(size=5)))
                        f.add_hline(y=0, line_dash="dash", line_color="#94a3b8")
                        f.update_layout(height=300, legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
                        st.plotly_chart(f, use_container_width=True)
                    with x2:
                        st.markdown(f"**② {target_site} 历年非品牌词销售额年度同比走势**")
                        ds = nb_detail[['Month', target_site]].copy()
                        ds['Date'] = pd.to_datetime(ds['Month'] + '-01')
                        ds['Year'] = ds['Date'].dt.year.astype(str)
                        ds['Mnum'] = ds['Date'].dt.month
                        f = go.Figure()
                        cs = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']
                        for i, y in enumerate(sorted(ds['Year'].unique())):
                            dy = ds[ds['Year'] == y].sort_values('Mnum')
                            f.add_trace(go.Scatter(x=dy['Mnum'], y=dy[target_site], mode='lines+markers', name=f'{y}年', line=dict(width=3, color=cs[i])))
                        f.update_layout(height=300, legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
                        st.plotly_chart(f, use_container_width=True)
                    
                    x3, x4 = st.columns(2)
                    with x3:
                        st.markdown(f"**③ {target_site} 非品牌词与 {target_site} ALL SEO 销售额综合对比**")
                        f = go.Figure()
                        f.add_trace(go.Scatter(x=nb_detail['Month'], y=nb_detail[target_site], mode='lines+markers', name=f'{target_site} NB'))
                        f.add_trace(go.Scatter(x=all_detail['Month'], y=all_detail[target_site], mode='lines+markers', name=f'{target_site} ALL'))
                        f.update_layout(height=300, legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
                        st.plotly_chart(f, use_container_width=True)
                    with x4:
                        st.markdown(f"**④ {target_site} 网站总销售额月度趋势**")
                        f = go.Figure()
                        f.add_trace(go.Scatter(x=site_detail['Month'], y=site_detail[target_site], mode='lines+markers', name=f'{target_site} Total'))
                        f.update_layout(height=300, legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
                        st.plotly_chart(f, use_container_width=True)

        # ==========================================
        # 🌊 流量看板内容
        # ==========================================
        elif tab_selected == 'traffic':
            traffic_months = st.session_state['monthly_data'].get('traffic_months', [])
            traffic_total = st.session_state['monthly_data'].get('traffic_total', {})
            traffic_onsite = st.session_state['monthly_data'].get('traffic_onsite', {})
            traffic_blog = st.session_state['monthly_data'].get('traffic_blog', {})

            if not traffic_months:
                st.warning("⚠️ 流量数据未找到。请检查Excel是否包含「SEO月度流量数据汇总」表单，或点击「清空本地缓存」后重新上传。")
            else:
                tf = pd.DataFrame(traffic_total)
                tf["Month"] = traffic_months
                tf["Total"] = tf[["DE","FR","ES","IT","NL","NO","SE","FI","PL"]].sum(axis=1)
                
                # --- 🔥 新增：全站 2026 累计 KPI ---
                df_2026_traffic = tf[tf['Month'] >= '2026-01']
                global_onsite_sum = sum([sum([v for i, v in enumerate(traffic_onsite[s]) if traffic_months[i] >= '2026-01']) for s in ['DE','FR','IT'] if s in traffic_onsite])
                global_blog_sum = sum([sum([v for i, v in enumerate(traffic_blog[s]) if traffic_months[i] >= '2026-01']) for s in ['DE','FR','IT'] if s in traffic_blog])
                
                st.markdown("### 🏆 2026年累计核心指标 (全站大盘)")
                k1, k2, k3 = st.columns(3)
                with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🚀 2026 全站总流量</div><div class="kpi-value green">{df_2026_traffic["Total"].sum():,.0f}</div></div>', unsafe_allow_html=True)
                with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🏠 2026 站内总流量 (三大主站)</div><div class="kpi-value orange">{global_onsite_sum:,.0f}</div></div>', unsafe_allow_html=True)
                with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">📝 2026 Blog总流量 (三大主站)</div><div class="kpi-value purple">{global_blog_sum:,.0f}</div></div>', unsafe_allow_html=True)

                st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
                
                st.markdown("### 🌐 全站流量汇总大盘 (不分站点)")
                
                st.markdown("#### 全站月度总流量趋势")
                with st.container(border=True):
                    f_agg_traffic = go.Figure()
                    f_agg_traffic.add_trace(go.Scatter(x=tf["Month"], y=tf["Total"], mode='lines+markers', name='全站总流量', line=dict(width=3, color='#2563EB'), marker=dict(size=8)))
                    f_agg_traffic.update_layout(height=350, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(type='category', tickangle=-45, showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                    st.plotly_chart(f_agg_traffic, use_container_width=True)

                st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 全站总流量年度同比 (各月对比)")
                with st.container(border=True):
                    tf["Date"] = pd.to_datetime(tf["Month"] + "-01")
                    tf["Year"] = tf["Date"].dt.year.astype(str)
                    tf["Mnum"] = tf["Date"].dt.month
                    f_yoy = go.Figure()
                    cs_t = ["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                    for i, y in enumerate(sorted(tf["Year"].unique())):
                        dy = tf[tf["Year"] == y].sort_values("Mnum")
                        f_yoy.add_trace(go.Scatter(x=dy["Mnum"], y=dy["Total"], mode="lines+markers", name=f'{y}年', line=dict(width=3, color=cs_t[i])))
                    f_yoy.update_layout(height=350, hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickmode="array", tickvals=list(range(1,13)), ticktext=[f'{i}月' for i in range(1,13)]),
                        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"))
                    st.plotly_chart(f_yoy, use_container_width=True)

                st.markdown("<hr style='margin:32px 0; border-color:#e2e8f0;'/>", unsafe_allow_html=True)
                
                st.markdown("### 🏬 各站点流量数据对比与详情")
                
                st.markdown("#### 1. 各站点月度总流量对比趋势 (2025.01 ~ 至今)")
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

                st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                st.markdown("#### 2. 各站点独立数据下钻")
                st.markdown(get_nav_html('tjump', '🌊', '流量站点'), unsafe_allow_html=True)
                
                for _tsite in ["DE","FR","ES","IT","NL","NO","SE","FI","PL"]:
                    st.markdown(f'<div id="tjump-{_tsite}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                    with st.expander(f"📌 {_tsite} 站点 — 流量详情", expanded=True):
                        
                        # --- 🔥 新增：分站点 2026 累计 KPI ---
                        t_2026 = sum([v for m, v in zip(traffic_months, traffic_total[_tsite]) if m >= '2026-01'])
                        o_2026 = sum([v for m, v in zip(traffic_months, traffic_onsite.get(_tsite, [])) if m >= '2026-01']) if _tsite in traffic_onsite else 0
                        b_2026 = sum([v for m, v in zip(traffic_months, traffic_blog.get(_tsite, [])) if m >= '2026-01']) if _tsite in traffic_blog else 0
                        
                        sc1, sc2, sc3 = st.columns(3)
                        with sc1: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 总流量 ({_tsite})</div><div class="kpi-value green" style="font-size:24px;">{t_2026:,.0f}</div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 站内流量 ({_tsite})</div><div class="kpi-value orange" style="font-size:24px;">{o_2026:,.0f}</div></div>', unsafe_allow_html=True)
                        with sc3: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 Blog流量 ({_tsite})</div><div class="kpi-value purple" style="font-size:24px;">{b_2026:,.0f}</div></div>', unsafe_allow_html=True)
                        st.write("")
                        
                        x1,x2=st.columns(2)
                        with x1:
                            st.markdown(f"**① {_tsite} 月度总流量趋势**")
                            f_t=go.Figure()
                            f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_total[_tsite],mode="lines+markers",name=f'{_tsite} 总流量',line=dict(width=2,color="#3b82f6"),marker=dict(size=6)))
                            f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                            st.plotly_chart(f_t,use_container_width=True)
                        with x2:
                            st.markdown(f"**② {_tsite} 流量年度同比**")
                            tdf=pd.DataFrame({'Month':traffic_months,_tsite:traffic_total[_tsite]})
                            tdf['Date']=pd.to_datetime(tdf['Month']+'-01')
                            tdf['Year']=tdf['Date'].dt.year.astype(str)
                            tdf['Mnum']=tdf['Date'].dt.month
                            f_t=go.Figure();cs_t=["#10b981","#3b82f6","#f59e0b","#8b5cf6"]
                            for i,y in enumerate(sorted(tdf['Year'].unique())):
                                dy=tdf[tdf['Year']==y].sort_values('Mnum')
                                f_t.add_trace(go.Scatter(x=dy['Mnum'],y=dy[_tsite],mode="lines+markers",name=f'{y}年',line=dict(width=2,color=cs_t[i])))
                            f_t.update_xaxes(tickvals=list(range(1,13)),ticktext=[f'{i}月' for i in range(1,13)])
                            f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",yanchor="top",y=-0.2,xanchor="center",x=0.5))
                            st.plotly_chart(f_t,use_container_width=True)
                        
                        x3,x4=st.columns(2)
                        with x3:
                            st.markdown(f"**③ {_tsite} 站内流量趋势**")
                            if _tsite in traffic_onsite and any(v > 0 for v in traffic_onsite[_tsite]):
                                f_t=go.Figure()
                                f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_onsite[_tsite],mode="lines+markers",name=f'{_tsite} 站内',line=dict(width=2,color="#f59e0b"),marker=dict(size=6)))
                                f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                                st.plotly_chart(f_t,use_container_width=True)
                            else:
                                st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无站内流量数据</div>",unsafe_allow_html=True)
                        with x4:
                            st.markdown(f"**④ {_tsite} Blog流量趋势**")
                            if _tsite in traffic_blog and any(v > 0 for v in traffic_blog[_tsite]):
                                f_t=go.Figure()
                                f_t.add_trace(go.Scatter(x=traffic_months,y=traffic_blog[_tsite],mode="lines+markers",name=f'{_tsite} Blog',line=dict(width=2,color="#8b5cf6"),marker=dict(size=6)))
                                f_t.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(type="category",tickangle=-45,nticks=12),yaxis=dict(showgrid=True,gridcolor="#f1f5f9"))
                                st.plotly_chart(f_t,use_container_width=True)
                            else:
                                st.markdown("<div style='color:#94a3b8;text-align:center;padding:40px 0;'>暂无Blog流量数据</div>",unsafe_allow_html=True)

        # ==========================================
        # 🖱️ GSC 点击数据看板
        # ==========================================
        elif tab_selected == 'gsc':
            gsc_data = st.session_state['monthly_data'].get('gsc_data', {})
            if not gsc_data:
                st.warning("⚠️ GSC 点击数据未找到，请确认Excel包含「SEO GSC月度点击数据汇总」表单。")
            else:
                all_gsc_records = []
                for site, d2 in gsc_data.items():
                    for i, m in enumerate(d2['months']):
                        if i < len(d2['total']):
                            all_gsc_records.append({
                                'Site': site,
                                'Month': m,
                                'Total': d2['total'][i],
                                'Brand': d2['brand'][i] if i < len(d2['brand']) else 0,
                                'Blog': d2['blog'][i] if i < len(d2['blog']) else 0,
                                'Onsite': d2['onsite'][i] if i < len(d2['onsite']) else 0
                            })
                
                if all_gsc_records:
                    df_gsc_all = pd.DataFrame(all_gsc_records)
                    df_gsc_agg = df_gsc_all.groupby('Month').sum().reset_index().sort_values('Month')
                    
                    # --- 🔥 新增：全站 2026 累计 KPI ---
                    df_2026_gsc = df_gsc_agg[df_gsc_agg['Month'] >= '2026-01']
                    st.markdown("### 🏆 2026年累计核心指标 (全站大盘)")
                    k1, k2, k3 = st.columns(3)
                    with k1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🖱️ 2026 全站总点击</div><div class="kpi-value blue">{df_2026_gsc["Total"].sum():,.0f}</div></div>', unsafe_allow_html=True)
                    with k2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🏷️ 2026 品牌词点击</div><div class="kpi-value purple">{df_2026_gsc["Brand"].sum():,.0f}</div></div>', unsafe_allow_html=True)
                    with k3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">📝 2026 Blog点击</div><div class="kpi-value orange">{df_2026_gsc["Blog"].sum():,.0f}</div></div>', unsafe_allow_html=True)
                    
                    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
                    
                    st.markdown("### 🌐 全站 GSC 汇总大盘 (不分站点)")
                    st.markdown("#### 全站 GSC 总点击走势")
                    with st.container(border=True):
                        f_agg_total = go.Figure()
                        f_agg_total.add_trace(go.Scatter(x=df_gsc_agg['Month'], y=df_gsc_agg['Total'], mode='lines+markers', name='全站总点击', line=dict(width=3, color='#2563EB'), marker=dict(size=8)))
                        f_agg_total.update_layout(height=350, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(type='category', tickangle=-45, showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                        st.plotly_chart(f_agg_total, use_container_width=True)
                    
                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                    
                    st.markdown("#### 全站总点击年度同比 (各月对比)")
                    with st.container(border=True):
                        df_gsc_yoy = df_gsc_agg.copy()
                        df_gsc_yoy['Date'] = pd.to_datetime(df_gsc_yoy['Month'] + '-01')
                        df_gsc_yoy['Year'] = df_gsc_yoy['Date'].dt.year.astype(str)
                        df_gsc_yoy['Mnum'] = df_gsc_yoy['Date'].dt.month
                        
                        f_gsc_yoy = go.Figure()
                        cs_gsc_yoy = ["#10b981", "#f59e0b", "#3b82f6", "#8b5cf6"]
                        
                        for i, y in enumerate(sorted(df_gsc_yoy['Year'].unique())):
                            dy = df_gsc_yoy[df_gsc_yoy['Year'] == y].sort_values('Mnum')
                            f_gsc_yoy.add_trace(go.Scatter(
                                x=dy['Mnum'], y=dy['Total'], 
                                mode="lines+markers", name=f'{y}年', 
                                line=dict(width=3, color=cs_gsc_yoy[i % len(cs_gsc_yoy)]),
                                marker=dict(size=8)
                            ))
                            
                        f_gsc_yoy.update_layout(
                            height=350, hovermode="x unified", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=10, b=10),
                            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                            xaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickmode="array", tickvals=list(range(1,13)), ticktext=[f'{i}月' for i in range(1,13)]),
                            yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
                        )
                        st.plotly_chart(f_gsc_yoy, use_container_width=True)

                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                    
                    st.markdown("#### 全站各细分维度点击走势")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        with st.container(border=True):
                            st.markdown("**① 品牌词总点击**")
                            f_agg_brand = go.Figure()
                            f_agg_brand.add_trace(go.Scatter(x=df_gsc_agg['Month'], y=df_gsc_agg['Brand'], mode='lines+markers', name='全站品牌词', line=dict(width=2, color='#EF4444'), marker=dict(size=6)))
                            f_agg_brand.update_layout(height=280, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(type='category', tickangle=-45, showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                            st.plotly_chart(f_agg_brand, use_container_width=True)
                    with c2:
                        with st.container(border=True):
                            st.markdown("**② Blog 总点击**")
                            f_agg_blog = go.Figure()
                            f_agg_blog.add_trace(go.Scatter(x=df_gsc_agg['Month'], y=df_gsc_agg['Blog'], mode='lines+markers', name='全站 Blog', line=dict(width=2, color='#F59E0B'), marker=dict(size=6)))
                            f_agg_blog.update_layout(height=280, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(type='category', tickangle=-45, showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                            st.plotly_chart(f_agg_blog, use_container_width=True)
                    with c3:
                        with st.container(border=True):
                            st.markdown("**③ 站内总点击**")
                            f_agg_onsite = go.Figure()
                            f_agg_onsite.add_trace(go.Scatter(x=df_gsc_agg['Month'], y=df_gsc_agg['Onsite'], mode='lines+markers', name='全站站内', line=dict(width=2, color='#10B981'), marker=dict(size=6)))
                            f_agg_onsite.update_layout(height=280, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(type='category', tickangle=-45, showgrid=True, gridcolor='#f1f5f9'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
                            st.plotly_chart(f_agg_onsite, use_container_width=True)

                    st.markdown("<hr style='margin:32px 0; border-color:#e2e8f0;'/>", unsafe_allow_html=True)
                
                st.markdown("### 🏬 各站点 GSC 数据对比与详情")
                st.markdown("#### 1. 各站点GSC总点击趋势 (2024.06 ~ 至今)")
                with st.container(border=True):
                    _all_months = sorted(set().union(*[set(gsc_data[s]['months']) for s in ['DE','FR','ES','IT','NL','NO','SE','FI','PL'] if s in gsc_data]))
                    f_g=go.Figure()
                    _gsc_colors = ['#3b82f6','#ef4444','#f59e0b','#22c55e','#06b6d4','#ec4899','#8b5cf6','#14b8a6','#f97316']
                    for _i,_s in enumerate(['DE','FR','ES','IT','NL','NO','SE','FI','PL']):
                        _gd = gsc_data.get(_s, {})
                        if _gd:
                            f_g.add_trace(go.Scatter(x=_gd['months'],y=_gd['total'],mode='lines+markers',name=f'{_s} 总点击',line=dict(width=2,color=_gsc_colors[_i]),marker=dict(size=5)))
                    f_g.update_layout(height=400,hovermode='x unified',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=20,r=20,t=20,b=20),
                        legend=dict(orientation='h',yanchor='top',y=-0.15,xanchor='center',x=0.5),
                        xaxis=dict(showgrid=True,gridcolor='#f1f5f9',type='category',tickangle=-45,nticks=18),
                        yaxis=dict(showgrid=True,gridcolor='#f1f5f9'))
                    st.plotly_chart(f_g,use_container_width=True)
                
                st.markdown(get_nav_html('gjump', '🖱️', 'GSC站点'), unsafe_allow_html=True)
                
                for _s2 in ['DE','FR','ES','IT','NL','NO','SE','FI','PL']:
                    _d2 = gsc_data.get(_s2, {})
                    if not _d2: continue
                    st.markdown(f'<div id="gjump-{_s2}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
                    with st.expander(f"📌 GSC {_s2} 站点 — 点击详情", expanded=True):
                        
                        # --- 🔥 新增：分站点 2026 累计 KPI ---
                        g_t_2026 = sum([v for m, v in zip(_d2['months'], _d2['total']) if m >= '2026-01'])
                        g_b_2026 = sum([v for m, v in zip(_d2['months'], _d2['brand']) if m >= '2026-01'])
                        g_l_2026 = sum([v for m, v in zip(_d2['months'], _d2['blog']) if m >= '2026-01'])
                        
                        sc1, sc2, sc3 = st.columns(3)
                        with sc1: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 总点击 ({_s2})</div><div class="kpi-value blue" style="font-size:24px;">{g_t_2026:,.0f}</div></div>', unsafe_allow_html=True)
                        with sc2: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 品牌词 ({_s2})</div><div class="kpi-value purple" style="font-size:24px;">{g_b_2026:,.0f}</div></div>', unsafe_allow_html=True)
                        with sc3: st.markdown(f'<div class="kpi-card" style="padding:15px;"><div class="kpi-title">2026 Blog ({_s2})</div><div class="kpi-value orange" style="font-size:24px;">{g_l_2026:,.0f}</div></div>', unsafe_allow_html=True)
                        st.write("")
                        
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
