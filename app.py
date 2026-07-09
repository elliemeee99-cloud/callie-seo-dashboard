import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import datetime
import re
from openai import OpenAI

# 网页基础设置 (宽屏模式，隐藏默认侧边栏)
st.set_page_config(page_title="小语种SEO日报", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 终极定制 CSS (精美看板 UI)
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f4f7f9 !important; }
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}
.block-container { padding-top: 2rem !important; max-width: 95% !important; }
button[data-testid="stPill"] {
    background-color: #ffffff !important; border: 1px solid #e2e8f0 !important;
    color: #64748b !important; font-weight: 500 !important; border-radius: 6px !important;
    padding: 8px 24px !important; margin-right: 8px !important; transition: all 0.2s;
}
button[data-testid="stPill"][aria-selected="true"] {
    background-color: #2563eb !important; color: #ffffff !important;
    border-color: #2563eb !important; font-weight: 600 !important;
}
div[data-testid="metric-container"] {
    background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); display: flex;
    flex-direction: column; align-items: center;
}
div[data-testid="metric-container"] label { color: #64748b !important; font-size: 15px !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] > div {
    color: #2563eb !important; font-size: 34px !important; font-weight: 700 !important;
}
/* AI 分析框样式 */
.ai-insight-box {
    background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 20px;
    border-radius: 4px; color: #1e3a8a; font-size: 15px; line-height: 1.6; margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 核心数据获取与清洗 (跳过空数据版)
# ==========================================
@st.cache_data(ttl="1h")
def load_and_transform_google_sheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit").sheet1
        raw_data = sheet.get_all_values()
        
        clean_records = []
        current_site = None
        dates_row = []
        
        for row_idx, row in enumerate(raw_data):
            if not row or not row[0]: continue
            first_cell = str(row[0]).strip()
            if first_cell.startswith("Callie ") and len(first_cell) <= 10:
                current_site = first_cell.replace("Callie ", "").strip()
                dates_row = row[1:]
                continue
            if current_site and first_cell not in ["星期五", "星期六", "星期日", "星期一", "星期二", "星期三", "星期四", "网站要事记", "TDK优化记录表"]:
                metric_name = first_cell
                values = row[1:]
                for i in range(len(values)):
                    if i < len(dates_row) and dates_row[i].strip() != "":
                        val_str = str(values[i]).strip()
                        # 跳过空数据，避免日历陷阱
                        if not val_str or val_str == "-" or val_str.lower() in ["n/a", "null"]: continue
                        
                        clean_str = val_str.replace("$", "").replace(",", "").replace("%", "").replace("€", "").replace("£", "")
                        clean_str = re.sub(r'[^\d\.-]', '', clean_str)
                        try:
                            clean_val = float(clean_str) if clean_str else 0.0
                        except:
                            clean_val = 0.0
                            
                        clean_records.append({
                            "Date": dates_row[i], "Site": current_site, 
                            "Metric": metric_name, "Value": clean_val
                        })
                        
        df_long = pd.DataFrame(clean_records)
        df_long['Date'] = pd.to_datetime(df_long['Date'], errors='coerce')
        df_long = df_long.dropna(subset=['Date']) 
        return df_long
    except Exception as e:
        st.error(f"🔌 云端连接失败: {e}")
        return pd.DataFrame()

# ==========================================
# 🤖 DeepSeek AI 分析功能
# ==========================================
@st.cache_data(ttl="2h") # 缓存2小时，省API钱
def get_ai_insight(data_summary):
    try:
        client = OpenAI(api_key=st.secrets["DEEPSEEK"]["api_key"], base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个资深的小语种SEO数据分析专家。请根据提供的昨日核心指标对比，用简练专业的中文给出2点核心洞察（例如趋势分析、异常跌幅预警或优化建议）。不要废话，直接给出结论。"},
                {"role": "user", "content": f"以下是看板昨日数据的精简摘要：\n{data_summary}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI 洞察暂时不可用，请检查 API Key 是否配置正确。错误信息: {e}"


# ==========================================
# 📐 UI 布局与渲染
# ==========================================
today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
st.markdown(f"""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #2563eb; font-size: 38px; font-weight: bold; margin-bottom: 8px;">小语种SEO日报</h1>
    <div style="color: #64748b; font-size: 16px;">{today_str}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("🚀 正在同步 Google Sheets 数据..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}
    raw_sites = sorted(df_master['Site'].unique().tolist())
    display_sites = ["全部站点"] + [en_to_cn.get(s, s) for s in raw_sites]
    
    col_nav1, col_nav2, col_nav3 = st.columns([1, 6, 1])
    with col_nav2:
        selected_site_cn = st.pills("站点切换", display_sites, default="全部站点", label_visibility="collapsed")
    
    st.write("") 
    
    col_filter1, col_filter2 = st.columns([1, 1])
    with col_filter1:
        times = ["过去1天", "过去7天", "过去14天", "全部数据"]
        selected_time = st.pills("时间选择", times, default="过去7天", label_visibility="collapsed")
    with col_filter2:
        all_metrics = sorted(df_master['Metric'].unique().tolist())
        default_metrics = [m for m in all_metrics if "SEO流量" in m or "网站总流量" in m]
        if not default_metrics: default_metrics = [all_metrics[0]]
        selected_metrics = st.multiselect("📊 图表附加展示指标：", all_metrics, default=default_metrics, label_visibility="collapsed")

    st.write("---")

    target_sites = raw_sites if selected_site_cn == "全部站点" or selected_site_cn is None else [cn_to_en.get(selected_site_cn, selected_site_cn)]
    df_site = df_master[df_master['Site'].isin(target_sites)]
    
    if not df_site.empty:
        available_dates = sorted(df_site['Date'].dropna().unique())
        if len(available_dates) > 0:
            latest_date = pd.Timestamp(available_dates[-1])
            prev_date = pd.Timestamp(available_dates[-2]) if len(available_dates) >= 2 else latest_date
            
            if selected_time == "过去1天": start_date = latest_date - pd.Timedelta(days=1)
            elif selected_time == "过去7天": start_date = latest_date - pd.Timedelta(days=7)
            elif selected_time == "过去14天": start_date = latest_date - pd.Timedelta(days=14)
            else: start_date = df_site['Date'].min()
                
            mask = (df_site['Date'] >= start_date) & (df_site['Date'] <= latest_date)
            df_filtered = df_site[mask]
            
            day_data = df_site[df_site['Date'] == latest_date].groupby('Metric')['Value'].sum()
            prev_day_data = df_site[df_site['Date'] == prev_date].groupby('Metric')['Value'].sum()
            
            # --- 🤖 唤醒 DeepSeek 分析 ---
            st.subheader("💡 专家数据洞察")
            # 构建要发给 AI 的摘要数据
            ai_summary = f"当前分析站点: {selected_site_cn}\n日期: {latest_date.strftime('%Y-%m-%d')}\n"
            for m in selected_metrics:
                cur_v = day_data.get(m, 0)
                pre_v = prev_day_data.get(m, 0)
                diff = f"{((cur_v-pre_v)/pre_v)*100:.1f}%" if pre_v > 0 else "0%"
                ai_summary += f"- {m}: {cur_v} (较前日 {diff})\n"
                
            with st.spinner("🧠 DeepSeek 正在极速分析数据..."):
                insight_text = get_ai_insight(ai_summary)
                st.markdown(f'<div class="ai-insight-box">🤖 <b>AI 分析：</b><br>{insight_text}</div>', unsafe_allow_html=True)
            
            # --- 渲染卡片区域 ---
            sales_metric_key = next((m for m in all_metrics if "SEO销售" in m or "总销售" in m), None)
            if not sales_metric_key:
                sales_metric_key = next((m for m in all_metrics if any(kw in m for kw in ["销售额", "转化价值", "Sales"])), None)
            traffic_metric = next((m for m in all_metrics if m in ["SEO流量", "网站总流量"]), None)
            if not traffic_metric:
                traffic_metric = next((m for m in all_metrics if "流量" in m or "Traffic" in m), all_metrics[0])
                    
            col_c1, col_c2, col_c3 = st.columns(3)
            date_label = latest_date.strftime('%m/%d')
            
            with col_c1:
                title_text = f"[{date_label}] {sales_metric_key}" if sales_metric_key else f"[{date_label}] SEO销售额"
                current_sales = day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
                prev_sales = prev_day_data.get(sales_metric_key, 0.0) if sales_metric_key else 0.0
                delta_str = f"{((current_sales - prev_sales) / prev_sales) * 100:+.1f}% 对比上一记录日" if prev_sales > 0 else "0.0% 对比上一记录日"
                st.metric(label=title_text, value=f"${current_sales:,.2f}", delta=delta_str)
                
            with col_c2:
                t_val = day_data.get(traffic_metric, 0.0)
                p_val = prev_day_data.get(traffic_metric, 0.0)
                d_str = f"{((t_val-p_val)/p_val)*100:+.1f}% 对比上一记录日" if p_val > 0 else "0%"
                st.metric(label=f"[{date_label}] {traffic_metric}", value=f"{t_val:,.0f}", delta=d_str)

            with col_c3:
                st.metric(label="当前分析视图", value=f"{selected_site_cn}", delta=f"真实数据更至 {date_label}")
                
            st.write("---")
            
            # --- 渲染图表区域 ---
            st.subheader("📈 核心指标时序走势")
            df_chart = df_filtered[df_filtered['Metric'].isin(selected_metrics)].copy()
            if not df_chart.empty:
                df_chart['Legend'] = df_chart['Site'] + " - " + df_chart['Metric']
                fig = px.line(
                    df_chart, x="Date", y="Value", color="Legend", markers=True, template="plotly_white",
                    color_discrete_sequence=["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#0284c7"]
                )
                fig.update_layout(xaxis_title="", yaxis_title="数值", hovermode="x unified", margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig, use_container_width=True)
                
            # --- 渲染表格区域 ---
            st.write("---")
            st.subheader("🗄️ 明细数据报表")
            df_pivot = df_chart.pivot_table(index=['Date', 'Site'], columns='Metric', values='Value', aggfunc='sum').reset_index()
            df_pivot = df_pivot.sort_values(by="Date", ascending=False)
            df_pivot['Date'] = df_pivot['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(df_pivot, use_container_width=True, hide_index=True)
            
        else:
            st.warning(f"在 {selected_site_cn} 站点中未解析到有效的日期格式数据。")
    else:
        st.warning(f"没有找到 {selected_site_cn} 的数据，请检查谷歌表格。")
