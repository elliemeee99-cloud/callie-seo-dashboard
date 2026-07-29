import streamlit as st
import pandas as pd
import datetime
import os
import urllib.request
import re

# ==========================================
# 网页基础设置 (默认折叠原生侧边栏)
# ==========================================
st.set_page_config(page_title="SEO重点事件记录", page_icon="📅", layout="wide", initial_sidebar_state="collapsed")

# 强制使用新版缓存名称，确保数据稳定固化
CACHE_FILE = "seo_events_cache_v2.pkl"

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

/* 各种表单小控件 */
div[data-testid="stRadio"] div[role="radiogroup"] { display: flex !important; flex-direction: row !important; gap: 10px !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] { background-color: #f1f5f9 !important; padding: 8px 24px !important; border-radius: 8px !important; cursor: pointer !important; transition: all 0.2s; }
div[data-testid="stRadio"] label[data-baseweb="radio"] div:first-child { display: none !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"] p { color: #64748b !important; font-weight: 600 !important; margin: 0 !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"], div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background-color: #2563eb !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"][aria-checked="true"] p, div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) p { color: #ffffff !important; }
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
# 🎨 标签色彩自动分配引擎 (多巴胺色系)
# ==========================================
def get_tag_style(tag_name):
    tag_name = str(tag_name).strip()
    palettes = [
        {"bg": "#fce7f3", "text": "#db2777"}, # 草莓粉
        {"bg": "#e0e7ff", "text": "#4f46e5"}, # 靛青蓝
        {"bg": "#dcfce7", "text": "#059669"}, # 翡翠绿
        {"bg": "#fef3c7", "text": "#d97706"}, # 琥珀黄
        {"bg": "#f3e8ff", "text": "#7c3aed"}, # 薰衣草紫
        {"bg": "#ffedd5", "text": "#ea580c"}, # 活力橙
        {"bg": "#ccfbf1", "text": "#0d9488"}, # 薄荷青
    ]
    idx = sum(ord(c) for c in tag_name) % len(palettes)
    return palettes[idx]

# ==========================================
# 🕷️ 智能文章信息抓取引擎 (缩略图 + 摘要描述)
# ==========================================
@st.cache_data(ttl=86400*7, show_spinner=False)
def get_link_info(url):
    info = {
        "img": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=800&q=80", 
        "desc": "暂未抓取到详细的文章概览，请点击下方“行业阅读”按钮直接前往原文查看详情与分析。"
    }
    if not isinstance(url, str) or not url.startswith('http'):
        return info
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            img_match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not img_match: img_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.IGNORECASE)
            if img_match: info["img"] = img_match.group(1)
            
            desc_match = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not desc_match: desc_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:description["\']', html, re.IGNORECASE)
            if not desc_match: desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if desc_match: 
                desc_text = desc_match.group(1).replace('\n', '').replace('\r', '')
                if len(desc_text) > 100: desc_text = desc_text[:97] + "..."
                info["desc"] = desc_text
    except Exception:
        pass
    return info

# ==========================================
# 🎯 页面头部结构与排版优化 (Fix UI)
# ==========================================
col_title, col_actions = st.columns([1.5, 1])
with col_title:
    st.markdown("# 📅 SEO 重点事件记录")
    st.markdown("<p style='color:#6B7280; font-size:15px; margin-top:-12px; margin-bottom:16px;'>复盘流量起伏核心依据，追踪记录所有优化动作与 Google 核心算法更迭</p>", unsafe_allow_html=True)
    
with col_actions:
    st.markdown(f"<div style='text-align:right; font-size:12px; color:#9CA3AF; margin-bottom: 8px;'>最后访问：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</div>", unsafe_allow_html=True)
    btn1, btn2, btn3 = st.columns([1.2, 1, 1])
    with btn2:
        if st.button("✨ 清空缓存", use_container_width=True):
            if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
            if 'event_data' in st.session_state: del st.session_state['event_data']
            st.rerun()
    with btn3:
        pass # 占位，保持排版齐平

# ==========================================
# 📥 强力缓存与文件自动解析引擎
# ==========================================
# 第一步：不管用户传没传文件，只要有本地缓存，立刻拿出来！
if 'event_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try:
        st.session_state['event_data'] = pd.read_pickle(CACHE_FILE)
    except:
        pass

with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>🔄 更新事件记录台账 (无更新则跳过此步)</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("若有新事件记录，请在此上传《要事记录》台账 (Excel)，系统将自动刷新并永久缓存", type=['xlsx', 'xls'], label_visibility="collapsed")
    msg_area = st.empty()
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            df_events = pd.read_excel(xls, sheet_name='重点事件记录') if '重点事件记录' in xls.sheet_names else pd.DataFrame()
            df_algo = pd.read_excel(xls, sheet_name='Google算法更新记录') if 'Google算法更新记录' in xls.sheet_names else pd.DataFrame()
            data_dict = {'events': df_events, 'algo': df_algo}
            
            # 🔥 重点：保存到本地持久化文件，并立刻写入内存
            pd.to_pickle(data_dict, CACHE_FILE)
            st.session_state['event_data'] = data_dict
            msg_area.success("✅ 事件台账解析并保存成功！由于缓存引擎生效，刷新页面数据也不会丢失。")
        except Exception as e:
            msg_area.error(f"❌ 文件解析失败，请检查文件格式。报错详情：{e}")


# ==========================================
# 📊 双轨看板渲染引擎
# ==========================================
if 'event_data' in st.session_state:
    data = st.session_state['event_data']
    df_events = data.get('events', pd.DataFrame())
    df_algo = data.get('algo', pd.DataFrame())
    
    tab_events, tab_algo = st.tabs(["🚩 重点事件记录库", "🤖 核心算法波动"])

    # ----------------------------------------------------
    # 🚩 模块 1：重点事件记录 (带动态标签筛选)
    # ----------------------------------------------------
    with tab_events:
        if not df_events.empty and '日期' in df_events.columns:
            # 数据清洗与标签合并
            df_events['日期_dt'] = pd.to_datetime(df_events['日期'], errors='coerce')
            df_events = df_events.sort_values(by='日期_dt', ascending=False)
            
            def process_tag(r):
                t = str(r.get('标签', '')).strip()
                if t == 'nan' or not t: 
                    t = str(r.get('内容类型', '事件')).strip()
                    if t == 'nan' or not t: t = '事件'
                return t
            
            df_events['最终标签'] = df_events.apply(process_tag, axis=1)
            
            # 🔥 注入动态胶囊筛选器
            unique_tags = ["全部"] + sorted(df_events['最终标签'].unique().tolist())
            st.markdown("<div style='font-size: 14px; font-weight: 700; color: #64748b; margin-top: 10px; margin-bottom: 8px;'>🎯 按标签快速筛选事件：</div>", unsafe_allow_html=True)
            
            try:
                selected_tag = st.pills("筛选器", unique_tags, default="全部", label_visibility="collapsed")
                if not selected_tag: selected_tag = "全部"
            except AttributeError:
                selected_tag = st.radio("筛选器", unique_tags, horizontal=True, label_visibility="collapsed")
                
            # 执行过滤
            if selected_tag != "全部":
                df_events_display = df_events[df_events['最终标签'] == selected_tag]
            else:
                df_events_display = df_events

            if df_events_display.empty:
                st.info(f"📂 未找到带有【{selected_tag}】标签的历史事件记录。")
            else:
                html = "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 16px;'>"
                for _, row in df_events_display.iterrows():
                    date_str = row['日期_dt'].strftime('%Y-%m-%d') if pd.notna(row['日期_dt']) else "未知时间"
                    overview = str(row.get('内容概览', '暂无概览')).strip()
                    if overview == 'nan': overview = "记录详情"
                    
                    details = str(row.get('内容详情', '')).strip()
                    if details == 'nan': details = "无详细描述"
                    details_html = details.replace('\n', '<br>')
                    
                    tag = row['最终标签']
                    tag_colors = get_tag_style(tag)
                    
                    card_html = f"""
                    <div style="background: #fff; border: 1px solid #e2e8f0; border-top: 4px solid #0ea5e9; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); display: flex; flex-direction: column; height: 100%;">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                            <span style="font-size: 13px; font-weight: 700; color: #0284c7; background: #e0f2fe; padding: 4px 10px; border-radius: 6px;">📅 {date_str}</span>
                            <span style="font-size: 12px; font-weight: 700; color: {tag_colors['text']}; background: {tag_colors['bg']}; padding: 4px 10px; border-radius: 12px;">{tag}</span>
                        </div>
                        <div style="font-size: 17px; font-weight: 800; color: #1e293b; margin-bottom: 12px; line-height: 1.4;">{overview}</div>
                        <div style="font-size: 14px; color: #475569; line-height: 1.6; background-color: #f8fafc; padding: 14px; border-radius: 8px; flex-grow: 1; border: 1px dashed #cbd5e1;">{details_html}</div>
                    </div>
                    """
                    html += card_html
                html += "</div>"
                
                st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
        else:
            st.info("📂 当前台账中缺乏规范的【重点事件记录】数据。")

    # ----------------------------------------------------
    # 🤖 模块 2：Google算法更新 (1 行 4 个)
    # ----------------------------------------------------
    with tab_algo:
        if not df_algo.empty and '开始时间' in df_algo.columns:
            df_algo['开始_dt'] = pd.to_datetime(df_algo['开始时间'], errors='coerce')
            df_algo = df_algo.sort_values(by='开始_dt', ascending=False)
            
            html = "<div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 20px;'>"
            for _, row in df_algo.iterrows():
                name = str(row.get('名称', '未命名更新')).strip()
                if name == 'nan': name = '未知算法更新'
                
                start_str = row['开始_dt'].strftime('%Y-%m-%d') if pd.notna(row['开始_dt']) else "未知"
                end_raw = row.get('结束时间', '')
                end_dt = pd.to_datetime(end_raw, errors='coerce')
                end_str = end_dt.strftime('%Y-%m-%d') if pd.notna(end_dt) else "至今"
                
                doc_url = str(row.get('Google说明文档', '')).strip()
                if doc_url == 'nan' or not doc_url: doc_url = '#'
                
                read_url = str(row.get('相关阅读', '')).strip()
                if read_url == 'nan' or not read_url: read_url = '#'
                
                target_url = read_url if read_url.startswith('http') else doc_url
                
                link_info = get_link_info(target_url)
                img_url = link_info['img']
                article_desc = link_info['desc']
                
                card_html = f"""
                <div style="display: flex; flex-direction: column; background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.03); height: 100%;">
                    <div style="height: 140px; width: 100%; background-image: url('{img_url}'); background-size: cover; background-position: center; border-bottom: 1px solid #e2e8f0;"></div>
                    <div style="padding: 16px; display: flex; flex-direction: column; flex-grow: 1;">
                        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 12px;">
                            <span style="font-size: 11px; font-weight: 700; color: #d97706; background: #fef3c7; padding: 4px 8px; border-radius: 6px; white-space: nowrap;">🤖 算法波动</span>
                            <span style="font-size: 11px; color: #64748b; font-weight: 600;">{start_str}<br>~ {end_str}</span>
                        </div>
                        <div style="font-size: 16px; font-weight: 800; color: #1e293b; margin-bottom: 10px; line-height: 1.4;">{name}</div>
                        <div style="font-size: 12px; color: #64748b; line-height: 1.5; margin-bottom: 20px; flex-grow: 1;">
                            {article_desc}
                        </div>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: auto;">
                            <a href="{doc_url}" target="_blank" style="text-decoration: none; font-size: 12px; font-weight: 600; color: #0284c7; background: #e0f2fe; padding: 6px 12px; border-radius: 6px; transition: 0.2s;">📄 官方文档</a>
                            <a href="{read_url}" target="_blank" style="text-decoration: none; font-size: 12px; font-weight: 600; color: #7c3aed; background: #ede9fe; padding: 6px 12px; border-radius: 6px; transition: 0.2s;">🔗 行业阅读</a>
                        </div>
                    </div>
                </div>
                """
                html += card_html
            html += "</div>"
            
            st.markdown(html.replace('\n', ''), unsafe_allow_html=True)
        else:
            st.info("📂 当前台账中缺乏规范的【Google算法更新记录】数据。")

else:
    st.info("👈 您的系统缓存中目前没有数据。请在上方上传本地事件台账 (Excel) 以激活记录追踪功能，此后只需在有数据更新时再次上传即可。")
