import streamlit as st
import pandas as pd
import datetime

# ==========================================
# 网页基础设置 (默认折叠原生侧边栏)
# ==========================================
st.set_page_config(page_title="SEO需求管理", page_icon="📋", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# ⚙️ 核心数据字段配置 
# ==========================================
# 代码会自动将 Excel 的 Sheet 名字作为这个字段的值
COL_CATEGORY = "需求分类"  
COL_ONLINE_DATE = "需求上线时间"


# ==========================================
# 🧭 全局 UI 组件 (导航栏 + 多巴胺悬浮置顶)
# ==========================================
st.markdown("""
<div id="top-anchor"></div>
<style>
/* 1. 隐藏 Streamlit 默认的侧边栏、左上角箭头及顶部白条 */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stHeader"] { display: none !important; }

/* 2. 顶部吸顶悬浮容器：毛玻璃背景 + 完美居中 */
.top-nav-container {
    position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important;
    background-color: rgba(248, 250, 252, 0.85) !important;
    backdrop-filter: blur(16px) !important; -webkit-backdrop-filter: blur(16px) !important;
    z-index: 99999 !important; padding: 14px 0 !important; margin: 0 !important;
    display: flex !important; justify-content: center !important; align-items: center !important;
    border-bottom: 1px solid rgba(226, 232, 240, 0.8); box-shadow: 0 4px 20px rgba(0,0,0,0.03);
}

/* 紧凑内部排布 */
.top-nav-inner {
    display: flex !important; justify-content: center !important; align-items: center !important;
    gap: 16px !important; width: 100% !important; max-width: 800px !important; padding: 0 20px !important;
}
.top-nav-inner > div { flex: 1 !important; }

/* 导航卡片本体 */
[data-testid="stPageLink-NavLink"] { 
    background-color: #ffffff !important; border: 1.5px solid #e2e8f0 !important; border-radius: 12px !important; 
    padding: 10px 14px !important; text-align: center !important; display: flex !important;
    justify-content: center !important; align-items: center !important; transition: all 0.25s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.01) !important; text-decoration: none !important;
}
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #ffffff !important; border-color: #3b82f6 !important; transform: translateY(-2px) !important;
    box-shadow: 0 8px 16px rgba(37, 99, 235, 0.1) !important;
}
[data-testid="stPageLink-NavLink"] p { font-weight: 700 !important; color: #1e293b !important; font-size: 14.5px !important; margin: 0 !important; }

/* 3. 🍓 草莓牛奶多巴胺粉：回到顶部按钮 */
.back-to-top {
    position: fixed; bottom: 40px; right: 40px; background-color: #FF8FAB; color: #ffffff !important; 
    border: none; width: 50px; height: 50px; border-radius: 50%; display: flex; justify-content: center; align-items: center;
    font-size: 24px; font-weight: 800; box-shadow: 0 4px 15px rgba(255, 143, 171, 0.35); 
    text-decoration: none !important; z-index: 99999; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.back-to-top:hover {
    background-color: #FF5D8F; transform: translateY(-5px); box-shadow: 0 8px 20px rgba(255, 143, 171, 0.55); color: #ffffff !important;
}

/* 4. 页面主体下移避让 */
.block-container { padding-top: 6.5rem !important; max-width: 95% !important; }
.stApp { background-color: #f8fafc !important; }

/* 5. 覆盖原生容器圆角与字体 */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px !important; border: 1px solid #e2e8f0 !important; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); padding: 20px; }
div[data-testid="stMetricValue"] > div { color: #0f172a !important; font-size: 28px !important; font-weight: 800 !important; }
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 15px !important; font-weight: 600 !important; }

/* 6. Tabs 胶囊美化 */
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

# 🔥 注入顶部导航栏 (已扩展为 4 个模块)
st.markdown('<div class="top-nav-container"><div class="top-nav-inner">', unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
with nav_col1: st.page_link("app.py", label="App 首页", icon="🏠")
with nav_col2: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with nav_col3: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with nav_col4: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
st.markdown('</div></div>', unsafe_allow_html=True)


# ==========================================
# 🎯 页面头部结构
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📋 SEO 需求落地与项目追踪</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>统一管理产品与数据中心需求状态，追踪研发跟进闭环。</div>", unsafe_allow_html=True)
with col_refresh:
    st.write("") 
    if st.button("🗑️ 清空本地缓存"):
        if 'req_data' in st.session_state:
            del st.session_state['req_data']
            st.rerun()

# ==========================================
# 📥 文件上传引擎 (支持多Sheet融合)
# ==========================================
with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>🔄 一键更新需求池数据</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请在此拖拽或上传最新的需求台账 (支持 CSV 或 Excel xlsx 格式)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_raw = pd.read_csv(uploaded_file)
                if COL_CATEGORY not in df_raw.columns:
                    df_raw[COL_CATEGORY] = "未知分类"
            else:
                # 🔥 自动读取 Excel 中的所有 Sheet，并将 Sheet 名作为分类写入数据
                xls = pd.ExcelFile(uploaded_file)
                df_list = []
                for sheet_name in xls.sheet_names:
                    temp_df = pd.read_excel(xls, sheet_name=sheet_name)
                    temp_df[COL_CATEGORY] = sheet_name  # 关键：以工作表名称作为需求分类
                    df_list.append(temp_df)
                df_raw = pd.concat(df_list, ignore_index=True)
            
            # 存入缓存
            st.session_state['req_data'] = df_raw
            st.success("✅ 需求数据解析并装载成功！请查看下方看板。")
        except Exception as e:
            st.error(f"❌ 文件解析失败，请检查文件格式是否损坏。报错详情：{e}")


# ==========================================
# 📊 双轨需求看板渲染引擎
# ==========================================
if 'req_data' in st.session_state:
    df = st.session_state['req_data'].copy()
    
    # 诊断数据表列名是否匹配
    if COL_ONLINE_DATE not in df.columns:
        st.error(f"⚠️ 数据格式匹配失败！\n\n您上传的文件中找不到用来判断状态的 `{COL_ONLINE_DATE}` 列。\n当前文件拥有的列名为：`{list(df.columns)}`。")
    else:
        # 🔥 日期字段的绝对清洗：格式化为 YYYY-MM-DD，并剥离所有的 NaT / NaN
        if '需求提出日期' in df.columns:
            df['需求提出日期'] = pd.to_datetime(df['需求提出日期'], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        
        df[COL_ONLINE_DATE] = pd.to_datetime(df[COL_ONLINE_DATE], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
        
        # 过滤“产品需求”与“数据中心需求” (基于 Sheet Name 生成的分类)
        df_product = df[df[COL_CATEGORY].astype(str).str.contains("产品需求", na=False, case=False)].drop(columns=[COL_CATEGORY])
        df_data_center = df[df[COL_CATEGORY].astype(str).str.contains("数据中心需求", na=False, case=False)].drop(columns=[COL_CATEGORY])
        
        tab_product, tab_data = st.tabs(["📦 核心产品需求看板", "🗄️ 数据中心需求看板"])

        # -------------------------------------
        # 📦 模块 1：产品需求
        # -------------------------------------
        with tab_product:
            if not df_product.empty:
                # 状态判定：上线时间为空即为“进行中”，非空即为“已完成”
                df_prod_completed = df_product[df_product[COL_ONLINE_DATE] != ""]
                df_prod_progress = df_product[df_product[COL_ONLINE_DATE] == ""]
                
                # 渲染头部卡片
                st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
                mc1, mc2, mc3 = st.columns(3)
                with mc1: 
                    with st.container(border=True): st.metric("📦 产品需求总数", f"{len(df_product)} 项")
                with mc2: 
                    with st.container(border=True): st.metric("🏃 正在进行中", f"{len(df_prod_progress)} 项", "加速推进中", delta_color="normal")
                with mc3: 
                    with st.container(border=True): st.metric("✅ 已完成落地", f"{len(df_prod_completed)} 项", "已闭环上线", delta_color="off")
                
                st.markdown("<hr style='border-color: #EEF2F6; margin: 24px 0;'/>", unsafe_allow_html=True)
                
                # 双轨列表渲染
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("<h4 style='color: #0284c7;'>🏃 正在进行中 (Pending)</h4>", unsafe_allow_html=True)
                    if not df_prod_progress.empty:
                        st.dataframe(df_prod_progress.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("💡 当前没有正在进行中的产品需求。")
                        
                with col_right:
                    st.markdown("<h4 style='color: #10b981;'>✅ 已完成闭环 (Completed)</h4>", unsafe_allow_html=True)
                    if not df_prod_completed.empty:
                        st.dataframe(df_prod_completed.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("💡 当前暂无已完成的产品需求。")
            else:
                st.info("📂 您上传的文件中没有匹配到【产品需求】数据。")

        # -------------------------------------
        # 🗄️ 模块 2：数据中心需求
        # -------------------------------------
        with tab_data:
            if not df_data_center.empty:
                # 状态判定
                df_data_completed = df_data_center[df_data_center[COL_ONLINE_DATE] != ""]
                df_data_progress = df_data_center[df_data_center[COL_ONLINE_DATE] == ""]
                
                # 渲染头部卡片
                st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
                mc1, mc2, mc3 = st.columns(3)
                with mc1: 
                    with st.container(border=True): st.metric("🗄️ 数据中心需求总数", f"{len(df_data_center)} 项")
                with mc2: 
                    with st.container(border=True): st.metric("🏃 正在进行中", f"{len(df_data_progress)} 项", "开发抓取中", delta_color="normal")
                with mc3: 
                    with st.container(border=True): st.metric("✅ 已完成落地", f"{len(df_data_completed)} 项", "已稳定运行", delta_color="off")
                
                st.markdown("<hr style='border-color: #EEF2F6; margin: 24px 0;'/>", unsafe_allow_html=True)
                
                # 双轨列表渲染
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("<h4 style='color: #0284c7;'>🏃 正在进行中 (Pending)</h4>", unsafe_allow_html=True)
                    if not df_data_progress.empty:
                        st.dataframe(df_data_progress.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("💡 当前没有正在进行中的数据中心需求。")
                        
                with col_right:
                    st.markdown("<h4 style='color: #10b981;'>✅ 已完成闭环 (Completed)</h4>", unsafe_allow_html=True)
                    if not df_data_completed.empty:
                        st.dataframe(df_data_completed.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("💡 当前暂无已完成的数据中心需求。")
            else:
                st.info("📂 您上传的文件中没有匹配到【数据中心需求】数据。")

else:
    st.info("👈 请在上方上传本地需求文件 (Excel / CSV) 以生成需求台账。")
