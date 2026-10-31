from io import BytesIO

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = HexColor("#0f172a")
TEAL = HexColor("#0f766e")
MUTED = HexColor("#475569")


def build_cv_pdf(bundle: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Name", parent=styles["Heading1"], textColor=NAVY, fontSize=22, spaceAfter=2
    )
    headline = ParagraphStyle(
        "Headline", parent=styles["Normal"], textColor=TEAL, fontSize=11, spaceAfter=8
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        textColor=NAVY,
        fontSize=12,
        spaceBefore=10,
        spaceAfter=4,
        borderPadding=0,
    )
    body = ParagraphStyle("Body", parent=styles["Normal"], textColor=MUTED, fontSize=9, leading=13)
    item_title = ParagraphStyle(
        "ItemTitle", parent=styles["Normal"], textColor=NAVY, fontSize=10, leading=13
    )

    profile = bundle["profile"]
    story = [
        Paragraph(profile.get("full_name") or bundle["user"]["username"], title),
        Paragraph(profile.get("headline") or "", headline),
        Paragraph(
            " · ".join(
                filter(
                    None,
                    [
                        profile.get("location"),
                        profile.get("public_email"),
                        profile.get("phone"),
                        f"Birthday: {profile.get('birthday')}" if profile.get("birthday") else "",
                        profile.get("website"),
                        profile.get("github"),
                        profile.get("linkedin"),
                        profile.get("twitter"),
                    ],
                )
            ),
            body,
        ),
        Spacer(1, 6),
        Paragraph("Professional summary", h2),
        Paragraph((profile.get("bio") or "").replace("\n", "<br/>"), body),
    ]

    if bundle["skills"]:
        story.append(Paragraph("Skills", h2))
        grouped = {}
        for skill in bundle["skills"]:
            grouped.setdefault(skill.get("category") or "Skills", []).append(skill["name"])
        if len(grouped) == 1 and "Skills" in grouped:
            story.append(Paragraph(", ".join(grouped["Skills"]), body))
        else:
            for category, names in grouped.items():
                story.append(Paragraph(f"<b>{category}:</b> {', '.join(names)}", body))

    if bundle["projects"]:
        story.append(Paragraph("Selected projects", h2))
        for item in bundle["projects"]:
            if "professional portfolio platform" in (item.get("title") or "").lower():
                story.append(PageBreak())
            story.append(Paragraph(f"<b>{item['title']}</b> — {item.get('summary') or ''}", item_title))
            story.append(Paragraph(item.get("description") or "", body))
            if item.get("repo_url"):
                story.append(Paragraph(item["repo_url"], body))

    if bundle["experiences"]:
        story.append(Paragraph("Experience", h2))
        for item in bundle["experiences"]:
            dates = " – ".join(
                filter(None, [item.get("start_date"), item.get("end_date") or ("Present" if item.get("is_current") else "")])
            )
            story.append(
                Paragraph(
                    f"<b>{item['title']}</b> — {item['company']} <font color='#64748b'>({dates})</font>",
                    item_title,
                )
            )
            story.append(Paragraph(item.get("description") or "", body))

    if bundle["education"]:
        story.append(Paragraph("Education", h2))
        for item in bundle["education"]:
            dates = " – ".join(filter(None, [item.get("start_date"), item.get("end_date")]))
            story.append(
                Paragraph(
                    f"<b>{item['degree']}</b> — {item['institution']} <font color='#64748b'>({dates})</font>",
                    item_title,
                )
            )
            story.append(Paragraph(item.get("description") or "", body))

    if bundle["languages"]:
        story.append(Paragraph("Languages", h2))
        story.append(
            Paragraph(
                " · ".join(
                    f"{lang['name']} ({lang['proficiency']})" for lang in bundle["languages"]
                ),
                body,
            )
        )

    header = Table([[""]], colWidths=[doc.width], rowHeights=[4])
    header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TEAL)]))
    story.insert(0, header)
    story.insert(1, Spacer(1, 8))

    photo_path = bundle.get("photo_path")
    if photo_path:
        try:
            portrait = Image(photo_path, width=28 * mm, height=28 * mm)
            heading = story[2:5]
            intro = Table(
                [[portrait, heading]],
                colWidths=[32 * mm, doc.width - 32 * mm],
            )
            intro.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (0, 0), 8),
                    ]
                )
            )
            story[2:5] = [intro]
        except Exception:
            pass

    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, A4[0], 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(18 * mm, 5 * mm, "NTARINDWA Jean Dieudonne · Machine Learning portfolio")
        canvas.restoreState()

    doc.build(story, onLaterPages=_footer, onFirstPage=_footer)
    return buffer.getvalue()
