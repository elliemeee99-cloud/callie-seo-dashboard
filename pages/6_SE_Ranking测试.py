import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="SE Ranking 审计测试", page_icon="🩺", layout="wide")
st.markdown("### 🩺 SE Ranking 网站审计 (Audit) 接口扫描")

try:
    # 注入 API Key
    raw_key = """
    d5cf8caa-acd4-a096-166c-49670c92a88c
    """
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace(" ", "")
    
    test_site_id = "9339803" # FR 法国站
    st.info(f"正在扫描 **FR 法国站 (ID: {test_site_id})** 的体检数据接口...")

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    # 涵盖 SE Ranking v1 和 v3 版本所有可能的审计接口
    audit_endpoints = [
        f"https://api.seranking.com/v1/audit/projects/{test_site_id}",
        f"https://api.seranking.com/v3/audit/{test_site_id}",
        f"https://api.seranking.com/v1/project-management/sites/{test_site_id}/audit",
        f"https://api.seranking.com/audit/site/{test_site_id}",
        f"https://api.seranking.com/v3/project-audit/{test_site_id}"
    ]

    success_data = None
    successful_url = ""
    diagnostic_logs = []

    with st.spinner("正在轮询扫描正确的 API 路径..."):
        for url in audit_endpoints:
            try:
                res = requests.get(url, headers=headers)
                diagnostic_logs.append({
                    "测试接口": url,
                    "状态码": res.status_code,
                    "返回摘要": res.text[:100]
                })
                
                # 如果状态码是 200，说明找对路了！
                if res.status_code == 200:
                    success_data = res.json()
                    successful_url = url
                    break
            except Exception as e:
                diagnostic_logs.append({"测试接口": url, "状态码": "网络错误", "返回摘要": str(e)})

    if success_data:
        st.balloons()
        st.success(f"✅ 找对接口了！成功路径：`{successful_url}`")
        with st.container(border=True):
            st.markdown("#### 🔍 原始体检数据")
            st.json(success_data)
            
        st.info("💡 请把上面的 JSON 截图发我，确认后我们立刻用它画多站点对比看板！")
        
    else:
        st.error("❌ 所有已知接口均返回失败。诊断明细如下：")
        # 修复了 Streamlit 弃用警告，将 use_container_width 替换为 width="stretch"
        st.dataframe(pd.DataFrame(diagnostic_logs), width="stretch")

except Exception as e:
    st.error(f"⚠️ 发生未知错误: {e}")
