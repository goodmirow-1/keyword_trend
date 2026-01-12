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
- ⏰ **커스텀 스케줄링**: 대시보드에서 여러 개의 발행 시간을 자유롭게 설정 가능 (NEW!)
- 🔄 **중복 방지**: 이미 사용한 키워드는 자동으로 제외
- 🏷️ **카테고리 세분화 분류**: 키워드 특성에 따른 14개 세부 카테고리 자동 분류 및 맞춤형 프롬프트 적용
- 🌐 **WordPress 자동 포스팅**: WordPress REST API를 통한 자동 게시 및 "이슈트래킹" 카테고리 통합
- 🎭 **블로그 페르소나 설정**: `friendly`, `professional`, `analytical` 등 원하는 말투 설정 가능 (NEW!)
- ✅ **팩트 체크 및 정보 통합**: 여러 뉴스 소스를 교차 검증하여 신뢰도 높은 콘텐츠 생성 (NEW!)
- 🖼️ **Gemini AI 이미지 생성**: Gemini Imagen 4.0 모델을 사용한 고유 썸네일 자동 생성 (NEW!)
- 🎬 **YouTube 영상 자동 임베딩**: 키워드 관련 최신 인기 영상을 본문에 자동으로 삽입 (NEW!)
- 🔗 **스마트 내부 링크 시스템**: 과거에 작성된 관련 포스트를 자동으로 추천하여 내부 순환 유도 (NEW!)

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

# 블로그 페르소나 설정 (선택사항)
# friendly (기본), professional, analytical 중 선택
BLOG_PERSONA=friendly
```

**Gemini API Key 발급 방법:**
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. "Create API Key" 클릭
3. 생성된 키를 `.env` 파일에 입력

## 💻 사용 방법

### 기본 실행 (로컬 파일만 저장)

```bash
python3 trend_blog_system.py
```

실행하면:
1. 즉시 첫 번째 블로그 포스트 생성
2. 이후 매일 08:00, 12:00, 16:00, 20:00에 자동 실행
3. `Ctrl+C`로 중지 가능

### WordPress 자동 포스팅 (NEW!)

WordPress에 자동으로 게시하려면:

```bash
# 워드프레스 포스팅 활성화
python3 wordpress_trend_blog.py --doPost

# 테스트 실행 (파일만 생성, 포스팅 제외)
python3 wordpress_trend_blog.py
```

### 📊 관리 대시보드 (NEW!)

Streamlit을 사용하여 생성된 글을 관리하고 실시간 트렌드를 확인할 수 있습니다:

```bash
streamlit run dashboard.py
```

- **Dashboard**: 시스템 상태 및 최근 포스팅 현황 요약
- **Keyword Generator**: 실시간 트렌드 키워드 조회 및 즉시 블로그 생성
- **Post Management**: 생성된 로컬 마크다운 파일 관리 및 수동 워드프레스 포스팅
- **System Settings**: 발행 시간 추가/삭제 및 관리 (NEW!)
- **System Logs**: 시스템 로그 실시간 확인

### 🔔 실시간 알림 (NEW!)

텔레그램 봇을 연동하여 블로그 생성 및 포스팅 결과를 실시간으로 받을 수 있습니다.
1. [BotFather](https://t.me/botfather)를 통해 봇 생성 및 토큰 획득
2. [GetIDs Bot](https://t.me/getidsbot) 등을 통해 본인의 Chat ID 확인
3. `.env` 파일에 `TELEGRAM_TOKEN` 및 `TELEGRAM_CHAT_ID` 입력

실행하면:
1. 트렌드 키워드 수집 및 AI 콘텐츠 생성
2. 로컬 파일(`blog_posts/`)로 저장
3. **`--doPost` 플래그 사용 시**: WordPress에 자동 포스팅 ("이슈트래킹" 카테고리)
4. 태그 자동 생성 및 적용

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
├── trend_blog_system.py    # 메인 시스템 코드 (로컬 저장)
├── wordpress_trend_blog.py # WordPress 자동 포스팅 (NEW!)
├── requirements.txt         # Python 패키지 목록
├── .env.example            # 환경 변수 예제
├── .env                    # 환경 변수 설정 (gitignore)
├── .gitignore              # Git 제외 파일 목록
├── README.md               # 프로젝트 설명서
├── blog_posts/             # 생성된 블로그 포스트 (gitignore)
│   ├── images/            # 다운로드된 이미지
│   └── *.md               # 생성된 Markdown 파일
├── used_keywords.json      # 사용된 키워드 기록 (gitignore)
├── system_config.json      # 시스템 설정 파일 (발행 시간 등) (NEW!)
└── system_log.txt          # 시스템 로그 (gitignore)
```

