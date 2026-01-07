# 🔥 Google Trends 기반 자동 블로그 생성 시스템

Google Trends에서 실시간 인기 키워드를 추출하여 AI가 자동으로 SEO 최적화된 블로그 포스트를 생성하는 시스템입니다.

## ✨ 주요 기능

- 🔍 **실시간 트렌드 키워드 추출**: Google Trends에서 최신 인기 검색어 자동 수집
- 🤖 **AI 기반 콘텐츠 생성**: Google Gemini AI를 활용한 고품질 블로그 글 작성
- 📰 **관련 뉴스 자동 수집**: 키워드 관련 최신 뉴스 3개 자동 추가 (출처 표기 포함)
- 🖼️ **대표 이미지 자동 삽입**: Google 이미지 검색에서 관련 이미지 자동 다운로드
- 🔍 **SEO 최적화**: Meta tags, Open Graph, Twitter Card 자동 생성
- 📝 **Markdown 출력**: Jekyll, Hugo 등 정적 사이트 생성기 호환 마크다운 파일 생성
- 📊 **YAML Frontmatter**: 제목, 날짜, 카테고리, 태그 등 메타데이터 자동 생성
- 📱 **반응형 디자인**: 모바일/태블릿/데스크톱 완벽 대응
- ⏰ **자동 스케줄링**: 매일 정해진 시간에 자동 실행 (08:00, 12:00, 16:00, 20:00)
- 🔄 **중복 방지**: 이미 사용한 키워드는 자동으로 제외

## 📋 요구사항

- Python 3.10 이상
- Google Gemini API Key
- Chromium (Playwright가 자동 설치)

## 🚀 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/goodmirow-1/keyword_trend.git
cd keyword_trend
```

### 2. 가상환경 생성 (권장)

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. Playwright 브라우저 설치

```bash
python3 -m playwright install chromium
```

### 5. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 API 키를 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일 내용:

```env
# Gemini API Key (필수)
GEMINI_API_KEY=your_gemini_api_key_here

# WordPress 설정 (선택사항)
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=your_application_password
```

**Gemini API Key 발급 방법:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. 생성된 키를 `.env` 파일에 입력

## 💻 사용 방법

### 기본 실행

```bash
python3 trend_blog_system.py
```

실행하면:
1. 즉시 첫 번째 블로그 포스트 생성
2. 이후 매일 08:00, 12:00, 16:00, 20:00에 자동 실행
3. `Ctrl+C`로 중지 가능

### 생성된 파일 확인

```bash
ls blog_posts/
```

생성된 Markdown 파일을 텍스트 에디터로 확인:

```bash
cat blog_posts/20260107_165629_키워드.md
```

## 📁 프로젝트 구조

```
keyword_trend/
├── trend_blog_system.py    # 메인 시스템 코드
├── requirements.txt         # Python 패키지 목록
├── .env.example            # 환경 변수 예제
├── .gitignore              # Git 제외 파일 목록
├── README.md               # 프로젝트 설명서
├── blog_posts/             # 생성된 블로그 포스트 (gitignore)
│   ├── images/            # 다운로드된 이미지
│   └── *.md               # 생성된 Markdown 파일
├── used_keywords.json      # 사용된 키워드 기록 (gitignore)
└── system_log.txt          # 시스템 로그 (gitignore)
```

## 🎨 생성되는 블로그 구조

1. **YAML Frontmatter** (메타데이터)
2. **대표 이미지** (Google 이미지 검색 결과)
3. **본문 내용** (AI 생성 콘텐츠)
4. **관련 뉴스** (맨 아래)
   - 뉴스 제목 (하이퍼링크)
   - 출처 표기 (법적 필수)
   - 뉴스 이미지
   - 요약

## 🔧 설정 커스터마이징

### 스케줄 변경

`trend_blog_system.py` 파일의 `main()` 함수에서 스케줄 수정:

```python
# 매일 08:00, 12:00, 16:00, 20:00 실행
schedule.every().day.at("08:00").do(system.run_blog_creation)
schedule.every().day.at("12:00").do(system.run_blog_creation)
schedule.every().day.at("16:00").do(system.run_blog_creation)
schedule.every().day.at("20:00").do(system.run_blog_creation)
```

### AI 모델 변경

`__init__` 메서드에서 모델 변경:

```python
self.model = genai.GenerativeModel('gemini-pro')  # 또는 다른 모델
```

## 🌐 워드프레스 연동

생성된 HTML 파일을 워드프레스에 게시하는 방법:

### 방법 1: 수동 게시
1. 생성된 HTML 파일 열기
2. 내용 복사
3. 워드프레스 편집기에서 "코드 편집기" 모드로 전환
4. 붙여넣기

### 방법 2: REST API 자동 게시 (개발 예정)
`.env` 파일에 워드프레스 정보 입력 후 자동 게시

## 📊 로그 확인

```bash
tail -f system_log.txt
```

로그에서 확인 가능한 정보:
- 키워드 추출 상태
- 뉴스 수집 결과
- 이미지 다운로드 상태
- 블로그 생성 완료 여부

## ⚠️ 주의사항

1. **API 사용량**: Gemini API는 무료 티어에서 일일 요청 제한이 있습니다
2. **저작권**: 생성된 콘텐츠는 AI가 작성하지만, 뉴스 출처는 반드시 표기됩니다
3. **트렌드 API 안정성**: Google Trends API가 불안정할 경우 더미 데이터 사용

## 🐛 문제 해결

### Playwright 설치 오류
```bash
python3 -m playwright install chromium --force
```

### API 키 오류
- `.env` 파일이 올바른 위치에 있는지 확인
- API 키에 공백이 없는지 확인
- Gemini API가 활성화되어 있는지 확인

### 트렌드 추출 실패
- 인터넷 연결 확인
- 로그 파일에서 상세 오류 확인
- 더미 데이터로 폴백되어 계속 작동

## 📝 라이선스

MIT License

## 👨‍💻 개발자

goodmirow-1

## 🤝 기여

Pull Request는 언제나 환영합니다!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 문의

프로젝트 관련 문의사항이 있으시면 Issue를 등록해주세요.

---

⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
