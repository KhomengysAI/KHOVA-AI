"""Exporters for Khova AI: real PDF (WeasyPrint), real XLSX (openpyxl),
and standalone responsive website HTML.
"""
import base64
import html as _html
import logging
from io import BytesIO

logger = logging.getLogger("khova.exporters")

DEFAULT_PALETTE = {
    "primary": "#0B6E6B",
    "secondary": "#111C2E",
    "accent": "#C07A2B",
    "background": "#FBFAF7",
    "text": "#0B1220",
}

# Structural "chrome" strings for generated documents/pages. These are NOT
# AI-generated content — they are fixed UI labels baked into exported
# assets, so they must follow the selected Product Language explicitly
# (this fixes the previous bug where these were hardcoded in Indonesian
# regardless of product_language).
LABELS = {
    "id": {
        "chapter": "Bab", "toc": "Daftar Isi", "introduction": "Pendahuluan",
        "bonus_kicker": "Bonus", "bonus_title": "Materi Bonus",
        "outcomes_intro": "Yang akan Anda kuasai:", "no_content": "Bagian ini belum dibuat.",
        "copyright": "Hak Cipta", "rights": "Semua hak dilindungi. Konten ini disediakan untuk tujuan edukasi. Meskipun disusun dengan cermat, pembaca bertanggung jawab atas keputusan mereka sendiri.",
        "before": "Sebelum", "after": "Sesudah", "get_started": "Mulai Sekarang",
        "made_with": "Dibuat dengan Khova AI", "the_problem": "Masalahnya", "benefits": "Manfaat",
        "how_it_works": "Cara Kerjanya", "whats_included": "Apa yang Anda Dapatkan",
        "testimonials": "Kata Mereka", "testimonials_ph": "Testimoni akan tampil di sini.", "faq": "Tanya Jawab",
        "by": "oleh",
    },
    "en": {
        "chapter": "Chapter", "toc": "Table of Contents", "introduction": "Introduction",
        "bonus_kicker": "Bonus", "bonus_title": "Bonus Materials",
        "outcomes_intro": "What you'll master:", "no_content": "This section has not been written yet.",
        "copyright": "Copyright", "rights": "All rights reserved. This content is provided for educational purposes. While carefully prepared, readers are responsible for their own decisions.",
        "before": "Before", "after": "After", "get_started": "Get Started",
        "made_with": "Made with Khova AI", "the_problem": "The Problem", "benefits": "Benefits",
        "how_it_works": "How It Works", "whats_included": "What's Included",
        "testimonials": "What People Say", "testimonials_ph": "Testimonials will appear here.", "faq": "FAQ",
        "by": "by",
    },
    "es": {
        "chapter": "Capítulo", "toc": "Índice", "introduction": "Introducción",
        "bonus_kicker": "Bono", "bonus_title": "Materiales de Bono",
        "outcomes_intro": "Lo que dominarás:", "no_content": "Esta sección aún no ha sido escrita.",
        "copyright": "Derechos de autor", "rights": "Todos los derechos reservados. Este contenido se ofrece con fines educativos. El lector es responsable de sus propias decisiones.",
        "before": "Antes", "after": "Después", "get_started": "Empezar Ahora",
        "made_with": "Hecho con Khova AI", "the_problem": "El Problema", "benefits": "Beneficios",
        "how_it_works": "Cómo Funciona", "whats_included": "Qué Incluye",
        "testimonials": "Lo Que Dicen", "testimonials_ph": "Los testimonios aparecerán aquí.", "faq": "Preguntas Frecuentes",
        "by": "por",
    },
    "fr": {
        "chapter": "Chapitre", "toc": "Table des matières", "introduction": "Introduction",
        "bonus_kicker": "Bonus", "bonus_title": "Contenus Bonus",
        "outcomes_intro": "Ce que vous allez maîtriser :", "no_content": "Cette section n'a pas encore été rédigée.",
        "copyright": "Droits d'auteur", "rights": "Tous droits réservés. Ce contenu est fourni à des fins éducatives. Le lecteur reste responsable de ses propres décisions.",
        "before": "Avant", "after": "Après", "get_started": "Commencer",
        "made_with": "Créé avec Khova AI", "the_problem": "Le Problème", "benefits": "Avantages",
        "how_it_works": "Comment ça marche", "whats_included": "Ce qui est inclus",
        "testimonials": "Ce Qu'ils Disent", "testimonials_ph": "Les témoignages apparaîtront ici.", "faq": "FAQ",
        "by": "par",
    },
    "de": {
        "chapter": "Kapitel", "toc": "Inhaltsverzeichnis", "introduction": "Einführung",
        "bonus_kicker": "Bonus", "bonus_title": "Bonusmaterial",
        "outcomes_intro": "Das wirst du beherrschen:", "no_content": "Dieser Abschnitt wurde noch nicht geschrieben.",
        "copyright": "Urheberrecht", "rights": "Alle Rechte vorbehalten. Dieser Inhalt dient Bildungszwecken. Die Leser sind für ihre eigenen Entscheidungen verantwortlich.",
        "before": "Vorher", "after": "Nachher", "get_started": "Jetzt Starten",
        "made_with": "Erstellt mit Khova AI", "the_problem": "Das Problem", "benefits": "Vorteile",
        "how_it_works": "So funktioniert's", "whats_included": "Was enthalten ist",
        "testimonials": "Das Sagen Kunden", "testimonials_ph": "Erfahrungsberichte erscheinen hier.", "faq": "FAQ",
        "by": "von",
    },
    "pt": {
        "chapter": "Capítulo", "toc": "Índice", "introduction": "Introdução",
        "bonus_kicker": "Bônus", "bonus_title": "Materiais Bônus",
        "outcomes_intro": "O que você vai dominar:", "no_content": "Esta seção ainda não foi escrita.",
        "copyright": "Direitos de autor", "rights": "Todos os direitos reservados. Este conteúdo é fornecido para fins educacionais. O leitor é responsável por suas próprias decisões.",
        "before": "Antes", "after": "Depois", "get_started": "Comece Agora",
        "made_with": "Feito com Khova AI", "the_problem": "O Problema", "benefits": "Benefícios",
        "how_it_works": "Como Funciona", "whats_included": "O Que Está Incluído",
        "testimonials": "O Que Dizem", "testimonials_ph": "Os depoimentos aparecerão aqui.", "faq": "Perguntas Frequentes",
        "by": "por",
    },
    "ja": {
        "chapter": "第", "toc": "目次", "introduction": "はじめに",
        "bonus_kicker": "ボーナス", "bonus_title": "ボーナス資料",
        "outcomes_intro": "習得できること:", "no_content": "このセクションはまだ作成されていません。",
        "copyright": "著作権", "rights": "全著作権所有。本コンテンツは教育目的で提供されています。読者は自身の判断に責任を負います。",
        "before": "前", "after": "後", "get_started": "今すぐ始める",
        "made_with": "Khova AI で作成", "the_problem": "課題", "benefits": "メリット",
        "how_it_works": "仕組み", "whats_included": "含まれるもの",
        "testimonials": "お客様の声", "testimonials_ph": "お客様の声がここに表示されます。", "faq": "よくある質問",
        "by": "著者",
    },
}


