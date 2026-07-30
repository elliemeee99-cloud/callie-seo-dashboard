import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking 最终测试", page_icon="🔥", layout="wide")
st.markdown("### 🔥 SE Ranking API 暴力直连测试")

try:
    # 💥 直接绕过 secrets 配置，把 Key 硬编码写死在这里！
    # 即使它在下面换成了两行，三引号也能完美包容，代码会自动把它拼成一行。
    raw_key = """
    d5cf8caa-acd4-a096-166c-49670c92a88c
    """
    
    # 强行清洗所有隐藏的换行、空格和多余符号
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace(" ", "")
    
    st.info(f"🔑 当前暴力注入的 API Key: `{api_key[:6]}......{api_key[-4:]}`")

    # 官方 v1 核心接口
    url = "https://api.seranking.com/v1/project-management/sites"
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    with st.spinner("正在直连官方 v1 核心接口..."):
        res = requests.get(url, headers=headers)

    if res.status_code == 200:
        projects = res.json()
        st.balloons()
        st.success("✅ 完美通关！终于拿到数据了！下方就是你的所有站点信息：")
        
        parsed_data = []
        for p in projects:
            parsed_data.append({
                "🔑 站点 ID (id)": p.get("id", "N/A"),
                "🌍 站点名称 (title)": p.get("title", p.get("name", "N/A")),
                "🔗 监控的域名": p.get("name", "N/A"),
                "📊 收录关键词数": p.get("keyword_count", 0)
            })
            
        st.dataframe(pd.DataFrame(parsed_data), use_container_width=True)
        st.write("---")
        with st.expander("🧩 查看完整原始 JSON 数据"):
            st.json(projects)
            
    else:
        st.error(f"❌ 请求失败。状态码: {res.status_code}")
        st.code(res.text)

except Exception as e:
    st.error(f"⚠️ 发生未知错误: {e}")
