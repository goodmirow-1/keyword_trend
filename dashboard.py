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
    page_title="트렌드 블로그 관리자",
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
st.sidebar.title("🔥 트렌드 블로그 관리")
st.sidebar.markdown("---")
menu = st.sidebar.radio("메뉴", ["시스템 개요", "키워드 생성기", "포스트 관리", "사용된 키워드", "시스템 로그"])

st.sidebar.markdown("---")
st.sidebar.info(f"**페르소나**: {trend_sys.persona.capitalize()}")
if trend_sys.tg_token:
    st.sidebar.success("텔레그램 알림: 활성화")
else:
    st.sidebar.warning("텔레그램 알림: 비활성화")

# 메인 화면
if menu == "시스템 개요":
    st.title("🚀 시스템 현황")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # 0. 스마트 작업 실행
    with col1:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("💡 스마트 액션")
        if st.button("🚀 실행: 다음 트렌드 즉시 작성"):
            with st.spinner("다음 미사용 트렌드 찾는 중..."):
                # run_blog_creation logic inside dashboard
                all_keywords = trend_sys.get_trending_keywords()
                selected_kw = trend_sys.select_keyword(all_keywords)
                
                if selected_kw:
                    content = wp_sys.generate_blog_content(selected_kw)
                    if content:
                        filepath = wp_sys.save_blog_post(selected_kw, content)
                        st.success(f"✅ 생성 완료: {selected_kw}")
                        wp_sys._send_telegram_notification(f"✅ *블로그 로컬 저장 완료*\n\n*키워드*: {selected_kw}\n*파일*: `{os.path.basename(filepath)}`")
                        
                        # 세션 상태에 저장하여 다이얼로그 표시
                        st.session_state.selected_preview = os.path.basename(filepath)
                        st.session_state.show_wp_dialog = True
                        st.session_state.dialog_content = content
                        st.session_state.dialog_keyword = selected_kw
                        st.session_state.dialog_filepath = filepath
                        st.rerun()
                else:
                    st.warning("현재 사용 가능한 새로운 트렌드가 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 워드프레스 포스팅 다이얼로그
    @st.dialog("🌐 워드프레스 포스팅")
    def wordpress_post_dialog():
        st.write(f"**키워드**: {st.session_state.dialog_keyword}")
        st.write(f"**파일**: {os.path.basename(st.session_state.dialog_filepath)}")
        st.markdown("---")
        st.info("💡 로컬에 저장이 완료되었습니다. 워드프레스에 바로 게시하시겠습니까?")
        
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("✅ 예, 게시합니다", use_container_width=True):
                if wp_sys.wp_url:
                    with st.spinner("워드프레스에 포스팅 중..."):
                        title = wp_sys.extract_title_from_markdown(st.session_state.dialog_content)
                        tags = wp_sys.extract_tags_from_markdown(st.session_state.dialog_content) or [st.session_state.dialog_keyword]
                        success = wp_sys.post_to_wordpress(title, st.session_state.dialog_content, tags)
                        if success:
                            st.balloons()
                            st.success("워드프레스 포스팅 성공!")
                            time.sleep(1)
                else:
                    st.error("워드프레스 설정이 없습니다.")
                
                # 다이얼로그 닫기
                st.session_state.show_wp_dialog = False
                st.rerun()
        
        with col_no:
            if st.button("❌ 아니오, 나중에", use_container_width=True):
                st.session_state.show_wp_dialog = False
                st.rerun()
    
    # 다이얼로그 표시
    if st.session_state.get('show_wp_dialog', False):
        wordpress_post_dialog()

    # 1. 최신 키워드 현황
    with col2:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("📈 실시간 트렌드")
        if st.button("키워드 새로고침"):
            with st.spinner("구글 트렌드 불러오는 중..."):
                all_keywords = trend_sys.get_trending_keywords()
                used_keywords = trend_sys._load_used_keywords()
                st.session_state.keywords = [kw for kw in all_keywords if kw not in used_keywords]
        
        keywords = st.session_state.get('keywords', [])
        if keywords:
            for kw in keywords[:10]:
                st.markdown(f'<span class="keyword-badge">{kw}</span>', unsafe_allow_html=True)
        else:
            st.write("새로고침 버튼을 눌러주세요.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. 최근 생성된 글
    with col3:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("📝 최근 생성 포스트")
        posts = sorted([f for f in os.listdir(trend_sys.blog_posts_dir) if f.endswith('.md')], reverse=True)
        if posts:
            for post in posts[:10]:
                if st.button(f"📄 {post[:30]}", key=f"dash_{post}"):
                    st.session_state.selected_preview = post
        else:
            st.write("아직 생성된 포스트가 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    # 퀵 미리보기 섹션
    if st.session_state.get('selected_preview'):
        selected_file = st.session_state.selected_preview
        st.markdown(f"### 🔍 빠른 미리보기: {selected_file}")
        filepath = os.path.join(trend_sys.blog_posts_dir, selected_file)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            with st.expander("내용 보기/숨기기", expanded=True):
                st.markdown(content, unsafe_allow_html=True)
                
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    if st.button("미리보기 닫기"):
                        st.session_state.selected_preview = None
                        st.rerun()
                with col_p2:
                    if st.button("이 포스트 관리하기"):
                        st.session_state.manage_file = selected_file
                        st.info("포스트 관리 탭에서 해당 파일을 선택해 주세요.")
        else:
            st.error("파일을 찾을 수 없습니다.")

    # 3. 시스템 상태
    with col4:
        st.markdown('<div class="status-card">', unsafe_allow_html=True)
        st.subheader("⚙️ 시스템 상태")
        st.write(f"**API 준비**: {'✅' if trend_sys.client_ready else '❌'}")
        st.write(f"**WP 준비**: {'✅' if wp_sys.wp_url else '❌'}")
        st.write(f"**총 포스트 수**: {len(posts)}")
        
        st.markdown("---")
        st.subheader("🔔 알림 테스트")
        if trend_sys.tg_token:
            if st.button("텔레그램 테스트 메시지 전송"):
                with st.spinner("전송 중..."):
                    # 직접 성공/실패 여부를 알기 위해 _send_telegram_notification 수정 없이 여기서 시도
                    import requests
                    url = f"https://api.telegram.org/bot{trend_sys.tg_token}/sendMessage"
                    data = {"chat_id": trend_sys.tg_chat_id, "text": "✅ 대시보드 연결 테스트 메시지입니다!"}
                    try:
                        res = requests.post(url, data=data, timeout=5)
                        if res.status_code == 200:
                            st.success("전송 성공!")
                        else:
                            st.error(f"실패: {res.json().get('description')}")
                            st.info("💡 도움이 필요하세요? 봇이 채널에 '관리자'로 초대되어 있는지, ID가 정확한지 확인해 주세요.")
                    except Exception as e:
                        st.error(f"오류: {e}")
        else:
            st.warning("텔레그램 설정이 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

elif menu == "키워드 생성기":
    st.title("🎯 키워드 생성기")
    st.write("트렌드 키워드를 선택하거나 직접 입력하여 블로그를 생성합니다.")
    
    tab1, tab2 = st.tabs(["트렌드 목록", "직접 입력"])
    
    with tab1:
        if st.button("현재 트렌드 가져오기"):
            all_keywords = trend_sys.get_trending_keywords()
            used_keywords = trend_sys._load_used_keywords()
            st.session_state.keywords = [kw for kw in all_keywords if kw not in used_keywords]
            
        keywords = st.session_state.get('keywords', [])
        if keywords:
            selected_kw = st.selectbox("작성할 키워드 선택:", keywords)
            do_post = st.checkbox("워드프레스에 즉시 포스팅하시겠습니까?", value=False)
            
            if st.button("생성 및 발행"):
                used_keywords = wp_sys._load_used_keywords()
                if selected_kw in used_keywords:
                    st.error(f"'{selected_kw}'은(는) 이미 작성된 키워드입니다.")
                else:
                    with st.spinner(f"'{selected_kw}' 블로그 생성 중..."):
                        # WordPress 시스템의 run_blog_creation을 활용하되, 특정 키워드만 처리하도록 로직이 필요함
                        # 여기서는 직접 메서드들을 호출
                        content = wp_sys.generate_blog_content(selected_kw)
                        if content:
                            filepath = wp_sys.save_blog_post(selected_kw, content)
                            st.success(f"블로그 저장 완료: {filepath}")
                            wp_sys._send_telegram_notification(f"✅ *블로그 로컬 저장 완료*\n\n*키워드*: {selected_kw}\n*파일*: `{os.path.basename(filepath)}`")
                            if do_post:
                                title = wp_sys.extract_title_from_markdown(content)
                                tags = wp_sys.extract_tags_from_markdown(content) or [selected_kw]
                                success = wp_sys.post_to_wordpress(title, content, tags)
                                if success:
                                    st.balloons()
                                    st.success("워드프레스 포스팅 성공!")
                                    if st.button("생성된 포스트 보기"):
                                        st.session_state.selected_preview = os.path.basename(filepath)
                                        st.rerun()
                        else:
                            st.error("콘텐츠 생성에 실패했습니다.")
        else:
            st.info("먼저 트렌드를 가져와주세요.")

    with tab2:
        manual_kw = st.text_input("직접 키워드 입력:")
        if st.button("수동 생성 실행") and manual_kw:
            used_keywords = wp_sys._load_used_keywords()
            if manual_kw in used_keywords:
                st.error(f"'{manual_kw}'은(는) 이미 작성된 키워드입니다.")
            else:
                with st.spinner(f"'{manual_kw}' 블로그 생성 중..."):
                    content = wp_sys.generate_blog_content(manual_kw)
                    if content:
                        filepath = wp_sys.save_blog_post(manual_kw, content)
                        st.success("블로그 생성이 완료되었습니다.")
                        wp_sys._send_telegram_notification(f"✅ *블로그 수동 생성 완료*\n\n*키워드*: {manual_kw}")
                        if st.button("생성된 포스트 보기", key="view_manual"):
                            st.session_state.selected_preview = os.path.basename(filepath)
                            st.rerun()
                    else:
                        st.error("콘텐츠 생성에 실패했습니다.")

elif menu == "포스트 관리":
    st.title("📁 포스트 관리")
    posts = sorted([f for f in os.listdir(trend_sys.blog_posts_dir) if f.endswith('.md')], reverse=True)
    
    if not posts:
        st.write("발견된 포스트가 없습니다.")
    else:
        # Pre-selection logic from Dashboard
        default_index = 0
        managed_file = st.session_state.get('manage_file')
        if managed_file in posts:
            default_index = posts.index(managed_file)
            
        selected_file = st.selectbox("조회/발행할 포스트 선택:", posts, index=default_index)
        filepath = os.path.join(trend_sys.blog_posts_dir, selected_file)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        st.markdown("---")
        col_view, col_action = st.columns([3, 1])
        
        with col_view:
            st.markdown(content)
            
        with col_action:
            st.subheader("액션")
            if st.button("워드프레스에 포스팅"):
                title = wp_sys.extract_title_from_markdown(content)
                tags = wp_sys.extract_tags_from_markdown(content)
                with st.spinner("워드프레스에 포스팅 중..."):
                    success = wp_sys.post_to_wordpress(title, content, tags)
                    if success:
                        st.success("포스팅 완료!")
            
            if st.button("파일 삭제"):
                os.remove(filepath)
                st.warning("파일이 삭제되었습니다.")
                st.rerun()

elif menu == "사용된 키워드":
    st.title("📚 사용된 키워드 관리")
    st.write("이미 사용된 키워드 목록을 확인하고 관리합니다.")
    
    used_keywords = trend_sys._load_used_keywords()
    
    if not used_keywords:
        st.info("아직 사용된 키워드가 없습니다.")
    else:
        # 키워드 데이터프레임으로 표시
        df = pd.DataFrame(used_keywords, columns=["키워드"])
        df = df.iloc[::-1] # 최신순
        
        st.markdown(f"**총 사용 키워드**: {len(used_keywords)}")
        
        # 삭제 기능을 위한 멀티셀렉트
        to_delete = st.multiselect("삭제할 키워드 선택:", used_keywords)
        
        if st.button("선택한 키워드 삭제"):
            if to_delete:
                new_list = [kw for kw in used_keywords if kw not in to_delete]
                trend_sys._save_used_keywords(new_list)
                st.success(f"{len(to_delete)}개의 키워드가 삭제되었습니다.")
                st.rerun()
            else:
                st.warning("삭제할 키워드를 선택해주세요.")
        
        st.markdown("---")
        st.table(df)

elif menu == "시스템 로그":
    st.title("🪵 시스템 로그")
    st.write("`system_log.txt` 실시간 로그 확인")
    
    if os.path.exists(trend_sys.log_file):
        with open(trend_sys.log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # 마지막 100줄만 표시
        log_text = "".join(logs[-100:]).replace("\n", "<br>")
        st.markdown(f'<div class="log-container">{log_text}</div>', unsafe_allow_html=True)
        
        if st.button("로그 비우기"):
            with open(trend_sys.log_file, 'w', encoding='utf-8') as f:
                f.write("")
            st.rerun()
    else:
        st.write("로그 파일을 찾을 수 없습니다.")

st.sidebar.markdown("---")
st.sidebar.caption(f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
