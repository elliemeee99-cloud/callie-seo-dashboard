import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking API 测试", page_icon="🔧", layout="wide")
st.markdown("## 🔧 SE Ranking API 终极穿透测试 (锁定 api4 节点)")

try:
    # 自动读取并清洗 Key
    raw_key = str(st.secrets["seranking_api_key"])
    api_key = raw_key.strip().strip('"').strip("'")
    
    # 💥 精确制导：专门针对 api4 节点，必须带结尾斜杠，同时测试 Token 和 Bearer 两种规范
    test_cases = [
        {"auth": f"Token {api_key}", "url": "https://api4.seranking.com/sites/"},
        {"auth": f"Token {api_key}", "url": "https://api4.seranking.com/projects/"},
        {"auth": f"Bearer {api_key}", "url": "https://api4.seranking.com/sites/"}
    ]
    
    success_data = None
    successful_url = ""
    diagnostic_logs = []
    
    with st.spinner("锁定 api4 服务器，正在发送强力鉴权请求..."):
        for case in test_cases:
            headers = {
                "Authorization": case["auth"],
                "Content-Type": "application/json"
            }
            try:
                # 核心修复：allow_redirects=False，禁止跳转，防止丢失 Token
                res = requests.get(case["url"], headers=headers, allow_redirects=False)
                
                diagnostic_logs.append({
                    "请求接口": case["url"],
                    "Auth模式": case["auth"].split()[0],
                    "状态码": res.status_code,
                    "返回内容": res.text[:100]
                })
                
                if res.status_code == 200:
                    success_data = res.json()
                    successful_url = case["url"]
                    break
            except Exception as e:
                diagnostic_logs.append({
                    "请求接口": case["url"],
                    "Auth模式": case["auth"].split()[0],
                    "状态码": "请求失败",
                    "返回内容": str(e)[:100]
                })

    if success_data is not None:
        st.balloons()
        st.success(f"✅ 完美破解！正确的接口通道是: `{successful_url}`")
        
        parsed_data = []
        for p in success_data:
            parsed_data.append({
                "🔑 站点 ID (Site ID)": p.get("id", "N/A"),
                "🌍 站点名称 (Title)": p.get("title", p.get("name", "N/A"))
            })
        
        st.dataframe(pd.DataFrame(parsed_data), use_container_width=True)
        st.info("💡 终于搞定了！请把上方表格中的【站点 ID】发给我（例如 DE=123, FR=456），我们马上去画看板！")
        
        with st.expander("🧩 查看原始 JSON 数据"):
            st.json(success_data)
            
    else:
        st.error("❌ 依然未能突破。请把新的诊断雷达图发给我，距离真相已经非常近了！")
        st.dataframe(pd.DataFrame(diagnostic_logs), use_container_width=True)

except KeyError:
    st.error("❌ 无法读取 `seranking_api_key`，请检查 secrets 配置。")
