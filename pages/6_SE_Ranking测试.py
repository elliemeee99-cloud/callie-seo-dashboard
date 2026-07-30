import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking API 测试", page_icon="🔧", layout="wide")

st.markdown("## 🔧 SE Ranking API 终极连通测试")
st.markdown("正在自动探测正确的官方接口路径并拉取站点...")

try:
    # 自动读取并清洗 Key，防止任何隐藏空格
    raw_key = str(st.secrets["seranking_api_key"])
    api_key = raw_key.strip().strip('"').strip("'")
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # 🔥 API 探测列表 (涵盖所有官方可能的节点与尾斜杠变体)
    endpoints = [
        "https://api4.seranking.com/sites/",
        "https://api4.seranking.com/sites",
        "https://api4.seranking.com/projects/",
        "https://api4.seranking.com/projects"
    ]
    
    success_data = None
    successful_url = ""
    
    with st.spinner("正在突破重定向限制，逐一探测接口，请稍候..."):
        for url in endpoints:
            # allow_redirects=False 是核心！防止 301 跳转时静默丢失 Token
            response = requests.get(url, headers=headers, allow_redirects=False)
            
            if response.status_code == 200:
                success_data = response.json()
                successful_url = url
                break
            
    if success_data is not None:
        st.balloons()
        st.success(f"✅ API 连接成功！(匹配到的正确接口为: `{successful_url}`)")
        st.markdown(f"### 🎉 共找到 **{len(success_data)}** 个站点项目。")
        
        parsed_data = []
        for p in success_data:
            parsed_data.append({
                "🔑 站点 ID (Site ID)": p.get("id", "N/A"),
                "🌍 站点名称 (Title)": p.get("title", p.get("name", "N/A")),
                "🔍 搜索引擎数量": len(p.get("search_engines", [])),
            })
        
        df = pd.DataFrame(parsed_data)
        st.dataframe(df, use_container_width=True)
        
        st.info("💡 **大功告成！请把上方表格中你需要监控的【站点 ID】发给我（例如 DE=123, FR=456），我们马上进入正式看板的开发！**")
        
        with st.expander("🧩 点击查看 API 返回的完整原始数据 (JSON)"):
            st.json(success_data)
    else:
        st.error("❌ 所有已知接口均探测失败，请检查以下诊断信息：")
        # 打印最后一次尝试的详细报错
        res = requests.get("https://api4.seranking.com/sites/", headers=headers)
        st.code(f"最终状态码: {res.status_code}\n返回内容: {res.text}", language="json")

except KeyError:
    st.error("❌ 无法读取 `seranking_api_key`，请检查 `.streamlit/secrets.toml` 文件的拼写。")
except Exception as e:
    st.error(f"⚠️ 发生网络或未知错误: {e}")
