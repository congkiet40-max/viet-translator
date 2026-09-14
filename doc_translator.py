#!/usr/bin/env python3
"""
doc_translator.py - Bộ dịch PDF/DOCX Siêu Nhẹ & Siêu Tốc (Lightweight & Fast)
v6.0 - 0% Heavy PyTorch, 100% Fast Vector PDF Translation into Vietnamese
"""
import os, sys, re, io, json, time
import urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
import pymupdf
from docx import Document

# ─── TRANSLATION ENGINE (GTX + MyMemory Fallback) ────────────────────────────
_trans_cache: dict = {}

def _skip(text: str) -> bool:
    t = text.strip()
    if not t or len(t) < 2:
        return True
    if t.isdigit() or re.match(r'^\d{1,4}(-\d{1,4})?$', t):
        return True
    # Chord symbol
    if len(t) <= 7 and re.match(r'^[A-G][b#]?(maj7?|min7?|m7?|dim7?|aug|sus[24]?|add\d|7|9|11|13)?(\/[A-G][b#]?)?$', t, re.I):
        return True
    if all(c in '©®™°•·-–—_|/\\' for c in t):
        return True
    return False

def translate_text_fast(text: str, target: str = 'vi') -> str:
    text_clean = text.strip()
    if _skip(text_clean):
        return text
    if text_clean in _trans_cache:
        return _trans_cache[text_clean]

    result = text
    # 1. Try Google GTX
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target}&dt=t&q={urllib.parse.quote(text_clean)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as r:
            res = json.loads(r.read().decode('utf-8'))
            tr = "".join([item[0] for item in res[0] if item and item[0]])
            if tr.strip() and tr.strip() != text_clean:
                result = tr.strip()
    except Exception:
        pass

    # 2. If GTX failed or returned original text, fallback to MyMemory
    if result == text:
        try:
            from deep_translator import MyMemoryTranslator
            tr = MyMemoryTranslator(source='en-US', target='vi-VN').translate(text_clean[:5000])
            if tr and tr.strip():
                result = tr.strip()
        except Exception:
            pass

    _trans_cache[text_clean] = result
    return result

def batch_translate(texts: list, target: str = 'vi') -> list:
    if not texts:
        return []
    results = [None] * len(texts)
    for i, t in enumerate(texts):
        results[i] = translate_text_fast(t, target=target)
    return results

# ─── FONT SETUP ──────────────────────────────────────────────────────────────
_FONT_VARIANTS = {
    'regular':     '/usr/share/fonts/google-carlito-fonts/Carlito-Regular.ttf',
    'bold':        '/usr/share/fonts/google-carlito-fonts/Carlito-Bold.ttf',
    'italic':      '/usr/share/fonts/google-carlito-fonts/Carlito-Italic.ttf',
    'bold_italic': '/usr/share/fonts/google-carlito-fonts/Carlito-BoldItalic.ttf',
}
_FALLBACK_FONTS = {
    'regular':     '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf',
    'bold':        '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf',
    'italic':      '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Oblique.ttf',
    'bold_italic': '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-BoldOblique.ttf',
}
for k, v in list(_FONT_VARIANTS.items()):
    if not os.path.exists(v):
        _FONT_VARIANTS[k] = _FALLBACK_FONTS[k]

_font_cache: dict = {}

def get_font(size: int, bold=False, italic=False) -> ImageFont.FreeTypeFont:
    key = (max(size, 6), bold, italic)
    if key not in _font_cache:
        v = 'bold_italic' if bold and italic else 'bold' if bold else 'italic' if italic else 'regular'
        try:
            _font_cache[key] = ImageFont.truetype(_FONT_VARIANTS[v], key[0])
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]

