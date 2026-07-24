import streamlit as st
import pandas as pd
import datetime
import os
import plotly.graph_objects as go

# ==========================================
# 网页基础设置
# ==========================================
st.set_page_config(page_title="SEO月度数据对比", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")

CACHE_FILE = "seo_monthly_sales_v5.pkl"

# ==========================================
# 🧭 极限防乱码单行 CSS + 6栏导航
# ==========================================
compressed_css = """<div id="top-anchor"></div><style>[data-testid="stSidebar"]{display:none !important;}[data-testid="collapsedControl"]{display:none !important;}[data-testid="stHeader"]{display:none !important;}.block-container{padding-top:2rem !important;max-width:95% !important;}.stApp{background-color:#f8fafc !important;}[data-testid="stPageLink-NavLink"]{background-color:#ffffff !important;border:1px solid #cbd5e1 !important;border-radius:12px !important;padding:12px 6px !important;text-align:center !important;display:flex !important;justify-content:center !important;align-items:center !important;transition:all 0.25s ease !important;box-shadow:0 2px 4px rgba(0,0,0,0.02) !important;text-decoration:none !important;white-space:nowrap;}[data-testid="stPageLink-NavLink"]:hover{background-color:#ffffff !important;border-color:#3b82f6 !important;transform:translateY(-2px) !important;box-shadow:0 8px 16px rgba(37,99,235,0.1) !important;}[data-testid="stPageLink-NavLink"] p{font-weight:800 !important;color:#1e293b !important;font-size:14px !important;margin:0 !important;}.back-to-top{position:fixed;bottom:40px;right:40px;background-color:#FF8FAB;color:#ffffff !important;border:none;width:50px;height:50px;border-radius:50%;display:flex;justify-content:center;align-items:center;font-size:24px;font-weight:800;box-shadow:0 4px 15px rgba(255,143,171,0.35);text-decoration:none !important;z-index:99999;transition:all 0.3s ease;}.back-to-top:hover{background-color:#FF5D8F;transform:translateY(-5px);box-shadow:0 8px 20px rgba(255,143,171,0.55);color:#ffffff !important;}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px !important;border:1px solid #e2e8f0 !important;background-color:#ffffff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);padding:20px;}</style><a href="#top-anchor" class="back-to-top" title="回到顶部">↑</a>"""
st.markdown(compressed_css, unsafe_allow_html=True)

spacer_left, nav1, nav2, nav3, nav4, nav5, nav6, spacer_right = st.columns([0.1, 1, 1, 1, 1, 1, 1, 0.1])
with nav1: st.page_link("app.py", label="App 首页", icon="🏠")
with nav2: st.page_link("pages/1_SEO目标概览.py", label="SEO 目标概览", icon="🎯")
with nav3: st.page_link("pages/2_SEO站点明细.py", label="SEO 站点明细", icon="🗄️")
with nav4: st.page_link("pages/3_SEO需求管理.py", label="SEO 需求管理", icon="📋")
with nav5: st.page_link("pages/4_SEO重点事件记录.py", label="重点事件记录", icon="📅")
with nav6: st.page_link("pages/5_SEO月度数据对比.py", label="月度数据对比", icon="📊")
st.markdown("<hr style='margin-top: 10px; margin-bottom: 25px; border-color: #e2e8f0;'/>", unsafe_allow_html=True)

# ==========================================
# ⚙️ 核心解析引擎 (容错率 MAX 版)
# ==========================================
def parse_excel_dates(date_series):
    parsed_dates = []
    for val in date_series:
        if pd.isna(val) or str(val).strip() == '':
            parsed_dates.append(pd.NaT)
            continue
        # 如果 Excel 直接读出了 datetime 格式，完美接收
        if isinstance(val, datetime.datetime):
            parsed_dates.append(val)
            continue
        try:
            if isinstance(val, (int, float)):
                parsed_dates.append(pd.to_datetime(val, origin='1899-12-30', unit='D'))
            else:
                # 强力过滤中文年月日符号
                v_str = str(val).strip()
                v_str = v_str.replace('年', '-').replace('月', '-').replace('日', '')
                if v_str.endswith('-'): v_str = v_str[:-1]
                parsed_dates.append(pd.to_datetime(v_str))
        except:
            parsed_dates.append(pd.NaT)
    return pd.Series(parsed_dates)

def extract_table(df_raw, start_idx, end_idx):
    # 分割出目标大块
    df = df_raw.iloc[start_idx:end_idx].copy().reset_index(drop=True)
    if df.empty: return pd.DataFrame()
    
    # 定位真实的表头行
    header_row_idx = 0
    for i in range(len(df)):
        row_vals = [str(x).strip() for x in df.iloc[i].values if pd.notna(x)]
        if any('总计' in x or '合计' in x for x in row_vals):
            header_row_idx = i
            break
            
    df.columns = [str(c).strip() for c in df.iloc[header_row_idx]]
    df = df.iloc[header_row_idx+1:].dropna(how='all')
    
    if len(df) == 0: return pd.DataFrame()
    
    # 强制规范第一列为日期列
    cols = list(df.columns)
    cols[0] = 'RawDate'
    df.columns = cols
    
    # 清理非日期的多余汇总行
    df = df[df['RawDate'].astype(str).str.contains('总计|合计') == False]
    
    df['Date'] = parse_excel_dates(df['RawDate'])
    df = df.dropna(subset=['Date'])
    
    # 智能提取总计数值 (剥离金额符号 $)
    total_col = None
    for c in df.columns:
        if '总计' in str(c) or '合计' in str(c):
            total_col = c
            break
    if not total_col:
        for c in df.columns[1:]:
            if any(x in str(c).upper() for x in ['销售', 'ALL', 'SEO', 'TOTAL', '金额']):
                total_col = c
                break
    if not total_col and len(df.columns) > 1:
        total_col = df.columns[1]
        
    if total_col:
        s = df[total_col]
        if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
        # 🔥 关键修复：剥离金额里的 $ 和逗号，防止转成 NaN 变成 0.00
        s = s.astype(str).str.replace(r'[$,]', '', regex=True)
        df['Total'] = pd.to_numeric(s, errors='coerce').fillna(0)
    else:
        df['Total'] = 0.0
        
    df['Month'] = df['Date'].dt.strftime('%Y-%m')
    return df.groupby('Month')['Total'].sum().reset_index()

# ==========================================
# 🎯 页面头部与数据持久化上传
# ==========================================
col_header, col_refresh = st.columns([5, 1])
with col_header:
    st.markdown("<div style='font-size: 28px; font-weight: 800; color: #111827; margin-bottom: 8px; margin-top: 10px;'>📊 SEO 核心指标深度对比</div>", unsafe_allow_html=True)
    st.markdown("<div style='color: #6B7280; margin-bottom: 24px; font-size: 15px;'>取消繁琐确认，AI 自动提取非品牌词与整体销售额的同环比走势。</div>", unsafe_allow_html=True)
with col_refresh:
    st.write("") 
    if st.button("🗑️ 清空本地缓存"):
        if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
        if 'monthly_data' in st.session_state: del st.session_state['monthly_data']
        st.success("缓存已清空！")
        st.rerun()

with st.container(border=True):
    st.markdown("<div style='font-weight: 700; color: #334155; font-size: 16px; margin-bottom: 12px;'>📥 上传数据报表</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("请上传最新版的《SEO 整体数据情况》台账 (支持 Excel xlsx 格式)", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            target_sheet = 'SEO销售额汇总' if 'SEO销售额汇总' in xls.sheet_names else xls.sheet_names[0]
            df_raw = pd.read_excel(xls, sheet_name=target_sheet, header=None)
            
            # 智能切割上下表
            header_indices = []
            for i, row in df_raw.iterrows():
                row_strs = [str(x).strip() for x in row if pd.notna(x)]
                if any('总计' in x or '合计' in x for x in row_strs): 
                    header_indices.append(i)
            
            if len(header_indices) >= 2:
                idx1 = header_indices[0]
                idx2 = header_indices[1]
                df_nb = extract_table(df_raw, idx1, idx2)
                df_all = extract_table(df_raw, idx2, len(df_raw))
                
                data_dict = {'nonbrand': df_nb, 'allseo': df_all}
                pd.to_pickle(data_dict, CACHE_FILE)
                st.session_state['monthly_data'] = data_dict
                st.success("✅ 数据报表解析成功，已自动抽取上下表的【总计】数据并安全留存！")
            else:
                st.error("❌ 表格结构未匹配！请确保上下两张表头中都包含'总计'列。")
                
        except Exception as e:
            st.error(f"❌ 解析失败，请检查文件格式。报错详情: {e}")

if 'monthly_data' not in st.session_state and os.path.exists(CACHE_FILE):
    try: st.session_state['monthly_data'] = pd.read_pickle(CACHE_FILE)
    except: pass

# ==========================================
# 📈 深度对比图表渲染
# ==========================================
if 'monthly_data' in st.session_state:
    df_nb = st.session_state['monthly_data']['nonbrand']
    df_all = st.session_state['monthly_data']['allseo']
    
    if df_nb.empty or df_all.empty:
        st.warning("⚠️ 提取到的数据为空，请检查上传的表格内是否包含有效数据。")
    else:
        # 数据融合，计算涨降幅
        df_merge = pd.merge(df_nb, df_all, on='Month', how='outer', suffixes=('_NB', '_All')).fillna(0)
        df_merge = df_merge.sort_values('Month').reset_index(drop=True)
        df_merge['NB_Growth'] = df_merge['Total_NB'].pct_change() * 100
        df_merge['All_Growth'] = df_merge['Total_All'].pct_change() * 100

        # ------------------------------------------
        # 📉 1. 历年【非品牌词销售额】同比走势
        # ------------------------------------------
        st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📉 1. 历年【非品牌词销售额总计】年度同环比走势")
        with st.container(border=True):
            df_yoy = df_nb.copy()
            df_yoy['Date'] = pd.to_datetime(df_yoy['Month'] + '-01')
            df_yoy['Year'] = df_yoy['Date'].dt.year.astype(str)
            df_yoy['Month_Num'] = df_yoy['Date'].dt.month
            
            fig1 = go.Figure()
            colors = ['#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']
            for i, year in enumerate(sorted(df_yoy['Year'].unique())):
                df_year = df_yoy[df_yoy['Year'] == year].sort_values('Month_Num')
                fig1.add_trace(go.Scatter(
                    x=df_year['Month_Num'], y=df_year['Total'],
                    mode='lines+markers', name=f'{year}年',
                    line=dict(width=3, color=colors[i % len(colors)]),
                    marker=dict(size=8, color='#ffffff', line=dict(color=colors[i % len(colors)], width=2)),
                    # 🔥 修复了美元与百分号冲突的问题
                    hovertemplate='<b>%{data.name}%{x}月</b><br>非品牌词总计: $%{y:,.2f}<extra></extra>'
                ))
                
            fig1.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickmode='array', tickvals=list(range(1, 13)), ticktext=[f"{i}月" for i in range(1, 13)]),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig1, use_container_width=True)

        # ------------------------------------------
        # 📊 2. 非品牌词 vs ALL SEO 绝对值走势
        # ------------------------------------------
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📊 2. 【非品牌词】与【ALL SEO】销售额总计综合对比")
        with st.container(border=True):
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['Total_NB'],
                mode='lines+markers', name='非品牌词销售额总计',
                line=dict(width=3, color='#0ea5e9'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>非品牌词: $%{y:,.2f}<extra></extra>'
            ))
            fig2.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['Total_All'],
                mode='lines+markers', name='ALL SEO销售额总计',
                line=dict(width=3, color='#8b5cf6'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>ALL SEO: $%{y:,.2f}<extra></extra>'
            ))
            fig2.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickprefix="$")
            )
            st.plotly_chart(fig2, use_container_width=True)

        # ------------------------------------------
        # ⚡ 3. 销售额月度涨降幅对比
        # ------------------------------------------
        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("#### ⚡ 3. 销售额月度涨降幅 (Growth Rate) 对比")
        with st.container(border=True):
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['NB_Growth'],
                mode='lines+markers', name='非品牌词涨跌幅(%)',
                line=dict(width=3, color='#f43f5e'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>非品牌词涨跌: %{y:+.2f}%<extra></extra>'
            ))
            fig3.add_trace(go.Scatter(
                x=df_merge['Month'], y=df_merge['All_Growth'],
                mode='lines+markers', name='ALL SEO涨跌幅(%)',
                line=dict(width=3, color='#10b981'), marker=dict(size=8),
                hovertemplate='<b>%{x}</b><br>ALL SEO涨跌: %{y:+.2f}%<extra></extra>'
            ))
            
            fig3.add_hline(y=0, line_dash="dash", line_color="#94a3b8", annotation_text="0% 基准线")
            fig3.update_layout(
                height=380, hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
                xaxis=dict(showgrid=True, gridcolor='#f1f5f9', type='category'),
                yaxis=dict(showgrid=True, gridcolor='#f1f5f9', ticksuffix="%")
            )
            st.plotly_chart(fig3, use_container_width=True)

        # ------------------------------------------
        # 💡 4. 智能数据分析与总结
        # ------------------------------------------
        st.markdown("### 💡 自动数据洞察报告")
        st.info("""
        **📌 基于以上三大核心图表的业务洞察分析：**
        
        1. **年度同环比成长性（参考图 1）**：
           通过折线纵向对比，可直观判定业务在今年的**增长动能**。若今年折线（如 2026 年）整体浮于去年上方，且波峰未滞后，说明我们的非品牌词 SEO 获取了真实的同比增量突破，未受到行业大盘淡季的过度影响。
           
        2. **非品牌词与整体大盘粘性（参考图 2）**：
           非品牌词的曲线在 ALL SEO 下方的占比反映了我们**长尾词矩阵**的健康度。当两条曲线起伏贴合极其紧密时，意味着我们的长尾排名极其稳固，甚至已经成为拉动全盘 SEO 的决定性力量。
           
        3. **策略波动敏感度分析（参考图 3）**：
           在涨降幅比值中，若【非品牌词（红线）】的涨幅**明显超越**【ALL SEO（绿线）】，标志着我们在小语种特定类目上的优化取得了独立于大盘的超额红利；反之，若跌幅大于均值，则需重点排查近期核心算法是否对长尾泛词页面造成了冲击。
        """)

else:
    st.info("👈 您的缓存池为空。请在上方上传最新整理好的《SEO 整体数据情况》台账以激活对比引擎。")
