import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import calendar
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
.block-container { padding-top: 2rem !important; max-width: 98% !important; }

/* 圆角分区容器 */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    padding: 12px;
}

/* 覆盖原生卡片字体 */
div[data-testid="stMetricValue"] > div {
    color: #0f172a !important; font-size: 24px !important; font-weight: 800 !important;
}
div[data-testid="stMetricLabel"] { color: #475569 !important; font-size: 13px !important; font-weight: 600 !important; }
div[data-testid="stMetricDelta"] > div { font-size: 13px !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取引擎 (支持多月/多年轻量级解析)
# ==========================================
@st.cache_data(ttl="1h")
def load_and_transform_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit")
        
        sales_records = []
        target_data = {}
        
        sheet2 = spreadsheet.worksheet("Sheet2")
        raw_data_2 = sheet2.get_all_values()
        
        if raw_data_2:
            headers = raw_data_2[0]
            # 默认年份基准，如果在行里匹配到其他年份标记可以动态延伸
            default_year = str(datetime.datetime.now().year)
            if '年' in headers[0]:
                default_year = headers[0].replace('年', '').strip()
                
            for row in raw_data_2[1:]:
                if not row or not row[0]: continue
                first_col = row[0].strip()
                        
                # 1. 抓取历史明细行 (动态识别类似 "7月1日", "6月15日" 的所有结构)
                if "月" in first_col and "日" in first_col:
                    try:
                        month = first_col.split('月')[0].strip()
                        day = first_col.split('月')[1].replace('日', '').strip()
                        # 组合成标准的日期字符串进行归档
                        date_val = pd.to_datetime(f"{default_year}-{month}-{day}", errors='coerce')
                        
                        if pd.notna(date_val):
                            for i in range(1, min(len(headers), len(row))):
                                site = headers[i].strip()
                                if site in ["总计", ""]: continue
                                val_str = row[i].strip()
                                clean_str = re.sub(r'[^\d\.-]', '', val_str)
                                val = float(clean_str) if clean_str else 0.0
                                
                                sales_records.append({
                                    "Date": date_val,
                                    "Site": site,
                                    "Value": val
                                })
                    except:
                        continue
                        
                # 2. 抓取“分站点目标”行
                elif first_col == "分站点目标":
                    for i in range(1, min(len(headers), len(row))):
                        site = headers[i].strip()
                        if site == "": continue
                        val_str = row[i].strip()
                        clean_str = re.sub(r'[^\d\.-]', '', val_str)
                        target_data[site] = float(clean_str) if clean_str else 0.0
                        
        df_sales = pd.DataFrame(sales_records)
        if not df_sales.empty:
            df_sales['Date'] = pd.to_datetime(df_sales['Date']).dt.normalize()
            
        return {"sales_df": df_sales, "targets": target_data}
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None

# ==========================================
# 📐 UI 布局与数据大盘渲染
# ==========================================

# 锁定物理世界绝对时间
real_today = pd.Timestamp(datetime.datetime.now().date())
latest_date = real_today - pd.Timedelta(days=1)  

st.markdown(f"""
<div style="margin-bottom: 25px;">
    <h1 style="color: #1e293b; font-size: 32px; font-weight: 800; margin-bottom: 4px;">🚀 SEO数据看板</h1>
    <div style="color: #64748b; font-size: 14px;">报表同步基准日：{latest_date.strftime('%Y-%m-%d')}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("✨ 正在深度挖掘历史同环比数据..."):
    data_dict = load_and_transform_google_sheet()

if data_dict:
    df_sales = data_dict["sales_df"]
    target_data = data_dict["targets"]
    
    # 固定业务专属顺序
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    en_to_cn = {"DE":"德国", "FR":"法国", "ES":"西班牙", "IT":"意大利", "NL":"荷兰", "NO":"挪威", "SE":"瑞典", "FI":"芬兰", "PL":"波兰"}
    
    # --- 1. 基础时间流速变量计算 ---
    days_in_month = calendar.monthrange(latest_date.year, latest_date.month)[1]
    current_day = latest_date.day
    time_progress_rate = (current_day / days_in_month) * 100

    # --- 2. 智能化 MTD 交叉时间窗口滑动推算 ---
    # 【当前 MTD】
    start_of_current_month = latest_date.replace(day=1)
    
    # 【环比 MTD - 上月同期】
    # 动态推算上个月的目标日期，自动处理跨年及月份天数差异
    try:
        start_of_last_month = (start_of_current_month - pd.Timedelta(days=1)).replace(day=1)
        end_of_last_month_mtd = start_of_last_month + pd.Timedelta(days=current_day - 1)
    except:
        start_of_last_month = start_of_current_month - pd.DateOffset(months=1)
        end_of_last_month_mtd = start_of_last_month + pd.DateOffset(days=current_day - 1)

    # 【同比 MTD - 去年同期】
    start_of_last_year_month = start_of_current_month - pd.DateOffset(years=1)
    end_of_last_year_mtd = start_of_last_year_month + pd.DateOffset(days=current_day - 1)

    # --- 3. 提取各版块实际销售额数据 ---
    actual_sales_map = {}
    mom_sales_map = {}
    yoy_sales_map = {}
    
    for s in fixed_sites_order:
        if not df_sales.empty:
            # 当前 MTD 销售
            mask_curr = (df_sales['Site'] == s) & (df_sales['Date'] >= start_of_current_month) & (df_sales['Date'] <= latest_date)
            actual_sales_map[s] = df_sales[mask_curr]['Value'].sum()
            
            # 上月同期 MTD 销售
            mask_mom = (df_sales['Site'] == s) & (df_sales['Date'] >= start_of_last_month) & (df_sales['Date'] <= end_of_last_month_mtd)
            mom_sales_map[s] = df_sales[mask_mom]['Value'].sum()
            
            # 去年同期 MTD 销售
            mask_yoy = (df_sales['Site'] == s) & (df_sales['Date'] >= start_of_last_year_month) & (df_sales['Date'] <= end_of_last_year_mtd)
            yoy_sales_map[s] = df_sales[mask_yoy]['Value'].sum()
        else:
            actual_sales_map[s] = 0.0
            mom_sales_map[s] = 0.0
            yoy_sales_map[s] = 0.0

    # 全局数据大盘汇总
    total_actual = sum(actual_sales_map.values())
    total_target = sum([target_data.get(s, 0) for s in fixed_sites_order])
    total_rate = (total_actual / total_target * 100) if total_target > 0 else 0
    capped_rate = min(total_rate, 100) 
    
    total_mom_historical = sum(mom_sales_map.values())
    total_yoy_historical = sum(yoy_sales_map.values())

    # ------------------------------------------
    # 🏆 板块一：全盘目标进度条
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
            cheer_msg = "🎉 完美达标！" if total_rate >= 100 else ("🔥 超前完成！" if total_rate >= time_progress_rate else "✨ 稳步前行，冲鸭！")
            custom_progress_html = (
                f'<div style="padding: 0px 20px;">'
                f'<div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #475569; font-weight: 600; font-size: 15px;">'
                f'<span>{cheer_msg}</span><span style="color: #f43f5e; font-size: 18px;">{total_rate:.1f}%</span>'
                f'</div>'
                f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 28px; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 22px;">'
                f'<div style="background: linear-gradient(90deg, #fbcfe8 0%, #f43f5e 100%); border-radius: 30px; width: {capped_rate}%; height: 100%;"></div>'
                f'<div style="position: absolute; top: -12px; left: calc({capped_rate}% - 20px); font-size: 32px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1));">🚀</div>'
                f'<div style="position: absolute; top: 0px; right: 10px; line-height: 28px; font-size: 18px;">🏁</div>'
                f'</div>'
                f'<div style="display: flex; justify-content: space-between; margin-bottom: 6px; color: #64748b; font-weight: 500; font-size: 13px;">'
                f'<span>⏳ 本月时间进度 ({current_day} / {days_in_month} 天)</span><span>{time_progress_rate:.1f}%</span>'
                f'</div>'
                f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 10px; position: relative; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">'
                f'<div style="background: linear-gradient(90deg, #bae6fd 0%, #3b82f6 100%); border-radius: 30px; width: {time_progress_rate}%; height: 100%;"></div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(custom_progress_html, unsafe_allow_html=True)

    st.write("---")

    # ------------------------------------------
    # 📈 板块二：新增 MTD 同比与环比大盘分析
    # ------------------------------------------
    st.markdown("### 📊 全局 MTD 同环比分析")
    with st.container(border=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        
        with col_m1:
            st.metric(label=f"本月累计销售额 (1日-{current_day}日)", value=f"${total_actual:,.2f}")
            
        with col_m2:
            # 计算环比 (MoM)
            if total_mom_historical > 0:
                mom_delta = ((total_actual - total_mom_historical) / total_mom_historical) * 100
                mom_str = f"{mom_delta:+.1f}%"
            else:
                mom_str = "0.0% (无历史录入)"
            st.metric(label=f"上月同期累计 ({start_of_last_month.strftime('%m/%d')}-{end_of_last_month_mtd.strftime('%m/%d')})", 
                      value=f"${total_mom_historical:,.2f}", delta=f"环比增速 {mom_str}")
                      
        with col_m3:
            # 计算同比 (YoY)
            if total_yoy_historical > 0:
                yoy_delta = ((total_actual - total_yoy_historical) / total_yoy_historical) * 100
                yoy_str = f"{yoy_delta:+.1f}%"
            else:
                yoy_str = "0.0% (无历史录入)"
            st.metric(label=f"去年同期累计 ({start_of_last_year_month.strftime('%Y/%m/%d')}-昨日)", 
                      value=f"${total_yoy_historical:,.2f}", delta=f"同比增速 {yoy_str}")

    st.write("---")

    # ------------------------------------------
    # 🌍 板块三：各站点完成明细 (双轨业务进度条)
    # ------------------------------------------
    st.markdown("### 🌍 各站点完成明细 (业绩 vs 时间)")
    with st.container(border=True):
        cols = st.columns(9)
        for i, site in enumerate(fixed_sites_order):
            with cols[i]:
                s_actual = actual_sales_map[site]
                s_target = target_data.get(site, 0)
                s_rate = (s_actual / s_target * 100) if s_target > 0 else 0
                
                # 提取该站点各自的同环比数值用于前端浮动标签提示
                s_mom_hist = mom_sales_map.get(site, 0)
                s_mom_text = f"{((s_actual-s_mom_hist)/s_mom_hist)*100:+.0f}%" if s_mom_hist > 0 else "0%"
                
                color = "normal" if s_rate >= time_progress_rate else "off"
                delta_str = f"环比 {s_mom_text}" if s_mom_hist > 0 else f"差额 ${s_target - s_actual:,.0f}"
                
                st.metric(
                    label=f"{en_to_cn[site]} (🎯${s_target:,.0f})", 
                    value=f"${s_actual:,.0f}", 
                    delta=delta_str,
                    delta_color=color
                )
                
                bar_color = '#10b981' if s_rate >= time_progress_rate else '#f43f5e'
                
                site_html = (
                    f'<div style="margin-top: 5px;">'
                    f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">'
                    f'<span>业绩</span><span style="font-weight: 600; color: {bar_color};">{s_rate:.1f}%</span>'
                    f'</div>'
                    f'<div style="background-color: #f1f5f9; border-radius: 10px; width: 100%; height: 6px; margin-bottom: 10px;">'
                    f'<div style="background-color: {bar_color}; border-radius: 10px; width: {min(s_rate, 100)}%; height: 100%;"></div>'
                    f'</div>'
                    f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom: 4px;">'
                    f'<span>时间</span><span>{time_progress_rate:.1f}%</span>'
                    f'</div>'
                    f'<div style="background-color: #f1f5f9; border-radius: 10px; width: 100%; height: 6px;">'
                    f'<div style="background-color: #3b82f6; border-radius: 10px; width: {time_progress_rate}%; height: 100%;"></div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(site_html, unsafe_allow_html=True)
else:
    st.info("👈 请配置 GCP JSON 密钥以接入数据。")
