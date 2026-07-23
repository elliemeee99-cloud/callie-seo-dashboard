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

CACHE_FILE = "seo_events_cache.pkl"

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
# 🧭 极限压缩防乱码 CSS + 导航栏
# ==========================================
compressed_css = """
<div id="top-anchor"></div>
<style>[data-testid="stSidebar"]{display:none !important;}[data-testid="collapsedControl"]{display:none !important;}[data-testid="stHeader"]{display:none !important;}.block-container{padding-top:2rem !important;max-width:95% !important;}.stApp{background-color:#f8fafc !important;}[data-testid="stPageLink-NavLink"]{background-color:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:12px !important;padding:12px 10px !important;text-align:center !important;display:flex !important;justify-content:center !important;align-items:center !important;transition:all 0.25s ease !important;box-shadow:0 2px 4px rgba(0,0,0,0.02) !important;text-decoration:none !important;}[data-testid="stPageLink-NavLink"]:hover{background-color:#ffffff !important;border-color:#3b82f6 !important;transform:translateY(-2px) !important;box-shadow:0 8px 16px rgba(37,99,235,0.1) !important;}[data-testid="stPageLink-NavLink"] p{font-weight:800 !important;color:#1e293b !important;font-size:15.5px !important;margin:0 !important;}.back-to-top{position:fixed;bottom:40px;right:40px;background-color:#FF8FAB;color:#ffffff !important;border:none;width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:24px;font-weight:800;box-shadow:0 4px 15px rgba(255,143,171,0.35);text-decoration:none !important;z-index:99999;transition:all 0.3s ease;}.back-to-top:hover{background-color:#FF5D8F;transform:translateY(-5px);box-shadow:0 8px 20px rgba(255,143,171,0.55);color:#ffffff !important;}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;border:1px solid #e2e8f0 !important;background-color:#ffffff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);padding:20px;}div[data-testid="stTabs"] div[data-baseweb="tab-list"]{gap:12px !important;border-bottom:none !important;}div[data-testid="stTabs"] div[data-baseweb="tab-highlight"]{display:none !important;}div[data-testid="stTabs"] button[data-baseweb="tab"]{background-color:#f1f5f9 !important;border-radius:8px !important;padding:12px 28px !important;border:none !important;transition:all 0.3s ease;}div[data-testid="stTabs"] button[data-baseweb="tab"] p{color:#64748b !important;font-weight:700 !important;font-size:16px !important;}div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"]{background-color:#2563eb !important;box-shadow:0 4px 6px rgba(37,99,235,0.2) !important;}div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] p{color:#ffffff !important;}</style>
<a href="#top-anchor" class="back-to-top" title="回到顶部">↑</a>
"""
st.markdown(compressed_css, unsafe_allow_html=True)

spacer_left, nav1, nav2, nav3, nav4, nav5, spacer_right = st.columns([0.1, 1.2, 1.2, 1.2, 1.2, 1.2, 0.1])
with nav1: st.page_link("app.py", label="App 首页", icon="🏠")
with nav2: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with nav3: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with nav4: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with nav5: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

# ==========================================
# 🎯 页面头部结构与持久化引擎
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📅 SEO 重点事件与算法追踪</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>复盘流量起伏核心依据，追踪记录所有优化动作与 Google 核心算法更迭。</div>", unsafe_allow_html=True)
with col_refresh:
    st.write("") 
    if st.button("🗑️ 清空本地缓存"):
        if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
        if 'event_data' in st.session_state: del st.session_state['event_data']
        st.success("缓存已清空！")
        st.rerun()

# 📥 文件上传与自动解析引擎
with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>🔄 一键更新事件台账</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请在此上传《要事记录》台账 (支持 Excel xlsx 格式)", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            df_events = pd.read_excel(xls, sheet_name='重点事件记录') if '重点事件记录' in xls.sheet_names else pd.DataFrame()
            df_algo = pd.read_excel(xls, sheet_name='Google算法更新记录') if 'Google算法更新记录' in xls.sheet_names else pd.DataFrame()
            data_dict = {'events': df_events, 'algo': df_algo}
            pd.to_pickle(data_dict, CACHE_FILE)
            st.session_state['event_data'] = data_dict
            st.success("✅ 事件台账解析并保存成功！刷新页面数据也不会丢失。")
        except Exception as e:
            st.error(f"❌ 文件解析失败，请检查文件格式。报错详情：{e}")

if 'event_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['event_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

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
    st.info("👈 您的记录库为空，请在上方上传台账 (Excel) 以激活记录追踪功能。")