def sample_bg(img: Image.Image, x0, y0, x1, y1) -> tuple:
    try:
        w, h = img.size
        xi0, yi0 = max(0, int(x0)), max(0, int(y0))
        xi1, yi1 = min(w - 1, int(x1)), min(h - 1, int(y1))
        if xi0 >= xi1 or yi0 >= yi1:
            return (255, 255, 255)
        px = img.load()
        samples = []
        strip_y = max(0, yi0 - 1)
        for x in range(xi0, min(xi1, xi0 + 20)):
            p = px[x, strip_y]
            samples.append(p[:3] if len(p) >= 3 else (255, 255, 255))
        for cx, cy in [(xi0, yi0), (xi1, yi0), (xi0, yi1), (xi1, yi1)]:
            cx, cy = max(0, min(cx, w-1)), max(0, min(cy, h-1))
            p = px[cx, cy]
            samples.append(p[:3] if len(p) >= 3 else (255, 255, 255))
        if not samples:
            return (255, 255, 255)
        return tuple(sum(c[i] for c in samples) // len(samples) for i in range(3))
    except Exception:
        return (255, 255, 255)

def wrap_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, max_width: float) -> list:
    words = text.split()
    if not words:
        return ['']
    lines = []
    current = words[0]
    for word in words[1:]:
        test = current + ' ' + word
        if draw.textlength(test, font=font) <= max_width:
            current = test
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines

def draw_translated_block(draw, img, x0, y0, x1, y1, trans_text, orig_size, bold, italic, rgb, line_height):
    bbox_w = x1 - x0
    if bbox_w <= 0:
        return
    font = get_font(orig_size, bold=bold, italic=italic)
    text_w = draw.textlength(trans_text, font=font)
    if text_w <= bbox_w * 1.05:
        bg = sample_bg(img, x0, y0, x1, y1)
        draw.rectangle([x0 - 1, y0, x1 + 1, y1 + 1], fill=bg)
        draw.text((x0, y0), trans_text, fill=rgb, font=font)
        return

    wrapped = wrap_text(draw, trans_text, font, bbox_w * 1.02)
    line_h = line_height
    if len(wrapped) <= 3:
        total_h = line_h * len(wrapped)
        bg = sample_bg(img, x0, y0, x1, y0 + total_h + 2)
        draw.rectangle([x0 - 1, y0, x1 + 1, y0 + total_h + 2], fill=bg)
        for i, wline in enumerate(wrapped):
            draw.text((x0, y0 + i * line_h), wline, fill=rgb, font=font)
        return

    shrunk_size = max(int(orig_size * bbox_w / text_w) - 1, 6)
    font = get_font(shrunk_size, bold=bold, italic=italic)
    bg = sample_bg(img, x0, y0, x1, y1)
    draw.rectangle([x0 - 1, y0, x1 + 1, y1 + 1], fill=bg)
    draw.text((x0, y0), trans_text, fill=rgb, font=font)

