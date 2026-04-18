"""
일일 뉴스 블로그 자동화 — 메인 실행 파일
매일 오전 8:30 Windows 작업 스케줄러에 의해 자동 실행됩니다.

실행 파이프라인:
  1. 전날 뉴스 수집 (Google News RSS)
  2. Claude AI로 블로그 포스트 6개 생성
  3. PDF 리포트 생성
  4. Gmail 발송
  5. Notion 저장 (설정 시 활성화)
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 프로젝트 루트를 sys.path에 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from config import REPORTS_DIR, LOGS_DIR
from news_collector import collect_news
from pdf_generator import generate_pdf_report
from gmail_sender import send_report_email
from notion_client import save_to_notion


def setup_logging(log_date_str: str) -> logging.Logger:
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file = os.path.join(LOGS_DIR, f"automation_{log_date_str}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("main")


def main():
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")      # 대상 날짜 (YYYY-MM-DD)
    log_date = today.strftime("%Y%m%d")            # 로그 파일명용

    logger = setup_logging(log_date)

    logger.info("=" * 60)
    logger.info(f"  일일 뉴스 블로그 자동화 시작")
    logger.info(f"  대상일: {date_str}")
    logger.info(f"  실행시각: {today.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # ── 1단계: 뉴스 수집 ────────────────────────────────────
        logger.info("[1/4] 뉴스 수집 시작")
        news_items = collect_news(date_str)
        if not news_items:
            logger.warning("수집된 뉴스가 없습니다. 네트워크 연결을 확인하세요.")
            sys.exit(1)
        logger.info(f"      완료 — {len(news_items)}개 뉴스 수집")

        # ── 2단계: 블로그 포스트 생성 (건너뜀) ─────────────────────
        blog_posts = []

        # ── 3단계: PDF 리포트 생성 ──────────────────────────────
        logger.info("[3/4] PDF 리포트 생성")
        os.makedirs(REPORTS_DIR, exist_ok=True)
        pdf_filename = f"news_blog_report_{date_str}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
        generate_pdf_report(news_items, blog_posts, date_str, pdf_path)
        logger.info(f"      완료 — {pdf_path}")

        # ── 4단계: Gmail 발송 ───────────────────────────────────
        logger.info("[4/4] Gmail 발송")
        send_report_email(pdf_path, blog_posts, news_items, date_str)
        logger.info("      완료 — 이메일 발송 성공")

        # ── 5단계: Notion 저장 (선택) ───────────────────────────
        logger.info("[5/5] Notion 저장 (미설정 시 건너뜀)")
        save_to_notion(blog_posts, news_items, date_str)

        logger.info("=" * 60)
        logger.info("  자동화 완료!")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        sys.exit(0)
    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        logger.error("실패 — 위 오류를 확인하고 .env 설정을 점검하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
