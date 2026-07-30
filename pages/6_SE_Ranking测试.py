import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking 审计接口测试", page_icon="🩺", layout="wide")
st.markdown("### 🩺 SE Ranking Website Audit 官方接口测试")

try:
    # 注入 API Key
    raw_key = """
    d5cf8caa-acd4-a096-166c-49670c92a88c
    """
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace(" ", "")
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    # 官方 Website Audit 获取审计列表的接口
    url = "https://api.seranking.com/v1/site-audit/audits"
    
    with st.spinner("正在请求 Website Audit 接口..."):
        res = requests.get(url, headers=headers)

    st.info(f"请求状态码: {res.status_code}")

    if res.status_code == 200:
        st.balloons()
        st.success("✅ 成功获取 Website Audit 列表！")
        audits_data = res.json()
        
        with st.container(border=True):
            st.json(audits_data)
    else:
        st.error("❌ 请求未成功，返回内容如下：")
        st.code(res.text)

except Exception as e:
    st.error(f"⚠️ 发生错误: {e}")
