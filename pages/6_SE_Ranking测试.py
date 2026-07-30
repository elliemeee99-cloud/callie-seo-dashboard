import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking 最终测试", page_icon="🔥", layout="wide")
st.markdown("### 🔥 SE Ranking API 官方标准接口测试")

try:
    # 自动清理 Key（防止万一真的有物理换行，这里也会被代码强行合并）
    raw_key = str(st.secrets["seranking_api_key"])
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "")
    
    st.info(f"🔑 当前使用的 API Key: `{api_key[:6]}......{api_key[-4:]}`")

    # 🔥 核心修正：SE Ranking 官方最新的 v1 项目管理接口！
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

except KeyError:
    st.error("❌ 无法读取 `seranking_api_key`，请检查 `secrets.toml` 配置。")
except Exception as e:
    st.error(f"⚠️ 发生未知错误: {e}")
