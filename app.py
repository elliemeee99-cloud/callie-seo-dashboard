import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import re

# 网页基础设置
st.set_page_config(page_title="SEO数据看板", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 🎨 极简定制 CSS
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f4f7f9 !important; }
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
[data-testid="collapsedControl"] {display: none;}
.block-container { padding-top: 2rem !important; max-width: 95% !important; }

/* 圆角分区容器 */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    background-color: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

/* 核心数据大字卡片样式 */
div[data-testid="stMetricValue"] > div {
    color: #2563eb !important; font-size: 38px !important; font-weight: 700 !important;
}
div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 15px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# ⚙️ 极速数据获取引擎 (仅读取 Sheet2 底部总计)
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
        current_month_totals = {}
        
        try:
            sheet2 = spreadsheet.worksheet("Sheet2")
            raw_data_2 = sheet2.get_all_values()
            
            if raw_data_2:
                headers = raw_data_2[0]
                for row in raw_data_2[1:]:
                    if not row or not row[0]: continue
                    first_col = row[0].strip()
                            
                    # 💡 强力抓取底部的“总计”行
                    if first_col == "总计":
                        current_month_totals = {} # 确保抓到的是最底下的最新总计
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
            print(f"Sheet2 读取失败: {e}")
            
        if current_month_totals:
            for site, val in current_month_totals.items():
                s_name = "ALL" if site == "Global" else site
                clean_records.append({
                    "Date": "2099-12-31", "Site": s_name, "Metric": "SEO销售额_当月总计", "Value": val
                })

        return pd.DataFrame(clean_records)
    except Exception as e:
        st.error(f"🔌 云端连接失败: {e}")
        return pd.DataFrame()


# ==========================================
# 📐 UI 布局与页面渲染
# ==========================================

# 锁定物理世界绝对时间
real_today = pd.Timestamp(datetime.datetime.now().date())
latest_date = real_today - pd.Timedelta(days=1)  

st.markdown(f"""
<div style="margin-bottom: 25px;">
    <h1 style="color: #1e293b; font-size: 32px; font-weight: 700; margin-bottom: 4px;">SEO数据看板</h1>
    <div style="color: #64748b; font-size: 14px;">报表同步基准日：{latest_date.strftime('%Y-%m-%d')}</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("🚀 正在极速同步 Sheet2 数据..."):
    df_master = load_and_transform_google_sheet()

if not df_master.empty:
    cn_to_en = {"德国": "DE", "法国": "FR", "西班牙": "ES", "意大利": "IT", "荷兰": "NL", "波兰": "PL", "挪威": "NO", "瑞典": "SE", "芬兰": "FI"}
    en_to_cn = {v: k for k, v in cn_to_en.items()}
    
    # ------------------------------------------
    # 💰 唯一核心看板：本月累计SEO销售额
    # ------------------------------------------
    st.markdown("### 💰 本月累计SEO销售额")
    with st.container(border=True):
        mtd_data = df_master[df_master['Metric'] == 'SEO销售额_当月总计']
        
        if not mtd_data.empty:
            global_val = mtd_data[mtd_data['Site'] == 'ALL']['Value'].sum()
            
            st.markdown(f"<div style='color:#64748b; font-size:14px; margin-bottom:15px;'>📊 数据源：直接读取 Sheet2 底栏总计行</div>", unsafe_allow_html=True)
            
            # 第一层：全局总计
            st.metric(f"🌐 全局本月累计SEO销售额", f"${global_val:,.2f}")
            st.markdown("---")
            
            # 第二层：各站点横向拆解
            st.markdown("<span style='color:#64748b; font-size:14px;'>🌍 各站点累计贡献排名</span>", unsafe_allow_html=True)
            site_mtd = mtd_data[mtd_data['Site'] != 'ALL'].set_index('Site')['Value'].sort_values(ascending=False)
            
            if not site_mtd.empty:
                num_cols = min(len(site_mtd), 6)
                cols = st.columns(num_cols)
                for i, (site_code, val) in enumerate(site_mtd.items()):
                    with cols[i % num_cols]:
                        site_name = en_to_cn.get(site_code, site_code)
                        st.metric(site_name, f"${val:,.0f}")
        else:
            st.info("尚未抓取到 Sheet2 的'总计'行数据，请检查表格是否正确配置。")
else:
    st.info("👈 请配置 GCP JSON 密钥以接入数据湖。")
