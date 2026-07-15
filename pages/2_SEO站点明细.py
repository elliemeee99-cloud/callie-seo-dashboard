import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import re
import gc

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO站点明细", page_icon="🌍", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #f8fafc !important; }
.site-header {
    background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
    color: white;
    padding: 12px 24px;
    border-radius: 12px 12px 0 0;
    font-size: 20px;
    font-weight: 700;
    margin-top: 30px;
}
.site-container {
    background-color: white;
    border: 1px solid #e2e8f0;
    border-radius: 0 0 12px 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ 站点全量明细数据引擎 (🔥 修复同行识别 Bug)
# ==========================================
@st.cache_data(ttl=3600)
def load_site_full_details():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit")
        
        cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
        default_year = str(datetime.datetime.now().year)
        
        ws_all = spreadsheet.worksheet("All")
        raw_data = ws_all.get_all_values()
        
        records = []
        dates_row = []
        current_site = None
        
        for row in raw_data:
            if not row: continue
            first_cell = str(row[0]).strip()
            
            # 1. 捕捉时间轴 (去掉了 continue，防止跳过同行的 Callie 站点名)
            if len(row) > 1:
                check_val = str(row[1]).strip()
                if not check_val and len(row) > 2: check_val = str(row[2]).strip()
                if "202" in check_val or ("月" in check_val and "日" in check_val) or re.match(r'^\d{1,2}[-/]\d{1,2}$', check_val):
                    dates_row = [str(x).strip() for x in row[1:]]
                
            # 2. 捕捉国家区块
            if first_cell.startswith("Callie ") and len(first_cell) <= 15:
                current_site = first_cell.replace("Callie ", "").strip()
                if current_site in cn_to_en:
                    current_site = cn_to_en[current_site]
                continue
            
            # 3. 动态抓取该国家下的【所有】指标行，原样保留字符串
            if current_site and first_cell and first_cell not in ["", "总计"]:
                metric_name = first_cell
                # 排除星期几这种无用行
                if metric_name in ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日", "占比情况"]:
                    continue
                    
                values = row[1:]
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i] != "":
                        raw_val = str(values[i]).strip()
                        if raw_val:
                            # 统一日期格式以便后续排序
                            d_str = dates_row[i]
                            if "月" in d_str and "日" in d_str:
                                try:
                                    m = d_str.split('月')[0].strip()
                                    d = d_str.split('月')[1].replace('日', '').strip()
                                    d_str = f"{default_year}-{m}-{d}"
                                except:
                                    pass
                            
                            records.append({
                                "Site": current_site,
                                "Metric": metric_name,
                                "Date_str": d_str,
                                "Value": raw_val # 原样保留：金额、百分比、文本全收录
                            })
                            
        df = pd.DataFrame(records)
        
        # 🔥 增加安全判定锁，防止空表报错
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date_str'], errors='coerce')
            df = df.dropna(subset=['Date'])
        
        del raw_data
        gc.collect()
        
        return df
    except Exception as e:
        st.error(f"🔌 数据连接失败: {e}")
        return None

# ==========================================
# 📐 页面布局与交互
# ==========================================
real_today = pd.Timestamp(datetime.datetime.now().date())
# 默认展示最近 14 天的数据
default_start = real_today - pd.Timedelta(days=15)
default_end = real_today - pd.Timedelta(days=1)

st.title("🌍 各站点 SEO 全量明细数据")
st.markdown("<div style='color: #64748b; margin-bottom: 20px;'>本页面展示了底层 All 表单中录入的所有原始细分指标矩阵。</div>", unsafe_allow_html=True)

with st.spinner("✨ 正在逐行扫描站点明细数据..."):
    df_all = load_site_full_details()

if df_all is not None and not df_all.empty:
    # 顶部统一时间控制器
    with st.container(border=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            date_range = st.date_input(
                "📅 选择查询日期范围", 
                value=(default_start.date(), default_end.date()),
                max_value=real_today.date()
            )
            
    # 日期解析逻辑
    if isinstance(date_range, (tuple, list)):
        if len(date_range) == 2:
            start_date, end_date = date_range
        elif len(date_range) == 1:
            start_date = end_date = date_range[0]
        else:
            start_date, end_date = default_start.date(), default_end.date()
    else:
        start_date = end_date = date_range
        
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # 应用日期过滤
    mask = (df_all['Date'].dt.date >= start_date) & (df_all['Date'].dt.date <= end_date)
    df_filtered = df_all[mask].copy()

    if df_filtered.empty:
        st.warning(f"⚠️ 在 {start_date} 至 {end_date} 期间没有提取到任何数据，请尝试放宽时间范围。")
    else:
        # 指定严格的展示顺序: 德法西意荷挪瑞芬波
        fixed_sites_order = ["DE", "FR", "ES", "IT", "NL", "NO", "SE", "FI", "PL"]
        en_to_cn = {
            "DE": "🇩🇪 德国 (Callie DE)", "FR": "🇫🇷 法国 (Callie FR)", "ES": "🇪🇸 西班牙 (Callie ES)", 
            "IT": "🇮🇹 意大利 (Callie IT)", "NL": "🇳🇱 荷兰 (Callie NL)", "NO": "🇳🇴 挪威 (Callie NO)", 
            "SE": "🇸🇪 瑞典 (Callie SE)", "FI": "🇫🇮 芬兰 (Callie FI)", "PL": "🇵🇱 波兰 (Callie PL)"
        }

        # 遍历国家顺序渲染视图
        for site in fixed_sites_order:
            df_site = df_filtered[df_filtered['Site'] == site]
            if not df_site.empty:
                # 绘制表头
                site_title = en_to_cn.get(site, f"🌍 {site}")
                st.markdown(f"<div class='site-header'>{site_title}</div>", unsafe_allow_html=True)
                
                with st.container():
                    st.markdown("<div class='site-container'>", unsafe_allow_html=True)
                    
                    # 宽长转换 (Pivot)：让 Metric 做行，Date 做列
                    df_pivot = df_site.pivot_table(
                        index='Metric', 
                        columns='Date', 
                        values='Value', 
                        aggfunc=lambda x: ' '.join(str(v) for v in x) # 保留字符串原始样貌
                    )
                    
                    # 将列名(日期)转换为字符串并降序排列 (最新的一天排在最左边)
                    sorted_dates = sorted(df_pivot.columns, reverse=True)
                    df_pivot = df_pivot[sorted_dates]
                    df_pivot.columns = [d.strftime('%Y-%m-%d') for d in df_pivot.columns]
                    
                    # 使用 Streamlit 自带的交互式表格渲染
                    st.dataframe(
                        df_pivot, 
                        use_container_width=True,
                        height=400 
                    )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("尚未扫描到有效的站点数据，请检查网络连接或表单格式。")
