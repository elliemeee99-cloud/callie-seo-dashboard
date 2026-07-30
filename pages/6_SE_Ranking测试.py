import streamlit as st
import requests

st.set_page_config(page_title="SE Ranking 审计测试", page_icon="🩺", layout="wide")
st.markdown("### 🩺 SE Ranking 网站审计 (Audit) 数据抓取测试")

try:
    # 填入我们刚才验证成功的 API Key
    raw_key = """
    d5cf8caa-acd4-a096-166c-49670c92a88c
    """
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace(" ", "")
    
    # 选取法国站 FR 作为测试目标
    test_site_id = "9339803"
    st.info(f"正在尝试拉取 **FR 法国站 (ID: {test_site_id})** 的审计健康数据...")

    # SE Ranking 官方 Audit 摘要接口 (不同版本的 API 路径可能微调，这里用主流的 v1/v3 探测)
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    # 测试常用的审计接口路径
    audit_urls = [
        f"https://api.seranking.com/v1/audit/projects/{test_site_id}/reports/latest",
        f"https://api.seranking.com/audit/{test_site_id}",
        f"https://api.seranking.com/v1/project-management/sites/{test_site_id}/audit"
    ]

    success_data = None
    
    with st.spinner("正在连接 Audit 服务器..."):
        for url in audit_urls:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                success_data = res.json()
                break

    if success_data:
        st.balloons()
        st.success("✅ 审计数据拉取成功！")
        
        # 提取核心数据 (不同账号数据结构可能不同，直接展示全貌)
        with st.container(border=True):
            st.markdown("#### 🔍 原始审计数据拆解")
            st.json(success_data)
            
        st.info("💡 请把上面的 JSON 截图发我，我看看它的数据字段叫什么（比如 health_score），确认后我们立刻用它画多站点对比看板！")
        
    else:
        st.error(f"❌ 请求失败。服务器最后返回的状态码: {res.status_code}")
        st.code(res.text)

except Exception as e:
    st.error(f"⚠️ 发生未知错误: {e}")
