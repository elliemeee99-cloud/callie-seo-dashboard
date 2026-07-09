import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import re

# 页面基础配置
st.set_page_config(page_title="小语种SEO日报", page_icon="📈", layout="wide")

# ==========================================
# 1. 数据读取逻辑 (增强版)
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1GLAGMkVx5DMXylG0bbdvkzuqTd8IVfDANhcRrAX6LFU/edit").sheet1
        
        # 获取所有数据并直接转化为 DataFrame
        raw_data = sheet.get_all_values()
        if not raw_data: return "表格为空"
        
        # 假设第一行是列名
        df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
        return df
    except Exception as e:
        return str(e)

# ==========================================
# 2. DeepSeek AI 分析逻辑
# ==========================================
def get_ai_insight(data_summary):
    try:
        client = OpenAI(api_key=st.secrets["DEEPSEEK"]["api_key"], base_url="https://api.deepseek.com")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个资深的SEO数据分析专家。请根据提供的昨日数据指标，用专业、简练的中文给出2-3点核心洞察（趋势分析、异常预警或优化建议）。"},
                {"role": "user", "content": f"以下是昨日SEO数据摘要：{data_summary}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI 分析暂时不可用: {e}"

# ==========================================
# 3. 主界面渲染
# ==========================================
st.title("📈 小语种SEO日报")

data = load_data()

if isinstance(data, str):
    st.error(f"读取数据失败，请检查 GCP 权限: {data}")
else:
    # 顶部数据概览
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("原始数据预览")
        st.dataframe(data.tail(5), use_container_width=True)
    
    with col2:
        # 触发 AI 分析
        st.subheader("🤖 AI 智能洞察")
        if st.button("生成今日 SEO 分析报告"):
            with st.spinner("正在询问 DeepSeek..."):
                # 提取最后一行作为数据样本
                summary = data.iloc[-1].to_string()
                insight = get_ai_insight(summary)
                st.info(insight)
    
    st.success("数据已同步，DeepSeek 接口已联通。")
