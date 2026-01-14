import os
import base64
import requests
import re
from dotenv import load_dotenv
from trend_blog_system import TrendBlogSystem

# Load environment variables
load_dotenv()

class WordPressTrendBlogSystem(TrendBlogSystem):
    """WordPress 포스팅 기능이 추가된 트렌드 블로그 시스템"""
    
    def __init__(self):
        super().__init__()
        
        # WordPress 설정
        self.wp_url = os.getenv('WORDPRESS_URL')
        self.wp_username = os.getenv('WORDPRESS_USERNAME')
        self.wp_app_password = os.getenv('WORDPRESS_APP_PASSWORD')
        self.wp_category = "이슈트래킹"  # 기본 카테고리 설정 (모든 글 통일)
        
        if self.wp_url:
            self._log(f"WordPress 설정 완료: {self.wp_url}")
        else:
            self._log("WordPress 설정이 없습니다. 로컬 파일로만 저장됩니다.")

    def get_related_posts(self, current_keyword):
        """
        WordPress에서 최신 게시물 3개를 가져와 추천 글로 반환
        """
        if not self.wp_url or not self.wp_username or not self.wp_app_password:
            self._log("WordPress 설정이 없어 로컬 관련글 로직을 사용합니다.")
            return super().get_related_posts(current_keyword)

        try:
            self._log("WordPress에서 최신 게시물 가져오는 중...")
            headers = self.get_wp_headers()
            
            # 최신 게시물 3개 가져오기
            api_url = f"{self.wp_url}/wp-json/wp/v2/posts?per_page=3&status=publish"
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            posts = response.json()
            related = []
            
            for post in posts:
                # 렌더링된 제목에서 HTML 태그 제거 (있는 경우)
                title = post.get('title', {}).get('rendered', '제목 없음')
                title = re.sub(r'<[^>]+>', '', title)
                link = post.get('link')
                
                if link:
                    related.append({'title': title, 'url': link})
            
            if related:
                self._log(f"WordPress에서 {len(related)}개의 추천 글을 가져왔습니다.")
                return related
            else:
                self._log("WordPress에 게시된 글이 없습니다.")
                return []
                
        except Exception as e:
            self._log(f"WordPress 게시물 가져오기 실패: {e}")
            return []
    
    def get_wp_headers(self):
        """WordPress API 인증 헤더 생성"""
        credentials = f"{self.wp_username}:{self.wp_app_password}"
        token = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
    
    def get_or_create_category(self, category_name):
        """카테고리 ID 가져오기 또는 생성"""
        if not self.wp_url or not self.wp_username or not self.wp_app_password:
            self._log("WordPress 설정이 없습니다.")
            return None
            
        self._log(f"카테고리 확인 중: {category_name}...")
        headers = self.get_wp_headers()
        
        try:
            # 카테고리 검색
            search_url = f"{self.wp_url}/wp-json/wp/v2/categories?search={category_name}"
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            categories = response.json()
            
            for cat in categories:
                if cat['name'] == category_name:
                    self._log(f"카테고리 발견: {category_name} (ID: {cat['id']})")
                    return cat['id']
            
            # 카테고리 생성
            self._log(f"카테고리 생성 중: {category_name}...")
            create_url = f"{self.wp_url}/wp-json/wp/v2/categories"
            data = {"name": category_name}
            response = requests.post(create_url, headers=headers, json=data)
            response.raise_for_status()
            category_id = response.json()['id']
            self._log(f"카테고리 생성 완료: {category_name} (ID: {category_id})")
            return category_id
            
        except Exception as e:
            self._log(f"카테고리 관리 오류 {category_name}: {e}")
            return None
    
    def get_or_create_tag(self, tag_name):
        """태그 ID 가져오기 또는 생성"""
        if not self.wp_url or not self.wp_username or not self.wp_app_password:
            return None
            
        headers = self.get_wp_headers()
        try:
            search_url = f"{self.wp_url}/wp-json/wp/v2/tags?search={tag_name}"
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            tags = response.json()
            
            for tag in tags:
                if tag['name'] == tag_name:
                    return tag['id']
            
            create_url = f"{self.wp_url}/wp-json/wp/v2/tags"
            data = {"name": tag_name}
            response = requests.post(create_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['id']
        except Exception as e:
            self._log(f"태그 관리 오류 {tag_name}: {e}")
            return None
    
    def extract_title_from_markdown(self, markdown_content):
        """Markdown에서 제목 추출"""
        # Frontmatter에서 title 추출
        # Frontmatter에서 title 추출 (유연한 구분자 처리)
        # 구분자: ---, –, —, 또는 그 조합 (3개 이상)
        fm_match = re.match(r'^([-–—]{3,})\s*\n(.*?)\n\1', markdown_content.strip(), re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(2)
            for line in frontmatter.split('\n'):
                if line.strip().startswith('title:'):
                    title = line.split('title:', 1)[1].strip()
                    # 따옴표 제거
                    title = title.strip('"').strip("'")
                    return title
        
        # Frontmatter가 없으면 첫 번째 # 헤더 찾기
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        
        return "제목 없음"
    
    def extract_tags_from_markdown(self, markdown_content):
        """Markdown frontmatter에서 태그 추출"""
        tags = []
        # Frontmatter 유연한 처리
        fm_match = re.match(r'^([-–—]{3,})\s*\n(.*?)\n\1', markdown_content.strip(), re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(2)
            in_tags = False
            for line in frontmatter.split('\n'):
                line = line.strip()
                if line.startswith('tags:'):
                    # tags: [tag1, tag2] 형식
                    tag_part = line.split('tags:', 1)[1].strip()
                    if tag_part.startswith('[') and tag_part.endswith(']'):
                        tag_part = tag_part[1:-1]
                        tags = [t.strip().strip('"').strip("'") for t in tag_part.split(',')]
                    else:
                        in_tags = True
                elif in_tags:
                    if line.startswith('-'):
                        tag = line[1:].strip().strip('"').strip("'")
                        tags.append(tag)
                    elif line and not line.startswith(' '):
                        in_tags = False
        return tags
    
    def markdown_to_html(self, markdown_content):
        """Markdown을 HTML로 변환 (완전한 변환 및 스타일링 강화)"""
        html = markdown_content.strip()
        
        # 0. 초기 정리: 불필요한 마크다운 기호 및 LLM 잔재 제거
        # 줄 시작부분의 이상한 기호들 정리
        html = re.sub(r'^[ \t]*(\*|\-|\+)[ \t]*(\*|\-|\+)+', r'\1', html, flags=re.MULTILINE)
        
        # YouTube iframe을 WordPress oEmbed 용 URL로 미리 변환
        youtube_pattern = r'<iframe.*?src="https://www\.youtube\.com/embed/([^"]+)".*?></iframe>'
        html = re.sub(youtube_pattern, r'https://www.youtube.com/watch?v=\1', html)
        
        # 1. Frontmatter 제거 (유연한 구분자 처리)
        # 시작과 끝 구분자가 ---, –, — 등으로 다양할 수 있음
        html = re.sub(r'^([-–—]{3,})\s*\n.*?\n\1(\s*\n|$)', '', html, flags=re.DOTALL)
        
        # 2. 코드 블록 처리 (``` 또는 ~~~)
        def convert_code_block(match):
            lang = match.group(1) or ''
            code = match.group(2)
            code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f'<pre><code class="language-{lang}">{code}</code></pre>'
        
        html = re.sub(r'```(\w+)?\n(.*?)```', convert_code_block, html, flags=re.DOTALL)
        
        # 3. 뉴스 섹션 특수 처리 (카드 디자인 적용)
        # 📰 관련 뉴스 섹션을 찾아서 커스텀 HTML로 변환
        if "## 📰 관련 뉴스" in html:
            parts = html.split("## 📰 관련 뉴스")
            before_news = parts[0]
            after_news_parts = parts[1].split("##", 1) # 다음 섹션(보통 함께 보면 좋은 글) 분리
            news_content = after_news_parts[0]
            remaining = "##" + after_news_parts[1] if len(after_news_parts) > 1 else ""
            
            # 뉴스 아이템 추출 및 변환
            # 형식: ### [제목](URL)\n* **출처**: ... \n![이미지](...)\n> 요약...
            news_items_html = '<div class="news-container">\n'
            
            # 뉴스 아이템별로 분리 (### [ 로 시작하는 부분 기준)
            raw_items = re.split(r'###\s*\[', news_content)
            for item in raw_items:
                if not item.strip(): continue
                
                try:
                    # 제목과 URL 추출
                    title_url_match = re.search(r'([^\]]+)\]\(([^\)]+)\)', item)
                    if not title_url_match: continue
                    title = title_url_match.group(1)
                    url = title_url_match.group(2)
                    
                    # 출처 추출
                    source = "뉴스"
                    source_match = re.search(r'\*\s*\*\*출처\*\*\s*:\s*([^\n]+)', item)
                    if source_match:
                        source = source_match.group(1).strip()
                    
                    # 이미지 추출
                    img_url = ""
                    img_match = re.search(r'!\[[^\]]*\]\(([^\)]+)\)', item)
                    if img_match:
                        img_url = img_match.group(1)
                    
                    # 요약 추출
                    summary = ""
                    summary_match = re.search(r'>\s*([^\n]+)', item)
                    if summary_match:
                        summary = summary_match.group(1).strip()
                    
                    # 카드 HTML 생성
                    news_items_html += f'''
                    <div class="news-card">
                        {f'<div class="news-image"><img src="{img_url}" alt="{title}"></div>' if img_url else ''}
                        <div class="news-body">
                            <div class="news-source">{source}</div>
                            <h4 class="news-title"><a href="{url}" target="_blank">{title}</a></h4>
                            <p class="news-summary">{summary}</p>
                        </div>
                    </div>
                    '''
                except Exception as e:
                    self._log(f"뉴스 아이템 파싱 오류: {e}")
                    continue
            
            news_items_html += '</div>\n'
            html = before_news + "<h2>📰 관련 뉴스</h2>\n" + news_items_html + remaining

        # 4. 이미지 변환 (일반 이미지)
        html = re.sub(r'!\[([^\]]*)\]\(([^\)]*)\)', r'<img src="\2" alt="\1" class="post-image" />', html)
        
        # 5. 링크 변환 (file:// 제거 및 일반 링크 정리)
        def convert_link(match):
            text, url = match.group(1), match.group(2)
            if url.startswith('file://'): return f'<strong>{text}</strong>'
            return f'<a href="{url}" target="_blank">{text}</a>'
        html = re.sub(r'\[([^\]]*)\]\(([^\)]*)\)', convert_link, html)
        
        # 6. 헤더 변환 (H1-H4)
        for i in range(4, 0, -1):
            html = re.sub(rf'^{"#"*i} (.+)$', rf'<h{i+1}>\1</h{i+1}>', html, flags=re.MULTILINE)
        
        # 7. 인라인 스타일 (볼드, 이탤릭, 취소선)
        html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'~~(.+?)~~', r'<del>\1</del>', html)
        
        # 8. 리스트 처리 (중요: 마크다운 기호가 남지 않도록)
        # 먼저 리스트 아이템을 <li>로 변환
        html = re.sub(r'^[ \t]*[\*\-\+] (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # 9. 인용문 변환
        html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
        
        # 10. 단락 처리: 빈 줄로 구분된 텍스트를 <p>로 감싸기
        # 주의: 이미 HTML 태그로 시작하는 줄은 건너뜀
        final_lines = []
        is_list = False
        for line in html.split('\n'):
            line = line.strip()
            if not line: 
                if is_list:
                    final_lines.append('</ul>')
                    is_list = False
                continue
            
            if line.startswith('<li>'):
                if not is_list:
                    final_lines.append('<ul class="post-list">')
                    is_list = True
                final_lines.append(line)
            elif line.startswith('<h') or line.startswith('<blockquote') or line.startswith('<div') or line.startswith('<pre') or line.startswith('<p') or line.startswith('<hr') or line.startswith('<img'):
                if is_list:
                    final_lines.append('</ul>')
                    is_list = False
                final_lines.append(line)
            else:
                if is_list:
                    final_lines.append('</ul>')
                    is_list = False
                final_lines.append(f'<p>{line}</p>')
        
        if is_list: final_lines.append('</ul>')
        
        return '\n'.join(final_lines)
    
    def post_to_wordpress(self, title, content, tags=None):
        """WordPress에 게시글 포스팅 (스타일 시트 추가)"""
        if not self.wp_url or not self.wp_username or not self.wp_app_password:
            self._log("WordPress 설정이 없어 포스팅을 건너뜁니다.")
            return False
        
        # 워드프레스용 스타일 시트
        style_css = """
        <style>
            .post-image { max-width: 100%; height: auto; border-radius: 8px; margin: 20px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            .post-list { margin: 20px 0; padding-left: 20px; line-height: 1.8; }
            .post-list li { margin-bottom: 10px; list-style-type: decimal; }
            
            /* 뉴스 카드 컨테이너 */
            .news-container { display: flex; flex-direction: column; gap: 20px; margin: 30px 0; }
            .news-card { 
                display: flex; background: #fff; border: 1px solid #eee; border-radius: 12px; 
                overflow: hidden; transition: transform 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            .news-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
            .news-image { width: 150px; min-width: 150px; }
            .news-image img { width: 100%; height: 100%; object-fit: cover; }
            .news-body { padding: 15px; display: flex; flex-direction: column; justify-content: center; }
            .news-source { font-size: 0.8em; color: #ff4757; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; }
            .news-title { margin: 0 0 10px 0; font-size: 1.1em; line-height: 1.4; }
            .news-title a { color: #2f3542; text-decoration: none; font-weight: 700; }
            .news-title a:hover { color: #ff4757; }
            .news-summary { font-size: 0.9em; color: #57606f; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
            
            @media (max-width: 600px) {
                .news-card { flex-direction: column; }
                .news-image { width: 100%; height: 180px; }
            }
        </style>
        """
        
        self._log("WordPress에 포스팅 중...")
        
        try:
            headers = self.get_wp_headers()
            
            # 카테고리 ID 가져오기
            category_id = self.get_or_create_category(self.wp_category)
            
            # 태그 ID 가져오기
            tag_ids = [self.get_or_create_tag(t) for t in tags if t] if tags else []
            
            # Markdown을 HTML로 변환하고 스타일 시트 추가
            html_content = style_css + self.markdown_to_html(content)
            
            # 게시글 데이터
            wp_post_data = {
                "title": title,
                "content": html_content,
                "status": "publish",
                "categories": [category_id] if category_id else [],
                "tags": [tid for tid in tag_ids if tid]
            }
            
            # 포스팅
            api_url = f"{self.wp_url}/wp-json/wp/v2/posts"
            response = requests.post(api_url, headers=headers, json=wp_post_data)
            response.raise_for_status()
            
            post_link = response.json().get('link')
            self._log(f"WordPress 포스팅 성공: {post_link}")
            self._send_telegram_notification(f"🌐 *워드프레스 포스팅 완료*\n\n*제목*: {title}\n*링크*: {post_link}")
            return True
            
        except Exception as e:
            self._log(f"WordPress 포스팅 오류: {e}")
            self._send_telegram_notification(f"⚠️ *워드프레스 포스팅 오류*\n\n*제목*: {title}\n*오류*: `{str(e)[:100]}`")
            if 'response' in locals() and response:
                self._log(f"응답: {response.text}")
            return False
    
    def run_blog_creation(self, do_post=False):
        """
        전체 블로그 작성 프로세스 실행 (WordPress 포스팅 포함)
        
        Args:
            do_post (bool): True일 경우에만 워드프레스에 포스팅 수행
        """
        self._log("=" * 50)
        self._log(f"블로그 작성 프로세스 시작 (doPost={do_post})")
        
        # 1. 트렌드 키워드 가져오기
        keywords = self.get_trending_keywords()
        
        if not keywords:
            self._log("키워드를 가져올 수 없습니다.")
            return
        
        # 2. 사용 가능한 키워드 선택
        selected_keyword = self.select_keyword(keywords)
        
        if not selected_keyword:
            self._log("모든 키워드가 이미 사용되었습니다.")
            return
        
        # 3. 블로그 콘텐츠 생성 (부모 클래스의 메서드 사용 - 카테고리 로직 포함됨)
        content = self.generate_blog_content(selected_keyword)
        
        if not content:
            self._log("콘텐츠 생성에 실패했습니다.")
            return
        
        # 4. 블로그 포스트 저장 (로컬)
        filepath = self.save_blog_post(selected_keyword, content)
        
        if filepath:
            self._log(f"블로그 작성 완료: {selected_keyword}")
            
            # 5. WordPress에 포스팅 (do_post=True 일 때만)
            if do_post:
                title = self.extract_title_from_markdown(content)
                tags = self.extract_tags_from_markdown(content)
                
                if not tags:
                    tags = [selected_keyword]
                
                self.post_to_wordpress(title, content, tags)
            else:
                self._log("워드프레스 포스팅 생략 (doPost=False)")
        else:
            self._log("블로그 저장에 실패했습니다.")
        
        self._log("블로그 작성 프로세스 종료")
        self._log("=" * 50)


def main():
    """
    메인 실행 함수 - 스케줄링 및 CLI 인자 처리
    """
    import schedule
    import time
    import argparse
    import sys
    
    # CLI 인자 파싱
    parser = argparse.ArgumentParser(description='WordPress Trend Blog System')
    parser.add_argument('--doPost', action='store_true', help='Set this flag to enable posting to WordPress')
    args = parser.parse_args()
    
    start_msg = "블로그 자동 작성 시스템 시작"
    if args.doPost:
        start_msg += " (워드프레스 포스팅 활성화)"
    else:
        start_msg += " (워드프레스 포스팅 비활성화 - 파일만 저장)"
    
    print(start_msg)
    
    system = WordPressTrendBlogSystem()
    
    # 스케줄 설정: 오전 8시부터 4시간 간격
    # 인자 전달을 위해 lambda 사용
    schedule.every().day.at("08:00").do(lambda: system.run_blog_creation(do_post=args.doPost))
    schedule.every().day.at("12:00").do(lambda: system.run_blog_creation(do_post=args.doPost))
    schedule.every().day.at("16:00").do(lambda: system.run_blog_creation(do_post=args.doPost))
    schedule.every().day.at("20:00").do(lambda: system.run_blog_creation(do_post=args.doPost))
    
    print("스케줄: 08:00, 12:00, 16:00, 20:00")
    print("중지하려면 Ctrl+C를 누르세요.")
    
    # 즉시 한 번 실행 (테스트용)
    print("초기 실행 중...")
    system.run_blog_creation(do_post=args.doPost)
    
    # 스케줄 루프 실행
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

if __name__ == "__main__":
    main()
