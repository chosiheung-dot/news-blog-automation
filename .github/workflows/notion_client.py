"""
Notion 연동 모듈 (추후 활성화 예정)
현재는 스텁으로만 존재합니다.

=== Notion 설정 방법 ===
1. https://www.notion.so/my-integrations 에서 새 Integration 생성
2. 생성된 토큰을 .env의 NOTION_TOKEN에 입력
3. Notion에서 데이터베이스 생성 후 Integration에 공유 권한 부여
4. 데이터베이스 URL의 ID 부분을 .env의 NOTION_DATABASE_ID에 입력
5. 아래 주석 해제 후 main.py에서 호출

=== 데이터베이스 속성 구조 ===
- 날짜 (Date): 대상 날짜
- 제목 (Title): 블로그 포스트 제목
- 카테고리 (Select): 카테고리
- 키워드 (Multi-select): SEO 키워드
- 요약 (Text): 포스트 요약
- 본문 (Text): 포스트 전문
"""

import logging
from config import NOTION_TOKEN, NOTION_DATABASE_ID

logger = logging.getLogger(__name__)


def save_to_notion(
    blog_posts: list[dict],
    news_items: list[dict],
    date_str: str,
) -> bool:
    """
    Notion 데이터베이스에 블로그 포스트 저장 (현재 비활성)

    Returns:
        True if saved successfully, False otherwise
    """
    if not NOTION_TOKEN or not NOTION_DATABASE_ID:
        logger.info("Notion 미설정 — 저장 건너뜀 (.env에 NOTION_TOKEN, NOTION_DATABASE_ID 추가 필요)")
        return False

    logger.info("Notion 저장 시작 (추후 구현 예정)")

    # ─── 아래 코드는 Notion 연동 준비 완료 시 주석 해제 ───────────────────────
    # import requests
    #
    # headers = {
    #     "Authorization": f"Bearer {NOTION_TOKEN}",
    #     "Content-Type": "application/json",
    #     "Notion-Version": "2022-06-28",
    # }
    #
    # for post in blog_posts:
    #     payload = {
    #         "parent": {"database_id": NOTION_DATABASE_ID},
    #         "properties": {
    #             "날짜": {"date": {"start": date_str}},
    #             "제목": {"title": [{"text": {"content": post["title"]}}]},
    #             "카테고리": {"select": {"name": post.get("category", "시사")}},
    #             "키워드": {
    #                 "multi_select": [{"name": kw} for kw in post.get("keywords", [])]
    #             },
    #             "요약": {"rich_text": [{"text": {"content": post.get("summary", "")[:2000]}}]},
    #             "본문": {"rich_text": [{"text": {"content": post.get("content", "")[:2000]}}]},
    #         },
    #     }
    #     resp = requests.post(
    #         "https://api.notion.com/v1/pages",
    #         headers=headers,
    #         json=payload,
    #         timeout=15,
    #     )
    #     resp.raise_for_status()
    #     logger.info(f"  Notion 저장: {post['title']}")
    #
    # return True
    # ─────────────────────────────────────────────────────────────────────────

    return False
