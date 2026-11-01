from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
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
ROOT = Path(__file__).resolve().parents[3]


def _fitted_image(path: str, width: float, height: float) -> Image:
    with PILImage.open(path) as raw:
        photo = raw.convert("RGB")
        target = height / max(width, 1)
        w, h = photo.size
        current = h / max(w, 1)
        if current > target:
            new_h = max(int(w * target), 1)
            top = max((h - new_h) // 2, 0)
            photo = photo.crop((0, top, w, top + new_h))
        else:
            new_w = max(int(h / target), 1)
            left = max((w - new_w) // 2, 0)
            photo = photo.crop((left, 0, left + new_w, h))
        buffer = BytesIO()
        photo.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)
    return Image(buffer, width=width, height=height)


def _portrait_path(bundle: dict) -> str:
    candidates = []
    given = bundle.get("photo_path") or ""
    if given:
        candidates.append(Path(given))
    app_dir = Path(__file__).resolve().parents[1]
    candidates.extend(
        [
            app_dir / "static" / "avatar.jpg",
            ROOT / "profile-web-app" / "public" / "avatar.jpg",
            ROOT / "backend" / "app" / "static" / "uploads" / "avatar.jpg",
            app_dir / "static" / "uploads" / "avatar.jpg",
        ]
    )
    for path in candidates:
        if path.exists() and path.is_file():
            return str(path)
    return ""


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
    contact = Paragraph(
        " · ".join(
            filter(
                None,
                [
                    profile.get("location"),
                    profile.get("public_email"),
                    profile.get("phone"),
                    f"Birthday: {profile.get('birthday')}" if profile.get("birthday") else "",
                    profile.get("github"),
                    profile.get("linkedin"),
                    profile.get("twitter"),
                    profile.get("website"),
                ],
            )
        ),
        body,
    )
    identity = [
        Paragraph(profile.get("full_name") or bundle["user"]["username"], title),
        Paragraph(profile.get("headline") or "", headline),
        contact,
    ]
    photo_file = _portrait_path(bundle)
    if photo_file:
        try:
            photo_width = 28 * mm
            text_width = doc.width - photo_width - 5 * mm
            text_height = sum(item.wrap(text_width, 80 * mm)[1] for item in identity)
            portrait = _fitted_image(photo_file, photo_width, text_height)
            intro = Table(
                [[portrait, identity]],
                colWidths=[photo_width + 2 * mm, text_width],
            )
            intro.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (0, 0), 6),
                        ("LEFTPADDING", (1, 0), (1, 0), 2),
                    ]
                )
            )
            heading = [KeepTogether(intro)]
        except Exception:
            heading = identity
    else:
        heading = identity

    story = [
        *heading,
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
