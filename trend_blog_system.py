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
        self.config_file = 'system_config.json'
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
            
        # 블로그 페르소나 설정 (friendly, professional, analytical)
        self.persona = os.getenv('BLOG_PERSONA', 'friendly').lower()
        self._log(f"블로그 페르소나 설정: {self.persona}")
        
        # 텔레그램 알림 설정
        self.tg_token = os.getenv('TELEGRAM_TOKEN', '').strip()
        self.tg_chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
        if self.tg_token and self.tg_chat_id:
            self._log("텔레그램 알림 활성화됨")
            
        # 초기화: 디렉토리 및 파일 생성
        if not os.path.exists(self.blog_posts_dir):
            os.makedirs(self.blog_posts_dir)
            
        if not os.path.exists(self.used_keywords_file):
            self._save_used_keywords([])
            
        # 설정 로드
        self.config = self._load_config()

    def _log(self, message):
        """로그 메시지 기록"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
            
    def _send_telegram_notification(self, message):
        """텔레그램 알림 전송"""
        if not self.tg_token or not self.tg_chat_id:
            return
            
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.tg_token}/sendMessage"
            data = {
                "chat_id": self.tg_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
        except Exception as e:
            error_details = f"{e}"
            if 'response' in locals():
                error_details += f" (응답: {response.text})"
            self._log(f"텔레그램 알림 전송 실패: {error_details}")
    
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

    def _load_config(self):
        """시스템 설정 불러오기"""
        default_config = {
            "publication_times": ["08:00", "12:00", "16:00", "20:00"]
        }
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self._save_config(default_config)
                return default_config
        except Exception as e:
            self._log(f"설정 파일 로드 오류: {e}")
            return default_config

    def _save_config(self, config):
        """시스템 설정 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"설정 파일 저장 오류: {e}")
    
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
                    page.goto('https://trends.google.co.kr/trending?geo=KR&hours=24', timeout=30000)
                    
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
    
    def fetch_ai_image(self, keyword):
        """
        Gemini Imagen 3를 사용하여 AI 이미지 생성
        """
        try:
            self._log(f"'{keyword}' 관련 AI 이미지 생성 시도 중...")
            import os
            import requests
            from datetime import datetime
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                self._log("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. AI 이미지 생성을 건너뜁니다.")
                return None
                
            # Imagen 4.0 API 호출 (REST)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict?key={api_key}"
            
            # 보다 구체적인 이미지 생성을 위한 프롬프트 가공
            prompt = f"A professional, photorealistic blog header image for the topic: '{keyword}'. High quality, centered composition, no text."
            
            data = {
                "instances": [{"prompt": prompt}],
                "parameters": {"sampleCount": 1}
            }
            
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "predictions" in result and len(result["predictions"]) > 0:
                    # 응답은 보통 base64 인코딩된 이미지 데이터
                    b64_data = result["predictions"][0].get("bytesBase64Encoded")
                    if b64_data:
                        import base64
                        image_data = base64.b64decode(b64_data)
                        
                        # 로컬 저장
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"ai_featured_{timestamp}.png"
                        filepath = os.path.join(self.blog_posts_dir, 'images', filename)
                        
                        if not os.path.exists(os.path.join(self.blog_posts_dir, 'images')):
                            os.makedirs(os.path.join(self.blog_posts_dir, 'images'))
                            
                        with open(filepath, 'wb') as f:
                            f.write(image_data)
                            
                        self._log(f"AI 이미지 생성 및 저장 완료: {filepath}")
                        # 프론트엔드에서 참조 가능하도록 상대 경로 반환
                        return f"images/{filename}"
            
            # 실패 시 로그 남기고 None 반환 (자동으로 기존 구글 이미지 fetch로 넘어감)
            self._log(f"AI 이미지 생성 실패 (HTTP {response.status_code}): {response.text[:100]}")
            return None
        except Exception as e:
            self._log(f"AI 이미지 생성 중 오류: {e}")
            return None

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
        
    def fetch_youtube_video(self, keyword):
        """
        YouTube에서 관련 인기 영상의 임베딩 코드 가져오기
        """
        try:
            self._log(f"'{keyword}' 관련 YouTube 영상 검색 중...")
            import requests
            import re
            search_query = f"{keyword} 최신 뉴스"
            url = f"https://www.youtube.com/results?search_query={search_query}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 비디오 목록에서 실제 검색 결과 비디오 ID만 추출하기 위해 "videoRenderer" 패턴 사용
                # 이는 유튜브 검색 결과 페이지의 JSON 데이터 구조에서 비디오 항목을 식별하는 키워드입니다.
                results = re.findall(r"\"videoRenderer\":\{\"videoId\":\"([^\"]+)\"", response.text)
                if results:
                    # 첫 번째 검색 결과 사용
                    video_id = results[0]
                    self._log(f"유튜브 영상 발견: https://youtu.be/{video_id}")
                    return f'<iframe width="100%" height="450" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
                
                # 차선책: 기존의 단순 videoId 추출 (최신 데이터 구조 대응)
                video_ids = re.findall(r"\"videoId\":\"([^\"]+)\"", response.text)
                if video_ids:
                    video_id = video_ids[0]
                    self._log(f"유튜브 영상 발견(차선책): https://youtu.be/{video_id}")
                    return f'<iframe width="100%" height="450" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
            return None
        except Exception as e:
            self._log(f"YouTube 영상 검색 실패: {e}")
            return None

    def get_related_posts(self, current_keyword):
        """
        기존 게시물 중 현재 키워드와 연관성 높은 2개 선정
        """
        try:
            if not os.path.exists(self.blog_posts_dir):
                return []
                
            all_files = [f for f in os.listdir(self.blog_posts_dir) if f.endswith('.md')]
            if not all_files:
                return []
            
            # 현재 키워드 제외
            other_files = [f for f in all_files if current_keyword not in f]
            if not other_files:
                return []
            
            # 간단하게 최근 게시물 2개 반환
            other_files.sort(reverse=True)
            related = []
            for f in other_files[:2]:
                # 파일명에서 키워드 추출 (timestamp_keyword.md)
                parts = f.replace('.md', '').split('_')
                if len(parts) >= 3:
                    title = " ".join(parts[2:]) # 언더스코어가 더 있을 수 있으므로
                    related.append({'title': title, 'filename': f})
                else:
                    # 형식이 다르면 그냥 파일명 사용
                    related.append({'title': f.replace('.md', ''), 'filename': f})
            return related
        except Exception as e:
            self._log(f"관련 게시물 검색 실패: {e}")
            return []
            
    
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

    def _analyze_keyword_category(self, keyword):
        """
        키워드 카테고리 분석 (Gemini 사용) - 세분화된 14개 카테고리
        """
        try:
            prompt = f"""
            다음 키워드를 분석하여 아래 세부 카테고리 중 하나로 분류하고, 글의 핵심 포커스를 한 문장으로 요약해줘.
            
            [키워드] : {keyword}
            
            [세부 카테고리]
            1. SPORTS_MATCH (경기 일정, 결과, 중계 정보)
            2. SPORTS_GENERAL (선수 이적, 부상, 팀 이슈, 일반 스포츠 뉴스)
            3. STOCK (개별 주식 종목, 기업 실적, 공시)
            4. ECONOMY (거시 경제, 부동산, 정책, 환율, 금리)
            5. SOCIAL_ISSUE (사회적 논란, 쟁점, 찬반 토론)
            6. SOCIAL_INCIDENT (사건, 사고, 재해, 팩트 중심)
            7. POLITICS (정치, 선거, 정당, 법안)
            8. ENTERTAINMENT_NEWS (연예인 가십, 열애, 사건, 근황)
            9. ENTERTAINMENT_CONTENT (드라마, 영화, 웹툰, 방송 프로그램 리뷰/정보)
            10. TECH_DEVICE (스마트폰, 가전, 하드웨어 스펙/비교)
            11. TECH_TREND (IT 서비스, AI, 플랫폼, 소프트웨어 트렌드)
            12. HEALTH (건강 정보, 질병, 운동, 의학)
            13. LIVING_INFO (생활 꿀팁, 날씨, 여행, 요리, 쇼핑 정보)
            14. OTHER (그 외 분류하기 어려운 일반 정보)
            
            [응답 형식]
            Category: [카테고리명]
            Focus: [핵심 포커스]
            """
            
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            category = "OTHER"
            focus = "정보 전달 및 개요 설명"
            
            for line in result.split('\n'):
                if line.startswith('Category:'):
                    category = line.replace('Category:', '').strip().upper()
                elif line.startswith('Focus:'):
                    focus = line.replace('Focus:', '').strip()
            
            # 유효한 카테고리인지 확인
            valid_categories = [
                'SPORTS_MATCH', 'SPORTS_GENERAL', 
                'STOCK', 'ECONOMY', 
                'SOCIAL_ISSUE', 'SOCIAL_INCIDENT', 'POLITICS',
                'ENTERTAINMENT_NEWS', 'ENTERTAINMENT_CONTENT',
                'TECH_DEVICE', 'TECH_TREND',
                'HEALTH', 'LIVING_INFO', 'OTHER'
            ]
            
            # 매칭되는 것이 없으면 유사한 것 찾거나 OTHER
            if category not in valid_categories:
                # 공백이나 특수문자 제거 후 비교 등 유연한 처리 가능하나 일단 OTHER
                category = 'OTHER'
                
            self._log(f"키워드 분석 결과: {category} / {focus}")
            return category, focus
            
        except Exception as e:
            self._log(f"키워드 분석 실패: {e}")
            return "OTHER", "정보 전달"

    def _get_persona_instruction(self):
        """
        설정된 페르소나에 따른 글쓰기 지침 반환
        """
        if self.persona == 'professional':
            return """
            [Persona: Professional (전문가형)]
            - 말투: 신뢰감 있고 깔끔한 '하십시오체' 또는 단정한 '해요체'를 사용하십시오.
            - 어조: 객관적이고 권위 있는 정보를 전달하는 전문가의 목소리를 유지하십시오.
            - 특징: 불필요한 수식어를 줄이고, 정확한 용어와 논리적인 구조로 독자의 이해를 돕습니다.
            """
        elif self.persona == 'analytical':
            return """
            [Persona: Analytical (분석가형)]
            - 말투: 논리적이고 객관적인 어조를 사용하십시오. (~입니다, ~함)
            - 어조: 현상의 이면을 분석하고 데이터나 근거를 바탕으로 다각도의 시각을 제공하십시오.
            - 특징: 단순 정보 전달을 넘어 '왜' 이런 일이 일어났는지, 앞으로 어떤 영향을 미칠지에 집중합니다.
            """
        else:  # friendly (default)
            return """
            [Persona: Friendly (친근한 이웃형)]
            - 말투: 다정하고 친근한 '해요체'를 사용하세요. 가끔 이모지(😊, ✨ 등)를 적절히 섞어주세요.
            - 어조: 친구에게 이야기하듯 편안하면서도 유익한 정보를 전달하는 따뜻한 목소리입니다.
            - 특징: 독자의 공감을 이끌어내는 문구(예: "여러분도 궁금하셨죠?", "정말 놀랍지 않나요?")를 포함합니다.
            """

    def _get_category_prompt(self, keyword, category, news_items_text, news_summary):
        """
        세분화된 카테고리별 맞춤 프롬프트 생성 (페르소나 및 팩트체크 포함)
        """
        persona_instruction = self._get_persona_instruction()
        
        fact_check_instruction = """
        [Fact-Check 및 정보 통합 지침]
        - 제공된 여러 뉴스 항목({len(news_items_text)}개)을 면밀히 비교하여 공통된 핵심 사실을 추출하십시오.
        - 뉴스 간에 내용이 상충되는 경우, 가장 최신의 정보이거나 더 구체적인 보도를 우선시하되, 불확실한 부분은 '~라고 전해졌습니다'와 같은 신중한 표현을 사용하십시오.
        - 단순히 기사를 나열하지 말고, 전체적인 맥락을 파악하여 하나의 완성된 스토리로 재구성하십시오.
        """

        base_instructions = f"""
        이 글은 반드시 'front-matter + 본문'을 함께 생성해야 하며,
        front-matter의 성격은 본문 내용과 정확히 일치해야 한다.
        
        {persona_instruction}
        
        {fact_check_instruction}
        
        [Front-matter 작성 규칙]
        - title: '{keyword}' + (카테고리별 특성에 맞는 매력적인 제목)
        - categories: 반드시 [정보, 분석, 후기] 등 적절한 것 선택 (트렌드 사용 금지)
        - tags: ['{keyword}', 관련태그1, 관련태그2]
        - description: 글의 핵심 내용을 요약한 메타 설명
        
        [공통 작성 원칙]
        - 가독성을 위해 적절한 소헤더와 불렛 포인트 사용
        - '최신', '트렌드' 같은 단어 남발 금지
        - Markdown 형식 준수
        """

        # 1. 스포츠 매치 (경기 중심)
        if category == 'SPORTS_MATCH':
            return f"""
            '{keyword}'에 대한 스포츠 경기 프리뷰 또는 리뷰를 작성해줘.
            
            [상황 판단 (현재: {datetime.now().strftime('%Y-%m-%d')})]
            뉴스 데이터를 바탕으로 경기가 '예정'인지 '종료'인지 파악하여 작성.
            
            A. 예정된 경기:
               - 일정(한국 시간), 장소
               - **중계 채널 및 시청 방법** (가장 중요하게 다룸)
               - 양팀 전력/상대 전적/관전 포인트
               
            B. 종료된 경기:
               - **스코어 및 경기 결과**
               - 주요 하이라이트 장면 설명
               - 승패 요인 분석 및 선수 활약상
               - 다음 일정
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """
            
        # 2. 스포츠 일반 (선수, 팀)
        elif category == 'SPORTS_GENERAL':
            return f"""
            '{keyword}'에 대한 스포츠 이슈/선수 정보를 작성해줘.
            
            [필수 포함 내용]
            - 이슈의 핵심 내용 (이적, 부상, 기록 달성 등)
            - 해당 선수의 최근 활약상 또는 팀 분위기
            - 팬들의 반응 및 전문가 의견
            - 향후 예상되는 시나리오
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """
            
        # 3. 주식 (개별 종목)
        elif category == 'STOCK':
            return f"""
            '{keyword}' 주가 흐름 및 기업 이슈 분석 글을 작성해줘.
            
            [필수 포함 내용]
            - 현재 주가 동향 및 최근 흐름
            - **상승/하락의 구체적 원인** (호재/악재, 실적, 공시)
            - 증권가 목표가 리포트 및 투자 의견 요약
            - 향후 주가 전망 및 체크포인트
            
            * 주의: "무조건 사라/팔라"는 식의 조언 금지. 객관적 정보 위주.
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """
            
        # 4. 경제 (거시/부동산/정책)
        elif category == 'ECONOMY':
            return f"""
            '{keyword}' 관련 경제/정책 이슈 해설 글을 작성해줘.
            
            [필수 포함 내용]
            - 이슈 개요 및 배경 설명 (초보자도 이해하기 쉽게)
            - 이것이 우리 삶/경제에 미치는 영향
            - 찬반 의견이나 다양한 시각
            - 요약 및 시사점
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """
            
        # 5. 사회 이슈 (논란/쟁점)
        elif category == 'SOCIAL_ISSUE':
            return f"""
            '{keyword}' 관련 사회적 이슈/논란 정리 글을 작성해줘.
            
            [필수 포함 내용]
            - 논란의 발단 및 핵심 쟁점
            - 각계의 입장 (찬성 vs 반대, 혹은 A측 vs B측)
            - 대중의 반응 (커뮤니티, 댓글 분위기 등)
            - 시사하는 바 및 향후 전개 예상
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 6. 사회 사건 (팩트 중심)
        elif category == 'SOCIAL_INCIDENT':
            return f"""
            '{keyword}' 사건/사고 종합 정리 글을 작성해줘.
            
            [필수 포함 내용]
            - 사건 발생 일시, 장소, 경위 (육하원칙)
            - 현재까지의 수사/진행 상황
            - 피해 규모 또는 사회적 파장
            - 관련 주의사항 (유사 피해 방지 등)
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 7. 정치
        elif category == 'POLITICS':
            return f"""
            '{keyword}' 관련 정치 이슈 브리핑을 작성해줘.
            
            [필수 포함 내용]
            - 이슈의 핵심 내용 및 팩트
            - 여/야 혹은 관련 정치인들의 발언 및 입장 차이
            - 이번 사안이 갖는 정치적 의미
            - 향후 일정 및 예상 시나리오
            
            * 최대한 중립적이고 객관적인 톤 유지.
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 8. 연예 뉴스 (가십/근황)
        elif category == 'ENTERTAINMENT_NEWS':
            return f"""
            '{keyword}' 관련 연예계 소식을 정리해줘.
            
            [필수 포함 내용]
            - 무슨 일이 있었는지 상세 내용 (기사 내용 기반)
            - 소속사 공식 입장 혹은 본인 해명
            - 네티즌/팬들의 반응
            - 과거 유사 사례 혹은 배경 지식
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 9. 연예 콘텐츠 (드라마/영화 리뷰)
        elif category == 'ENTERTAINMENT_CONTENT':
            return f"""
            '{keyword}' (드라마/영화/방송) 프리뷰 또는 리뷰를 작성해줘.
            
            [필수 포함 내용]
            - 기본 정보 (출연진, 줄거리, 방영시간/개봉일)
            - 관전 포인트 혹은 감상 포인트 (재미 요소)
            - 시청률/관객수 추이 및 반응
            - (종영/결말인 경우) 결말 요약 및 해석
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 10. 테크 기기 (하드웨어)
        elif category == 'TECH_DEVICE':
            return f"""
            '{keyword}' 제품에 대한 스펙/정보 리뷰를 작성해줘.
            
            [필수 포함 내용]
            - 주요 스펙 및 디자인 특징
            - 전작 대비 달라진 점 (Upgrades)
            - 장점 및 단점 (비판적 시각 포함)
            - 출시일, 가격, 구매 정보
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 11. 테크 트렌드 (IT/AI)
        elif category == 'TECH_TREND':
            return f"""
            '{keyword}' 관련 IT/테크 트렌드 분석 글을 작성해줘.
            
            [필수 포함 내용]
            - 기술/서비스의 개념 정의
            - 최근 화제가 된 이유 (새로운 기능, 업데이트 등)
            - 업계 동향 및 경쟁사 상황
            - 향후 전망 및 사용자에게 미치는 영향
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 12. 건강
        elif category == 'HEALTH':
            return f"""
            '{keyword}' 관련 건강/의학 정보를 작성해줘.
            
            [필수 포함 내용]
            - 증상 및 원인 설명
            - 치료 방법 및 예방 수칙
            - 좋은 음식/나쁜 음식 혹은 생활 습관
            - 전문가 조언 (뉴스 기반)
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """

        # 13. 생활 정보 (리빙)
        elif category == 'LIVING_INFO':
            return f"""
            '{keyword}' 관련 생활 꿀팁/정보를 작성해줘.
            
            [필수 포함 내용]
            - 이게 왜 필요한지/무엇인지 (관심 유발)
            - 구체적인 정보 (날씨라면 예보, 축제라면 일정/장소, 요리라면 레시피)
            - 이용 꿀팁 및 주의사항
            - 요약
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """
            
        # 14. 기타 (OTHER)
        else:
            return f"""
            '{keyword}'에 대해 정보를 찾는 사용자를 위한 친절한 설명 글을 작성해줘.
            
            [작성 포인트]
            - '{keyword}'의 정의 및 핵심 개요
            - 최근 이슈가 된 이유 (있다면)
            - 사람들이 궁금해할 만한 3가지 포인트
            - 결론 및 요약
            
            [참고 뉴스]
            {news_summary}
            
            {base_instructions}
            """
    
    def generate_blog_content(self, keyword):
        """
        선택된 키워드로 카테고리별 맞춤 블로그 콘텐츠 생성
        """
        if not self.client_ready:
            return f"<h1>{keyword}에 대한 블로그 포스트</h1><p>(API 키 설정 필요)</p>"
        
        try:
            self._log(f"'{keyword}' 키워드로 블로그 콘텐츠 생성 시작...")
            
            # 1. Google 뉴스 가져오기
            news_items = self.fetch_google_news(keyword, max_news=5)
            
            # 뉴스 요약 텍스트 생성 (프롬프트 참고용)
            news_summary = ""
            if news_items:
                for idx, item in enumerate(news_items):
                    news_summary += f"{idx+1}. {item['title']} ({item.get('source', '')}): {item['summary']}\n"
            else:
                news_summary = "관련된 구체적인 뉴스 기사가 없습니다. 일반적인 정보에 기반해 작성해주세요."

            # 2. 키워드 카테고리 분석
            category, category_focus = self._analyze_keyword_category(keyword)
            
            # 3. 이미지 가져오기 (AI 우선, 실패 시 Google)
            featured_image = self.fetch_ai_image(keyword)
            if not featured_image:
                self._log("AI 이미지 생성 실패 또는 권한 없음. Google 이미지를 사용합니다.")
                featured_image = self.fetch_google_image(keyword)
            
            # 4. 맞춤형 프롬프트 생성
            prompt = self._get_category_prompt(keyword, category, news_items, news_summary)
            
            self._log(f"Gemini 콘텐츠 생성 중... (Category: {category})")
            
            # 5. AI 생성
            response = self.model.generate_content(prompt)
            main_content = response.text
            
            # 6. 추가 콘텐츠 fetching
            youtube_embed = self.fetch_youtube_video(keyword)
            related_posts = self.get_related_posts(keyword)
            
            # 7. Markdown 콘텐츠 조립
            markdown_content = self._build_markdown_content(
                keyword, main_content, news_items, featured_image, 
                youtube_embed=youtube_embed, related_posts=related_posts
            )
            
            self._log("블로그 콘텐츠 생성 완료")
            return markdown_content
        
        except Exception as e:
            self._log(f"콘텐츠 생성 오류: {e}")
            import traceback
            self._log(traceback.format_exc())
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
    
    def _build_markdown_content(self, keyword, main_content, news_items, featured_image, youtube_embed=None, related_posts=None):
        """
        Markdown 콘텐츠 생성 (Frontmatter 포함)
        """
        # 대표 이미지 처리
        local_featured_image = None
        if featured_image:
            if featured_image.startswith('http'):
                local_featured_image = self.download_image(featured_image, keyword, 'featured')
            else:
                # 이미 로컬 경로인 경우 (AI 생성 등)
                local_featured_image = featured_image
        
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
        
        # YouTube 섹션 추가
        if youtube_embed:
            markdown += "## 🎬 관련 영상\n\n"
            markdown += f"{youtube_embed}\n\n"
            
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
                
        # 내부 링크 섹션 추가
        if related_posts:
            markdown += "## 🔗 함께 보면 좋은 글\n\n"
            for post in related_posts:
                markdown += f"* [{post['title']}](file://{post['filename']})\n"
            markdown += "\n"
            
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
            
            # 사용된 키워드 목록에 추가 (중복 방지)
            used_keywords = self._load_used_keywords()
            if keyword not in used_keywords:
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
            self._send_telegram_notification(f"✅ *블로그 생성 완료*\n\n*키워드*: {selected_keyword}\n*파일*: `{os.path.basename(filepath)}`")
        else:
            self._log("블로그 저장에 실패했습니다.")
            self._send_telegram_notification(f"❌ *블로그 생성 실패*\n\n*키워드*: {selected_keyword}\n*원인*: 파일 저장 실패")
        
        self._log("블로그 작성 프로세스 종료")
        self._log("=" * 50)

def main():
    """
    메인 실행 함수 - 스케줄링 설정
    """
    system = TrendBlogSystem()
    
    # 설정에서 발행 시간 가져오기
    publication_times = system.config.get('publication_times', ["08:00", "12:00", "16:00", "20:00"])
    
    # 스케줄 설정
    for t in publication_times:
        try:
            schedule.every().day.at(t).do(system.run_blog_creation)
        except Exception as e:
            print(f"스케줄 설정 오류 ({t}): {e}")
    
    print("블로그 자동 작성 시스템 시작")
    print(f"스케줄: {', '.join(publication_times)}")
    print("중지하려면 Ctrl+C를 누르세요.")
    
    # 즉시 한 번 실행 (테스트용)
    # system.run_blog_creation()
    
    # 스케줄 루프 실행
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

if __name__ == "__main__":
    main()