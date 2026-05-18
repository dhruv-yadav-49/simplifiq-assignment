"""
pdf_generator.py — PDF using ReportLab (Windows compatible)
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_pdf(name, email, company, role, enriched):
    os.makedirs("output_pdfs", exist_ok=True)
    safe_name = company.replace(" ", "_").lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = f"output_pdfs/{safe_name}_{timestamp}.pdf"

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    # Colors
    dark_blue  = HexColor("#1a1a2e")
    accent     = HexColor("#4361ee")
    light_bg   = HexColor("#f0f4ff")
    green_bg   = HexColor("#e8f5e9")
    red_bg     = HexColor("#fdecea")
    blue_bg    = HexColor("#e3f2fd")
    green_text = HexColor("#2e7d32")
    red_text   = HexColor("#b71c1c")
    blue_text  = HexColor("#0d47a1")
    muted      = HexColor("#666666")

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("title", fontSize=22, textColor=white,
                                  fontName="Helvetica-Bold", spaceAfter=4)
    sub_style   = ParagraphStyle("sub", fontSize=11, textColor=HexColor("#ccccff"),
                                  fontName="Helvetica")
    h2_style    = ParagraphStyle("h2", fontSize=11, textColor=accent,
                                  fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6,
                                  borderPadding=(0,0,4,0))
    body_style  = ParagraphStyle("body", fontSize=10, textColor=dark_blue,
                                  fontName="Helvetica", leading=16)
    muted_style = ParagraphStyle("muted", fontSize=9, textColor=muted,
                                  fontName="Helvetica")
    bullet_style = ParagraphStyle("bullet", fontSize=10, textColor=dark_blue,
                                   fontName="Helvetica", leftIndent=12, leading=15)

    story = []
    date_str = datetime.now().strftime("%B %d, %Y")

    # ── Header block ──────────────────────────────────────────
    header_data = [[
        Paragraph(f"<b>SimplifIQ</b> — AI Audit Report", title_style),
        Paragraph(f"{date_str}<br/>Confidential", ParagraphStyle("r", fontSize=9,
                   textColor=HexColor("#aaaacc"), fontName="Helvetica", alignment=2))
    ]]
    header_table = Table(header_data, colWidths=[120*mm, 60*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), dark_blue),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (0,-1), 16),
        ("RIGHTPADDING",  (-1,0),(-1,-1), 12),
        ("ROUNDEDCORNERS", [8,8,8,8]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6*mm))

    # Subtitle
    story.append(Paragraph(f"Personalized insights for <b>{company}</b>  •  Industry: {enriched.get('industry','—')}", sub_style))
    story.append(Spacer(1, 2*mm))

    # ── Prospect info bar ────────────────────────────────────
    info_data = [[
        Paragraph(f"<b>{name}</b><br/><font size=8 color='#666'>Prospect</font>", body_style),
        Paragraph(f"<b>{company}</b><br/><font size=8 color='#666'>Company</font>", body_style),
        Paragraph(f"<b>{role or 'Decision Maker'}</b><br/><font size=8 color='#666'>Role</font>", body_style),
        Paragraph(f"<b>{email}</b><br/><font size=8 color='#666'>Email</font>", body_style),
    ]]
    info_table = Table(info_data, colWidths=[45*mm]*4)
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), light_bg),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("LINEAFTER",     (0,0), (2,-1), 0.5, HexColor("#c5cae9")),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 5*mm))

    # ── Opening ──────────────────────────────────────────────
    story.append(Paragraph(enriched.get("personalized_opening", ""), body_style))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#e0e7ff")))
    story.append(Spacer(1, 3*mm))

    # ── Company Overview ─────────────────────────────────────
    story.append(Paragraph("COMPANY OVERVIEW", h2_style))
    story.append(Paragraph(enriched.get("company_summary", ""), body_style))
    story.append(Spacer(1, 4*mm))

    # ── 3-column grid ────────────────────────────────────────
    def make_col_content(title, items, txt_color):
        content = [Paragraph(f"<b>{title}</b>",
                              ParagraphStyle("ct", fontSize=9, textColor=txt_color,
                                             fontName="Helvetica-Bold", spaceAfter=6))]
        for item in items:
            content.append(Paragraph(f"• {item}", bullet_style))
        return content

    col_width = 56*mm
    gap = 3*mm
    grid_data = [[
        make_col_content("SERVICES",         enriched.get("services",[]),              blue_text),
        "", # empty gap
        make_col_content("FINDINGS",         enriched.get("findings",[]),              red_text),
        "", # empty gap
        make_col_content("RECOMMENDATIONS",  enriched.get("recommendations",[]),       green_text),
    ]]
    
    grid = Table(grid_data, colWidths=[col_width, gap, col_width, gap, col_width], hAlign="CENTER")
    grid.setStyle(TableStyle([
        # Backgrounds
        ("BACKGROUND",    (0,0), (0,0), blue_bg),
        ("BACKGROUND",    (2,0), (2,0), red_bg),
        ("BACKGROUND",    (4,0), (4,0), green_bg),
        
        # Top borders
        ("LINEABOVE",     (0,0), (0,0), 2, blue_text),
        ("LINEABOVE",     (2,0), (2,0), 2, red_text),
        ("LINEABOVE",     (4,0), (4,0), 2, green_text),
        
        # Padding
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        
        # Remove padding from gaps
        ("LEFTPADDING",   (1,0), (1,0), 0),
        ("RIGHTPADDING",  (1,0), (1,0), 0),
        ("LEFTPADDING",   (3,0), (3,0), 0),
        ("RIGHTPADDING",  (3,0), (3,0), 0),
        
        # Align content to top
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    story.append(grid)
    story.append(Spacer(1, 6*mm))

    # ── CTA ──────────────────────────────────────────────────
    cta_data = [[
        Paragraph(f"Ready to transform <b>{company}</b>?<br/>"
                  f"<font size=9>Schedule a free 30-min strategy call with our AI specialists.</font>",
                  ParagraphStyle("cta", fontSize=12, textColor=white,
                                  fontName="Helvetica-Bold", leading=18)),
        Paragraph("Book a Call →\nsimplifiq.ai/call",
                  ParagraphStyle("ctabtn", fontSize=10, textColor=HexColor("#4361ee"),
                                  fontName="Helvetica-Bold", alignment=TA_CENTER))
    ]]
    cta_table = Table(cta_data, colWidths=[120*mm, 55*mm])
    cta_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,-1), accent),
        ("BACKGROUND",    (1,0), (1,-1), white),
        ("TOPPADDING",    (0,0), (-1,-1), 14),
        ("BOTTOMPADDING", (0,0), (-1,-1), 14),
        ("LEFTPADDING",   (0,0), (0,-1), 16),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (1,0), (1,-1), "CENTER"),
    ]))
    story.append(cta_table)
    story.append(Spacer(1, 4*mm))

    # ── Footer ───────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#eeeeee")))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"SimplifIQ AI Solutions  |  simplifiq.ai  |  Auto-generated report  |  © {date_str[:4]}",
        ParagraphStyle("footer", fontSize=8, textColor=muted, alignment=TA_CENTER)
    ))

    doc.build(story)
    print(f"[PDF] Saved to {pdf_path}")
    return pdf_path