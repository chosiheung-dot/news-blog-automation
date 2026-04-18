"""
PDF 리포트 생성 모듈 — 깔끔한 미니멀 스타일
"""

import os
import re
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, HRFlowable, PageBreak, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import FONT_REGULAR, FONT_BOLD

logger = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm

C_TITLE   = colors.HexColor("#1A1A1A")
C_SUMMARY = colors.HexColor("#444444")
C_SOURCE  = colors.HexColor("#888888")
C_DIVIDER = colors.HexColor("#E0E0E0")
C_ACCENT  = colors.HexColor("#2C3E7A")
C_ACCENT2 = colors.HexColor("#E8ECF8")
C_WHITE   = colors.white
C_BG      = colors.HexColor("#F7F8FC")

TOPIC_COLORS = [
    colors.HexColor("#2C3E7A"),
    colors.HexColor("#1A7A4A"),
    colors.HexColor("#7A2C2C"),
    colors.HexColor("#7A5C1A"),
]


def _register_fonts():
    regular_name, bold_name = "MalgunGothic", "MalgunGothic-Bold"
    try:
        if os.path.exists(FONT_REGULAR):
            pdfmetrics.registerFont(TTFont(regular_name, FONT_REGULAR))
        else:
            return "Helvetica", "Helvetica-Bold"
        if os.path.exists(FONT_BOLD):
            pdfmetrics.registerFont(TTFont(bold_name, FONT_BOLD))
        else:
            bold_name = regular_name
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily(regular_name, normal=regular_name, bold=bold_name)
        return regular_name, bold_name
    except Exception as e:
        logger.warning(f"폰트 등록 오류: {e}")
        return "Helvetica", "Helvetica-Bold"


def _safe(text: str) -> str:
    """ReportLab Paragraph 안전 문자열 변환"""
    if not text:
        return ""
    # 연합뉴스 기자 서명 제거
    text = re.sub(r"^\([^)]+\)\s*[\w\s]+기자\s*=\s*", "", text).strip()
    # XML 특수문자 이스케이프
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _build_styles(font, bold_font):
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName=bold_font, fontSize=30,
            textColor=C_TITLE, leading=38, alignment=1,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName=font, fontSize=12,
            textColor=C_SOURCE, leading=16, alignment=1,
        ),
        "cover_stats": ParagraphStyle(
            "cover_stats", fontName=font, fontSize=10,
            textColor=C_SOURCE, leading=14, alignment=1,
        ),
        "topic_header": ParagraphStyle(
            "topic_header", fontName=bold_font, fontSize=12,
            textColor=C_WHITE, leading=16,
        ),
        "news_title": ParagraphStyle(
            "news_title", fontName=bold_font, fontSize=10,
            textColor=C_TITLE, leading=15, spaceAfter=3,
            leftIndent=8, rightIndent=8,
        ),
        "news_summary": ParagraphStyle(
            "news_summary", fontName=font, fontSize=8.5,
            textColor=C_SUMMARY, leading=14, spaceAfter=2,
            leftIndent=8, rightIndent=8,
        ),
        "news_source": ParagraphStyle(
            "news_source", fontName=font, fontSize=7.5,
            textColor=C_SOURCE, leading=11, alignment=2,
            leftIndent=8, rightIndent=8,
        ),
    }


def _draw_cover(canvas, doc, font, bold_font, date_str, news_count):
    canvas.saveState()
    w, h = PAGE_W, PAGE_H

    # 흰 배경
    canvas.setFillColor(C_WHITE)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # 상단 굵은 포인트 바
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, h - 8, w, 8, fill=1, stroke=0)

    # 상단 바 아래 얇은 색 줄 3개
    bar_colors = [colors.HexColor("#4A6BC7"), colors.HexColor("#7A9AE8"), colors.HexColor("#B0C4F5")]
    for i, bc in enumerate(bar_colors):
        canvas.setFillColor(bc)
        canvas.rect(0, h - 8 - (i + 1) * 3, w, 3, fill=1, stroke=0)

    cx = w / 2

    # 날짜 / 구분선 / 통계 — 중앙에서 아래로 이동
    group_y = h * 0.42

    canvas.setFillColor(C_SOURCE)
    canvas.setFont(font, 13)
    canvas.drawCentredString(cx, group_y, date_str)

    canvas.setStrokeColor(C_DIVIDER)
    canvas.setLineWidth(1)
    canvas.line(cx - 40 * mm, group_y - 16, cx + 40 * mm, group_y - 16)

    canvas.setFont(font, 10)
    canvas.setFillColor(C_SOURCE)
    canvas.drawCentredString(cx, group_y - 32, f"총 {news_count}건의 뉴스")

    # 타이틀 — 페이지 하단
    canvas.setFillColor(C_TITLE)
    canvas.setFont(bold_font, 32)
    canvas.drawCentredString(cx, 22 * mm, "일일 뉴스 리포트")

    # 하단 바
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, 0, w, 5, fill=1, stroke=0)

    canvas.restoreState()


