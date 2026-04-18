"""
Gmail 발송 모듈
생성된 PDF 리포트를 Gmail 앱 비밀번호를 사용해 이메일로 발송합니다.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from config import GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _build_html_body(blog_posts: list[dict], news_items: list[dict], date_str: str) -> str:
    """HTML 이메일 본문 생성"""
    # 뉴스 요약 (주제별 전체)
    news_by_topic: dict[str, list] = {}
    for item in news_items:
        news_by_topic.setdefault(item["topic"], []).append(item)

    import re

    def clean_summary(s):
        if not s:
            return ""
        s = re.sub(r"^\([^)]+\)\s*[\w\s]+기자\s*=\s*", "", s).strip()
        return s[:200] + "..." if len(s) > 200 else s

    news_html = ""
    for topic, items in news_by_topic.items():
        news_html += f'<div style="margin:14px 0 6px 0;padding:6px 10px;background:#1a73e8;border-radius:4px;display:inline-block;color:#fff;font-size:12px;font-weight:bold;">{topic}</div>'
        for item in items:
            summary = clean_summary(item.get("summary", ""))
            summary_html = f'<p style="margin:2px 0 6px 12px;font-size:11px;color:#5f6368;line-height:1.5;">{summary}</p>' if summary else ""
            news_html += f'''
            <div style="margin:4px 0 8px 0;padding:10px 12px;border-left:3px solid #1a73e8;background:#f8f9fa;">
              <p style="margin:0 0 4px 0;font-size:13px;font-weight:bold;color:#202124;">• {item["title"]}</p>
              {summary_html}
            </div>'''

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="font-family:'맑은 고딕',Arial,sans-serif;max-width:680px;margin:0 auto;padding:20px;background:#f5f5f5;">

  <!-- 헤더 -->
  <div style="background:linear-gradient(135deg,#1a73e8,#0d47a1);padding:24px;border-radius:12px 12px 0 0;text-align:center;">
    <h1 style="margin:0;color:#fff;font-size:22px;">일일 뉴스 리포트</h1>
    <p style="margin:6px 0 0;color:#b3d4ff;font-size:14px;">대상일: {date_str}</p>
  </div>

  <!-- 통계 배지 -->
  <div style="background:#fff;padding:16px;border-bottom:2px solid #e8f0fe;text-align:center;">
    <div style="display:inline-block;padding:12px 32px;background:#e8f0fe;border-radius:8px;">
      <div style="font-size:24px;font-weight:bold;color:#1a73e8;">{len(news_items)}</div>
      <div style="font-size:12px;color:#5f6368;">수집 뉴스</div>
    </div>
  </div>

  <!-- 뉴스 요약 -->
  <div style="background:#fff;padding:20px;">
    <h2 style="color:#1a73e8;font-size:16px;margin:0 0 12px 0;">수집된 주요 뉴스</h2>
    {news_html}
    <p style="font-size:11px;color:#9e9e9e;margin-top:8px;">* 전체 뉴스는 첨부된 PDF를 확인하세요.</p>
  </div>

  <!-- 푸터 -->
  <div style="background:#f8f9fa;padding:12px;text-align:center;border-radius:0 0 12px 12px;border-top:1px solid #e0e0e0;">
    <p style="margin:0;font-size:11px;color:#9e9e9e;">자동화된 일일 뉴스 리포트</p>
  </div>

</body>
</html>"""


def send_report_email(
    pdf_path: str,
    blog_posts: list[dict],
    news_items: list[dict],
    date_str: str,
) -> None:
    """
    Gmail로 리포트 이메일 발송

    Args:
        pdf_path: 첨부할 PDF 파일 경로
        blog_posts: 생성된 블로그 포스트 목록
        news_items: 수집된 뉴스 목록
        date_str: 대상 날짜 문자열
    """
    if not all([GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT]):
        raise ValueError(
            ".env 파일에 GMAIL_SENDER, GMAIL_APP_PASSWORD, GMAIL_RECIPIENT를 설정해주세요."
        )

    recipients = [r.strip() for r in GMAIL_RECIPIENT.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["From"] = GMAIL_SENDER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"[일일 뉴스] {date_str} 경제·주식 브리핑"

    # HTML 본문
    html_body = _build_html_body(blog_posts, news_items, date_str)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # PDF 첨부
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        pdf_filename = os.path.basename(pdf_path)
        part.add_header(
            "Content-Disposition",
            f'attachment; filename="{pdf_filename}"',
        )
        msg.attach(part)
        logger.info(f"PDF 첨부 완료: {pdf_filename}")
    else:
        logger.warning(f"PDF 파일 없음, 첨부 생략: {pdf_path}")

    # Gmail 발송
    logger.info(f"Gmail 발송 중: {GMAIL_SENDER} → {recipients}")
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, recipients, msg.as_string())

    logger.info("이메일 발송 완료")