## 🎨 생성되는 블로그 구조

1. **YAML Frontmatter** (메타데이터)
2. **대표 이미지** (Gemini AI 생성 또는 Google 검색 결과)
3. **본문 내용** (AI 생성 콘텐츠)
4. **🎬 관련 영상** (YouTube 인기 영상 자동 임베딩)
5. **📰 관련 뉴스** (뉴스 제목, 출처, 이미지, 요약)
6. **🔗 함께 보면 좋은 글** (스마트 내부 링크 시스템)

## 🔧 설정 커스터마이징

대시보드의 **"시스템 설정"** 메뉴에서 발행 시간을 자유롭게 추가하거나 삭제할 수 있습니다. 설정된 값은 `system_config.json`에 저장되며, 시스템 재시작 시 적용됩니다.

직접 코드를 수정하려면 `trend_blog_system.py` 파일의 `main()` 함수 부분을 참고하세요.

### AI 모델 변경

`__init__` 메서드에서 모델 변경:

```python
self.model = genai.GenerativeModel('gemini-pro')  # 또는 다른 모델
```

## 🌐 WordPress 자동 포스팅 (NEW!)

WordPress REST API를 통해 생성된 블로그를 자동으로 게시할 수 있습니다.

### WordPress 설정 방법

#### 1. Application Password 생성

WordPress 관리자 페이지에서:
1. **사용자** → **프로필** 이동
2. **Application Passwords** 섹션 찾기
3. 새 애플리케이션 이름 입력 (예: "Trend Blog System")
4. **Add New Application Password** 클릭
5. 생성된 비밀번호 복사 (공백 포함)

#### 2. .env 파일 설정

```env
# WordPress 설정
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

#### 3. 실행

```bash
python3 wordpress_trend_blog.py
```

### 주요 기능

- ✅ **세분화된 카테고리 분류**: `SPORTS_MATCH`, `STOCK`, `SOCIAL_ISSUE` 등 14개 세부 분류
- ✅ **이슈트래킹 카테고리 통합**: 모든 게시글은 "이슈트래킹" 카테고리로 자동 분류 및 생성
- ✅ **Markdown → HTML 변환**: WordPress 호환 HTML로 자동 변환 (Frontmatter 및 코드 블록 자동 제거)
- ✅ **이미지 포함**: 본문 이미지 및 뉴스 이미지 자동 포함 (로컬 다운로드 후 삽입)
- ✅ **로컬 백업**: WordPress 포스팅 여부와 관계없이 모든 글은 로컬에 Markdown으로 저장
- ✅ **스마트 링크 변환**: 로컬 파일 링크(`file://`)를 WordPress 검색 링크로 자동 변환
- ✅ **안정적인 YouTube 임베딩**: 개선된 로직으로 유효한 동영상 ID만 추출하여 플레이어 오류 방지

### 🗂️ 세부 카테고리 (14개)

시스템은 키워드를 분석하여 다음 중 가장 적합한 카테고리로 분류합니다:
- `SPORTS_MATCH` (경기 일정/결과), `SPORTS_GENERAL` (선수 이슈)
- `STOCK` (개별 종목), `ECONOMY` (거시 경제/정책)
- `SOCIAL_ISSUE` (논란/쟁점), `SOCIAL_INCIDENT` (사건/사고), `POLITICS` (정치)
- `ENTERTAINMENT_NEWS` (가십), `ENTERTAINMENT_CONTENT` (방송/영화 리뷰)
- `TECH_DEVICE` (하드웨어), `TECH_TREND` (서비스/AI)
- `HEALTH` (건강), `LIVING_INFO` (생활 정보), `OTHER` (기타)

### 포스팅 결과 확인
WordPress 관리자 페이지 → **글** → **모든 글**에서 확인 가능하며, 모든 글은 **"이슈트래킹"** 카테고리에 할당됩니다.

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
