import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking API 测试", page_icon="🔧", layout="wide")
st.markdown("## 🔧 SE Ranking API 终极矩阵扫描测试")

try:
    # 自动读取并清洗 Key，防止任何隐藏空格
    raw_key = str(st.secrets["seranking_api_key"])
    api_key = raw_key.strip().strip('"').strip("'")
    
    # 💥 定义要测试的所有可能组合 (全矩阵覆盖)
    test_cases = [
        {"auth": f"Token {api_key}", "url": "https://api.seranking.com/sites"},
        {"auth": f"Token {api_key}", "url": "https://api.seranking.com/projects"},
        {"auth": f"Bearer {api_key}", "url": "https://api.seranking.com/sites"},
        {"auth": f"Token {api_key}", "url": "https://api.seranking.com/sites/"}, # 防御斜杠丢失
        {"auth": f"Token {api_key}", "url": "https://api4.seranking.com/sites"}  # 保底测试
    ]
    
    success_data = None
    successful_url = ""
    diagnostic_logs = []
    
    with st.spinner("正在执行全矩阵扫描，寻找正确的 API 通道..."):
        for case in test_cases:
            headers = {
                "Authorization": case["auth"],
                "Content-Type": "application/json"
            }
            try:
                # 发起请求
                res = requests.get(case["url"], headers=headers, allow_redirects=True)
                
                # 记录每一次的诊断结果
                diagnostic_logs.append({
                    "测试接口": case["url"],
                    "Auth前缀": case["auth"].split()[0],
                    "状态码": res.status_code,
                    "返回内容": res.text[:100]
                })
                
                # 如果命中 200，立刻抓取数据并跳出循环
                if res.status_code == 200:
                    success_data = res.json()
                    successful_url = case["url"]
                    break
            except Exception as e:
                diagnostic_logs.append({
                    "测试接口": case["url"],
                    "Auth前缀": case["auth"].split()[0],
                    "状态码": "网络报错",
                    "返回内容": str(e)[:100]
                })

    if success_data is not None:
        st.balloons()
        st.success(f"✅ 成功破解！正确的接口通道是: `{successful_url}`")
        
        parsed_data = []
        for p in success_data:
            parsed_data.append({
                "🔑 站点 ID (Site ID)": p.get("id", "N/A"),
                "🌍 站点名称 (Title)": p.get("title", p.get("name", "N/A"))
            })
        
        st.dataframe(pd.DataFrame(parsed_data), use_container_width=True)
        st.info("💡 大功告成！请把上方表格中的【站点 ID】发给我（例如 DE=123, FR=456），我们马上进入正式看板的开发！")
        
        with st.expander("🧩 查看原始 JSON 数据"):
            st.json(success_data)
            
    else:
        st.error("❌ 扫描完毕，所有接口均被拒绝。请将下方的【诊断雷达图】完整截图发给我，底层的错误码将告诉我真相！")
        st.dataframe(pd.DataFrame(diagnostic_logs), use_container_width=True)

except KeyError:
    st.error("❌ 无法读取 `seranking_api_key`，请检查 secrets 配置。")
