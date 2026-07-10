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
    padding: 10px;
}

/* 覆盖原生卡片字体 */
div[data-testid="stMetricValue"] > div {
    color: #0f172a !important; font-size: 26px !important; font-weight: 800 !important;
}
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 14px !important; font-weight: 600 !important; }
div[data-testid="stMetricDelta"] > div { font-size: 14px !important; }

/* 自定义精美 HTML 表格悬浮效果 */
.custom-table-row:hover {
    background-color: #f1f5f9 !important;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 极速数据获取引擎 (同时抓取当月总计与历史明细)
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
        historical_records = []
        
        sheet2 = spreadsheet.worksheet("Sheet2")
        raw_data_2 = sheet2.get_all_values()
        
        if raw_data_2:
            headers = raw_data_2[0]
            default_year = str(datetime.datetime.now().year)
            if '年' in headers[0]:
                default_year = headers[0].replace('年', '').strip()
                
            for row in raw_data_2[1:]:
                if not row or not row[0]: continue
                first_col = row[0].strip()
                        
                # 1. 抓取底部的“总计”行
                if first_col == "总计":
                    sales_data = {} 
                    for i in range(1, min(len(headers), len(row))):
                        site = headers[i].strip()
                        if site == "": continue
                        val_str = row[i].strip()
                        clean_str = re.sub(r'[^\d\.-]', '', val_str)
                        sales_data[site] = float(clean_str) if clean_str else 0.0
                        
                # 2. 抓取“分站点目标”行
                elif first_col == "分站点目标":
                    target_data = {} 
                    for i in range(1, min(len(headers), len(row))):
                        site = headers[i].strip()
                        if site == "": continue
                        val_str = row[i].strip()
                        clean_str = re.sub(r'[^\d\.-]', '', val_str)
                        target_data[site] = float(clean_str) if clean_str else 0.0
                        
                # 3. 智能抓取所有历史明细行
                elif re.search(r'\d', first_col): 
                    try:
                        if "月" in first_col and "日" in first_col:
                            month = first_col.split('月')[0].strip()
                            day = first_col.split('月')[1].replace('日', '').strip()
                            date_val = pd.to_datetime(f"{default_year}-{month}-{day}", errors='coerce')
                        else:
                            date_val = pd.to_datetime(first_col, errors='coerce')
                        
                        if pd.notna(date_val):
                            for i in range(1, min(len(headers), len(row))):
                                site = headers[i].strip()
                                if site == "": continue
                                val_str = row[i].strip()
                                clean_str = re.sub(r'[^\d\.-]', '', val_str)
                                val = float(clean_str) if clean_str else 0.0
                                historical_records.append({
                                    "Date": date_val,
                                    "Site": site,
                                    "Value": val
                                })
                    except:
                        continue
                        
        df_hist = pd.DataFrame(historical_records)
        if not df_hist.empty:
            df_hist['Date'] = pd.to_datetime(df_hist['Date']).dt.normalize()
            
        return {"sales": sales_data, "targets": target_data, "historical_df": df_hist}
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
    <h1 style="color: #1e293b; font-size: 32px; font-weight: 800; margin-bottom: 4px;">🚀 SEO数据看板</h1>
    <div style="color: #64748b; font-size: 14px;">报表同步基准日：{latest_date.strftime('%Y-%m-%d')}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("✨ 正在召唤看板数据..."):
    data_dict = load_and_transform_google_sheet()

if data_dict:
    sales_data = data_dict["sales"]
    target_data = data_dict["targets"]
    df_hist = data_dict["historical_df"]
    
    # 强制固定业务顺序
    fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
    
    # 🔥 核心升级：在这里直接为国家名字前加上高颜值国旗 Emoji，全局通用！
    en_to_cn = {
        "DE": "🇩🇪 德国", 
        "FR": "🇫🇷 法国", 
        "ES": "🇪🇸 西班牙", 
        "IT": "🇮🇹 意大利", 
        "NL": "🇳🇱 荷兰", 
        "NO": "🇳🇴 挪威", 
        "SE": "🇸🇪 瑞典", 
        "FI": "🇫🇮 芬兰", 
        "PL": "🇵🇱 波兰"
    }
    
    # --- 原版计算逻辑 ---
    total_actual = sales_data.get("总计", sum([sales_data.get(s, 0) for s in fixed_sites_order]))
    total_target = sum([target_data.get(s, 0) for s in fixed_sites_order])
    total_rate = (total_actual / total_target * 100) if total_target > 0 else 0
    capped_rate = min(total_rate, 100) 
    
    days_in_month = calendar.monthrange(latest_date.year, latest_date.month)[1]
    current_day = latest_date.day
    time_progress_rate = (current_day / days_in_month) * 100

    if total_rate >= 100:
        cheer_msg = "🎉 完美达标！太棒啦，大家辛苦了！"
        st.balloons() 
    elif total_rate >= time_progress_rate:
        cheer_msg = "🔥 超前完成！继续保持这个节奏！"
    elif total_rate >= 80:
        cheer_msg = "💪 胜利就在眼前，加把劲冲刺！"
    else:
        cheer_msg = "✨ 稳步前行，今天也要冲鸭！"

    # ------------------------------------------
    # 🏆 第一板块：全盘进度 (火箭业绩 + 时间流逝 双进度条)
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
            custom_progress_html = (
                f'<div style="padding: 0px 20px;">'
                f'<div style="display: flex; justify-content: space-between; margin-bottom: 8px; color: #475569; font-weight: 600; font-size: 15px;">'
                f'<span>{cheer_msg}</span>'
                f'<span style="color: #f43f5e; font-size: 18px;">{total_rate:.1f}%</span>'
                f'</div>'
                f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 28px; position: relative; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 22px;">'
                f'<div style="background: linear-gradient(90deg, #fbcfe8 0%, #f43f5e 100%); border-radius: 30px; width: {capped_rate}%; height: 100%; transition: width 1.5s ease-in-out;"></div>'
                f'<div style="position: absolute; top: -12px; left: calc({capped_rate}% - 20px); font-size: 32px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.1)); transition: left 1.5s ease-in-out;">🚀</div>'
                f'<div style="position: absolute; top: 0px; right: 10px; line-height: 28px; font-size: 18px;">🏁</div>'
                f'</div>'
                f'<div style="display: flex; justify-content: space-between; margin-bottom: 6px; color: #64748b; font-weight: 500; font-size: 13px;">'
                f'<span>⏳ 本月时间进度 ({current_day} / {days_in_month} 天)</span>'
                f'<span>{time_progress_rate:.1f}%</span>'
                f'</div>'
                f'<div style="background-color: #f1f5f9; border-radius: 30px; width: 100%; height: 10px; position: relative; box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);">'
                f'<div style="background: linear-gradient(90deg, #bae6fd 0%, #3b82f6 100%); border-radius: 30px; width: {time_progress_rate}%; height: 100%; transition: width 1.5s ease-in-out;"></div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(custom_progress_html, unsafe_allow_html=True)

    st.write("---")

    # ------------------------------------------
    # 🌍 第二板块：各站点完成明细卡片
    # ------------------------------------------
    st.markdown("### 🌍 各站点完成明细 (业绩 vs 时间)")
    
    with st.container(border=True):
        cols = st.columns(9)
        for i, site in enumerate(fixed_sites_order):
            with cols[i]:
                s_actual = sales_data.get(site, 0)
                s_target = target_data.get(site, 0)
                s_rate = (s_actual / s_target * 100) if s_target > 0 else 0
                
                color = "normal" if s_rate >= time_progress_rate else "off"
                delta_str = f"差额 ${s_target - s_actual:,.0f}" if s_target > s_actual else "已达标"
                
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

    st.write("---")
    
    # ------------------------------------------
    # 📈 第三板块：MTD 同比与环比大盘分析
    # ------------------------------------------
    st.markdown("### 📊 全局 MTD 同环比趋势")
    
    with st.container(border=True):
        if not df_hist.empty:
            start_of_current_month = latest_date.replace(day=1)
            
            try:
                start_of_last_month = (start_of_current_month - pd.Timedelta(days=1)).replace(day=1)
                end_of_last_month_mtd = start_of_last_month + pd.Timedelta(days=current_day - 1)
            except:
                start_of_last_month = start_of_current_month - pd.DateOffset(months=1)
                end_of_last_month_mtd = start_of_last_month + pd.DateOffset(days=current_day - 1)

            start_of_last_year_month = start_of_current_month - pd.DateOffset(years=1)
            end_of_last_year_mtd = start_of_last_year_month + pd.DateOffset(days=current_day - 1)
            
            mask_mom = (df_hist['Date'] >= start_of_last_month) & (df_hist['Date'] <= end_of_last_month_mtd)
            total_mom_historical = df_hist[mask_mom]['Value'].sum()
            
            mask_yoy = (df_hist['Date'] >= start_of_last_year_month) & (df_hist['Date'] <= end_of_last_year_mtd)
            total_yoy_historical = df_hist[mask_yoy]['Value'].sum()
            
            col_m1, col_m2, col_m3 = st.columns(3)
            
            with col_m1:
                st.metric(label=f"当前本月累计 (1日-{current_day}日)", value=f"${total_actual:,.2f}")
                
            with col_m2:
                if total_mom_historical > 0:
                    mom_delta = ((total_actual - total_mom_historical) / total_mom_historical) * 100
                    mom_str = f"{mom_delta:+.1f}% (环比)"
                else:
                    mom_str = "0.0% (无历史)"
                st.metric(label=f"上月同期累计 ({start_of_last_month.strftime('%m/%d')}-{end_of_last_month_mtd.strftime('%m/%d')})", 
                          value=f"${total_mom_historical:,.2f}", delta=mom_str)
                          
            with col_m3:
                if total_yoy_historical > 0:
                    yoy_delta = ((total_actual - total_yoy_historical) / total_yoy_historical) * 100
                    yoy_str = f"{yoy_delta:+.1f}% (同比)"
                else:
                    yoy_str = "0.0% (无历史)"
                st.metric(label=f"去年同期累计 ({start_of_last_year_month.strftime('%Y/%m/%d')}-{end_of_last_year_mtd.strftime('%m/%d')})", 
                          value=f"${total_yoy_historical:,.2f}", delta=yoy_str)
        else:
            st.info("尚未在表格中抓取到有效的历史日期数据，同环比计算暂时休息中...")

    st.write("---")

    # ------------------------------------------
    # 🗄️ 第四板块：高级 HTML 报表 (带精美表头国旗图标)
    # ------------------------------------------
    st.markdown("### 🗄️ 本月各站点每日销售明细")
    with st.container(border=True):
        if not df_hist.empty:
            start_of_current_month = latest_date.replace(day=1)
            
            mask_mtd = (df_hist['Date'] >= start_of_current_month) & (df_hist['Date'] <= latest_date)
            df_mtd_daily = df_hist[mask_mtd].copy()

            if not df_mtd_daily.empty:
                df_pivot = df_mtd_daily.pivot_table(index='Date', columns='Site', values='Value', aggfunc='sum').reset_index()

                if "总计" not in df_pivot.columns:
                    avail_sites = [s for s in fixed_sites_order if s in df_pivot.columns]
                    df_pivot['总计'] = df_pivot[avail_sites].sum(axis=1)

                display_cols = ['Date'] + [s for s in fixed_sites_order if s in df_pivot.columns] + ['总计']
                df_pivot = df_pivot[display_cols]
                
                df_pivot = df_pivot.sort_values('Date', ascending=False)
                df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')

                # 重命名中文字段 (自动带上漂亮的国旗)
                rename_dict = {s: en_to_cn.get(s, s) for s in fixed_sites_order}
                rename_dict["Date"] = "日期"
                df_pivot = df_pivot.rename(columns=rename_dict)

                # HTML 表格构建
                html_table = '<div style="overflow-x: auto; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">'
                html_table += '<table style="width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; text-align: center;">'
                
                # 表头渲染 (国旗图标将在此完美呈现)
                html_table += '<thead><tr style="background-color: #ffffff;">'
                for col in df_pivot.columns:
                    html_table += f'<th style="color: #2563eb; font-weight: 600; padding: 14px 10px; border-bottom: 2px solid #e2e8f0;">{col}</th>'
                html_table += '</tr></thead><tbody>'
                
                # 数据行渲染
                for idx, row in df_pivot.iterrows():
                    bg_color = "#ffffff" if idx % 2 == 0 else "#f8fafc"
                    html_table += f'<tr class="custom-table-row" style="background-color: {bg_color}; border-bottom: 1px solid #f1f5f9; transition: background-color 0.2s;">'
                    
                    for col in df_pivot.columns:
                        val = row[col]
                        if isinstance(val, (int, float)):
                            display_val = f"${val:,.2f}" if val != 0 else "$0.00"
                        else:
                            display_val = str(val)
                        
                        cell_style = "padding: 12px 10px; color: #334155;"
                        if col == "总计":
                            cell_style += " background-color: #ecfdf5; font-weight: 700; color: #065f46; border-left: 1px solid #d1fae5;"
                        elif col == "日期":
                            cell_style += " font-weight: 500; color: #475569;"
                            
                        html_table += f'<td style="{cell_style}">{display_val}</td>'
                        
                    html_table += '</tr>'
                html_table += '</tbody></table></div>'

                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.info("本月暂无每日明细数据。")
        else:
            st.info("尚未抓取到历史明细数据。")

else:
    st.info("👈 请配置 GCP JSON 密钥以接入数据。")
