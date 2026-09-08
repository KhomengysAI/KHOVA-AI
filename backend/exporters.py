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
                     cover_mime: str = "image/png", illustrations: dict = None):
    """illustrations: {chapter_num: (bytes, mime)}"""
    ebook = ebook or {}
    meta = ebook.get("meta", {}) or {}
    design_system = ebook.get("design_system", {}) or {}
    pal = _palette(design_system, transformation)
    heading_font = FONT_STACKS.get((design_system.get("typography") or "serif").lower(), FONT_STACKS["serif"])
    body_font = FONT_STACKS["sans"]

    title = _html.escape(meta.get("title") or (branding or {}).get("title") or "Digital Product")
    subtitle = _html.escape(meta.get("subtitle") or (branding or {}).get("subtitle") or "")
    author = _html.escape((branding or {}).get("author") or "")

    cover_img = ""
    if cover_bytes:
        b64 = base64.b64encode(cover_bytes).decode()
        cover_img = f'<img class="cover-img" src="data:{cover_mime};base64,{b64}" />'

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
        content = sec.get("content_html", "") or "<p><em>Bagian ini belum dibuat.</em></p>"
        illo = ""
        if num in illustrations and illustrations[num][0]:
            ib, imime = illustrations[num]
            ib64 = base64.b64encode(ib).decode()
            illo = f'<div class="illo"><img src="data:{imime};base64,{ib64}" /></div>'
        chapters_html += f'''
        <section class="chapter">
          <div class="chapter-head">
            <div class="chapter-kicker">Bab {num}</div>
            <h2>{_html.escape(ch.get("title",""))}</h2>
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
        bonuses_html = f'<section class="chapter"><div class="chapter-head"><div class="chapter-kicker">Bonus</div><h2>Materi Bonus</h2></div>{items}</section>'

    # Learning outcomes
    outcomes = meta.get("learning_outcomes") or []
    outcomes_html = ""
    if outcomes:
        lis = "".join([f"<li>{_html.escape(o)}</li>" for o in outcomes])
        outcomes_html = f'<div class="callout"><strong>Yang akan Anda kuasai:</strong><ul>{lis}</ul></div>'

    css = f'''
    @page {{
        size: A4;
        margin: 2.2cm 2cm 2.4cm 2cm;
        @bottom-center {{ content: counter(page); color: {pal['secondary']}; font-family: {body_font}; font-size: 10px; }}
    }}
    @page :first {{ margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: {body_font}; color: {pal['text']}; font-size: 11.5pt; line-height: 1.6; }}
    h1, h2, h3, h4 {{ font-family: {heading_font}; color: {pal['secondary']}; line-height: 1.2; }}
    .cover {{ height: 297mm; width: 100%; background: {pal['primary']}; color: #fff; position: relative; page-break-after: always; }}
    .cover-inner {{ position: absolute; inset: 0; padding: 30mm 22mm; display: flex; flex-direction: column; }}
    .cover-img {{ width: 100%; height: 150mm; object-fit: cover; border-radius: 6px; margin-bottom: 14mm; }}
    .cover h1 {{ color: #fff; font-size: 34pt; margin: 0 0 6mm 0; }}
    .cover .sub {{ color: rgba(255,255,255,0.9); font-size: 15pt; font-family: {body_font}; }}
    .cover .author {{ margin-top: auto; color: rgba(255,255,255,0.9); font-size: 12pt; font-family: {body_font}; }}
    .cover .brandbar {{ height: 4mm; width: 40mm; background: {pal['accent']}; margin-bottom: 10mm; }}
    .page {{ page-break-after: always; }}
    .title-page {{ padding-top: 40mm; }}
    .title-page h1 {{ font-size: 26pt; color: {pal['secondary']}; }}
    .title-page .sub {{ font-size: 14pt; color: {pal['primary']}; }}
    .disclaimer {{ font-size: 9.5pt; color: #555; margin-top: 60mm; border-top: 1px solid {pal['accent']}; padding-top: 6mm; }}
    .toc-title-h {{ color: {pal['primary']}; border-bottom: 2px solid {pal['accent']}; padding-bottom: 3mm; }}
    .toc-row {{ display: flex; padding: 2.4mm 0; border-bottom: 1px dotted #ccc; }}
    .toc-num {{ color: {pal['accent']}; font-weight: 700; width: 12mm; }}
    .toc-title {{ color: {pal['text']}; }}
    .chapter {{ page-break-before: always; }}
    .chapter-head {{ margin-bottom: 6mm; border-bottom: 2px solid {pal['primary']}; padding-bottom: 3mm; }}
    .chapter-kicker {{ text-transform: uppercase; letter-spacing: 2px; font-size: 9pt; color: {pal['accent']}; font-weight: 700; }}
    .chapter h2 {{ font-size: 20pt; margin: 2mm 0 0 0; }}
    .chapter h3 {{ font-size: 13pt; color: {pal['primary']}; margin-top: 6mm; }}
    .chapter h4 {{ font-size: 11.5pt; color: {pal['secondary']}; margin: 0 0 2mm 0; }}
    .illo img {{ width: 100%; max-height: 110mm; object-fit: cover; border-radius: 6px; margin-bottom: 5mm; }}
    p {{ margin: 0 0 3mm 0; }}
    ul, ol {{ margin: 0 0 3mm 5mm; }}
    table {{ width: 100%; border-collapse: collapse; margin: 4mm 0; font-size: 10.5pt; }}
    th {{ background: {pal['primary']}; color: #fff; text-align: left; padding: 2.4mm 3mm; }}
    td {{ border: 1px solid {pal['border'] if pal.get('border') else '#E6E2D8'}; padding: 2.2mm 3mm; }}
    tr:nth-child(even) td {{ background: #f6f4ee; }}
    .callout {{ background: #eef7f6; border-left: 4px solid {pal['primary']}; padding: 4mm 5mm; border-radius: 4px; margin: 4mm 0; }}
    .example {{ background: #faf1e6; border-left: 4px solid {pal['accent']}; padding: 4mm 5mm; border-radius: 4px; margin: 4mm 0; }}
    .action-steps {{ background: #f4f6f8; border: 1px solid #dfe3e8; padding: 4mm 5mm; border-radius: 6px; margin: 4mm 0; }}
    .exercise {{ background: #fff; border: 1.5px dashed {pal['primary']}; padding: 4mm 5mm; border-radius: 6px; margin: 4mm 0; }}
    .summary {{ background: {pal['secondary']}; color: #fff; padding: 4mm 5mm; border-radius: 6px; margin: 5mm 0; }}
    .summary h4 {{ color: #fff; }}
    .bonus {{ border: 1px solid #e6e2d8; border-radius: 6px; padding: 4mm 5mm; margin-bottom: 4mm; }}
    .bonus h3 {{ color: {pal['primary']}; margin: 0 0 2mm 0; }}
    '''

    doc = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head><body>
      <div class="cover"><div class="cover-inner">
        <div class="brandbar"></div>
        {cover_img}
        <h1>{title}</h1>
        <div class="sub">{subtitle}</div>
        <div class="author">{("oleh " + author) if author else ""}</div>
      </div></div>

      <div class="page title-page">
        <h1>{title}</h1>
        <div class="sub">{subtitle}</div>
        <div class="disclaimer">
          <p><strong>{title}</strong>{(" — " + author) if author else ""}</p>
          <p>Hak Cipta &copy; {author or title}. Semua hak dilindungi. Konten ini disediakan untuk tujuan edukasi.
          Meskipun disusun dengan cermat, pembaca bertanggung jawab atas keputusan mereka sendiri.</p>
        </div>
      </div>

      <div class="page">
        <h2 class="toc-title-h">Daftar Isi</h2>
        {toc_rows}
      </div>

      <section class="chapter">
        <div class="chapter-head"><div class="chapter-kicker">Pendahuluan</div><h2>Pendahuluan</h2></div>
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


def build_website_html(spec: dict, palette: dict = None, style: str = "Modern") -> str:
    spec = spec or {}
    pal = palette or DEFAULT_PALETTE
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
<html lang="id"><head><meta charset="utf-8">
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
    <a class="btn alt" href="#cta">{esc(hero.get("cta") or "Get Started")}</a>
  </div></header>

  <section class="muted"><div class="wrap">
    <h2>{esc(problem.get("title") or "The Problem")}</h2>
    <p style="max-width:720px;margin-bottom:16px;">{esc(problem.get("body"))}</p>
    <ul>{li_list(problem.get("bullets"))}</ul>
  </div></section>

  <section><div class="wrap">
    <h2>{esc(transformation.get("title") or "Your Transformation")}</h2>
    <div class="cols">
      <div class="ba before"><h3>Sebelum</h3><ul>{before_list}</ul></div>
      <div class="ba after"><h3>Sesudah</h3><ul>{after_list}</ul></div>
    </div>
  </div></section>

  <section class="muted"><div class="wrap">
    <h2>{esc(benefits.get("title") or "Benefits")}</h2>
    <div class="grid">{benefit_cards}</div>
  </div></section>

  <section><div class="wrap">
    <h2>{esc(included.get("title") or "What's Included")}</h2>
    <ul>{included_list}</ul>
  </div></section>

  <section class="muted"><div class="wrap">
    <h2>{esc(how.get("title") or "How It Works")}</h2>
    {step_cards}
  </div></section>

  <section><div class="wrap">
    <h2>{esc(social.get("title") or "What People Say")}</h2>
    <div class="social">{esc(social.get("placeholder") or "Testimonials will appear here.")}</div>
  </div></section>

  <section class="muted"><div class="wrap">
    <h2>{esc(faq.get("title") or "FAQ")}</h2>
    {faq_items}
  </div></section>

  <section class="cta-band" id="cta"><div class="wrap">
    <h2>{esc(final_cta.get("headline") or hero.get("headline"))}</h2>
    <p style="margin-bottom:26px;opacity:.9;">{esc(hero.get("subheadline"))}</p>
    <a class="btn alt" href="#">{esc(final_cta.get("cta") or "Get Started")}</a>
  </div></section>

  <footer><div class="wrap">&copy; {esc(brand)} — Dibuat dengan Khova AI</div></footer>
</body></html>'''
