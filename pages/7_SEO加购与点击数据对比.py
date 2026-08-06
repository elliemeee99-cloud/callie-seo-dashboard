import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="加购与点击数据对比", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 UI 样式与左侧悬浮导航
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:140px!important}
h1, h2, h3, h4, h5, h6 {color:#111827!important}
p {color:#6B7280!important;font-size:14px!important}
hr{border-color:#E5E7EB!important;margin:8px 0!important}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px!important;border:1px solid #E5E7EB!important;background-color:#FFFFFF;box-shadow:0 1px 3px rgba(0,0,0,.06)!important;padding:16px!important;margin-bottom:12px!important}

/* KPI 卡片 */
.kpi-card {background: #fff; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); text-align: center; height: 100%;}
.kpi-title {font-size: 14px; color: #64748B; font-weight: 600; margin-bottom: 8px;}
.kpi-value {font-size: 30px; font-weight: 700; color: #0F172A; margin: 0;}
.kpi-value.blue {color: #2563EB;}
.kpi-value.green {color: #10B981;}
.kpi-value.purple {color: #8B5CF6;}
.kpi-value.orange {color: #F59E0B;}

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
[data-testid="stPageLink-NavLink"] p{font-weight:600!important;color:#64748B!important;font-size:14px!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"]{border-bottom:2px solid #2563EB!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"] p{color:#2563EB!important;font-weight:600!important}
.back-to-top{position:fixed;bottom:32px;right:32px;background:#2563EB;color:#fff!important;width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;text-decoration:none!important;z-index:99999}
.back-to-top:hover{background:#1D4ED8}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
</style>""", unsafe_allow_html=True)

# 导航辅助组件
def get_nav_html(prefix, icon, title):
    sites = [('DE', '🇩🇪', '#4285F4'), ('FR', '🇫🇷', '#EA4335'), ('ES', '🇪🇸', '#FBBC05'),
             ('IT', '🇮🇹', '#34A853'), ('NL', '🇳🇱', '#4285F4'), ('NO', '🇳🇴', '#EA4335'),
             ('SE', '🇸🇪', '#FBBC05'), ('FI', '🇫🇮', '#34A853'), ('PL', '🇵🇱', '#4285F4'),
             ('EN', '🇬🇧', '#111827')]
    links = ""
    for site, flag, color in sites:
        links += f'<a href="#{prefix}-{site}" style="border-left:4px solid {color};"><span class="c-flag">{flag}</span><span class="c-name" style="background:{color};">{site}</span></a>'
    return f'<div class="country-nav"><div style="font-size:12px;font-weight:800;color:#1e293b;margin-bottom:12px;display:flex;align-items:center;gap:4px;"><span style="font-size:14px;">{icon}</span> {title}</div><div style="display:flex;flex-direction:column;">{links}</div></div>'

# --- 顶部导航栏 ---
_nc = st.columns([0.1, 1, 1, 1, 1, 1, 1, 1, 1.2, 0.1])
with _nc[0]: pass
with _nc[1]: st.page_link("app.py", label="App 首页", icon="🏠")
with _nc[2]: st.page_link("pages/1_SEO目标概览.py", label="目标概览", icon="🎯")
with _nc[3]: st.page_link("pages/2_SEO站点明细.py", label="站点明细", icon="🗄️")
with _nc[4]: st.page_link("pages/3_SEO需求管理.py", label="需求管理", icon="📋")
with _nc[5]: st.page_link("pages/4_SEO重点事件记录.py", label="事件记录", icon="📅")
with _nc[6]: st.page_link("pages/5_SEO月度数据对比.py", label="月度对比", icon="📊")
with _nc[7]: st.page_link("pages/6_AI来源数据.py", label="AI 来源", icon="🤖")
with _nc[8]: st.page_link("pages/7_SEO加购与点击数据对比.py", label="加购与转化", icon="🛒")
st.markdown("<div style='height:1px;background:#E2E8F0;margin:2px 0 14px 0;'></div>", unsafe_allow_html=True)
st.markdown("<a href='#top-anchor' class='back-to-top' title='\u56de\u5230\u9876\u90e8'>\u2191</a>", unsafe_allow_html=True)

# --- 页面头部 ---
col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>🛒 SEO 加购与点击对比大盘</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>直连底层表格，深度比对 2025 vs 2026 前端引流与后端转化 (加购/订单) 表现</div>", unsafe_allow_html=True)
with col_h_right:
    st.markdown(f"<div style='color:#9CA3AF;font-size:11px;text-align:right;margin-bottom:2px;line-height:1;'>最后同步：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    if st.button("🔄 从云端刷新数据", type="primary"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# ⚙️ 数据直连与结构嗅探
# ==========================================
@st.cache_data(ttl=600)
def fetch_raw_data():
    url = "https://docs.google.com/spreadsheets/d/1CUaU-_F7sz9OkqGSblVfjODihzMiKPVvEGNDZD6mKVA/export?format=csv&gid=0"
    try:
        return pd.read_csv(url, header=None)
    except Exception as e:
        raise RuntimeError(f"CSV read failed: {e}")

try:
    with st.spinner("🚀 正在通过 API 直连 Google Sheets..."):
        df_raw = fetch_raw_data()
        
    st.info("✅ 成功连接 Google Sheets！正在进行底层数据结构嗅探...")
    
    st.markdown("👇 **诊断器预览：这是从云端抓取到的【原始数据前 15 行】**")
    st.dataframe(df_raw.head(15), width="stretch")
    
    st.markdown("<hr style='margin:32px 0; border-color:#e2e8f0;'/>", unsafe_allow_html=True)
    
    # ------------------------------------------
    # 看板骨架搭建展示区
    # ------------------------------------------
    st.markdown("### 🏆 2026 vs 2025 同期转化对决 (全站大盘)")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🛒 2026 累计加购数</div><div class="kpi-value blue">读取排版中...</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="kpi-card"><div class="kpi-title">📦 2026 累计订单数</div><div class="kpi-value green">读取排版中...</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="kpi-card"><div class="kpi-title">🖱️ 2026 各项点击总计</div><div class="kpi-value purple">读取排版中...</div></div>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    
    st.markdown("### 🏬 各分站点 YoY 同比下钻")
    st.markdown(get_nav_html('site', '📍', '分站导航'), unsafe_allow_html=True)
    
    st.markdown(f'<div id="site-DE" style="position:relative;top:-100px;"></div>', unsafe_allow_html=True)
    with st.expander("📌 DE 德国站 — 加购与点击转化趋势 (UI 占位)", expanded=True):
        st.write("⏳ 等待自动匹配【加购数】、【订单数】与【各项点击】的数据列后，这里将生成独占全宽的折线对比图...")

except Exception as e:
    st.error(f"❌ 读取异常：{e}")