def _labels(product_language: str) -> dict:
    return LABELS.get((product_language or "id").lower(), LABELS["en"])


FONT_STACKS = {
    "serif": "Georgia, 'Times New Roman', serif",
    "sans": "Helvetica, Arial, sans-serif",
    "modern": "Helvetica, Arial, sans-serif",
    "classic": "Georgia, 'Times New Roman', serif",
    "editorial": "Georgia, 'Times New Roman', serif",
}


def _palette(design_system, transformation):
    pal = dict(DEFAULT_PALETTE)
    ds = (design_system or {}) if isinstance(design_system, dict) else {}
    colors = ds.get("colors") or {}
    for k in ("primary", "secondary", "accent", "background", "text"):
        if colors.get(k):
            pal[k] = colors[k]
    # transformation palette overrides if present
    if transformation and isinstance(transformation.get("palette"), dict):
        for k, v in transformation["palette"].items():
            if v and k in pal:
                pal[k] = v
    return pal


def design_consistency_check(design_system, transformation):
    """Return a list of consistency findings (all elements use the palette)."""
    pal = _palette(design_system, transformation)
    checks = []
    for k in ("primary", "secondary", "accent", "background", "text"):
        val = pal.get(k, "")
        ok = isinstance(val, str) and val.startswith("#") and (len(val) in (4, 7))
        checks.append({"element": k, "hex": val, "valid": ok})
    return {"palette": pal, "checks": checks, "consistent": all(c["valid"] for c in checks)}