def _draw_page_chrome(canvas, doc, font, date_str):
    canvas.saveState()
    w, h = PAGE_W, PAGE_H

    # 상단 포인트 라인
    canvas.setFillColor(C_ACCENT)
    canvas.rect(0, h - 4, w, 4, fill=1, stroke=0)

    # 푸터
    canvas.setStrokeColor(C_DIVIDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 13 * mm, w - MARGIN, 13 * mm)

    canvas.setFont(font, 7.5)
    canvas.setFillColor(C_SOURCE)
    canvas.drawString(MARGIN, 8 * mm, f"일일 뉴스 리포트  |  {date_str}")
    canvas.setFillColor(C_ACCENT)
    canvas.drawRightString(w - MARGIN, 8 * mm, str(doc.page))

    canvas.restoreState()


def generate_pdf_report(news_items, blog_posts, date_str, output_path):
    font, bold_font = _register_fonts()
    styles = _build_styles(font, bold_font)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    content_w = PAGE_W - 2 * MARGIN

    cover_frame = Frame(0, 0, PAGE_W, PAGE_H,
                        leftPadding=0, rightPadding=0,
                        topPadding=0, bottomPadding=0)
    content_frame = Frame(MARGIN, 18 * mm, content_w,
                          PAGE_H - 18 * mm - 16 * mm)

    cover_tmpl = PageTemplate(
        id="cover", frames=[cover_frame],
        onPage=lambda c, d: _draw_cover(c, d, font, bold_font, date_str, len(news_items)),
    )
    content_tmpl = PageTemplate(
        id="content", frames=[content_frame],
        onPage=lambda c, d: _draw_page_chrome(c, d, font, date_str),
    )

    doc = BaseDocTemplate(output_path, pagesize=A4,
                          pageTemplates=[cover_tmpl, content_tmpl])

    story = []
    story.append(Spacer(PAGE_W, PAGE_H))
    story.append(PageBreak())

    # 주제별 그룹핑
    topics = {}
    topic_order = []
    for item in news_items:
        t = item["topic"]
        if t not in topics:
            topics[t] = []
            topic_order.append(t)
        topics[t].append(item)

    for t_idx, topic in enumerate(topic_order):
        items = topics[topic]
        tc = TOPIC_COLORS[t_idx % len(TOPIC_COLORS)]

        # 주제 헤더
        story.append(HRFlowable(width="100%", thickness=3, color=tc, spaceAfter=0))
        story.append(Paragraph(
            f'<font color="#{tc.hexval()[2:]}"><b>{topic}</b></font>',
            ParagraphStyle("th", fontName=bold_font, fontSize=13,
                           textColor=tc, leading=18,
                           spaceBefore=6, spaceAfter=8),
        ))

        for i, item in enumerate(items):
            block = []

            # 제목
            title_text = _safe(item["title"])
            if title_text:
                block.append(Paragraph(title_text, styles["news_title"]))

            # 요약 (RSS가 주는 전체 내용, 자르지 않음)
            summary_text = _safe(item.get("summary", ""))
            if summary_text:
                block.append(Paragraph(summary_text, styles["news_summary"]))

            # 출처
            source_text = _safe(item.get("source", ""))
            if source_text:
                block.append(Paragraph(source_text, styles["news_source"]))

            if block:
                story.append(KeepTogether(block))

            # 항목 구분선 (마지막 제외)
            if i < len(items) - 1:
                story.append(Spacer(1, 5))
                story.append(HRFlowable(
                    width="100%", thickness=0.5,
                    color=C_DIVIDER, dash=(2, 3), spaceAfter=5,
                ))

        # 주제 사이 페이지 나누기
        if t_idx < len(topic_order) - 1:
            story.append(PageBreak())

    doc.build(story)
    logger.info(f"PDF 생성 완료: {output_path}")
    return output_path
