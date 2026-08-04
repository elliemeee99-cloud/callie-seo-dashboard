import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(page_title="AI 来源数据监控", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
.stApp{background-color:#F8FAFC!important}
.block-container{padding-top:.8rem!important;max-width:96%!important;padding-left:140px!important}
h1, h2, h3, h4, h5, h6 {color:#111827!important}
hr{border-color:#E5E7EB!important;margin:8px 0!important}
.stButton button{height:38px!important;border-radius:10px!important;font-size:14px!important;font-weight:600!important;}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:12px!important;border:1px solid #E5E7EB!important;background-color:#FFFFFF;box-shadow:0 1px 3px rgba(0,0,0,.06)!important;padding:16px!important;margin-bottom:12px!important}

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

# --- 导航栏 (新增 AI 来源数据模块) ---
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

# --- 核心逻辑 ---
col_h_left, col_h_right = st.columns([1.8, 1.2])
with col_h_left:
    st.markdown("<div style='font-size:30px;font-weight:700;color:#111827;letter-spacing:-.03em;margin-bottom:2px;'>🤖 AI 来源数据监控</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#6B7280;font-size:14px;margin-bottom:16px;'>直连 Google Sheets 实时监控各大 AI 引擎数据表现</div>", unsafe_allow_html=True)
with col_h_right:
    st.markdown(f"<div style='color:#9CA3AF;font-size:11px;text-align:right;margin-bottom:2px;line-height:1;'>更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    if st.button("🔄 获取最新数据", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# 定义直连抓取函数
@st.cache_data(ttl=600)  # 默认缓存 10 分钟，防止频繁请求被拦截
def load_google_sheet(url):
    # 将常规编辑链接转换为 CSV 导出链接
    csv_url = url.replace("/edit?gid=", "/export?format=csv&gid=").split("#")[0]
    return pd.read_csv(csv_url)

target_url = "https://docs.google.com/spreadsheets/d/1cXuEZoa8o6fF3H9ycMIgvd3iKKY1tvmBrZHl7gnw2Gk/edit?gid=0#gid=0"

try:
    with st.spinner("正在从 Google Sheets 实时拉取底层数据..."):
        df = load_google_sheet(target_url)
    
    st.success("✅ 数据拉取成功！无需手动上传表格，实时与云端保持同步。")
    
    st.markdown("### 📋 原始数据清洗池")
    st.dataframe(df, width="stretch")
    
    st.markdown("### 📊 智能多维分析预览")
    st.info("💡 系统已自动嗅探表头与数据类型，并生成了以下快速预览。")
    
    # 动态匹配列类型，防止硬编码导致报错
    num_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    if num_cols and cat_cols:
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.markdown(f"**指标概览：{cat_cols[0]} 🆚 {num_cols[0]}**")
                fig1 = px.bar(df, x=cat_cols[0], y=num_cols[0], color=cat_cols[0], template="plotly_white")
                fig1.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig1, width="stretch")
                
        with col2:
            with st.container(border=True):
                df_agg = df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index()
                st.markdown(f"**大盘占比分布：{cat_cols[0]}**")
                fig2 = px.pie(df_agg, names=cat_cols[0], values=num_cols[0], template="plotly_white", hole=0.4)
                fig2.update_layout(margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig2, width="stretch")
    else:
        st.warning("⚠️ 表格中的数据格式不够明确，暂时无法自动生成智能图表。")

except Exception as e:
    st.error(f"❌ 读取 Google Sheets 失败，请检查以下设置：")
    st.markdown("1. 确保该 Google Sheet 的分享权限已设置为**「知道链接的人均可查看 (Anyone with the link can view)」**。")
    st.markdown("2. 表格没有被 Google 的防火墙限制访问。")
    st.code(str(e))
