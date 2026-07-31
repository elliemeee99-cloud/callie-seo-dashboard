import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="全球站点健康度大盘", page_icon="🩺", layout="wide")

st.markdown("## 🩺 全球站点技术 SEO 健康度监控")
st.markdown("数据来源于 SE Ranking Website Audit 官方接口。")

try:
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
                if item.get("status") == "finished":
                    stats = item.get("stats", {})
                    parsed_data.append({
                        "站点名称": item.get("title", "N/A"),
                        "健康分 (Score)": stats.get("score", 0),
                        "严重错误 (Errors)": stats.get("errors", 0),
                        "警告 (Warnings)": stats.get("warnings", 0),
                        "提示 (Notices)": stats.get("notices", 0),
                        "已抓取页面": stats.get("crawled", 0),
                        "最后体检时间": item.get("last_update", "N/A")[:10]
                    })
            
            if parsed_data:
                df = pd.DataFrame(parsed_data)
                df = df.sort_values(by="健康分 (Score)", ascending=False).reset_index(drop=True)
                
                st.markdown("### 🏆 各地区站点健康分排名")
                
                # 🌈 使用高饱和度清新配色：珊瑚红 -> 亮黄 -> 薄荷绿
                fresh_colors = ["#FF4B4B", "#FFD166", "#06D6A0"]
                
                fig = px.bar(
                    df, 
                    x="站点名称", 
                    y="健康分 (Score)", 
                    color="健康分 (Score)",
                    color_continuous_scale=fresh_colors, 
                    range_color=[50, 100],
                    text="健康分 (Score)",
                    height=450
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(xaxis_title="", yaxis_title="Health Score", margin=dict(b=0))
                
                # 移除了引发弃用警告的参数
                st.plotly_chart(fig)
                
                st.markdown("### 📋 详细技术指标对比")
                
                # ✨ 使用 Streamlit 原生组件，彻底解决 matplotlib 报错，并增加进度条展示
                st.dataframe(
                    df, 
                    column_config={
                        "健康分 (Score)": st.column_config.ProgressColumn(
                            "健康分 (Score)",
                            help="满分100，分数越高越健康",
                            format="%d",
                            min_value=0,
                            max_value=100,
                        ),
                        "严重错误 (Errors)": st.column_config.NumberColumn(
                            "严重错误 (Errors)",
                            format="%d 🔴"
                        ),
                        "警告 (Warnings)": st.column_config.NumberColumn(
                            "警告 (Warnings)",
                            format="%d 🟡"
                        ),
                        "提示 (Notices)": st.column_config.NumberColumn(
                            "提示 (Notices)",
                            format="%d 🔵"
                        )
                    }
                )
                
            else:
                st.warning("没有找到状态为 'finished' 的审计报告。")
        else:
            st.warning("返回的数据中没有审计项目。")
            
    else:
        st.error(f"❌ API 请求失败。状态码: {res.status_code}")
        st.code(res.text)

except Exception as e:
    st.error(f"⚠️ 发生错误: {e}")
