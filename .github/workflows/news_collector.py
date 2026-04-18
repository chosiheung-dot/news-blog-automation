"""
네이버 뉴스 검색 API 기반 뉴스 수집 모듈
"""

import html
import logging
import re
import requests
from bs4 import BeautifulSoup
from config import NEWS_TOPICS, NEWS_MAX_PER_TOPIC, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

logger = logging.getLogger(__name__)

NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"
SCRAPE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
ARTICLE_SELECTORS = [
    "#articleBodyContents", "#newsEndContents", "#articeBody",
    "#article-view-content-div", ".article_body", ".article_txt",
    ".news_end", "#content-body", "article", ".articleBody",
    ".article-body", "[class*='article_body']", "[class*='news-content']",
]

# 불필요 기사 제외 키워드
EXCLUDE_KEYWORDS = ["별세", "부고", "장인상", "부친상", "모친상", "빈소", "영결식", "발인"]


def clean_text(text: str) -> str:
    """HTML 태그·엔티티 제거 및 공백 정리"""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


NOISE_PATTERNS = [
    r"가\s*작게\s*가\s*보통\s*가\s*크게\s*가\s*매우크게",
    r"글자크기[가\s작보통크게매우]{0,30}",
    r"링크가 복사되었습니다",
    r"(페이스북|엑스|트위터|링크드인|텔레그램|카카오스토리|카카오|밴드|링크복사)\s*",
    r"이\s*기사를\s*공유합니다",
    r"저작권자\s*©.{0,60}",
    r"무단\s*전재\s*및\s*재배포\s*금지",
    r"\d{4}\.\d{2}\.\d{2}\s*\(.\)\s*\d{2}:\d{2}",  # 날짜 패턴
    r"\s+\d+\s+\d+\s+",  # 숫자만 있는 공유카운트
    r"\d{2,4}\s*[·•]\s*\d{2}:\d{2}",  # 날짜/시간 패턴
    r"조회수\s*:\s*\d*",  # 조회수
    r"발행\s*:\s*[\d.\s:・]+",  # 발행일
]


def clean_article_text(text: str) -> str:
    """스크래핑한 기사 본문에서 불필요 요소 제거"""
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # 한국어 문장 종결 패턴으로 문장 추출 (다. 습니다. 했다. 됩니다. 등)
    # 마침표로 끝나는 진짜 문장만 추출
    sentence_pattern = re.findall(r'[^.!?]*(?:다|습니다|했다|됩니다|입니다|이다|였다|겠다|한다|된다|않다|없다|있다)[.。]', text)
    korean_sentences = []
    for s in sentence_pattern:
        s = s.strip()
        korean_chars = len(re.findall(r'[가-힣]', s))
        if korean_chars >= 10 and len(s) >= 20:
            korean_sentences.append(s)
        if len(korean_sentences) >= 3:
            break

    result = " ".join(korean_sentences).strip()
    return result if result else text[:150]


def scrape_article(url: str) -> str:
    """기사 URL에서 본문 스크래핑 (500자 반환)"""
    try:
        r = requests.get(url, headers=SCRAPE_HEADERS, timeout=8, allow_redirects=True)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "figure"]):
            tag.decompose()

        # 선택자 순서대로 시도
        for sel in ARTICLE_SELECTORS:
            el = soup.select_one(sel)
            if el:
                text = clean_article_text(re.sub(r"\s+", " ", el.get_text()).strip())
                if len(text) > 100:
                    return text

        # 선택자 실패 시 <p> 태그 합산
        paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]
        text = clean_article_text(" ".join(paras))
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 100:
            return text
    except Exception as e:
        logger.debug(f"스크래핑 실패 ({url[:60]}): {e}")
    return ""


def fetch_naver_news(query: str, max_items: int) -> list[dict]:
    """네이버 뉴스 검색 API로 기사 수집"""
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": max_items * 3,   # 필터링 감안해 여유롭게 요청
        "sort": "date",
    }

    try:
        resp = requests.get(NAVER_API_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"네이버 API 오류 ({query}): {e}")
        return []

    items = []
    for item in data.get("items", []):
        title   = clean_text(item.get("title", ""))
        summary = clean_text(item.get("description", ""))
        source  = ""

        # 출처: originallink 도메인 추출
        link = item.get("originallink") or item.get("link", "")
        m = re.search(r"https?://(?:www\.)?([^/]+)", link)
        if m:
            source = m.group(1)

        # 부고 제외
        if any(ex in title for ex in EXCLUDE_KEYWORDS):
            continue

        # 노이즈 많은 사이트 제외
        if "tokenpost" in link or "토큰포스트" in title:
            continue

        # 기사 본문 스크래핑 시도 → 성공하면 네이버 요약 대체
        full_content = scrape_article(link)
        final_summary = full_content if full_content else summary

        items.append({
            "title":     title,
            "source":    source,
            "summary":   final_summary,
            "link":      link,
            "published": item.get("pubDate", ""),
        })

        if len(items) >= max_items:
            break

    return items


def collect_news(target_date_str: str) -> list[dict]:
    """모든 주제의 뉴스를 수집하여 반환"""
    all_news = []
    logger.info(f"뉴스 수집 시작 (대상일: {target_date_str})")

    for topic in NEWS_TOPICS:
        name    = topic["name"]
        query   = topic.get("query") or topic.get("name")  # query 없으면 name 사용
        logger.info(f"  수집 중: [{name}]")

        items = fetch_naver_news(query, NEWS_MAX_PER_TOPIC)
        for item in items:
            item["topic"] = name
            all_news.append(item)

        logger.info(f"  -> {len(items)}개 수집")

    logger.info(f"전체 수집 완료: {len(all_news)}개")
    return all_news


def format_news_for_prompt(news_items: list[dict]) -> str:
    """Claude 프롬프트용 뉴스 텍스트 포맷"""
    lines = []
    current_topic = None
    for item in news_items:
        if item["topic"] != current_topic:
            current_topic = item["topic"]
            lines.append(f"\n## [{current_topic}]")
        lines.append(f"- {item['title']}")
        if item["summary"]:
            lines.append(f"  {item['summary']}")
    return "\n".join(lines)
