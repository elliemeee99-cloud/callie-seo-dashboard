import streamlit as st

# 这个 app.py 只是一个大门，引导用户直接进入第一页
st.set_page_config(page_title="Callie SEO Dashboard", page_icon="🌍")

# 使用 Streamlit 1.35+ 的全新导航跳转功能，直接重定向到你的目标概览页
st.switch_page("pages/1_SEO目标概览.py")
