import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
import datetime
import re

# 网页基础设置
st.set_page_config(page_title="SEO数据看板", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 定制 CSS (极简高端排版)
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f8fafc !important; }
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}
.block-container { padding-top: 2rem !important; max-width: 95% !important; }

/* 圆角分区容器 */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    padding: 10px;
}

/* 覆盖原生卡片字体 */
div[data-testid="stMetricValue"] > div {
    color: #0f172a !important; font-size: 26px !important; font-weight: 800 !important;
}
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 14px !important; font-weight: 600 !important; }
div[data-testid="stMetricDelta"] > div { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 极速数据获取引擎 (精准抓取 销售额 & 目标)
# ==========================================
@st.cache_data(ttl="1h")
def load_and_transform_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit")
        
        sales_data = {}
        target_data = {}
        
        sheet2 = spreadsheet.worksheet("Sheet2")
        raw_data_2 = sheet2.get_all_values()
        
        if raw_data_2:
            headers = raw_data_2[0]
            for row in raw_data_2[1:]:
                if not row or not row[0]: continue
                first_col = row[0].strip()
                        
                # 💡 抓取底部的“总计”行 (实际销售额)
                if first_col == "总计":
                    sales_data = {} 
                    for i in range(1, min(len(headers), len(row))):
                        site = headers[i].strip()
                        if site == "": continue
                        val_str = row[i].strip()
                        clean_str = re.sub(r'[^\d\.-]', '', val_str)
                        sales_data[site] = float(clean_str) if clean_str else 0.0
                        
                # 💡 抓取“分站点目标”行 (各站目标)
                elif first_col == "分站点目标":
                    target_data = {} 
                    for i in range(1, min(len(headers), len(row))):
                        site = headers[i].strip()
                        if site == "": continue
                        val_str = row[i].strip()
                        clean_str = re.sub(r'[^\d\.-]', '', val_str)
                        target_data[site] = float(clean_str) if clean_str else 0.0
                        
        return {"sales": sales_data, "targets": target_data}
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None

# ==========================================
# 📐 UI 布局与可视化渲染
# ==========================================

real_today = pd.Timestamp(datetime.datetime.now().date())
latest_date = real_today - pd.Timedelta(days=1)  

st.markdown(f"""
<div style="margin-bottom: 25px;">
    <h1 style="color: #1e293b; font-size: 32px; font-weight: 800; margin-bottom: 4px;">🚀 SEO目标与业绩看板</h1>
    <div style="color: #64748b; font-size: 14px;">报表同步基准日：{latest_date.strftime('%Y-%m-%d')}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("✨ 正在召唤看板数据..."):
    data_dict = load_and_transform_google_sheet()

if data_dict:
    sales_data = data_dict["sales"]
    target_data = data_dict["targets"]
    
    # 强制固定业务顺序: 德法西意荷挪瑞芬
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI"]
    en_to_cn = {"DE":"德国", "FR":"法国", "ES":"西班牙", "IT":"意大利", "NL":"荷兰", "NO":"挪威", "SE":"瑞典", "FI":"芬兰"}
    
    total_actual = sales_data.get("总计", sum([sales_data.get(s, 0) for s in fixed_sites_order]))
    total_target = sum([target_data.get(s, 0) for s in fixed_sites_order])
    total_rate = (total_actual / total_target * 100) if total_target > 0 else 0
    capped_rate = min(total_rate, 100) # 用于控制进度条宽度不超过 100%

    # --- 可爱元气文案逻辑 ---
    if total_rate >= 100:
        cheer_msg = "🎉 完美达标！太棒啦，大家辛苦了！"
        st.balloons() # 🎊 达标自动撒气球彩蛋！
    elif total_rate >= 80:
        cheer_msg = "🔥 冲刺阶段，胜利就在眼前啦！"
    elif total_rate >= 50:
        cheer_msg = "🏃 稳步前行，进度已经过半咯！"
    else:
        cheer_msg = "✨ 起步加速中，这月也要冲鸭！"

    # ------------------------------------------
    # 🏆 第一板块：全盘总目标与进度 (趣味元气进度条)
    # ------------------------------------------
    st.markdown("### 🎯 本月总计进度")
    with st.container(border=True):
        col_text, col_chart = st.columns([1, 2.5])
        
        with col_text:
            st.write("")
            st.metric("🎯 本月 SEO 总目标", f"${total_target:,.2f}")
            st.metric("💰 累计实际完成", f"${total_actual:,.2f}", f"整体进度 {total_rate:.1f}%")
            
        with col_chart:
            st.write("")
            st.write("")
            # 绘制元气小火箭进度条 HTML/CSS
            custom_progress_html = f"""
            <div style="padding: 10px 20px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #475569; font-weight: 600; font-size: 15px;">
                    <span>{cheer_msg}</span>
                    <span style="color: #f43f5e; font-size: 18px;">{total_rate:.1f}%</span>
                </div>
                <div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 28px; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="background: linear-gradient(90deg, #fbcfe8 0%, #f43f5e 100%); border-radius: 30px; width: {capped_rate}%; height: 100%; transition: width 1.5s ease-in-out;"></div>
                    <div style="position: absolute; top: -12px; left: calc({capped_rate}% - 20px); font-size: 32px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1)); transition: left 1.5s ease-in-out;">🚀</div>
                    <div style="position: absolute; top: 0px; right: 10px; line-height: 28px; font-size: 18px;">🏁</div>
                </div>
            </div>
            """
            st.markdown(custom_progress_html, unsafe_allow_html=True)

    st.write("---")

    # ------------------------------------------
    # 🌍 第二板块：各站点目标完成情况
    # ------------------------------------------
    st.markdown("### 🌍 各站点目标完成情况")
    
    sites_cn = []
    actuals = []
    targets = []
    rates = []
    
    for site in fixed_sites_order:
        s_actual = sales_data.get(site, 0)
        s_target = target_data.get(site, 0)
        s_rate = (s_actual / s_target * 100) if s_target > 0 else 0
        
        sites_cn.append(en_to_cn[site])
        actuals.append(s_actual)
        targets.append(s_target)
        rates.append(s_rate)

    # --- 柱状对比图 ---
    with st.container(border=True):
        fig_bar = go.Figure(data=[
            go.Bar(name='目标值 (Target)', x=sites_cn, y=targets, marker_color='#cbd5e1', marker_line_color='#94a3b8', marker_line_width=1.5, text=[f"${t:,.0f}" for t in targets], textposition='auto'),
            go.Bar(name='实际值 (Actual)', x=sites_cn, y=actuals, marker_color='#3b82f6', marker_line_color='#2563eb', marker_line_width=1.5, text=[f"${a:,.0f}" for a in actuals], textposition='auto')
        ])
        fig_bar.update_layout(
            barmode='group',
            height=380,
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- 底部八大站点详情卡片 ---
    st.write("")
    with st.container(border=True):
        cols = st.columns(8)
        for i, site in enumerate(fixed_sites_order):
            with cols[i]:
                color = "normal" if rates[i] >= 100 else "off"
                delta_str = f"完成 {rates[i]:.1f}%"
                
                st.metric(
                    label=f"{en_to_cn[site]} (🎯${targets[i]:,.0f})", 
                    value=f"${actuals[i]:,.0f}", 
                    delta=delta_str,
                    delta_color=color
                )
                
                # 站点的绿色/粉色进度条
                progress_val = min(rates[i] / 100.0, 1.0)
                st.progress(progress_val)
else:
    st.info("👈 请配置 GCP JSON 密钥以接入数据。")
