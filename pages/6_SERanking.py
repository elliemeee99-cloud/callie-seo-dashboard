import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="欧洲区站点健康度大盘", page_icon="🩺", layout="wide")

# --- 🎨 注入自定义 CSS ---
st.markdown("""
<style>
div[role="radiogroup"] > label > div:first-child { display: none; }
div[role="radiogroup"] > label {
    background-color: #f1f3f4; padding: 8px 20px !important; border-radius: 20px !important;
    margin-right: 10px; border: 1px solid transparent; transition: all 0.2s ease; cursor: pointer;
}
div[role="radiogroup"] > label p { margin: 0; font-weight: 500; color: #5f6368; }
div[role="radiogroup"] > label[data-checked="true"] { background-color: #e8f0fe !important; border: 1px solid #d2e3fc !important; }
div[role="radiogroup"] > label[data-checked="true"] p { color: #1a73e8 !important; font-weight: 700 !important; }
.audit-card {
    padding: 20px; border: 1px solid #e6e6e6; border-radius: 8px; background-color: white; 
    height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: box-shadow 0.2s;
}
.audit-card:hover { box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🩺 欧洲区站点技术 SEO 健康度监控")

try:
    raw_key = """
    d5cf8caa-acd4-a096-166c-49670c92a88c
    """
    api_key = raw_key.strip().replace('"', '').replace("'", "").replace("\n", "").replace(" ", "")
    
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json"
    }

    # 💥 核心修复 1: 增加 limit=50 参数，防止 API 分页吃掉法国站数据
    url = "https://api.seranking.com/v1/site-audit/audits?limit=50"
    
    with st.spinner("正在从 SE Ranking 实时拉取各站点审计数据..."):
        res = requests.get(url, headers=headers)

    if res.status_code == 200:
        audits_data = res.json()
        items = audits_data.get("items", [])
        
        if items:
            parsed_data = []
            for item in items:
                title = item.get("title", "")
                # 💥 核心修复 2: 过滤掉非欧洲区的 US 站点
                if item.get("status") == "finished" and "US" not in title:
                    stats = item.get("stats", {})
                    parsed_data.append({
                        "站点名称": title,
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
                
                st.markdown("### 🏆 欧洲各国健康分大盘")
                
                google_colors = ["#DB4437", "#F4B400", "#0F9D58", "#4285F4"]
                
                fig = px.bar(
                    df, 
                    x="站点名称", 
                    y="健康分 (Score)", 
                    color="健康分 (Score)",
                    color_continuous_scale=google_colors, 
                    range_color=[40, 100],
                    text="健康分 (Score)",
                    height=350
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(xaxis_title="", yaxis_title="Health Score", margin=dict(b=0, t=20))
                st.plotly_chart(fig)
                
                st.divider()
                
                st.markdown("### 🔍 分站点详细体检报告")
                
                # 更新为纯欧洲站点列表
                target_sites = ['DE', 'FR', 'ES', 'IT', 'NL', 'NO', 'SE', 'FI', 'PL']
                
                selected_site_code = st.radio(
                    "选择要查看的站点:",
                    options=target_sites,
                    horizontal=True,
                    label_visibility="collapsed"
                )
                
                matched_row = df[df["站点名称"].str.contains(selected_site_code, case=False, na=False)]
                
                if not matched_row.empty:
                    site_data = matched_row.iloc[0]
                    
                    st.markdown(f"<p style='color: #666; font-size: 14px; margin-top: 15px;'>Last update <b>{site_data['最后体检时间']}</b> &nbsp;|&nbsp; Pages crawled <b>{site_data['已抓取页面']}</b></p>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        score = site_data['健康分 (Score)']
                        gauge_color = "#0F9D58" if score >= 80 else "#F4B400" if score >= 50 else "#DB4437"
                        
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = score,
                            title = {'text': "<span style='font-size:14px;color:#888'>HEALTH SCORE <i>i</i></span><br>"},
                            gauge = {
                                'axis': {'range': [None, 100], 'visible': False},
                                'bar': {'color': gauge_color, 'thickness': 0.85},
                                'steps': [{'range': [0, 100], 'color': "#f1f3f4"}],
                            }
                        ))
                        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
                        
                        st.markdown("<div class='audit-card'>", unsafe_allow_html=True)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    with col2:
                        err = site_data['严重错误 (Errors)']
                        warn = site_data['警告 (Warnings)']
                        notc = site_data['提示 (Notices)']
                        total = err + warn + notc
                        
                        p_err = (err/total*100) if total > 0 else 0
                        p_warn = (warn/total*100) if total > 0 else 0
                        p_notc = (notc/total*100) if total > 0 else 0
                        
                        # 💥 核心修复 3: HTML 代码全部顶格写，去掉缩进，防止 Markdown 误判为代码块
                        html_card2 = f"""<div class='audit-card'>
<p style="font-size: 13px; color: #888; font-weight: 600; margin-bottom: 5px;">ISSUES BY TYPE <i>i</i></p>
<h2 style="margin: 0; color: #1a73e8; font-size: 32px;">{total:,}</h2>
<p style="font-size: 12px; color: #888; margin-top: 0; margin-bottom: 20px;">Total Issues</p>
<div style="width: 100%; height: 16px; display: flex; border-radius: 4px; overflow: hidden; gap: 3px;">
<div style="width: {p_err}%; background-color: #DB4437;" title="Errors: {err}"></div>
<div style="width: {p_warn}%; background-color: #F4B400;" title="Warnings: {warn}"></div>
<div style="width: {p_notc}%; background-color: #4285F4;" title="Notices: {notc}"></div>
</div>
<div style="margin-top: 25px; font-size: 14px; color: #333;">
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span><span style="color: #DB4437;">●</span> Errors</span> <b>{err:,}</b>
</div>
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span><span style="color: #F4B400;">●</span> Warnings</span> <b>{warn:,}</b>
</div>
<div style="display: flex; justify-content: space-between;">
<span><span style="color: #4285F4;">●</span> Notices</span> <b>{notc:,}</b>
</div>
</div>
</div>"""
                        st.markdown(html_card2, unsafe_allow_html=True)

                    with col3:
                        crawled = site_data['已抓取页面']
                        html_card3 = f"""<div class='audit-card'>
<p style="font-size: 13px; color: #888; font-weight: 600; margin-bottom: 5px;">PAGE HEALTH RATIO <i>i</i></p>
<h2 style="margin: 0; color: #1a73e8; font-size: 32px;">{crawled:,}</h2>
<p style="font-size: 12px; color: #888; margin-top: 0; margin-bottom: 20px;">Pages Crawled</p>
<div style="width: 100%; height: 16px; display: flex; border-radius: 4px; overflow: hidden; gap: 3px;">
<div style="width: 100%; background-color: #0F9D58;"></div>
</div>
<div style="margin-top: 25px; font-size: 14px; color: #333;">
<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
<span><span style="color: #0F9D58;">●</span> Scanned Successfully</span> <b>{crawled:,}</b>
</div>
<p style="font-size: 12px; color: #888; margin-top: 15px;">*Detailed healthy vs error page breakdown requires deeper API call.</p>
</div>
</div>"""
                        st.markdown(html_card3, unsafe_allow_html=True)
                else:
                    st.warning(f"⚠️ 暂未在 API 数据中找到对应 {selected_site_code} 站点的体检完成记录。")
                    
            else:
                st.warning("没有找到状态为 'finished' 的审计报告。")
        else:
            st.warning("返回的数据中没有审计项目。")
            
    else:
        st.error(f"❌ API 请求失败。状态码: {res.status_code}")
        st.code(res.text)

except Exception as e:
    st.error(f"⚠️ 发生错误: {e}")