# ---------------------------------------------------------------------------
# EBOOK -> PDF
# ---------------------------------------------------------------------------
def build_ebook_html(ebook: dict, branding: dict, transformation: dict, cover_bytes: bytes = None,
                     cover_mime: str = "image/png", illustrations: dict = None, product_language: str = "id"):
    """illustrations: {chapter_num: (bytes, mime)}"""
    ebook = ebook or {}
    meta = ebook.get("meta", {}) or {}
    design_system = ebook.get("design_system", {}) or {}
    pal = _palette(design_system, transformation)
    L = _labels(product_language)
    heading_font = FONT_STACKS.get((design_system.get("typography") or "serif").lower(), FONT_STACKS["serif"])
    body_font = FONT_STACKS["sans"]

    title = _html.escape(meta.get("title") or (branding or {}).get("title") or "Digital Product")
    subtitle = _html.escape(meta.get("subtitle") or (branding or {}).get("subtitle") or "")
    author = _html.escape((branding or {}).get("author") or "")

    # TOC
    toc = ebook.get("toc", []) or []
    sections = {s.get("chapter_num"): s for s in (ebook.get("sections", []) or [])}
    toc_rows = ""
    for ch in toc:
        toc_rows += f'<div class="toc-row"><span class="toc-num">{ch.get("chapter_num","")}</span><span class="toc-title">{_html.escape(ch.get("title",""))}</span></div>'

    # Introduction
    intro_html = ebook.get("introduction_html", "")

    # Chapters
    chapters_html = ""
    illustrations = illustrations or {}
    for ch in toc:
        num = ch.get("chapter_num")
        sec = sections.get(num, {})
        content = sec.get("content_html", "") or f"<p><em>{L['no_content']}</em></p>"
        illo = ""
        if num in illustrations and illustrations[num][0]:
            ib, imime = illustrations[num]
            ib64 = base64.b64encode(ib).decode()
            illo = f'<div class="illo"><img src="data:{imime};base64,{ib64}" /></div>'
        dek = _html.escape(ch.get("purpose", "") or "")
        dek_html = f'<div class="chapter-dek">{dek}</div>' if dek else ""
        chapters_html += f'''
        <section class="chapter">
          <div class="chapter-head">
            <div class="chapter-num-badge">{num}</div>
            <div class="chapter-kicker">{L['chapter']} {num}</div>
            <h2>{_html.escape(ch.get("title",""))}</h2>
            {dek_html}
          </div>
          {illo}
          {content}
        </section>
        '''

    # Bonuses
    bonuses = meta.get("bonuses") or ebook.get("bonuses") or []
    bonuses_html = ""
    if bonuses:
        items = ""
        for b in bonuses:
            items += f'<div class="bonus"><h3>{_html.escape(b.get("title",""))}</h3><p>{_html.escape(b.get("description",""))}</p></div>'
        bonuses_html = f'<section class="chapter"><div class="chapter-head"><div class="chapter-kicker">{L["bonus_kicker"]}</div><h2>{L["bonus_title"]}</h2></div>{items}</section>'

    # Learning outcomes
    outcomes = meta.get("learning_outcomes") or []
    outcomes_html = ""
    if outcomes:
        lis = "".join([f"<li>{_html.escape(o)}</li>" for o in outcomes])
        outcomes_html = f'<div class="callout"><strong>{L["outcomes_intro"]}</strong><ul>{lis}</ul></div>'

    has_cover_img = bool(cover_bytes)

    css = f'''
    @page {{
        size: A4;
        margin: 2.4cm 2cm 2.4cm 2cm;
        @bottom-center {{ content: counter(page); color: {pal['secondary']}; font-family: {body_font}; font-size: 9.5px; }}
    }}
    @page :first {{ margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: {body_font}; color: {pal['text']}; font-size: 11.5pt; line-height: 1.65; orphans: 3; widows: 3; }}
    h1, h2, h3, h4 {{ font-family: {heading_font}; color: {pal['secondary']}; line-height: 1.2; page-break-after: avoid; }}
    p, li {{ orphans: 3; widows: 3; }}

    /* ---------- COVER (real designed cover, AI artwork + deterministic HTML typography) ---------- */
    .cover {{ height: 297mm; width: 100%; background: {pal['secondary']}; color: #fff; position: relative; page-break-after: always; overflow: hidden; }}
    .cover-bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
    .cover-scrim {{ position: absolute; inset: 0; background: {'linear-gradient(180deg, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.15) 45%, rgba(0,0,0,0.86) 100%)' if has_cover_img else f"linear-gradient(160deg, {pal['secondary']} 0%, {pal['primary']} 100%)"}; }}
    .cover-inner {{ position: absolute; inset: 0; padding: 24mm 20mm; display: flex; flex-direction: column; justify-content: flex-end; }}
    .cover .brandbar {{ height: 3mm; width: 32mm; background: {pal['accent']}; margin-bottom: 8mm; border-radius: 2px; }}
    .cover h1 {{ color: #fff; font-size: 30pt; margin: 0 0 5mm 0; line-height: 1.12; }}
    .cover .sub {{ color: rgba(255,255,255,0.88); font-size: 13.5pt; font-family: {body_font}; margin-bottom: 10mm; }}
    .cover .author {{ color: rgba(255,255,255,0.75); font-size: 10.5pt; font-family: {body_font}; text-transform: uppercase; letter-spacing: 1px; }}

    /* ---------- COLOPHON / copyright page ---------- */
    .page {{ page-break-after: always; }}
    .colophon {{ padding-top: 90mm; }}
    .colophon .ref-title {{ font-size: 11pt; color: {pal['primary']}; font-weight: 700; margin-bottom: 2mm; }}
    .disclaimer {{ font-size: 9.5pt; color: #6b6f76; margin-top: 8mm; border-top: 1px solid {pal['accent']}; padding-top: 6mm; max-width: 120mm; }}

    /* ---------- TOC ---------- */
    .toc-title-h {{ color: {pal['primary']}; border-bottom: 2px solid {pal['accent']}; padding-bottom: 3mm; margin-bottom: 6mm; }}
    .toc-row {{ display: flex; padding: 2.6mm 0; border-bottom: 1px dotted #ccc; }}
    .toc-num {{ color: {pal['accent']}; font-weight: 700; width: 12mm; }}
    .toc-title {{ color: {pal['text']}; }}

    /* ---------- CHAPTER OPENER ---------- */
    .chapter {{ page-break-before: always; }}
    .chapter-head {{ margin-bottom: 8mm; padding-bottom: 5mm; border-bottom: 1.5px solid {pal['border'] if pal.get('border') else '#E6E2D8'}; position: relative; }}
    .chapter-num-badge {{ position: absolute; top: -2mm; right: 0; font-family: {heading_font}; font-size: 30pt; font-weight: 700; color: {pal['accent']}; opacity: 0.22; line-height: 1; }}
    .chapter-kicker {{ text-transform: uppercase; letter-spacing: 2px; font-size: 9pt; color: {pal['accent']}; font-weight: 700; }}
    .chapter h2 {{ font-size: 21pt; margin: 2mm 0 0 0; max-width: 85%; }}
    .chapter-dek {{ font-size: 11pt; color: {pal['muted'] if pal.get('muted') else '#6b6f76'}; margin-top: 2mm; font-style: italic; max-width: 90%; }}
    .chapter h3 {{ font-size: 13pt; color: {pal['primary']}; margin-top: 7mm; margin-bottom: 2mm; }}
    .chapter h4 {{ font-size: 11.5pt; color: {pal['secondary']}; margin: 0 0 2mm 0; }}
    .illo {{ page-break-inside: avoid; margin: 5mm 0 6mm 0; text-align: center; }}
    .illo img {{ width: 100%; max-height: 100mm; object-fit: contain; background: #fff; border: 1px solid {pal['border'] if pal.get('border') else '#E6E2D8'}; border-radius: 6px; padding: 4mm; }}
    p {{ margin: 0 0 3.2mm 0; }}
    ul, ol {{ margin: 0 0 3.2mm 5mm; }}

    /* ---------- TABLES ---------- */
    table {{ width: 100%; border-collapse: collapse; margin: 4.5mm 0; font-size: 10.5pt; page-break-inside: auto; }}
    tr {{ page-break-inside: avoid; }}
    th {{ background: {pal['primary']}; color: #fff; text-align: left; padding: 2.6mm 3mm; }}
    td {{ border: 1px solid {pal['border'] if pal.get('border') else '#E6E2D8'}; padding: 2.4mm 3mm; }}
    tr:nth-child(even) td {{ background: #f6f4ee; }}

    /* ---------- EDITORIAL BLOCKS (varied weight, not repeated "colored box" spam) ---------- */
    .callout {{ background: {pal['background']}; border-left: 3px solid {pal['primary']}; padding: 4mm 5mm; margin: 5mm 0; page-break-inside: avoid; }}
    .pullquote {{ font-family: {heading_font}; font-style: italic; font-size: 15pt; color: {pal['primary']}; text-align: center; border-top: 1px solid {pal['accent']}; border-bottom: 1px solid {pal['accent']}; padding: 5mm 8mm; margin: 7mm 6mm; line-height: 1.4; page-break-inside: avoid; }}
    .example {{ background: #fff; border: 1px solid {pal['border'] if pal.get('border') else '#E6E2D8'}; border-left: 3px solid {pal['accent']}; padding: 4mm 5mm; border-radius: 3px; margin: 5mm 0; page-break-inside: avoid; }}
    .example h4 {{ margin-top: 0; }}
    .action-steps {{ background: #f7f8f9; border: 1px solid #e2e5e9; padding: 4.5mm 5.5mm; border-radius: 6px; margin: 5mm 0; page-break-inside: avoid; }}
    .exercise {{ background: #fff; border: 1.4px dashed {pal['primary']}; padding: 4.5mm 5.5mm; border-radius: 6px; margin: 5mm 0; page-break-inside: avoid; }}
    .answer-guide {{ background: {pal['background']}; border-radius: 4px; padding: 3mm 4mm; margin-top: 3mm; font-size: 10.2pt; }}
    .summary {{ background: {pal['secondary']}; color: #fff; padding: 4.5mm 5.5mm; border-radius: 6px; margin: 6mm 0 0 0; page-break-inside: avoid; }}
    .summary h4 {{ color: #fff; margin-top: 0; }}
    .bonus {{ border: 1px solid {pal['border'] if pal.get('border') else '#E6E2D8'}; border-radius: 6px; padding: 4mm 5mm; margin-bottom: 4mm; page-break-inside: avoid; }}
    .bonus h3 {{ color: {pal['primary']}; margin: 0 0 2mm 0; }}

    /* ---------- MATH NOTATION (reliable HTML/CSS-based; inline-block, NOT flexbox — WeasyPrint's
       flexbox support is unreliable for inline-flex and breaks fractions onto separate lines) ---------- */
    .equation {{ text-align: center; margin: 5mm 0; font-size: 13pt; }}
    .frac {{ display: inline-block; vertical-align: middle; text-align: center; margin: 0 2px; line-height: 1.05; }}
    .frac .num {{ display: block; padding: 0 2px 1px 2px; border-bottom: 1.3px solid currentColor; }}
    .frac .den {{ display: block; padding: 1px 2px 0 2px; }}
    .sqrt {{ display: inline-block; padding: 0 2px; border-top: 1.3px solid currentColor; position: relative; }}
    .sqrt:before {{ content: '\\221A'; margin-right: 1px; }}
    sup, sub {{ font-size: 75%; }}

    /* Screen-only "paper" look for the on-screen preview (ignored by WeasyPrint PDF print rendering) */
    @media screen {{
        body {{ background: #e9e7e2; padding: 32px 0 60px; }}
        .cover, .page, .chapter {{
            max-width: 210mm; margin: 0 auto 28px auto;
            box-shadow: 0 12px 36px rgba(0,0,0,0.16); padding: 20mm 18mm; border-radius: 3px;
        }}
        .page, .chapter {{ background: {pal['background']}; }}
        .cover {{ height: auto; min-height: 297mm; padding: 0; }}
        .cover-inner {{ padding: 24mm 20mm; height: 100%; min-height: 297mm; }}
        .page {{ min-height: 237mm; }}
        .chapter {{ min-height: auto; }}
    }}
    '''

    cover_visual = f'<img class="cover-bg" src="data:{cover_mime};base64,{base64.b64encode(cover_bytes).decode()}" />' if cover_bytes else ""

    doc = f'''<!DOCTYPE html><html lang="{product_language}"><head><meta charset="utf-8"><style>{css}</style></head><body>
      <div class="cover">
        {cover_visual}
        <div class="cover-scrim"></div>
        <div class="cover-inner">
          <div class="brandbar"></div>
          <h1>{title}</h1>
          <div class="sub">{subtitle}</div>
          <div class="author">{(L["by"] + " " + author) if author else ""}</div>
        </div>
      </div>

      <div class="page colophon">
        <div class="ref-title">{title}</div>
        <div class="disclaimer">
          <p><strong>{title}</strong>{(" — " + author) if author else ""}</p>
          <p>{L['copyright']} &copy; {author or title}. {L['rights']}</p>
        </div>
      </div>

      <div class="page">
        <h2 class="toc-title-h">{L['toc']}</h2>
        {toc_rows}
      </div>

      <section class="chapter">
        <div class="chapter-head"><div class="chapter-kicker">{L['introduction']}</div><h2>{L['introduction']}</h2></div>
        {outcomes_html}
        {intro_html}
      </section>

      {chapters_html}
      {bonuses_html}
    </body></html>'''
    return doc


