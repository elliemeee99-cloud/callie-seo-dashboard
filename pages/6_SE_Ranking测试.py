import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking API 测试", page_icon="🔧", layout="wide")
st.markdown("## 🔧 SE Ranking 防火墙穿透测试")

try:
    raw_key = str(st.secrets["seranking_api_key"])
    api_key = raw_key.strip().strip('"').strip("'")
    
    # 🕵️ 伪装成标准的 Windows Chrome 浏览器，规避 OpenResty 爬虫防火墙拦截
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # 涵盖所有可能的 Token 提交格式
    test_cases = [
        {"auth_key": "Authorization", "auth_val": f"Token {api_key}"},
        {"auth_key": "Authorization", "auth_val": f"Bearer {api_key}"},
        {"auth_key": "X-API-Key", "auth_val": api_key},
        {"auth_key": "Authorization", "auth_val": f"Api-Token {api_key}"}
    ]
    
    url = "https://api.seranking.com/sites"
    
    success_data = None
    diagnostic_logs = []
    
    with st.spinner("正在启动浏览器伪装并突破平台防火墙..."):
        for case in test_cases:
            headers = base_headers.copy()
            headers[case["auth_key"]] = case["auth_val"]
            
            try:
                res = requests.get(url, headers=headers, allow_redirects=True, timeout=5)
                # 记录核心返回信息
                diagnostic_logs.append({
                    "认证方式": f'{case["auth_key"]}: {case["auth_val"].split()[0]}...',
                    "状态码": res.status_code,
                    "返回摘要": res.text[:80].replace('\n', '')
                })
                
                if res.status_code == 200:
                    success_data = res.json()
                    break
            except Exception as e:
                diagnostic_logs.append({
                    "认证方式": f'{case["auth_key"]}',
                    "状态码": "网络错误",
                    "返回摘要": str(e)[:80]
                })

    if success_data is not None:
        st.balloons()
        st.success("✅ 突破成功！果然是服务器防火墙屏蔽了 Python 的默认请求头。")
        
        parsed_data = []
        for p in success_data:
            parsed_data.append({
                "🔑 站点 ID (Site ID)": p.get("id", "N/A"),
                "🌍 站点名称 (Title)": p.get("title", p.get("name", "N/A"))
            })
        st.dataframe(pd.DataFrame(parsed_data), use_container_width=True)
        
    else:
        st.error("❌ 依然被无情拦截。此时可以 100% 确认是 SE Ranking 平台层面的 Token 权限限制。")
        st.markdown("""
        **下一步排查建议：**
        1. 登录 SE Ranking 后台，进入刚才生成 API Key 的设置页面。
        2. 仔细检查是否有 **Allowed IPs (允许的 IP 白名单)** 相关的设置项。如果有，需要将当前服务器的 IP 填入。
        3. 检查这个 Key 是否需要针对 `Sites/Projects` 模块勾选特定的**读取权限 (Read Permissions)**。
        """)
        st.dataframe(pd.DataFrame(diagnostic_logs), use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 发生错误: {e}")
