"""
Claude AI 기반 블로그 포스트 생성 모듈
수집된 뉴스를 바탕으로 SEO 최적화된 블로그 글 6개를 생성합니다.
"""

import json
import logging
import re
from anthropic import Anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, BLOG_COUNT
from news_collector import format_news_for_prompt

logger = logging.getLogger(__name__)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def generate_blog_posts(news_items: list[dict], target_date_str: str) -> list[dict]:
    """
    Claude API로 뉴스 기반 블로그 포스트 생성

    Returns:
        list of dict: [{"title", "category", "keywords", "content", "summary"}, ...]
    """
    news_text = format_news_for_prompt(news_items)

    prompt = f"""당신은 전문 블로그 작가입니다. {target_date_str}의 주요 뉴스들을 바탕으로 독자들이 읽고 싶어 할 블로그 포스트 {BLOG_COUNT}개를 작성해주세요.

## 수집된 뉴스
{news_text}

## 작성 지침
- 각 포스트는 서로 다른 주제/관점을 다뤄야 합니다
- 독자들이 이해하기 쉬운 친근하고 설득력 있는 어조
- 서론 → 본론(소제목 포함) → 결론 구조
- 각 포스트 최소 800자 이상
- 제목은 클릭하고 싶게 만드는 SEO 최적화 제목

## 출력 형식 (JSON만 출력, 다른 텍스트 금지)
{{
  "posts": [
    {{
      "title": "SEO 최적화된 블로그 제목",
      "category": "카테고리명",
      "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
      "summary": "이 글의 핵심 내용을 2-3문장으로 요약",
      "content": "본문 내용 (마크다운 형식, ## 소제목 사용, 최소 800자)"
    }}
  ]
}}

{BLOG_COUNT}개의 포스트를 포함한 유효한 JSON만 출력하세요."""

    logger.info(f"Claude API 호출 중 (모델: {CLAUDE_MODEL})...")

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text
    logger.info(f"Claude API 응답 수신 ({len(raw_text)}자)")

    posts = _parse_response(raw_text)
    logger.info(f"블로그 포스트 파싱 완료: {len(posts)}개")
    return posts


def _parse_response(raw_text: str) -> list[dict]:
    """Claude 응답에서 JSON 파싱"""
    # JSON 블록 추출 (```json ... ``` 형식 대응)
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
    if json_match:
        raw_text = json_match.group(1).strip()

    # JSON 객체 경계 찾기
    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1
    if start != -1 and end > start:
        raw_text = raw_text[start:end]

    try:
        data = json.loads(raw_text)
        posts = data.get("posts", [])

        # 필수 필드 검증 및 기본값 보충
        validated = []
        for i, post in enumerate(posts):
            validated.append({
                "title": post.get("title", f"블로그 포스트 {i + 1}"),
                "category": post.get("category", "시사"),
                "keywords": post.get("keywords", []),
                "summary": post.get("summary", ""),
                "content": post.get("content", ""),
            })
        return validated

    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        logger.debug(f"원본 응답:\n{raw_text[:500]}")
        # 파싱 실패 시 원본 텍스트를 단일 포스트로 반환
        return [{
            "title": "오늘의 뉴스 요약",
            "category": "시사",
            "keywords": [],
            "summary": "뉴스 기반 블로그 포스트",
            "content": raw_text,
        }]
