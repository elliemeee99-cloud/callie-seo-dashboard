import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="全球站点健康度大盘", page_icon="🩺", layout="wide")

st.markdown("## 🩺 全球站点技术 SEO 健康度监控")
st.markdown("数据来源于 SE Ranking Website Audit 官方接口。")

try:
    # 使用我们验证过的三引号注入法，确保 Key 不会被意外换行破坏
    raw_key = """
    d5cf8caa-acd4-a096-166c-49670c92a88c
    """
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace(" ", "")
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    url = "https://api.seranking.com/v1/site-audit/audits"
    
    with st.spinner("正在从 SE Ranking 实时拉取各站点审计数据..."):
        res = requests.get(url, headers=headers)

    if res.status_code == 200:
        audits_data = res.json()
        items = audits_data.get("items", [])
        
        if items:
            parsed_data = []
            for item in items:
                # 仅筛选已经完成审计的站点
                if item.get("status") == "finished":
                    stats = item.get("stats", {})
                    parsed_data.append({
                        "站点名称": item.get("title", "N/A"),
                        "健康分 (Score)": stats.get("score", 0),
                        "严重错误 (Errors)": stats.get("errors", 0),
                        "警告 (Warnings)": stats.get("warnings", 0),
                        "提示 (Notices)": stats.get("notices", 0),
                        "已抓取页面": stats.get("crawled", 0),
                        "最后体检时间": item.get("last_update", "N/A")[:10] # 截取日期部分
                    })
            
            if parsed_data:
                df = pd.DataFrame(parsed_data)
                
                # 按照健康分从高到低排序
                df = df.sort_values(by="健康分 (Score)", ascending=False).reset_index(drop=True)
                
                # --- 图表区：健康分排名对比 ---
                st.markdown("### 🏆 各地区站点健康分排名")
                
                # 设置柱状图颜色规则：分数越高越绿，越低越红
                fig = px.bar(
                    df, 
                    x="站点名称", 
                    y="健康分 (Score)", 
                    color="健康分 (Score)",
                    color_continuous_scale="RdYlGn", 
                    range_color=[50, 100],
                    text="健康分 (Score)",
                    height=400
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(xaxis_title="", yaxis_title="Health Score")
                st.plotly_chart(fig, use_container_width=True)
                
                # --- 表格区：详细数据清单 ---
                st.markdown("### 📋 详细技术指标对比")
                
                # 给表格加上条件格式高亮 (类似 Excel)
                styled_df = df.style.background_gradient(
                    subset=['健康分 (Score)'], cmap='Greens'
                ).background_gradient(
                    subset=['严重错误 (Errors)'], cmap='Reds'
                ).format({
                    "健康分 (Score)": "{:.0f}",
                    "严重错误 (Errors)": "{:,}",
                    "警告 (Warnings)": "{:,}",
                    "提示 (Notices)": "{:,}",
                    "已抓取页面": "{:,}"
                })
                
                st.dataframe(styled_df, use_container_width=True, height=400)
                
            else:
                st.warning("没有找到状态为 'finished' 的审计报告。")
        else:
            st.warning("返回的数据中没有审计项目。")
            
    else:
        st.error(f"❌ API 请求失败。状态码: {res.status_code}")
        st.code(res.text)

except Exception as e:
    st.error(f"⚠️ 发生错误: {e}")
