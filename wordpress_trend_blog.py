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
        """Markdown을 HTML로 변환 (간단한 변환)"""
        # Frontmatter 제거
        if markdown_content.strip().startswith('---'):
            parts = markdown_content.split('---', 2)
            if len(parts) >= 3:
                markdown_content = parts[2].strip()
        
        # 간단한 Markdown -> HTML 변환
        html = markdown_content
        
        # 이미지 변환
        html = re.sub(r'!\[([^\]]*)\]\(([^\)]*)\)', r'<img src="\2" alt="\1" style="max-width: 100%; height: auto;" />', html)
        
        # 링크 변환
        html = re.sub(r'\[([^\]]*)\]\(([^\)]*)\)', r'<a href="\2">\1</a>', html)
        
        # 헤더 변환
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # 리스트 변환 (간단하게)
        html = re.sub(r'^\* (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # 인용문 변환
        html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
        
        # 단락 변환
        paragraphs = html.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('<'):
                html_paragraphs.append(f'<p>{p}</p>')
            else:
                html_paragraphs.append(p)
        
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
            return True
            
        except Exception as e:
            self._log(f"WordPress 포스팅 오류: {e}")
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
