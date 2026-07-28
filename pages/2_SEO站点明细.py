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
# 🎨 UI Refinements V3 - Enterprise SaaS Style (修复左侧导航过宽问题)
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
/* 🔥 核心修复：把左边距从 270px 缩小到 140px，给右侧图表释放巨大空间 */
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:140px!important}
h1{font-size:30px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.02em!important;margin-bottom:0px!important;}
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

/* Expander (下拉面板) 样式 */
[data-testid="stExpander"]{border:1px solid #EEF2F6!important;border-radius:16px!important;background-color:#ffffff!important;box-shadow:0 4px 20px rgba(0,0,0,0.02)!important;margin-bottom:24px!important;overflow:hidden}
[data-testid="stExpander"] summary{padding:20px 24px!important;background-color:#ffffff!important}
[data-testid="stExpander"] summary p{font-size:18px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.5px}

/* 🔥 核心修复：左侧浮动导航菜单，宽度压缩为 100px，瘦身拉长 */
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

_nc = st.columns([0.1, 1, 1, 1, 1, 1, 1, 0.1])
with _nc[0]: pass
with _nc[1]: st.page_link("app.py", label="App 首页", icon="🏠")
with _nc[2]: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with _nc[3]: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with _nc[4]: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with _nc[5]: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
with _nc[6]: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比", icon="📊")
st.markdown("<div style='height:1px;background:#E2E8F0;margin:2px 0 14px 0;'></div>", unsafe_allow_html=True)
st.markdown("<a href='#top-anchor' class='back-to-top' title='\u56de\u5230\u9876\u90e8'>\u2191</a>", unsafe_allow_html=True)

# ==========================================
# ⚙️ 辅助模块：左侧挂件生成器 (补回丢失的国旗)
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

# ==========================================
# 🎯 页面头部结构与排版优化 (Fix UI)
# ==========================================
col_title, col_actions = st.columns([1.5, 1])
with col_title:
    st.markdown("# 🗄️ SEO 站点明细")
    st.markdown("<p style='color:#6B7280; font-size:15px; margin-top:-12px; margin-bottom:16px;'>全景掌握各个独立站点的详细数据波动情况</p>", unsafe_allow_html=True)
    
with col_actions:
    st.markdown(f"<div style='text-align:right; font-size:12px; color:#9CA3AF; margin-bottom: 8px;'>最后更新：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    btn1, btn2, btn3 = st.columns([1.2, 1, 1])
    with btn2:
        if st.button("✨ 清空缓存", use_container_width=True):
            if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
            if 'monthly_data' in st.session_state: del st.session_state['monthly_data']
            st.rerun()
    with btn3:
        if st.button("🔄 同步数据", type="primary", use_container_width=True):
            pass 

# ==========================================
# 📥 数据持久化上传模块
# ==========================================
with st.container(border=True):
    uploaded_file = st.file_uploader("📂 请在此上传最新版的《SEO 整体数据情况》Excel 台账", type=['xlsx', 'xls'])
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
                pd.to_pickle(data_dict, CACHE_FILE)
                st.session_state['monthly_data'] = data_dict
                msg_area.success("✅ 数据报表完美解析！已识别三张子表，含9站点逐月明细。")
            else:
                msg_area.error("❌ 表格结构未能精准匹配！请确保三张表头分别带有'非品牌'、'ALL'与'网站总销售额'字样，并且包含'总计'列。")
                
        except Exception as e:
            msg_area.error(f"❌ 解析失败，请检查文件格式。报错详情: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

# ==========================================
# 📈 站点明细图表渲染
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
        st.markdown("### 🏬 各站点详细数据")
        
        # 🔥 插入左侧精简悬浮窗 (包含国旗)
        st.markdown(get_nav_html('jump', '📍', '快速定位'), unsafe_allow_html=True)

        for target_site in ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']:
            st.markdown(f'<div id="jump-{target_site}" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
            with st.expander(f"📌 {target_site} 站点 — 4维度详情", expanded=True):
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
else:
    st.info("👈 您的缓存池为空。请在上方上传最新整理好的《SEO 整体数据情况》台账以激活对比引擎。")