def html_to_pdf(html_string: str) -> bytes:
    from weasyprint import HTML
    buf = BytesIO()
    HTML(string=html_string).write_pdf(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# SPREADSHEET -> XLSX
# ---------------------------------------------------------------------------
def _col_letter(idx):
    from openpyxl.utils import get_column_letter
    return get_column_letter(idx)


def build_xlsx(spec: dict, palette: dict = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    pal = palette or DEFAULT_PALETTE
    primary = (pal.get("primary") or "#0B6E6B").lstrip("#")
    accent = (pal.get("accent") or "#C07A2B").lstrip("#")

    wb = Workbook()
    default = wb.active
    wb.remove(default)

    header_fill = PatternFill(start_color=primary, end_color=primary, fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    title_font = Font(bold=True, size=14, color=primary)
    thin = Side(style="thin", color="D9D9D9")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    sheets = spec.get("sheets", []) or []
    if not sheets:
        sheets = [{"name": "Sheet1", "purpose": spec.get("concept", ""), "columns": [], "example_rows": []}]

    used_names = set()
    for sheet in sheets:
        raw_name = (sheet.get("name") or "Sheet")[:31]
        name = raw_name
        i = 1
        while name in used_names or not name:
            name = f"{raw_name[:28]}_{i}"
            i += 1
        used_names.add(name)
        ws = wb.create_sheet(title=name)

        row = 1
        # Title + instructions
        ws.cell(row=row, column=1, value=sheet.get("name", "")).font = title_font
        row += 1
        if sheet.get("purpose"):
            ws.cell(row=row, column=1, value=sheet["purpose"])
            row += 1
        if sheet.get("instructions"):
            c = ws.cell(row=row, column=1, value=sheet["instructions"])
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.font = Font(italic=True, color="5B6472")
            row += 2
        else:
            row += 1

        columns = sheet.get("columns", []) or []
        if not columns:
            ws.column_dimensions["A"].width = 60
            continue

        header_row = row
        for cidx, col in enumerate(columns, start=1):
            cell = ws.cell(row=header_row, column=cidx, value=col.get("header", f"Col{cidx}"))
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
            letter = _col_letter(cidx)
            ws.column_dimensions[letter].width = max(14, min(40, len(str(col.get("header", ""))) + 8))

        # Example rows
        example_rows = sheet.get("example_rows", []) or []
        data_start = header_row + 1
        r = data_start
        for erow in example_rows:
            values = erow if isinstance(erow, list) else list((erow or {}).values())
            for cidx, col in enumerate(columns, start=1):
                letter = _col_letter(cidx)
                if col.get("type") == "formula" and col.get("formula_template"):
                    formula = col["formula_template"].replace("{r}", str(r))
                    ws.cell(row=r, column=cidx, value=formula).border = border
                else:
                    val = values[cidx - 1] if cidx - 1 < len(values) else None
                    cell = ws.cell(row=r, column=cidx, value=val)
                    cell.border = border
                    if col.get("type") == "currency" and isinstance(val, (int, float)):
                        cell.number_format = '#,##0'
                    elif col.get("type") == "percent" and isinstance(val, (int, float)):
                        cell.number_format = '0%'
            r += 1
        data_end = max(data_start, r - 1)

        # add a few empty formula rows so the tool is usable
        if any(col.get("type") == "formula" for col in columns) or example_rows:
            for extra in range(3):
                for cidx, col in enumerate(columns, start=1):
                    if col.get("type") == "formula" and col.get("formula_template"):
                        formula = col["formula_template"].replace("{r}", str(r))
                        ws.cell(row=r, column=cidx, value=formula).border = border
                    else:
                        ws.cell(row=r, column=cidx).border = border
                r += 1
            data_end = r - 1

        # Dropdowns / data validation
        for cidx, col in enumerate(columns, start=1):
            opts = col.get("dropdown")
            if opts and isinstance(opts, list):
                letter = _col_letter(cidx)
                formula1 = '"' + ",".join([str(o).replace('"', "'") for o in opts])[:250] + '"'
                dv = DataValidation(type="list", formula1=formula1, allow_blank=True)
                ws.add_data_validation(dv)
                dv.add(f"{letter}{data_start}:{letter}{data_end + 5}")

        # Totals
        totals = sheet.get("totals", []) or []
        if totals:
            r += 1
            for t in totals:
                col_index = t.get("col_index", 1)
                ws.cell(row=r, column=1, value=t.get("label", "Total")).font = Font(bold=True)
                formula = (t.get("formula", "") or "").replace("{first}", str(data_start)).replace("{last}", str(data_end))
                if formula:
                    cell = ws.cell(row=r, column=col_index, value=formula)
                    cell.font = Font(bold=True, color=accent)
                r += 1

        ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# WEBSITE -> standalone HTML
# ---------------------------------------------------------------------------
STYLE_PRESETS = {
    "Minimal": {"radius": "6px", "shadow": "0 1px 2px rgba(0,0,0,0.06)", "hero_pad": "80px"},
    "Modern": {"radius": "16px", "shadow": "0 20px 45px rgba(0,0,0,0.10)", "hero_pad": "110px"},
    "Premium": {"radius": "20px", "shadow": "0 30px 60px rgba(0,0,0,0.14)", "hero_pad": "130px"},
    "Editorial": {"radius": "2px", "shadow": "0 1px 0 rgba(0,0,0,0.10)", "hero_pad": "90px"},
    "Bold": {"radius": "12px", "shadow": "0 24px 50px rgba(0,0,0,0.18)", "hero_pad": "120px"},
}


def build_website_html(spec: dict, palette: dict = None, style: str = "Modern", product_language: str = "id") -> str:
    spec = spec or {}
    pal = palette or DEFAULT_PALETTE
    L = _labels(product_language)
    primary = pal.get("primary", "#0B6E6B")
    secondary = pal.get("secondary", "#111C2E")
    accent = pal.get("accent", "#C07A2B")
    bg = pal.get("background", "#FBFAF7")
    text = pal.get("text", "#0B1220")
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["Modern"])

    def esc(x):
        return _html.escape(str(x or ""))

    hero = spec.get("hero", {})
    problem = spec.get("problem", {})
    transformation = spec.get("transformation", {})
    benefits = spec.get("benefits", {})
    included = spec.get("whats_included", {})
    how = spec.get("how_it_works", {})
    social = spec.get("social_proof", {})
    faq = spec.get("faq", {})
    final_cta = spec.get("final_cta", {})
    brand = spec.get("brand", hero.get("headline", "Product"))

    def li_list(items):
        return "".join([f"<li>{esc(i)}</li>" for i in (items or [])])

    benefit_cards = "".join([
        f'<div class="card"><h3>{esc(b.get("title"))}</h3><p>{esc(b.get("desc"))}</p></div>'
        for b in (benefits.get("items") or [])
    ])
    step_cards = "".join([
        f'<div class="step"><div class="step-n">{i+1}</div><div><h3>{esc(s.get("title"))}</h3><p>{esc(s.get("desc"))}</p></div></div>'
        for i, s in enumerate(how.get("steps") or [])
    ])
    faq_items = "".join([
        f'<details><summary>{esc(f.get("q"))}</summary><p>{esc(f.get("a"))}</p></details>'
        for f in (faq.get("items") or [])
    ])
    before_list = li_list(transformation.get("before"))
    after_list = li_list(transformation.get("after"))
    included_list = li_list(included.get("items"))

    return f'''<!DOCTYPE html>
<html lang="{product_language}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(brand)}</title>
<style>
  :root {{ --primary:{primary}; --secondary:{secondary}; --accent:{accent}; --bg:{bg}; --text:{text}; --radius:{preset['radius']}; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; color:var(--text); background:var(--bg); line-height:1.65; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:0 24px; }}
  .btn {{ display:inline-block; background:var(--primary); color:#fff; padding:15px 30px; border-radius:var(--radius); text-decoration:none; font-weight:700; box-shadow:{preset['shadow']}; }}
  .btn.alt {{ background:var(--accent); }}
  header.hero {{ background:var(--secondary); color:#fff; padding:{preset['hero_pad']} 0; }}
  header.hero h1 {{ font-size:clamp(30px,5vw,52px); line-height:1.1; margin-bottom:18px; }}
  header.hero p {{ font-size:20px; opacity:.9; max-width:640px; margin-bottom:30px; }}
  .brandbar {{ display:inline-block; font-weight:800; letter-spacing:1px; color:var(--accent); margin-bottom:18px; text-transform:uppercase; font-size:14px; }}
  section {{ padding:72px 0; }}
  section h2 {{ font-size:clamp(24px,3.5vw,36px); margin-bottom:26px; color:var(--secondary); }}
  .muted {{ background:#fff; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:22px; }}
  .card {{ background:#fff; border:1px solid #e6e2d8; border-radius:var(--radius); padding:26px; box-shadow:{preset['shadow']}; }}
  .card h3 {{ color:var(--primary); margin-bottom:8px; }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr; gap:24px; }}
  .ba {{ background:#fff; border-radius:var(--radius); padding:26px; border:1px solid #e6e2d8; }}
  .ba.before {{ border-top:5px solid #B42318; }}
  .ba.after {{ border-top:5px solid var(--primary); }}
  .ba h3 {{ margin-bottom:12px; }}
  ul {{ margin-left:20px; }} li {{ margin-bottom:8px; }}
  .step {{ display:flex; gap:16px; align-items:flex-start; margin-bottom:18px; }}
  .step-n {{ background:var(--primary); color:#fff; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-weight:800; flex:0 0 auto; }}
  details {{ background:#fff; border:1px solid #e6e2d8; border-radius:var(--radius); padding:16px 20px; margin-bottom:12px; }}
  summary {{ font-weight:700; cursor:pointer; color:var(--secondary); }}
  details p {{ margin-top:10px; color:#5b6472; }}
  .cta-band {{ background:var(--primary); color:#fff; text-align:center; }}
  .cta-band h2 {{ color:#fff; }}
  .social {{ background:#fff; border:1px dashed #cbd5c9; border-radius:var(--radius); padding:30px; text-align:center; color:#5b6472; }}
  footer {{ padding:30px 0; text-align:center; color:#8a8f98; font-size:14px; }}
  @media (max-width:720px) {{ .cols {{ grid-template-columns:1fr; }} }}
</style></head>
<body>
  <header class="hero"><div class="wrap">
    <span class="brandbar">{esc(brand)}</span>
    <h1>{esc(hero.get("headline"))}</h1>
    <p>{esc(hero.get("subheadline"))}</p>
    <a class="btn alt" href="#cta">{esc(hero.get("cta") or L["get_started"])}</a>
  </div></header>

  <section class="muted"><div class="wrap">
    <h2>{esc(problem.get("title") or L["the_problem"])}</h2>
    <p style="max-width:720px;margin-bottom:16px;">{esc(problem.get("body"))}</p>
    <ul>{li_list(problem.get("bullets"))}</ul>
  </div></section>

  <section><div class="wrap">
    <h2>{esc(transformation.get("title") or L["how_it_works"])}</h2>
    <div class="cols">
      <div class="ba before"><h3>{L["before"]}</h3><ul>{before_list}</ul></div>
      <div class="ba after"><h3>{L["after"]}</h3><ul>{after_list}</ul></div>
    </div>
  </div></section>

  <section class="muted"><div class="wrap">
    <h2>{esc(benefits.get("title") or L["benefits"])}</h2>
    <div class="grid">{benefit_cards}</div>
  </div></section>

  <section><div class="wrap">
    <h2>{esc(included.get("title") or L["whats_included"])}</h2>
    <ul>{included_list}</ul>
  </div></section>

  <section class="muted"><div class="wrap">
    <h2>{esc(how.get("title") or L["how_it_works"])}</h2>
    {step_cards}
  </div></section>

  <section><div class="wrap">
    <h2>{esc(social.get("title") or L["testimonials"])}</h2>
    <div class="social">{esc(social.get("placeholder") or L["testimonials_ph"])}</div>
  </div></section>

  <section class="muted"><div class="wrap">
    <h2>{esc(faq.get("title") or L["faq"])}</h2>
    {faq_items}
  </div></section>

  <section class="cta-band" id="cta"><div class="wrap">
    <h2>{esc(final_cta.get("headline") or hero.get("headline"))}</h2>
    <p style="margin-bottom:26px;opacity:.9;">{esc(hero.get("subheadline"))}</p>
    <a class="btn alt" href="#">{esc(final_cta.get("cta") or L["get_started"])}</a>
  </div></section>

  <footer><div class="wrap">&copy; {esc(brand)} — {L["made_with"]}</div></footer>
</body></html>'''
