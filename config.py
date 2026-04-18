import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

# ===== Claude API =====
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ===== 네이버 검색 API =====
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# ===== Gmail =====
GMAIL_SENDER = os.getenv("GMAIL_SENDER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GMAIL_RECIPIENT = os.getenv("GMAIL_RECIPIENT")

# ===== Notion (추후 추가) =====
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# ===== 뉴스 수집 설정 =====
NEWS_TOPICS = [
    {"name": "경제",    "query": "한국 경제 금융"},
    {"name": "주식",    "query": "코스피 코스닥 주식 증시"},
    {"name": "글로벌증시", "query": "미국 증시 나스닥 달러 환율"},
    {"name": "부동산",  "query": "부동산 아파트 매매 전세 분양"},
    {"name": "스포츠",  "query": "스포츠 축구 야구 농구 KBO 손흥민"},
]
NEWS_MAX_PER_TOPIC = 6  # 주제당 최대 뉴스 수

# ===== 블로그 설정 =====
BLOG_COUNT = 6
CLAUDE_MODEL = "claude-sonnet-4-6"

# ===== 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# ===== PDF 폰트 (Windows: 맑은고딕 / Linux: 나눔고딕) =====
import platform
if platform.system() == "Windows":
    FONT_REGULAR = "C:/Windows/Fonts/malgun.ttf"
    FONT_BOLD    = "C:/Windows/Fonts/malgunbd.ttf"
else:
    FONT_REGULAR = "fonts/NanumGothic.ttf"
    FONT_BOLD    = "fonts/NanumGothicBold.ttf"