def render_page(page: pymupdf.Page, page_idx: int, total: int, zoom: float = 2.0, target: str = 'vi') -> io.BytesIO:
    print(f"  Trang {page_idx}/{total}...", flush=True)
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    draw = ImageDraw.Draw(img)
    page_dict = page.get_text("dict")

    class LineInfo:
        __slots__ = ('x0','y0','x1','y1','text','size','bold','italic','rgb','line_h','translated')
        def __init__(self, x0,y0,x1,y1,text,size,bold,italic,rgb,line_h):
            self.x0,self.y0,self.x1,self.y1 = x0,y0,x1,y1
            self.text = text
            self.size = size
            self.bold = bold
            self.italic = italic
            self.rgb = rgb
            self.line_h = line_h
            self.translated = text

    lines: list[LineInfo] = []

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        block_lines = block.get("lines", [])
        for li, line in enumerate(block_lines):
            spans = line.get("spans", [])
            if not spans:
                continue
            line_text = "".join(s.get("text", "") for s in spans).strip()
            if not line_text or len(line_text) < 2:
                continue
            x0 = min(s["bbox"][0] for s in spans) * zoom
            y0 = min(s["bbox"][1] for s in spans) * zoom
            x1 = max(s["bbox"][2] for s in spans) * zoom
            y1 = max(s["bbox"][3] for s in spans) * zoom
            if li + 1 < len(block_lines):
                next_spans = block_lines[li + 1].get("spans", [])
                line_h = (min(s["bbox"][1] for s in next_spans) * zoom - y0) if next_spans else (y1 - y0)
            else:
                line_h = y1 - y0
            line_h = max(line_h, y1 - y0)

            first = spans[0]
            c_int = first.get("color", 0)
            rgb = ((c_int >> 16) & 255, (c_int >> 8) & 255, c_int & 255)
            pdf_size = first.get("size", 10)
            px_size = max(int(pdf_size * zoom * 0.90), 7)
            flags = first.get("flags", 0)
            bold   = bool(flags & 2)
            italic = bool(flags & 1)
            lines.append(LineInfo(x0, y0, x1, y1, line_text, px_size, bold, italic, rgb, line_h))

    if not lines:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        return buf

    translated = batch_translate([ln.text for ln in lines], target=target)
    for ln, tr in zip(lines, translated):
        ln.translated = tr or ln.text

    lines.sort(key=lambda ln: (ln.y0, ln.x0))
    for ln in lines:
        draw_translated_block(draw, img, ln.x0, ln.y0, ln.x1, ln.y1, ln.translated, ln.size, ln.bold, ln.italic, ln.rgb, ln.line_h)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf

def translate_pdf_file(pdf_path: str, output_pdf_path: str = None, service: str = 'google', workers: int = 2) -> str:
    p = Path(pdf_path)
    if output_pdf_path is None:
        output_pdf_path = str(p.with_name(p.stem + "_TiengViet.pdf"))

    doc = pymupdf.open(pdf_path)
    total = len(doc)
    print(f"\n📄 [Siêu Nhẹ & Siêu Tốc Engine] {p.name} ({total} trang)")
    doc_out = pymupdf.open()
    page_bufs: dict[int, io.BytesIO] = {}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(render_page, doc[i], i + 1, total): i for i in range(total)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                page_bufs[i] = fut.result()
            except Exception as e:
                print(f"  ⚠️ Lỗi trang {i + 1}: {e}", file=sys.stderr)
                page_bufs[i] = None

    for i in range(total):
        buf = page_bufs.get(i)
        if buf is None:
            continue
        buf.seek(0)
        img_doc = pymupdf.open(stream=buf.read(), filetype="jpeg")
        pdf_bytes = img_doc.convert_to_pdf()
        doc_out.insert_pdf(pymupdf.open("pdf", pdf_bytes))

    doc_out.save(output_pdf_path)
    print(f"✅ Đã tạo PDF Tiếng Việt: {output_pdf_path}\n")
    return output_pdf_path

def translate_docx_file(docx_path: str, output_docx_path: str = None) -> str:
    p = Path(docx_path)
    if output_docx_path is None:
        output_docx_path = str(p.with_name(p.stem + "_TiengViet.docx"))

    print(f"\n📝 {p.name}")
    src_doc = Document(docx_path)
    new_doc = Document()
    new_doc.add_heading(f"Bản dịch Tiếng Việt: {p.name}", level=1)

    paras = [p.text.strip() for p in src_doc.paragraphs if p.text.strip()]
    for t in batch_translate(paras):
        new_doc.add_paragraph(t)

    new_doc.save(output_docx_path)
    print(f"✅ Đã lưu: {output_docx_path}\n")
    return output_docx_path

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fp = sys.argv[1]
        if fp.lower().endswith('.pdf'):
            translate_pdf_file(fp)
        elif fp.lower().endswith('.docx'):
            translate_docx_file(fp)
        else:
            print("❌ Chỉ hỗ trợ .pdf hoặc .docx")
    else:
        print("Sử dụng: python3 doc_translator.py <path_to_pdf_or_docx>")
