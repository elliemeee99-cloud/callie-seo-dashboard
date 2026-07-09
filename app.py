import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import datetime
import re
from openai import OpenAI

# 网页基础设置
st.set_page_config(page_title="SEO数据看板", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 终极定制 CSS (高阶卡片与排版)
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f4f7f9 !important; }
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}
.block-container { padding-top: 2rem !important; max-width: 95% !important; }

/* 站点和时间 Pills 标签样式 */
button[data-testid="stPill"] {
    background-color: #ffffff !important; 
    border: 1px solid #e2e8f0 !important;
    color: #475569 !important; 
    font-weight: 500 !important; 
    border-radius: 6px !important;
    padding: 6px 20px !important; 
    margin-right: 8px !important; 
    transition: all 0.2s;
}
button[data-testid="stPill"][aria-selected="true"] {
    background-color: #2563eb !important; 
    color: #ffffff !important;
    border-color: #2563eb !important; 
    font-weight: 600 !important;
}

/* 圆角分区容器 */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

/* 核心数据大字卡片样式 */
div[data-testid="stMetricValue"] > div {
    color: #2563eb !important; font-size: 32px !important; font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 14px !important; font-weight: 600 !important; }

/* AI 洞察报告框 */
.ai-insight-box {
    background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 18px;
    border-radius: 8px; color: #1e3a8a; font-size: 14px; line-height: 1.6; margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取引擎 (双表融合读取)
# ==========================================
@st.cache_data(ttl="1h")
def load_and_transform_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit")
        
        clean_records = []
        
        # --- 1. 读取 Sheet2 (专属 SEO 销售额及底部总计) ---
        current_month_totals = {}
        try:
            sheet2 = spreadsheet.worksheet("Sheet2")
            raw_data_2 = sheet2.get_all_values()
            if raw_data_2:
                headers = raw_data_2[0]
                year_str = headers[0].replace('年', '').strip() if '年' in headers[0] else str(datetime.datetime.now().year)
                
                for row in raw_data_2[1:]:
                    if not row or not row[0]: continue
                    first_col = row[0].strip()
                    
                    # 抓取日常数据
                    if "月" in first_col and "日" in first_col:
                        month = first_col.split('月')[0].strip()
                        day = first_col.split('月')[1].replace('日', '').strip()
                        date_val = f"{year_str}-{month}-{day}"
                        
                        for i in range(1, min(len(headers), len(row))):
                            site = headers[i].strip()
                            if site in ["总计", ""] : continue
                            
                            val_str = row[i].strip()
                            if not val_str or val_str == "-" or val_str.lower() in ["n/a", "null", "#num!"]:
                                val = 0.0
                            else:
                                clean_str = re.sub(r'[^\d\.-]', '', val_str)
                                val = float(clean_str) if clean_str else 0.0
                                
                            clean_records.append({
                                "Date": date_val, "Site": site, "Metric": "SEO销售额", "Value": val
                            })
                            
                    # 💡 强力抓取底部的“总计”行，完美匹配你的表格
                    elif first_col == "总计":
                        current_month_totals = {} # 每次遇到覆盖，确保抓到的是最底下的最新总计
                        for i in range(1, min(len(headers), len(row))):
                            site = headers[i].strip()
                            if site == "": continue
                            
                            val_str = row[i].strip()
                            clean_str = re.sub(r'[^\d\.-]', '', val_str)
                            val = float(clean_str) if clean_str else 0.0
                            
                            if site == "总计":
                                current_month_totals['Global'] = val
                            else:
                                current_month_totals[site] = val
        except Exception as e:
            print(f"Sheet2 读取跳过: {e}")
            
        # 将总计作为特殊指标塞入数据源（设定一个未来日期以防污染走势图）
        if current_month_totals:
            for site, val in current_month_totals.items():
                s_name = "ALL" if site == "Global" else site
                clean_records.append({
                    "Date": "2099-12-31", "Site": s_name, "Metric": "SEO销售额_当月总计", "Value": val
                })

        # --- 2. 读取 Sheet1 (其他流量指标) ---
        sheet1 = spreadsheet.sheet1
        raw_data_1 = sheet1.get_all_values()
        current_site = None
        dates_row = []
        
        for row_idx, row in enumerate(raw_data_1):
            if not row or not row[0]: continue
            first_cell = str(row[0]).strip()
            
            if first_cell.startswith("Callie ") and len(first_cell) <= 10:
                current_site = first_cell.replace("Callie ", "").strip()
                dates_row = row[1:]
                continue
                
            if current_site and first_cell not in ["星期五", "星期六", "星期日", "星期一", "星期二", "星期三", "星期四", "网站要事记", "TDK优化记录表"]:
                metric_name = first_cell
                if any(kw in metric_name for kw in ["销售", "Sales", "成交", "转化价值"]):
                    continue
                    
                values = row[1:]
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i].strip() != "":
                        val_str = str(values[i]).strip()
                        if not val_str or val_str == "-" or val_str.lower() in ["n/a", "null"]:
                            clean_val = 0.0
                        else:
                            clean_str = re.sub(r'[^\d\.-]', '', val_str.replace("$", "").replace(",", "").replace("%", ""))
                            try: clean_val = float(clean_str) if clean_str else 0.0
                            except: clean_val = 0.0
                                
                        clean_records.append({
                            "Date": dates_row[i], "Site": current_site, 
                            "Metric": metric_name, "Value": clean_val
                        })
                        
        df_long = pd.DataFrame(clean_records)
        df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce').dt.normalize()
        df_long = df_long.dropna(subset=['Date']) 
        return df_long
    except Exception as e:
        st.error(f"🔌 云端连接失败: {e}")
        return pd.DataFrame()

# ==========================================
# 🤖 DeepSeek AI 分析
# ==========================================
@st.cache_data(ttl="2h") 
def get_ai_insight(data_summary):
    try:
        client = OpenAI(api_key=st.secrets["DEEPSEEK"]["api_key"], base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个资深的小语种SEO数据分析专家。请根据提供的昨日核心指标，用简练的中文给出2点洞察（趋势、异常或建议）。直接说结论。"},
                {"role": "user", "content": f"昨日数据：\n{data_summary}"}
            ]
        )
        return response.choices[0].message.content
    except:
        return "⚠️ AI 洞察暂时不可用，请检查网络或 API Key。"


