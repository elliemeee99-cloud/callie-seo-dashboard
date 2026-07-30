import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking API 测试", page_icon="🔧", layout="wide")

st.markdown("## 🔧 SE Ranking API 连通性测试")
st.markdown("正在尝试连接官方服务器并拉取您的所有站点项目...")

try:
    # 自动读取配置好的 Key
    api_key = st.secrets["seranking_api_key"]
    st.success("✅ 本地 API Key 读取成功！")
    
    # 🔥 核心修复：SE Ranking 官方获取站点列表的正确 endpoint 是 /sites
    url = "https://api4.seranking.com/sites"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }
    
    # 发起网络请求
    with st.spinner("数据拉取中，请稍候..."):
        response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        projects = response.json()
        st.balloons()
        st.markdown(f"### 🎉 API 连接成功！共找到 **{len(projects)}** 个站点项目。")
        
        # 将获取到的 JSON 数据清洗并转为可视化表格
        if projects:
            parsed_data = []
            for p in projects:
                parsed_data.append({
                    "🔑 站点 ID (Site ID)": p.get("id", "N/A"),
                    "🌍 站点名称 (Title)": p.get("title", p.get("name", "N/A")),
                    "🔍 监控的搜索引擎数": len(p.get("search_engines", [])),
                })
            
            df = pd.DataFrame(parsed_data)
            st.dataframe(df, use_container_width=True)
            
            st.info("💡 **请注意**：请核对上方表格中的【站点 ID】。在写正式看板前，我需要知道比如 `DE` 对应的 ID 是多少，`FR` 对应的 ID 是多少。")
            
            with st.expander("🧩 点击查看 API 返回的完整原始数据 (JSON)"):
                st.json(projects)
    else:
        st.error(f"❌ API 请求失败！HTTP 状态码: {response.status_code}")
        st.code(response.text, language="json")
        
except KeyError:
    st.error("❌ 无法读取 `seranking_api_key`，请检查 `.streamlit/secrets.toml` 文件的拼写和格式。")
except Exception as e:
    st.error(f"⚠️ 发生网络或未知错误: {e}")
