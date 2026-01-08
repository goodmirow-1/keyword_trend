import streamlit as st
import os
import pandas as pd
from datetime import datetime
import time
import re
from trend_blog_system import TrendBlogSystem
from wordpress_trend_blog import WordPressTrendBlogSystem

# 페이지 설정
st.set_page_config(
    page_title="Trend Blog Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS (Premium Look)
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #ff3333;
        border: none;
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .keyword-badge {
        display: inline-block;
        padding: 5px 10px;
        margin: 5px;
        border-radius: 20px;
        background-color: #e9ecef;
        font-size: 0.9em;
    }
    .log-container {
        font-family: 'Courier New', Courier, monospace;
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 15px;
        border-radius: 5px;
        height: 400px;
        overflow-y: scroll;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# 시스템 인스턴스 초기화 (캐시)
@st.cache_resource
def get_systems():
    return TrendBlogSystem(), WordPressTrendBlogSystem()

trend_sys, wp_sys = get_systems()

# 사이드바
st.sidebar.title("🔥 Trend Blog Admin")
st.sidebar.markdown("---")
menu = st.sidebar.radio("Menu", ["Dashboard", "Keyword Generator", "Post Management", "System Logs"])

st.sidebar.markdown("---")
st.sidebar.info(f"**Persona**: {trend_sys.persona.capitalize()}")
if trend_sys.tg_token:
    st.sidebar.success("Telegram Notifications: ON")
else:
    st.sidebar.warning("Telegram Notifications: OFF")

# 메인 화면
if menu == "Dashboard":
    st.title("🚀 System Overview")
    
    col1, col2, col3 = st.columns(3)
    
    # 1. 최신 키워드 현황
    with col1:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("📈 Trending Discovery")
        if st.button("Refresh Keywords"):
            with st.spinner("Fetching Google Trends..."):
                all_keywords = trend_sys.get_trending_keywords()
                used_keywords = trend_sys._load_used_keywords()
                st.session_state.keywords = [kw for kw in all_keywords if kw not in used_keywords]
        
        keywords = st.session_state.get('keywords', [])
        if keywords:
            for kw in keywords[:10]:
                st.markdown(f'<span class="keyword-badge">{kw}</span>', unsafe_allow_html=True)
        else:
            st.write("Click 'Refresh' to see trends.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. 최근 생성된 글
    with col2:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("📝 Recent Posts")
        posts = sorted([f for f in os.listdir(trend_sys.blog_posts_dir) if f.endswith('.md')], reverse=True)
        if posts:
            for post in posts[:5]:
                st.write(f"📄 {post[:25]}...")
        else:
            st.write("No posts generated yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. 시스템 상태
    with col3:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("⚙️ System Status")
        st.write(f"**API Ready**: {'✅' if trend_sys.client_ready else '❌'}")
        st.write(f"**WP Ready**: {'✅' if wp_sys.wp_url else '❌'}")
        st.write(f"**Total Posts**: {len(posts)}")
        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "Keyword Generator":
    st.title("🎯 Keyword Generator")
    st.write("트렌드 키워드를 선택하거나 직접 입력하여 블로그를 생성합니다.")
    
    tab1, tab2 = st.tabs(["Trends List", "Manual Input"])
    
    with tab1:
        if st.button("Fetch Current Trends"):
            all_keywords = trend_sys.get_trending_keywords()
            used_keywords = trend_sys._load_used_keywords()
            st.session_state.keywords = [kw for kw in all_keywords if kw not in used_keywords]
            
        keywords = st.session_state.get('keywords', [])
        if keywords:
            selected_kw = st.selectbox("Select a keyword to write about:", keywords)
            do_post = st.checkbox("Post to WordPress immediately?", value=True)
            
            if st.button("Generate & Publish"):
                used_keywords = wp_sys._load_used_keywords()
                if selected_kw in used_keywords:
                    st.error(f"'{selected_kw}'은(는) 이미 작성된 키워드입니다.")
                else:
                    with st.spinner(f"Creating blog for '{selected_kw}'..."):
                    # WordPress 시스템의 run_blog_creation을 활용하되, 특정 키워드만 처리하도록 로직이 필요함
                    # 여기서는 직접 메서드들을 호출
                    content = wp_sys.generate_blog_content(selected_kw)
                    if content:
                        filepath = wp_sys.save_blog_post(selected_kw, content)
                        st.success(f"Blog saved to {filepath}")
                        if do_post:
                            title = wp_sys.extract_title_from_markdown(content)
                            tags = wp_sys.extract_tags_from_markdown(content) or [selected_kw]
                            success = wp_sys.post_to_wordpress(title, content, tags)
                            if success:
                                st.balloons()
                                st.success("Successfully posted to WordPress!")
                    else:
                        st.error("Failed to generate content.")
        else:
            st.info("Fetch trends first.")

    with tab2:
        manual_kw = st.text_input("Enter a specific keyword:")
        if st.button("Generate Manual Post") and manual_kw:
            used_keywords = wp_sys._load_used_keywords()
            if manual_kw in used_keywords:
                st.error(f"'{manual_kw}'은(는) 이미 작성된 키워드입니다.")
            else:
                with st.spinner(f"Creating blog for '{manual_kw}'..."):
                content = wp_sys.generate_blog_content(manual_kw)
                if content:
                    wp_sys.save_blog_post(manual_kw, content)
                    st.success("Blog generated successfully.")
                else:
                    st.error("Failed to generate content.")

elif menu == "Post Management":
    st.title("📁 Post Management")
    posts = sorted([f for f in os.listdir(trend_sys.blog_posts_dir) if f.endswith('.md')], reverse=True)
    
    if not posts:
        st.write("No posts found.")
    else:
        selected_file = st.selectbox("Select a post to view/publish:", posts)
        filepath = os.path.join(trend_sys.blog_posts_dir, selected_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        st.markdown("---")
        col_view, col_action = st.columns([3, 1])
        
        with col_view:
            st.markdown(content)
            
        with col_action:
            st.subheader("Actions")
            if st.button("Post to WordPress"):
                title = wp_sys.extract_title_from_markdown(content)
                tags = wp_sys.extract_tags_from_markdown(content)
                with st.spinner("Posting to WordPress..."):
                    success = wp_sys.post_to_wordpress(title, content, tags)
                    if success:
                        st.success("Posted!")
            
            if st.button("Delete File"):
                os.remove(filepath)
                st.warning("File deleted.")
                st.rerun()

elif menu == "System Logs":
    st.title("🪵 System Logs")
    st.write("`system_log.txt` 실시간 로그 확인")
    
    if os.path.exists(trend_sys.log_file):
        with open(trend_sys.log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # 마지막 100줄만 표시
        log_text = "".join(logs[-100:]).replace("\n", "<br>")
        st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)
        
        if st.button("Clear Logs"):
            with open(trend_sys.log_file, 'w', encoding='utf-8') as f:
                f.write("")
            st.rerun()
    else:
        st.write("Log file not found.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
