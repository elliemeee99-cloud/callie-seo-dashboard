import streamlit as st
import pandas as pd
import datetime
import os

# ==========================================
# 网页基础设置 (默认折叠原生侧边栏)
# ==========================================
st.set_page_config(page_title="SEO需求管理", page_icon="📋", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# ⚙️ 核心数据字段配置与本地存储路径
# ==========================================
COL_CATEGORY = "需求分类"  
COL_ONLINE_DATE = "需求上线时间"
# 强制使用新版缓存名称，确保数据稳定固化
CACHE_FILE = "seo_requirements_cache_v2.pkl"

# ==========================================
# 🎨 现代 SaaS 顶级视觉重构 (统一全局风格)
# ==========================================
st.markdown("""<div id="top-anchor"></div>""", unsafe_allow_html=True)
st.markdown("""<style>
/* 1. 整体极简浅灰背景 */
.stApp { 
    background-color: #F8FAFC !important; 
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}

/* 2. 页面容器留白 */
.block-container { 
    padding-top: 1rem !important; 
    max-width: 96% !important; 
}

h1{font-size:30px!important;font-weight:800!important;color:#111827!important;letter-spacing:-0.02em!important;margin-bottom:0px!important;}
h2{font-size:24px!important;font-weight:700!important;color:#111827!important}
h3{font-size:20px!important;font-weight:700!important;color:#111827!important}
p{color:#6B7280!important;font-size:14px!important}
hr{border-color:#E5E7EB!important;margin:8px 0!important}

/* 按钮统一风格 */
.stButton button{height:38px!important;border-radius:10px!important;font-size:14px!important;font-weight:600!important;padding:0 16px!important}
.stButton button[kind="primary"]{background:#EFF6FF!important;color:#1D4ED8!important;border:1px solid #BFDBFE!important}
.stButton button[kind="primary"]:hover{background:#DBEAFE!important;border-color:#93C5FD!important;color:#1E40AF!important}
.stButton button[kind="secondary"]{background:#FFFFFF!important;color:#374151!important;border:1px solid #D1D5DB!important}
.stButton button[kind="secondary"]:hover{background:#F9FAFB!important;border-color:#9CA3AF!important;color:#111827!important}

/* 统一卡片容器 */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; border: 1px solid #e2e8f0 !important; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); padding: 20px; }

/* 顶部看板切换 Tabs 样式 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] { gap: 12px !important; border-bottom: none !important; }
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { display: none !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"] { background-color: #f1f5f9 !important; border-radius: 8px !important; padding: 12px 28px !important; border: none !important; box-shadow: none !important; transition: all 0.3s ease; }
div[data-testid="stTabs"] button[data-baseweb="tab"] p { color: #64748b !important; font-weight: 700 !important; font-size: 17px !important; margin: 0 !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] { background-color: #2563eb !important; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3) !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p { color: #ffffff !important; }

/* 顶部导航 Tabs (极简下划线风格) */
[data-testid="stPageLink-NavLink"]{background:transparent!important;border:none!important;border-radius:0!important;padding:8px 14px!important;border-bottom:2px solid transparent!important;margin-bottom:-1px;display:flex!important;justify-content:center!important;align-items:center!important;white-space:nowrap}
[data-testid="stPageLink-NavLink"]:hover{background:#F1F5F9!important}
[data-testid="stPageLink-NavLink"] p{font-weight:600!important;color:#64748B!important;font-size:16px!important;margin:0!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"]{border-bottom:2px solid #2563EB!important}
[aria-current="page"] [data-testid="stPageLink-NavLink"] p{color:#2563EB!important;font-weight:600!important}

.stAlert{border-radius:10px!important;padding:10px 14px!important;margin-bottom:8px!important}
.back-to-top{position:fixed;bottom:32px;right:32px;background:#2563EB;color:#fff!important;width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;text-decoration:none!important;z-index:99999}
.back-to-top:hover{background:#1D4ED8}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
[data-testid="stHeader"]{display:none!important}
</style>""", unsafe_allow_html=True)

# ==========================================
# 🧭 统一横向导航栏 
# ==========================================
_nc = st.columns([0.1, 1, 1, 1, 1, 1, 1, 0.1])
with _nc[0]: pass
with _nc[1]: st.page_link("app.py", label="App 首页", icon="🏠")
with _nc[2]: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with _nc[3]: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with _nc[4]: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with _nc[5]: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
with _nc[6]: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比", icon="📊")
st.markdown("<div style='height:1px;background:#E2E8F0;margin:2px 0 14px 0;'></div>", unsafe_allow_html=True)
st.markdown("<a href='#top-anchor' class='back-to-top' title='回到顶部'>↑</a>", unsafe_allow_html=True)

# ==========================================
# 💎 看板卡片渲染函数 (强制抹平换行，防乱码)
# ==========================================
def render_task_cards(df_subset, status="ongoing"):
    if df_subset.empty: return ""
    html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; margin-bottom: 24px;">'
    for _, row in df_subset.iterrows():
        title = str(row.get('需求标题', '无标题'))
        desc = str(row.get('需求详情描述', ''))
        if len(desc) > 80: desc = desc[:80] + "..."
        req_date = str(row.get('需求提出日期', ''))
        online_date = str(row.get(COL_ONLINE_DATE, ''))

        border_color = "#3b82f6" if status == "ongoing" else "#10b981"
        bg_color = "#eff6ff" if status == "ongoing" else "#ecfdf5"
        status_icon = "🏃" if status == "ongoing" else "✅"

        card_html = f"""
        <div draggable="true" style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid {border_color}; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); cursor: grab; transition: transform 0.2s;" ondragstart="this.style.opacity='0.5';" ondragend="this.style.opacity='1';">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="background: {bg_color}; color: {border_color}; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700;">{status_icon} {row.get(COL_CATEGORY, '需求')}</span>
                <span style="font-size: 12px; color: #64748b; font-weight: 500;">提出: {req_date}</span>
            </div>
            <div style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px; line-height: 1.4;">{title}</div>
            <div style="font-size: 13px; color: #64748b; line-height: 1.5; margin-bottom: 16px;">{desc}</div>
            <div style="font-size: 12px; color: #94a3b8; text-align: right; border-top: 1px dashed #f1f5f9; padding-top: 12px;">
                <span style="font-weight: 600; color: {'#3b82f6' if status == 'ongoing' else '#10b981'};">上线时间: {online_date if online_date else '待定'}</span>
            </div>
        </div>
        """
        html += card_html
    html += '</div>'
    
    return html.replace('\n', '').replace('\r', '')

# ==========================================
# 🎯 页面头部结构与排版优化 (Fix UI)
# ==========================================
col_title, col_actions = st.columns([1.5, 1])
with col_title:
    st.markdown("# 📋 SEO 需求管理")
    st.markdown("<p style='color:#6B7280; font-size:15px; margin-top:-12px; margin-bottom:16px;'>统一管理产品与数据中心需求状态，追踪研发跟进闭环</p>", unsafe_allow_html=True)
    
with col_actions:
    st.markdown(f"<div style='text-align:right; font-size:12px; color:#9CA3AF; margin-bottom: 8px;'>最后访问：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    btn1, btn2, btn3 = st.columns([1.2, 1, 1])
    with btn2:
        if st.button("✨ 清空缓存", use_container_width=True):
            if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
            if 'req_data' in st.session_state: del st.session_state['req_data']
            st.rerun()
    with btn3:
        pass # 占位，保持排版齐平

# ==========================================
# 📥 强力缓存与文件自动解析引擎
# ==========================================
# 第一步：不管用户传没传文件，只要有本地缓存，立刻拿出来！
if 'req_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try:
        st.session_state['req_data'] = pd.read_pickle(CACHE_FILE)
    except:
        pass

with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>🔄 更新需求池数据 (无更新则跳过此步)</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("若有新需求或状态变更，请在此上传最新版的台账 (CSV/Excel)，系统将自动刷新并永久缓存", type=['csv', 'xlsx', 'xls'], label_visibility="collapsed")
    msg_area = st.empty()
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
                if COL_CATEGORY not in df_raw.columns: df_raw[COL_CATEGORY] = "默认需求"
            else:
                xls = pd.ExcelFile(uploaded_file)
                df_list = []
                for sheet_name in xls.sheet_names:
                    temp_df = pd.read_excel(xls, sheet_name=sheet_name)
                    temp_df[COL_CATEGORY] = sheet_name  # 自动抓取 Sheet 名字作为分类
                    df_list.append(temp_df)
                df_raw = pd.concat(df_list, ignore_index=True)
            
            # 🔥 重点：保存到本地持久化文件，并立刻写入内存
            df_raw.to_pickle(CACHE_FILE)
            st.session_state['req_data'] = df_raw
            msg_area.success("✅ 需求数据解析并保存成功！由于缓存引擎生效，刷新页面数据也不会丢失。")
        except Exception as e:
            msg_area.error(f"❌ 文件解析失败，请检查文件格式。报错详情：{e}")

# ==========================================
# 📊 看板渲染引擎 (双向排序 + 拖拽卡片 + 表单)
# ==========================================
if 'req_data' in st.session_state:
    df = st.session_state['req_data'].copy()
    
    if COL_ONLINE_DATE not in df.columns:
        st.error(f"⚠️ 数据格式不匹配：找不到 `{COL_ONLINE_DATE}` 列，请检查表头。")
    else:
        # 日期预处理（用于排序计算）
        if '需求提出日期' in df.columns:
            df['req_date_dt'] = pd.to_datetime(df['需求提出日期'], errors='coerce')
            df['需求提出日期'] = df['req_date_dt'].dt.strftime('%Y-%m-%d').fillna('')
        else:
            df['req_date_dt'] = pd.NaT

        df['online_date_dt'] = pd.to_datetime(df[COL_ONLINE_DATE], errors='coerce')
        df[COL_ONLINE_DATE] = df['online_date_dt'].dt.strftime('%Y-%m-%d').fillna('')
        
        # 数据隔离
        df_product = df[df[COL_CATEGORY].astype(str).str.contains("产品需求", na=False, case=False)].copy()
        df_data_center = df[df[COL_CATEGORY].astype(str).str.contains("数据中心需求", na=False, case=False)].copy()
        
        tab_product, tab_data = st.tabs(["📦 核心产品需求", "🗄️ 数据中心需求"])

        # ----------------------------------------------------
        # 封装公用的上下版块渲染逻辑
        # ----------------------------------------------------
        def render_board(df_subset, board_type):
            if df_subset.empty:
                st.info(f"📂 未匹配到【{board_type}】的有效数据。")
                return
            
            # 分割状态
            df_progress = df_subset[df_subset[COL_ONLINE_DATE] == ""].copy()
            df_completed = df_subset[df_subset[COL_ONLINE_DATE] != ""].copy()
            
            # 🔥 核心：执行时间维度动态排序
            # 进行中：按“需求提出时间”最近到最远
            df_progress = df_progress.sort_values(by='req_date_dt', ascending=False)
            # 已完成：按“需求上线时间”最近到最远
            df_completed = df_completed.sort_values(by='online_date_dt', ascending=False)

            # 剔除辅助排序的日期列，避免在表格中显示
            df_progress_disp = df_progress.drop(columns=['req_date_dt', 'online_date_dt', COL_CATEGORY], errors='ignore')
            df_completed_disp = df_completed.drop(columns=['req_date_dt', 'online_date_dt', COL_CATEGORY], errors='ignore')

            # --- 上半部分：正在进行中 ---
            st.markdown("<h3 style='color: #0284c7; margin-top: 10px; font-weight: 800;'>🏃 正在进行中</h3>", unsafe_allow_html=True)
            if not df_progress.empty:
                st.markdown(render_task_cards(df_progress, status="ongoing"), unsafe_allow_html=True)
                st.markdown("<div style='font-size: 13px; color:#64748b; margin-bottom: 8px;'>👇 进行中需求明细表 (已按提出时间降序排列)</div>", unsafe_allow_html=True)
                st.dataframe(df_progress_disp.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.success("🎉 太棒了，目前没有积压的进行中需求！")

            st.markdown("<hr style='border-color: #e2e8f0; margin: 40px 0;'/>", unsafe_allow_html=True)

            # --- 下半部分：已完成的需求 ---
            st.markdown("<h3 style='color: #10b981; font-weight: 800;'>✅ 已完成的需求</h3>", unsafe_allow_html=True)
            if not df_completed.empty:
                st.markdown(render_task_cards(df_completed, status="completed"), unsafe_allow_html=True)
                st.markdown("<div style='font-size: 13px; color:#64748b; margin-bottom: 8px;'>👇 已完成需求明细表 (已按上线时间降序排列)</div>", unsafe_allow_html=True)
                st.dataframe(df_completed_disp.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.info("⌛ 暂无已完成落地的需求。")

        # 渲染两个 Tab
        with tab_product:
            render_board(df_product, "产品需求")
        with tab_data:
            render_board(df_data_center, "数据中心需求")

else:
    st.info("👈 您的系统缓存中目前没有数据。请在上方上传本地需求文件 (Excel/CSV) 以激活工作台，此后只需在有数据更新时再次上传即可。")
