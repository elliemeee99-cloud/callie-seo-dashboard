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
# 本地缓存文件路径（实现数据永不丢失）
CACHE_FILE = "seo_requirements_cache.pkl"

# ==========================================
# 🧭 全局 UI 组件 (绝对安全的导航栏与 CSS)
# ==========================================
st.markdown("""
<div id="top-anchor"></div>
<style>
/* 隐藏无用控件 */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stHeader"] { display: none !important; }

/* 页面主体下移避让 */
.block-container { padding-top: 2rem !important; max-width: 95% !important; }
.stApp { background-color: #f8fafc !important; }

/* 导航卡片本体美化 */
[data-testid="stPageLink-NavLink"] { 
    background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 12px !important; 
    padding: 12px 10px !important; text-align: center !important; display: flex !important;
    justify-content: center !important; align-items: center !important; transition: all 0.25s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; text-decoration: none !important;
}
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #ffffff !important; border-color: #3b82f6 !important; transform: translateY(-2px) !important;
    box-shadow: 0 8px 16px rgba(37, 99, 235, 0.1) !important;
}
[data-testid="stPageLink-NavLink"] p { font-weight: 800 !important; color: #1e293b !important; font-size: 16px !important; margin: 0 !important; }

/* 🍓 草莓牛奶多巴胺粉：回到顶部按钮 */
.back-to-top {
    position: fixed; bottom: 40px; right: 40px; background-color: #FF8FAB; color: #ffffff !important; 
    border: none; width: 50px; height: 50px; border-radius: 50%; display: flex; justify-content: center; align-items: center;
    font-size: 24px; font-weight: 800; box-shadow: 0 4px 15px rgba(255, 143, 171, 0.35); 
    text-decoration: none !important; z-index: 99999; transition: all 0.3s ease;
}
.back-to-top:hover {
    background-color: #FF5D8F; transform: translateY(-5px); box-shadow: 0 8px 20px rgba(255, 143, 171, 0.55); color: #ffffff !important;
}

/* 覆盖原生容器圆角与字体 */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; border: 1px solid #e2e8f0 !important; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); padding: 20px; }

/* Tabs 胶囊美化 */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] { gap: 12px !important; border-bottom: none !important; }
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"] { display: none !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"] { background-color: #f1f5f9 !important; border-radius: 8px !important; padding: 12px 28px !important; border: none !important; transition: all 0.3s ease; }
div[data-testid="stTabs"] button[data-baseweb="tab"] p { color: #64748b !important; font-weight: 700 !important; font-size: 16px !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] { background-color: #2563eb !important; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2) !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p { color: #ffffff !important; }
</style>

<!-- 粉色回到顶部锚点 -->
<a href="#top-anchor" class="back-to-top" title="回到顶部">↑</a>
""", unsafe_allow_html=True)

# 🔥 注入顶部导航栏 (安全居中排版 - 4个按钮)
spacer_left, nav1, nav2, nav3, nav4, spacer_right = st.columns([0.5, 1.2, 1.2, 1.2, 1.2, 0.5])
with nav1: st.page_link("app.py", label="App 首页", icon="🏠")
with nav2: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with nav3: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with nav4: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

# ==========================================
# 💎 看板卡片渲染函数 (支持前端拖拽)
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

        # 进行中用蓝色样式，已完成用绿色样式
        border_color = "#3b82f6" if status == "ongoing" else "#10b981"
        bg_color = "#eff6ff" if status == "ongoing" else "#ecfdf5"
        status_icon = "🏃" if status == "ongoing" else "✅"

        html += f"""
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
    html += '</div>'
    return html

# ==========================================
# 🎯 页面头部结构与持久化引擎
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📋 SEO 需求落地与项目追踪</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>统一管理产品与数据中心需求状态，追踪研发跟进闭环。</div>", unsafe_allow_html=True)
with col_refresh:
    st.write("") 
    if st.button("🗑️ 清空本地缓存"):
        if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
        if 'req_data' in st.session_state: del st.session_state['req_data']
        st.success("缓存已清空！")
        st.rerun()

# 📥 文件上传与自动解析引擎
with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>🔄 一键更新需求池数据</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请在此拖拽或上传最新的需求台账 (支持 CSV 或 Excel xlsx 格式)", type=['csv', 'xlsx', 'xls'])
    
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
            
            # 🔥 重点：保存到本地持久化文件
            df_raw.to_pickle(CACHE_FILE)
            st.session_state['req_data'] = df_raw
            st.success("✅ 需求数据解析并保存成功！刷新页面数据也不会丢失。")
        except Exception as e:
            st.error(f"❌ 文件解析失败，请检查文件格式。报错详情：{e}")

# 自动从本地加载历史缓存数据
if 'req_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try:
        st.session_state['req_data'] = pd.read_pickle(CACHE_FILE)
    except:
        pass

# ==========================================
# 📊 看板渲染引擎 (双向排序 + 拖拽卡片)
# ==========================================
if 'req_data' in st.session_state:
    df = st.session_state['req_data'].copy()
    
    if COL_ONLINE_DATE not in df.columns:
        st.error(f"⚠️ 数据格式不匹配：找不到 `{COL_ONLINE_DATE}` 列。")
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
                st.info(f"📂 未匹配到【{board_type}】的数据。")
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
            st.markdown("<h3 style='color: #0284c7; margin-top: 20px; font-weight: 800;'>🏃 正在进行中</h3>", unsafe_allow_html=True)
            if not df_progress.empty:
                # 渲染拖拽卡片
                st.markdown(render_task_cards(df_progress, status="ongoing"), unsafe_allow_html=True)
                # 渲染底层表单
                st.markdown("<div style='font-size: 13px; color:#64748b; margin-bottom: 8px;'>👇 进行中需求明细表 (已按提出时间排序)</div>", unsafe_allow_html=True)
                st.dataframe(df_progress_disp.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.success("🎉 目前没有积压的进行中需求！")

            st.markdown("<hr style='border-color: #e2e8f0; margin: 40px 0;'/>", unsafe_allow_html=True)

            # --- 下半部分：已完成的需求 ---
            st.markdown("<h3 style='color: #10b981; font-weight: 800;'>✅ 已完成的需求</h3>", unsafe_allow_html=True)
            if not df_completed.empty:
                # 渲染拖拽卡片
                st.markdown(render_task_cards(df_completed, status="completed"), unsafe_allow_html=True)
                # 渲染底层表单
                st.markdown("<div style='font-size: 13px; color:#64748b; margin-bottom: 8px;'>👇 已完成需求明细表 (已按上线时间排序)</div>", unsafe_allow_html=True)
                st.dataframe(df_completed_disp.reset_index(drop=True), use_container_width=True, hide_index=True)
            else:
                st.info("⌛ 暂无已完成落地的需求。")

        # 渲染两个 Tab
        with tab_product:
            render_board(df_product, "产品需求")
        with tab_data:
            render_board(df_data_center, "数据中心需求")

else:
    st.info("👈 您的缓存池为空，请在上方上传本地需求文件 (Excel) 以激活需求工作台。此后数据将被永久保存。")
