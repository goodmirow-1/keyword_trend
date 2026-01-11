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
        if markdown_content.strip().startswith('---'):
            parts = markdown_content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
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
        if markdown_content.strip().startswith('---'):
            parts = markdown_content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
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
        """Markdown을 HTML로 변환 (완전한 변환)"""
        html = markdown_content.strip()
        
        # 0. 전체를 감싸는 코드 블록 제거 (LLM이 자주 이렇게 줌)
        # 예: ```markdown ... ```
        # 주의: 내부의 코드 블록은 건드리지 않도록 조심해야 함.
        # 단순히 앞뒤의 ```markdown과 ```만 제거
        if html.startswith('```'):
            lines = html.split('\n')
            # 첫 줄이 ```로 시작하고
            if lines[0].strip().startswith('```'):
                # 마지막 줄이 ```로 끝나면
                if lines[-1].strip() == '```':
                    # 첫 줄과 마지막 줄 제거
                    html = '\n'.join(lines[1:-1]).strip()
        
        # 1. Frontmatter 제거 (YAML frontmatter) - 강화된 버전
        # --- 로 시작하고 --- 또는 -- 로 끝나는 모든 경우 처리
        if html.startswith('---'):
            # 정규식으로 frontmatter 전체 제거 (--- ... --- 또는 --- ... --)
            html = re.sub(r'^---\s*\n.*?\n(---|--)(\s*\n|$)', '', html, flags=re.DOTALL | re.MULTILINE)
        
        # 2. 코드 블록 안의 frontmatter 제거 (혹시 남아있을 경우)
        html = re.sub(r'```(?:markdown|yaml)\s*\n?---.*?---\s*\n?```', '', html, flags=re.DOTALL)
        
        # 3. 남아있는 독립적인 frontmatter 블록 제거 (혹시 모를 경우 대비)
        html = re.sub(r'^---\s*\ntitle:.*?\n(---|--)(\s*\n|$)', '', html, flags=re.DOTALL | re.MULTILINE)
        
        # 3. 코드 블록 변환 (``` 또는 ~~~)
        def convert_code_block(match):
            lang = match.group(1) or ''
            code = match.group(2)
            # HTML 이스케이프
            code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if lang:
                return f'<pre><code class="language-{lang}">{code}</code></pre>'
            return f'<pre><code>{code}</code></pre>'
        
        html = re.sub(r'```(\w+)?\n(.*?)```', convert_code_block, html, flags=re.DOTALL)
        html = re.sub(r'~~~(\w+)?\n(.*?)~~~', convert_code_block, html, flags=re.DOTALL)
        
        # 4. 마크다운 테이블 변환
        def convert_table(table_text):
            lines = [line.strip() for line in table_text.strip().split('\n') if line.strip()]
            if len(lines) < 2:
                return table_text
            
            # 헤더와 구분선 확인
            header_line = lines[0]
            separator_line = lines[1] if len(lines) > 1 else ''
            
            # 구분선이 아니면 테이블이 아님
            if not re.match(r'^\|?[\s\-:|]+\|?$', separator_line):
                return table_text
            
            # 테이블 HTML 생성
            table_html = '<table border="1" style="border-collapse: collapse; width: 100%;">\n'
            
            # 헤더 처리
            headers = [cell.strip() for cell in header_line.split('|') if cell.strip()]
            table_html += '<thead>\n<tr>\n'
            for header in headers:
                table_html += f'<th style="padding: 8px; background-color: #f2f2f2;">{header}</th>\n'
            table_html += '</tr>\n</thead>\n'
            
            # 본문 처리
            if len(lines) > 2:
                table_html += '<tbody>\n'
                for line in lines[2:]:
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    table_html += '<tr>\n'
                    for cell in cells:
                        table_html += f'<td style="padding: 8px;">{cell}</td>\n'
                    table_html += '</tr>\n'
                table_html += '</tbody>\n'
            
            table_html += '</table>'
            return table_html
        
        # 테이블 패턴 찾기 (| 로 시작하는 연속된 라인)
        table_pattern = r'(\|.+\|\n)+(\|[\s\-:|]+\|\n)(\|.+\|\n)+'
        html = re.sub(table_pattern, lambda m: convert_table(m.group(0)), html, flags=re.MULTILINE)
        
        # 5. 이미지 변환
        html = re.sub(r'!\[([^\]]*)\]\(([^\)]*)\)', r'<img src="\2" alt="\1" style="max-width: 100%; height: auto;" />', html)
        
        # 6. 링크 변환 (이미지 변환 후에 해야 함)
        # file:// 링크는 제거하고 텍스트만 남김 (또는 검색 링크로 대체)
        def convert_link(match):
            text = match.group(1)
            url = match.group(2)
            if url.startswith('file://'):
                # 워드프레스 검색 링크로 변환
                if self.wp_url:
                    return f'<a href="{self.wp_url}/?s={text}">{text}</a>'
                return text
            return f'<a href="{url}">{text}</a>'

        html = re.sub(r'\[([^\]]*)\]\(([^\)]*)\)', convert_link, html)
        
        # 7. 헤더 변환
        html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # 8. 인라인 마크다운 변환 (순서 중요!)
        # 볼드 이탤릭 (***text*** or ___text___)
        html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
        html = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', html)
        
        # 볼드 (**text** or __text__)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
        
        # 이탤릭 (*text* or _text_) - 단어 경계 고려
        html = re.sub(r'\*([^\*]+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'\b_([^_]+?)_\b', r'<em>\1</em>', html)
        
        # 인라인 코드 (`code`)
        html = re.sub(r'`([^`]+?)`', r'<code>\1</code>', html)
        
        # 취소선 (~~text~~)
        html = re.sub(r'~~(.+?)~~', r'<del>\1</del>', html)
        
        # 9. 리스트 변환
        html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^\d+\. (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # 10. 인용문 변환
        html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
        
        # 11. 수평선 변환
        html = re.sub(r'^---$', r'<hr />', html, flags=re.MULTILINE)
        html = re.sub(r'^\*\*\*$', r'<hr />', html, flags=re.MULTILINE)
        
        # 12. 단락 변환
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            # 이미 HTML 태그로 시작하면 그대로
            if p.startswith('<'):
                html_paragraphs.append(p)
            else:
                # 줄바꿈을 <br>로 변환
                p = p.replace('\n', '<br>\n')
                html_paragraphs.append(f'<p>{p}</p>')
        
        html = '\n'.join(html_paragraphs)
        
        return html
    
    def post_to_wordpress(self, title, content, tags=None):
        """WordPress에 게시글 포스팅"""
        if not self.wp_url or not self.wp_username or not self.wp_app_password:
            self._log("WordPress 설정이 없어 포스팅을 건너뜁니다.")
            return False
        
        self._log("WordPress에 포스팅 중...")
        
        try:
            headers = self.get_wp_headers()
            
            # 카테고리 ID 가져오기
            category_id = self.get_or_create_category(self.wp_category)
            
            # 태그 ID 가져오기
            tag_ids = []
            if tags:
                for tag_name in tags:
                    tid = self.get_or_create_tag(tag_name)
                    if tid:
                        tag_ids.append(tid)
            
            # Markdown을 HTML로 변환
            html_content = self.markdown_to_html(content)
            
            # 게시글 데이터
            wp_post_data = {
                "title": title,
                "content": html_content,
                "status": "publish",
                "categories": [category_id] if category_id else [],
                "tags": tag_ids
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
