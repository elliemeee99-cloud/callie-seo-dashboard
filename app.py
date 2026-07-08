import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import time

# 网页基础设置
st.set_page_config(page_title="全球矩阵 SEO 流量作战大屏 V1.0", page_icon="📈", layout="wide")

# ==========================================
# ⚙️ 核心数据获取与清洗引擎 (专为 Callie 日报定制)
# ==========================================

# 魔法缓存：每天自动刷新一次，避免超额调用 API
@st.cache_data(ttl="1d")
def load_and_transform_google_sheet():
    try:
        # 1. 读取谷歌授权秘钥
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        
        # 2. 连接到谷歌账号并打开表格
        client = gspread.authorize(creds)
        # 表格的 URL ID
        sheet_url = "https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit"
        sheet = client.open_by_url(sheet_url).sheet1
        
        # 3. 提取所有原始数据 (这是一个嵌套列表)
        raw_data = sheet.get_all_values()
        
        # 4. 🔥 针对 Callie 表格的“智能切割切割与翻转引擎”
        clean_records = []
        current_site = None
        dates_row = []
        
        for row_idx, row in enumerate(raw_data):
            if not row or not row[0]:
                continue
                
            first_cell = str(row[0]).strip()
            
            # 探测是不是国家站的开始行 (如 "Callie FR")
            if first_cell.startswith("Callie ") and len(first_cell) <= 10:
                current_site = first_cell.replace("Callie ", "").strip()
                # 日期就在这一行的后面
                dates_row = row[1:]
                continue
                
            # 探测指标行 (如果当前有国家站，且不是星期、要事记等文字描述)
            if current_site and first_cell not in ["星期五", "星期六", "星期日", "星期一", "星期二", "星期三", "星期四", "网站要事记", "TDK优化记录表"]:
                metric_name = first_cell
                values = row[1:]
                
                # 开始执行数据翻转：把横向日期和数值对齐拼装
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i].strip() != "":
                        date_str = dates_row[i]
                        val_str = values[i]
                        
                        # 清洗数值：去掉美元符号、逗号、百分号，转为浮点数
                        clean_val = 0.0
                        if val_str:
                            val_str = str(val_str).replace("$", "").replace(",", "").replace("%", "").strip()
                            try:
                                clean_val = float(val_str)
                            except:
                                clean_val = 0.0
                                
                        clean_records.append({
                            "Date": date_str,
                            "Site": current_site,
                            "Metric": metric_name,
                            "Value": clean_val
                        })
                        
        # 5. 转化为标准长表 DataFrame
        df_long = pd.DataFrame(clean_records)
        df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce')
        df_long = df_long.dropna(subset=['Date']) # 丢弃无效日期
        
        return df_long
    except Exception as e:
        st.error(f"🔌 连接云端数据湖失败，请检查 GCP 密钥配置是否正确。错误详情：{e}")
        return pd.DataFrame()

# ==========================================
# 📊 前端交互面板与可视化
# ==========================================

st.title("📈 全球矩阵 SEO 流量作战大屏")
st.caption("数据源直连 Google Sheets：Callie小语种日报数据汇总 (后台自动转置清洗版)")

with st.spinner("🚀 正在从谷歌云端抽取并切割清洗海量数据，请稍候..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    st.success(f"✅ 数据湖同步成功！已自动将人力宽表翻转为 {len(df_master)} 条标准时序数据单元。")
    st.write("---")
    
    # --- 全局控制器 ---
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    # 获取所有的站点和指标名称
    all_sites = sorted(df_master['Site'].unique().tolist())
    all_metrics = sorted(df_master['Metric'].unique().tolist())
    
    with col_filter1:
        selected_sites = st.multiselect("🌍 筛选目标分站：", all_sites, default=all_sites)
    with col_filter2:
        # 默认看流量相关的核心指标
        default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
        if not default_metrics: default_metrics = [all_metrics[0]]
        selected_metrics = st.multiselect("📊 筛选对比指标：", all_metrics, default=default_metrics)
    with col_filter3:
        # 时间范围选择器 (默认展示近 30 天)
        min_date = df_master['Date'].min()
        max_date = df_master['Date'].max()
        selected_dates = st.date_input("📅 筛选时间区间：", [min_date, max_date], min_value=min_date, max_value=max_date)

    if len(selected_dates) == 2 and selected_sites and selected_metrics:
        start_date, end_date = selected_dates
        
        # 根据用户的选择过滤数据
        mask = (df_master['Site'].isin(selected_sites)) & \
               (df_master['Metric'].isin(selected_metrics)) & \
               (df_master['Date'] >= pd.to_datetime(start_date)) & \
               (df_master['Date'] <= pd.to_datetime(end_date))
        df_filtered = df_master[mask]
        
        if not df_filtered.empty:
            st.subheader("📈 核心数据时序追踪 (Plotly 交互视图)")
            
            # 使用 Plotly Express 绘制绚丽的折线图 (Hover 支持，可缩放)
            # 为了在一张图里展示不同国家和不同指标，我们拼装一个组合 Label
            df_filtered['Legend'] = df_filtered['Site'] + " - " + df_filtered['Metric']
            
            fig = px.line(
                df_filtered, 
                x="Date", y="Value", color="Legend",
                markers=True,
                title="分站与指标多维对比走势图",
                template="plotly_white"
            )
            
            fig.update_layout(
                xaxis_title="日期",
                yaxis_title="数值",
                legend_title="图例 (分站 - 指标)",
                hovermode="x unified" # 鼠标放上去可以一根竖线对比当天所有数据
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("---")
            st.subheader("🗄️ 底层数据透视表 (已由横转竖，供运营直接下载审计)")
            # Pivot 回来，让数据看起来更紧凑一点展示
            df_pivot = df_filtered.pivot_table(index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum').reset_index()
            # 倒序排列，最新日期在上面
            df_pivot = df_pivot.sort_values(by="Date", ascending=False)
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        else:
            st.warning("所选区间或条件下无数据，请调整筛选器。")
else:
    st.info("👈 请先在 Streamlit Secrets 中配置好 GCP 的 JSON 密钥，并在 Google Sheets 中共享权限给 Bot 邮箱。")
