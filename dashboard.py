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
menu = st.sidebar.radio("Menu", ["Dashboard", "Keyword Generator", "Post Management", "Used Keywords", "System Logs"])

st.sidebar.markdown("---")
st.sidebar.info(f"**Persona**: {trend_sys.persona.capitalize()}")
if trend_sys.tg_token:
    st.sidebar.success("Telegram Notifications: ON")
else:
    st.sidebar.warning("Telegram Notifications: OFF")

# 메인 화면
if menu == "Dashboard":
    st.title("🚀 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 0. 스마트 작업 실행
    with col1:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("💡 Smart Actions")
        if st.button("🚀 Run: Write Next Trend"):
            with st.spinner("Finding next unused trend & writing..."):
                # run_blog_creation logic inside dashboard
                all_keywords = trend_sys.get_trending_keywords()
                selected_kw = trend_sys.select_keyword(all_keywords)
                
                if selected_kw:
                    content = wp_sys.generate_blog_content(selected_kw)
                    if content:
                        filepath = wp_sys.save_blog_post(selected_kw, content)
                        st.success(f"Generated: {selected_kw}")
                        # 워드프레스 설정이 있으면 자동 포스팅 시도
                        if wp_sys.wp_url:
                            title = wp_sys.extract_title_from_markdown(content)
                            tags = wp_sys.extract_tags_from_markdown(content) or [selected_kw]
                            wp_sys.post_to_wordpress(title, content, tags)
                            st.balloons()
                            st.success("And posted to WordPress!")
                        st.session_state.selected_preview = os.path.basename(filepath)
                else:
                    st.warning("No unused trends found currently.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 1. 최신 키워드 현황
    with col2:
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
    with col3:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("📝 Recent Posts")
        posts = sorted([f for f in os.listdir(trend_sys.blog_posts_dir) if f.endswith('.md')], reverse=True)
        if posts:
            for post in posts[:10]:
                if st.button(f"📄 {post[:30]}", key=f"dash_{post}"):
                    st.session_state.selected_preview = post
        else:
            st.write("No posts generated yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 퀵 미리보기 섹션
    if st.session_state.get('selected_preview'):
        selected_file = st.session_state.selected_preview
        st.markdown(f"### 🔍 Quick Preview: {selected_file}")
        filepath = os.path.join(trend_sys.blog_posts_dir, selected_file)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 이미지 경로 처리 (상대 경로 -> Streamlit에서 보이게)
            # Streamlit은 현재 디렉토리 기준이므로 blog_posts/images/... 를 찾을 수 있어야 함
            # MD 파일 내부에는 images/... 로 되어 있으므로 이를 blog_posts/images/... 로 치환
            preview_content = content.replace("](images/", "](app/blog_posts/images/")
            
            with st.expander("Show/Hide Content", expanded=True):
                st.markdown(content) # 일단 원본으로 시도 (Streamlit 세팅에 따라 다름)
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    if st.button("Close Preview"):
                        st.session_state.selected_preview = None
                        st.rerun()
                with col_p2:
                    if st.button("Manage this post"):
                        # Post Management 메뉴로 이동 (구현 편의상 현재 선택된 파일만 설정)
                        st.session_state.manage_file = selected_file
                        # menu를 바꾸려면 radio 설정을 state와 연동해야 함
                        st.info("Post Management 탭에서 해당 파일을 선택해 주세요.")
        else:
            st.error("File not found.")

    # 3. 시스템 상태
    with col4:
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
                                    if st.button("View Generated Post"):
                                        st.session_state.selected_preview = os.path.basename(filepath)
                                        st.rerun()
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
                        filepath = wp_sys.save_blog_post(manual_kw, content)
                        st.success("Blog generated successfully.")
                        if st.button("View Generated Post", key="view_manual"):
                            st.session_state.selected_preview = os.path.basename(filepath)
                            st.rerun()
                    else:
                        st.error("Failed to generate content.")

elif menu == "Post Management":
    st.title("📁 Post Management")
    posts = sorted([f for f in os.listdir(trend_sys.blog_posts_dir) if f.endswith('.md')], reverse=True)
    
    if not posts:
        st.write("No posts found.")
    else:
        # Pre-selection logic from Dashboard
        default_index = 0
        managed_file = st.session_state.get('manage_file')
        if managed_file in posts:
            default_index = posts.index(managed_file)
            
        selected_file = st.selectbox("Select a post to view/publish:", posts, index=default_index)
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

elif menu == "Used Keywords":
    st.title("📚 Used Keywords Management")
    st.write("이미 사용된 키워드 목록을 확인하고 관리합니다.")
    
    used_keywords = trend_sys._load_used_keywords()
    
    if not used_keywords:
        st.info("No used keywords yet.")
    else:
        # 키워드 데이터프레임으로 표시
        df = pd.DataFrame(used_keywords, columns=["Keyword"])
        df = df.iloc[::-1] # 최신순
        
        st.markdown(f"**Total Used Keywords**: {len(used_keywords)}")
        
        # 삭제 기능을 위한 멀티셀렉트
        to_delete = st.multiselect("Select keywords to delete:", used_keywords)
        
        if st.button("Delete Selected Keywords"):
            if to_delete:
                new_list = [kw for kw in used_keywords if kw not in to_delete]
                trend_sys._save_used_keywords(new_list)
                st.success(f"{len(to_delete)} keywords deleted.")
                st.rerun()
            else:
                st.warning("Please select keywords to delete.")
        
        st.markdown("---")
        st.table(df)

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
