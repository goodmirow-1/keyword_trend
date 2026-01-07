import json
import os
from datetime import datetime
import schedule
import time
from pytrends.request import TrendReq
import google.generativeai as genai

class TrendBlogSystem:
    def __init__(self):
        """
        구글 트렌드 기반 블로그 자동 작성 시스템 초기화
        """
        self.pytrends = TrendReq(hl='ko', tz=540)  # 한국어, 한국 시간대
        self.used_keywords_file = 'used_keywords.json'
        self.blog_posts_dir = 'blog_posts'
        self.log_file = 'system_log.txt'
        
        # Gemini API 설정 (환경변수에서 API 키 가져오기)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            # 혹시 GOOGLE_API_KEY로 설정했을 수도 있으니 확인
            api_key = os.getenv('GOOGLE_API_KEY')

        if api_key:
            genai.configure(api_key=api_key)
            # gemini-1.5-flash가 안될 경우 gemini-pro 사용
            self.model = genai.GenerativeModel('gemini-flash-latest')
            self.client_ready = True
        else:
            self.client_ready = False
            print("경고: GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
            
        # 초기화: 디렉토리 및 파일 생성
        if not os.path.exists(self.blog_posts_dir):
            os.makedirs(self.blog_posts_dir)
            
        if not os.path.exists(self.used_keywords_file):
            self._save_used_keywords([])

    def _log(self, message):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def _load_used_keywords(self):
        """이미 사용된 키워드 목록 불러오기"""
        try:
            with open(self.used_keywords_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self._log(f"키워드 파일 로드 오류: {e}")
            return []
    
    def _save_used_keywords(self, keywords):
        """사용된 키워드 목록 저장"""
        try:
            with open(self.used_keywords_file, 'w', encoding='utf-8') as f:
                json.dump(keywords, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"키워드 파일 저장 오류: {e}")
    
    def get_trending_keywords(self, region='south_korea'):
        """
        구글 트렌드에서 실시간 인기 검색어 가져오기 (Playwright 사용)
        """
        try:
            self._log("구글 트렌드에서 인기 검색어 가져오는 중...")
            
            keywords = []
            
            # 1. Playwright로 실제 Google Trends 페이지 스크래핑
            try:
                self._log("Playwright import 시도 중...")
                from playwright.sync_api import sync_playwright
                
                self._log("Playwright로 Google Trends 페이지 접근 중...")
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    
                    # Google Trends 페이지 접속
                    page.goto('https://trends.google.co.kr/trending?geo=KR&hours=4', timeout=30000)
                    
                    # 페이지 로딩 대기
                    page.wait_for_selector('tr[role="row"]', timeout=10000)
                    
                    # JavaScript로 키워드 추출
                    keywords = page.evaluate('''() => {
                        const rows = document.querySelectorAll('tr[role="row"]');
                        const keywords = [];
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            if (cells.length >= 2) {
                                const keywordDiv = cells[1].querySelector('div');
                                if (keywordDiv) {
                                    keywords.push(keywordDiv.innerText.trim());
                                }
                            }
                        });
                        return keywords;
                    }''')
                    
                    browser.close()
                    
                    if keywords:
                        self._log(f"Playwright로 {len(keywords)}개 키워드 획득")
                        return keywords
                        
            except Exception as playwright_error:
                import traceback
                self._log(f"Playwright 트렌드 가져오기 실패: {playwright_error}")
                self._log(f"상세 에러: {traceback.format_exc()}")

            # 2. RSS 피드 시도 (Fallback)
            try:
                import requests
                import xml.etree.ElementTree as ET
                
                rss_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR"
                response = requests.get(rss_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    for item in root.findall('.//item'):
                        title = item.find('title')
                        if title is not None:
                            keywords.append(title.text)
                    self._log(f"RSS 피드에서 {len(keywords)}개 키워드 획득")
                else:
                    self._log(f"RSS 요청 실패: Status Code {response.status_code}")
            except Exception as rss_error:
                self._log(f"RSS 트렌드 가져오기 실패: {rss_error}")

            if keywords:
                return keywords

            # 3. Pytrends 시도 (Fallback)
            try:
                trending_searches = self.pytrends.trending_searches(pn='south_korea')
                keywords = trending_searches[0].tolist()
                self._log(f"Pytrends에서 {len(keywords)}개 키워드 획득")
            except Exception as py_error:
                self._log(f"Pytrends 실패: {py_error}")

            if keywords:
                return keywords
            
            # 4. 모든 방법 실패 시 테스트용 더미 데이터 반환
            self._log("모든 트렌드 소스 가져오기 실패. 테스트용 더미 데이터를 사용합니다.")
            return ['생성형 AI', '파이썬 자동화', '주말 날씨', '최신 영화 순위', '맛집 추천']
        
        except Exception as e:
            self._log(f"트렌드 가져오기 치명적 오류: {e}")
            return ['테스트 키워드']
    
    def fetch_google_news(self, keyword, max_news=3):
        """
        Google 뉴스에서 관련 뉴스 가져오기
        
        Returns:
            list: [{'title': str, 'url': str, 'image': str, 'summary': str, 'source': str}, ...]
        """
        try:
            self._log(f"'{keyword}' 관련 Google 뉴스 검색 중...")
            
            from playwright.sync_api import sync_playwright
            import urllib.parse
            
            news_list = []
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Google 뉴스 검색
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&tbm=nws&hl=ko"
                page.goto(search_url, timeout=30000)
                page.wait_for_timeout(2000)
                
                # 뉴스 항목 추출
                news_data = page.evaluate('''() => {
                    const newsItems = [];
                    const articles = document.querySelectorAll('div.SoaBEf, div.WlydOe');
                    
                    for (let i = 0; i < Math.min(articles.length, 3); i++) {
                        const article = articles[i];
                        
                        // 제목
                        const titleElem = article.querySelector('div[role="heading"]');
                        const title = titleElem ? titleElem.innerText : '';
                        
                        // URL
                        const linkElem = article.querySelector('a');
                        const url = linkElem ? linkElem.href : '';
                        
                        // 이미지
                        const imgElem = article.querySelector('img');
                        const image = imgElem ? imgElem.src : '';
                        
                        // 요약
                        const summaryElem = article.querySelector('div.GI74Re');
                        const summary = summaryElem ? summaryElem.innerText : '';
                        
                        // 출처 - 다양한 셀렉터 시도
                        let source = '';
                        
                        // 방법 1: CEMjEf 클래스
                        let sourceElem = article.querySelector('div.CEMjEf span');
                        if (sourceElem) {
                            source = sourceElem.innerText;
                        }
                        
                        // 방법 2: MgUUmf 클래스 (뉴스 출처)
                        if (!source) {
                            sourceElem = article.querySelector('.MgUUmf.NUnG9d span');
                            if (sourceElem) source = sourceElem.innerText;
                        }
                        
                        // 방법 3: URL에서 도메인 추출
                        if (!source && url) {
                            try {
                                const urlObj = new URL(url);
                                source = urlObj.hostname.replace('www.', '');
                            } catch (e) {
                                source = '';
                            }
                        }
                        
                        if (title && url) {
                            newsItems.push({
                                title: title,
                                url: url,
                                image: image,
                                summary: summary || title,
                                source: source || 'Unknown Source'
                            });
                        }
                    }
                    
                    return newsItems;
                }''')
                
                browser.close()
                
                if news_data:
                    self._log(f"{len(news_data)}개의 뉴스 항목 발견")
                    return news_data[:max_news]
                
        except Exception as e:
            self._log(f"Google 뉴스 가져오기 실패: {e}")
        
        return []
    
    def fetch_google_image(self, keyword):
        """
        Google 이미지 검색에서 첫 번째 이미지 URL 가져오기
        
        Returns:
            str: 이미지 URL 또는 None
        """
        try:
            self._log(f"'{keyword}' 관련 Google 이미지 검색 중...")
            
            from playwright.sync_api import sync_playwright
            import urllib.parse
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Google 이미지 검색
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(keyword)}&tbm=isch&hl=ko"
                page.goto(search_url, timeout=30000)
                page.wait_for_timeout(2000)
                
                # 첫 번째 이미지 URL 추출
                image_url = page.evaluate('''() => {
                    const img = document.querySelector('img[data-src], img.rg_i');
                    if (img) {
                        return img.src || img.getAttribute('data-src');
                    }
                    return null;
                }''')
                
                browser.close()
                
                if image_url and image_url.startswith('http'):
                    self._log(f"대표 이미지 발견: {image_url[:50]}...")
                    return image_url
                
        except Exception as e:
            self._log(f"Google 이미지 가져오기 실패: {e}")
        
        return None
    
    def select_keyword(self, keywords):
        """
        사용되지 않은 첫 번째 키워드 선택
        
        Args:
            keywords: 키워드 리스트
        
        Returns:
            str: 선택된 키워드 또는 None
        """
        used_keywords = self._load_used_keywords()
        
        for keyword in keywords:
            if keyword not in used_keywords:
                self._log(f"선택된 키워드: {keyword}")
                return keyword
        
        self._log("사용 가능한 새로운 키워드가 없습니다.")
        return None
    
    def generate_blog_content(self, keyword):
        """
        선택된 키워드로 SEO 최적화된 블로그 콘텐츠 생성
        
        Args:
            keyword: 블로그 주제 키워드
        
        Returns:
            str: 생성된 블로그 콘텐츠 (HTML 형식)
        """
        if not self.client_ready:
            return f"<h1>{keyword}에 대한 블로그 포스트</h1>\n\n<p>(API 키가 설정되지 않아 실제 콘텐츠를 생성할 수 없습니다)</p>"
        
        try:
            self._log(f"'{keyword}' 키워드로 블로그 콘텐츠 생성 중...")
            
            # 1. Google 뉴스 가져오기
            news_items = self.fetch_google_news(keyword, max_news=3)
            
            # 2. Google 이미지 가져오기
            featured_image = self.fetch_google_image(keyword)
            
            # 3. AI로 본문 생성
            prompt = f"""
'{keyword}'에 대해 정보 탐색을 하는 사용자는
뉴스나 트렌드 요약이 아니라,
판단 기준과 구조를 이해하기 위한 개요 정보를 원한다.

이 글은 반드시 'front-matter + 본문'을 함께 생성해야 하며,
front-matter의 성격은 본문 내용과 정확히 일치해야 한다.

[Front-matter 작성 규칙]
- title: '{keyword}' + 판단/구조/기준/분석 중 하나를 포함한 정보형 제목
- categories: 반드시 [정보, 분석] 중에서만 선택 (트렌드 사용 금지)
- tags: ['{keyword}', 판단기준, 구조분석] 형태로 구성
- description: '{keyword}'에 대해 판단 기준과 한계를 정리한 정보성 분석 글
- '최신', '트렌드', '뉴스' 단어 사용 금지

[글의 목적]
- '{keyword}'를 처음 접하는 사람이
  이 개념이나 대상을 어떻게 바라봐야 할지
  판단 기준을 제공하는 정보성 콘텐츠 작성

[작성 원칙]
- 홍보, 마케팅, 뉴스 요약처럼 보이지 않게 작성
- 개인 경험, 시점 특정(최근, 요즘 등) 표현 사용 금지
- 일반적인 판단 기준 → 특징 → 한계 구조 유지

[필수 구성]
1. 서론: 사람들이 '{keyword}'를 검색하는 이유 요약
2. 본문 1: 이 주제를 판단할 때 자주 사용되는 기준 2~3가지
3. 본문 2: 해당 기준에서 본 '{keyword}'의 특징
4. 본문 3: 상황이나 조건에 따라 달라질 수 있는 한계나 주의점
5. 결론: 어떤 경우에 참고하면 적합한 정보인지 명확히 정리

[결론 필수 문장]
- "이 정보는 '{keyword}'를 처음 접하거나,
   개요 수준에서 판단 기준이 필요한 경우에 참고하기 적합하다."

[형식]
- Markdown
- front-matter는 YAML 형식으로 본문 최상단에 작성
- 전체 분량 900~1200자

위 기준을 어기지 말고 front-matter와 본문을 함께 작성하라.
"""

            
            response = self.model.generate_content(prompt)
            main_content = response.text
            
            # 4. Markdown 콘텐츠 생성 (Frontmatter 포함)
            markdown_content = self._build_markdown_content(keyword, main_content, news_items, featured_image)
            
            self._log("블로그 콘텐츠 생성 완료")
            return markdown_content
        
        except Exception as e:
            self._log(f"콘텐츠 생성 오류: {e}")
            return None
    
    def download_image(self, image_url, keyword, index=0):
        """
        이미지 다운로드 및 로컬 저장
        
        Returns:
            str: 로컬 이미지 경로 또는 원본 URL
        """
        try:
            import requests
            import os
            from urllib.parse import urlparse
            
            # images 디렉토리 생성
            images_dir = os.path.join(self.blog_posts_dir, 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            
            # 파일명 생성
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ext = '.jpg'  # 기본 확장자
            filename = f"{timestamp}_{keyword}_{index}{ext}"
            filepath = os.path.join(images_dir, filename)
            
            # 이미지 다운로드
            response = requests.get(image_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # 상대 경로 반환
                relative_path = f"images/{filename}"
                self._log(f"이미지 다운로드 완료: {relative_path}")
                return relative_path
            
        except Exception as e:
            self._log(f"이미지 다운로드 실패: {e}")
        
        return image_url  # 실패 시 원본 URL 반환
    
    def _build_markdown_content(self, keyword, main_content, news_items, featured_image):
        """
        Markdown 콘텐츠 생성 (Frontmatter 포함)
        """
        # 대표 이미지 다운로드
        local_featured_image = None
        if featured_image:
            local_featured_image = self.download_image(featured_image, keyword, 'featured')
        
        # 날짜 생성
        today = datetime.now().strftime('%Y-%m-%d')
        
        # AI가 생성한 본문에서 Frontmatter 처리 및 대표 이미지 삽입
        markdown = ""
        
        # Frontmatter 분리 (---로 시작하고 ---로 끝나는 부분 찾기)
        if main_content.strip().startswith('---'):
            parts = main_content.split('---', 2)
            if len(parts) >= 3:
                # parts[0]은 빈 문자열, parts[1]은 Frontmatter 내용, parts[2]는 본문
                frontmatter = f"---{parts[1]}---\n\n"
                body = parts[2].strip()
                
                markdown += frontmatter
                
                # 대표 이미지 추가 (Frontmatter 직후)
                if local_featured_image:
                    markdown += f"![{keyword}]({local_featured_image})\n\n"
                
                markdown += f"{body}\n\n"
            else:
                # Frontmatter 형식이 이상하면 그냥 합치기
                if local_featured_image:
                    markdown += f"![{keyword}]({local_featured_image})\n\n"
                markdown += f"{main_content}\n\n"
        else:
            # Frontmatter가 없는 경우 (만약을 대비해)
            if local_featured_image:
                markdown += f"![{keyword}]({local_featured_image})\n\n"
            markdown += f"{main_content}\n\n"
        
        # 뉴스 섹션 추가
        if news_items:
            markdown += "## 📰 관련 뉴스\n\n"
            for idx, news in enumerate(news_items):
                # 뉴스 이미지 다운로드
                news_image = news.get('image', '')
                if news_image and news_image.startswith('http'):
                    news_image = self.download_image(news_image, keyword, f'news_{idx}')
                
                markdown += f"### [{news['title']}]({news['url']})\n"
                markdown += f"* **출처**: {news.get('source', 'Unknown Source')}\n"
                if news_image:
                    markdown += f"![뉴스 이미지]({news_image})\n"
                markdown += f"> {news['summary'][:150]}...\n\n"
                
        return markdown
        
        # 전체 HTML 문서
        html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{keyword}에 대한 최신 정보와 뉴스를 확인하세요. 트렌드 분석과 상세 정보를 제공합니다.">
    <meta name="keywords" content="{keyword}, 트렌드, 뉴스, 정보">
    <meta name="author" content="Trend Blog System">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="article">
    <meta property="og:title" content="{keyword} - 최신 트렌드 분석">
    <meta property="og:description" content="{keyword}에 대한 최신 정보와 뉴스">
    {f'<meta property="og:image" content="{featured_image}">' if featured_image else ''}
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{keyword} - 최신 트렌드 분석">
    <meta name="twitter:description" content="{keyword}에 대한 최신 정보와 뉴스">
    {f'<meta name="twitter:image" content="{featured_image}">' if featured_image else ''}
    
    <title>{keyword} - 최신 트렌드 분석</title>
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .featured-image {{
            width: 100%;
            max-height: 400px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        h1 {{
            color: #1a1a1a;
            font-size: 2.5em;
            margin-bottom: 20px;
            line-height: 1.2;
        }}
        
        h2 {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        
        h3 {{
            color: #34495e;
            font-size: 1.3em;
            margin-top: 20px;
        }}
        
        p {{
            margin-bottom: 15px;
            font-size: 1.1em;
        }}
        
        .news-section {{
            margin: 40px 0;
            padding: 30px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }}
        
        .news-cards {{
            display: grid;
            gap: 20px;
            margin-top: 20px;
        }}
        
        .news-card {{
            display: flex;
            gap: 15px;
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .news-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .news-image {{
            width: 120px;
            height: 120px;
            object-fit: cover;
            border-radius: 4px;
            flex-shrink: 0;
        }}
        
        .news-content {{
            flex: 1;
        }}
        
        .news-content h3 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }}
        
        .news-content h3 a {{
            color: #2c3e50;
            text-decoration: none;
        }}
        
        .news-content h3 a:hover {{
            color: #3498db;
            text-decoration: underline;
        }}
        
        .news-summary {{
            color: #666;
            font-size: 0.95em;
            margin: 0;
        }}
        
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        
        em {{
            color: #7f8c8d;
            font-style: italic;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            .news-card {{
                flex-direction: column;
            }}
            
            .news-image {{
                width: 100%;
                height: 200px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {featured_image_html}
        {news_cards_html}
        {main_content}
    </div>
</body>
</html>'''
        
        return html
    
    def save_blog_post(self, keyword, content):
        """
        생성된 블로그 포스트 저장
        
        Args:
            keyword: 키워드
            content: 블로그 콘텐츠 (HTML)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{keyword}.md"
            filepath = os.path.join(self.blog_posts_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._log(f"블로그 포스트 저장 완료: {filepath}")
            
            # 사용된 키워드 목록에 추가
            used_keywords = self._load_used_keywords()
            used_keywords.append(keyword)
            self._save_used_keywords(used_keywords)
            
            return filepath
        
        except Exception as e:
            self._log(f"블로그 포스트 저장 오류: {e}")
            return None
    
    def run_blog_creation(self):
        """
        전체 블로그 작성 프로세스 실행
        """
        self._log("=" * 50)
        self._log("블로그 작성 프로세스 시작")
        
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
        
        # 3. 블로그 콘텐츠 생성
        content = self.generate_blog_content(selected_keyword)
        
        if not content:
            self._log("콘텐츠 생성에 실패했습니다.")
            return
        
        # 4. 블로그 포스트 저장
        filepath = self.save_blog_post(selected_keyword, content)
        
        if filepath:
            self._log(f"블로그 작성 완료: {selected_keyword}")
        else:
            self._log("블로그 저장에 실패했습니다.")
        
        self._log("블로그 작성 프로세스 종료")
        self._log("=" * 50)

def main():
    """
    메인 실행 함수 - 스케줄링 설정
    """
    system = TrendBlogSystem()
    
    # 스케줄 설정: 오전 8시부터 4시간 간격
    schedule.every().day.at("08:00").do(system.run_blog_creation)
    schedule.every().day.at("12:00").do(system.run_blog_creation)
    schedule.every().day.at("16:00").do(system.run_blog_creation)
    schedule.every().day.at("20:00").do(system.run_blog_creation)
    
    print("블로그 자동 작성 시스템 시작")
    print("스케줄: 08:00, 12:00, 16:00, 20:00")
    print("중지하려면 Ctrl+C를 누르세요.")
    
    # 즉시 한 번 실행 (테스트용)
    system.run_blog_creation()
    
    # 스케줄 루프 실행
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

if __name__ == "__main__":
    main()