# ==========================================
# 📐 UI 布局与页面渲染
# ==========================================

# 锁定物理世界绝对时间
real_today = pd.Timestamp(datetime.datetime.now().date())
latest_date = real_today - pd.Timedelta(days=1)  
prev_date = latest_date - pd.Timedelta(days=1)   

st.markdown(f"""
<div style="margin-bottom: 25px;">
    <h1 style="color: #1e293b; font-size: 28px; font-weight: 700; margin-bottom: 4px;">SEO数据看板</h1>
    <div style="color: #64748b; font-size: 13px;">报表同步基准日：{latest_date.strftime('%Y-%m-%d')}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("🚀 正在抓取报表底层总计与明细..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}
    raw_sites = sorted([s for s in df_master['Site'].unique().tolist() if s != "ALL"])
    display_sites = ["全部站点"] + [en_to_cn.get(s, s) for s in raw_sites]
    
    # ------------------------------------------
    # 📌 1. 顶部全局控制台
    # ------------------------------------------
    selected_site_cn = st.pills("🌍 站点选择", display_sites, default="全部站点", label_visibility="collapsed")
    
    col_filter1, col_filter2 = st.columns([1, 1.5])
    with col_filter1:
        with st.container(border=True):
            st.markdown("<span style='color:#64748b; font-size:13px;'>📅 分析周期</span>", unsafe_allow_html=True)
            times = ["过去1天", "过去7天", "过去14天"]
            selected_time = st.pills("时间选择", times, default="过去7天", label_visibility="collapsed")
            
    with col_filter2:
        with st.container(border=True):
            st.markdown("<span style='color:#64748b; font-size:13px;'>📈 附加指标展示</span>", unsafe_allow_html=True)
            all_metrics = sorted([m for m in df_master['Metric'].unique() if "当月总计" not in m])
            default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
            if not default_metrics: default_metrics = [all_metrics[0]]
            selected_metrics = st.pills("指标选择", all_metrics, default=default_metrics, selection_mode="multi", label_visibility="collapsed")
            if not selected_metrics: selected_metrics = default_metrics

    st.write("")

    sales_metric_key = "SEO销售额" 
    traffic_metric = next((m for m in all_metrics if m in ["SEO流量", "网站总流量"]), all_metrics[0])
    target_sites = raw_sites if selected_site_cn == "全部站点" else [cn_to_en.get(selected_site_cn, selected_site_cn)]

    # ------------------------------------------
    # 🤖 2. 单日表现 & AI 洞察 (置于大盘顶部)
    # ------------------------------------------
    st.markdown("### 📊 昨日核心表现")
    with st.container(border=True):
        df_site = df_master[df_master['Site'].isin(target_sites)]
        if not df_site.empty:
            day_data = df_site[df_site['Date'] == latest_date].groupby('Metric')['Value'].sum()
            prev_day_data = df_site[df_site['Date'] == prev_date].groupby('Metric')['Value'].sum()
            
            if not day_data.empty:
                ai_summary = f"站点: {selected_site_cn}\n日期: {latest_date.strftime('%Y-%m-%d')}\n"
                for m in selected_metrics + [sales_metric_key]:
                    cur_v = day_data.get(m, 0)
                    pre_v = prev_day_data.get(m, 0)
                    diff = f"{((cur_v-pre_v)/pre_v)*100:.1f}%" if pre_v > 0 else "0%"
                    ai_summary += f"- {m}: {cur_v} (较前日 {diff})\n"
                    
                with st.spinner("🧠 DeepSeek 正在分析昨日数据..."):
                    insight_text = get_ai_insight(ai_summary)
                    st.markdown(f'<div class="ai-insight-box">🤖 <b>AI 诊断：</b><br>{insight_text}</div>', unsafe_allow_html=True)
            
            col_c1, col_c2, col_c3 = st.columns(3)
            date_label = latest_date.strftime('%m/%d')
            
            with col_c1:
                title_text = f"昨日 {sales_metric_key}"
                current_sales = day_data.get(sales_metric_key, 0.0)
                prev_sales = prev_day_data.get(sales_metric_key, 0.0)
                delta_str = f"{((current_sales - prev_sales) / prev_sales) * 100:+.1f}% 对比前日" if prev_sales > 0 else "0.0% 对比前日"
                st.metric(label=title_text, value=f"${current_sales:,.2f}", delta=delta_str)
                
            with col_c2:
                t_val = day_data.get(traffic_metric, 0.0)
                p_val = prev_day_data.get(traffic_metric, 0.0)
                d_str = f"{((t_val-p_val)/p_val)*100:+.1f}% 对比前日" if p_val > 0 else "0.0% 对比前日"
                st.metric(label=f"昨日 {traffic_metric}", value=f"{t_val:,.0f}", delta=d_str)

            with col_c3:
                st.metric(label="当前透视对象", value=f"{selected_site_cn}", delta=f"数据完整")
        else:
            st.warning(f"没有找到 {selected_site_cn} 的单日数据。")

    # ------------------------------------------
    # 📈 3. 趋势图区域
    # ------------------------------------------
    st.markdown("### 📈 时序走势明细")
    
    if selected_time == "过去1天": start_date = latest_date
    elif selected_time == "过去7天": start_date = latest_date - pd.Timedelta(days=6)
    else: start_date = latest_date - pd.Timedelta(days=13)
        
    mask = (df_site['Date'] >= start_date) & (df_site['Date'] <= latest_date)
    df_filtered = df_site[mask]
    
    with st.container(border=True):
        df_chart = df_filtered[df_filtered['Metric'].isin(selected_metrics + [sales_metric_key])].copy()
        if not df_chart.empty:
            df_chart['Legend'] = df_chart['Site'] + " - " + df_chart['Metric']
            fig = px.line(
                df_chart, x="Date", y="Value", color="Legend", markers=True, template="plotly_white",
                color_discrete_sequence=["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#0284c7"]
            )
            fig.update_layout(xaxis_title="", yaxis_title="数值", hovermode="x unified", margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"选定区间尚未录入数据。")

    st.write("---")

    # ------------------------------------------
    # 💰 4. 本月累计SEO销售额 (直取 Sheet2 底栏总计，放在明细正上方)
    # ------------------------------------------
    st.markdown("### 💰 本月累计SEO销售额")
    with st.container(border=True):
        mtd_data = df_master[df_master['Metric'] == 'SEO销售额_当月总计']
        
        if not mtd_data.empty:
            global_val = mtd_data[mtd_data['Site'] == 'ALL']['Value'].sum()
            st.markdown(f"<div style='color:#64748b; font-size:14px; margin-bottom:10px;'>📊 匹配数据源：Sheet2 表底『总计』行实时抓取</div>", unsafe_allow_html=True)
            st.metric(f"🌐 全局本月累计SEO销售额", f"${global_val:,.2f}")
            st.markdown("---")
            
            st.markdown("<span style='color:#64748b; font-size:13px;'>🌍 各站点累计贡献排名</span>", unsafe_allow_html=True)
            site_mtd = mtd_data[mtd_data['Site'] != 'ALL'].set_index('Site')['Value'].sort_values(ascending=False)
            
            if not site_mtd.empty:
                num_cols = min(len(site_mtd), 6)
                cols = st.columns(num_cols)
                for i, (site_code, val) in enumerate(site_mtd.items()):
                    with cols[i % num_cols]:
                        site_name = en_to_cn.get(site_code, site_code)
                        st.metric(site_name, f"${val:,.0f}")
        else:
            st.info("尚未抓取到 Sheet2 的'总计'行数据。")

    st.write("---")
    
    # ------------------------------------------
    # 🗄️ 5. 明细数据报表
    # ------------------------------------------
    st.markdown("### 🗄️ 明细数据报表")
    if not df_chart.empty:
        df_pivot = df_chart.pivot_table(index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum').reset_index()
        df_pivot = df_pivot.sort_values(by="Date", ascending=False)
        df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
        st.dataframe(df_pivot, use_container_width=True, hide_index=True)
    else:
        st.write("暂无对应的明细报表。")
            
else:
    st.info("👈 请配置 GCP JSON 密钥以接入数据湖。")
