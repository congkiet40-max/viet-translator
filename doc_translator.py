#!/usr/bin/env python3
"""
doc_translator.py - Bộ dịch PDF/DOCX siêu tốc & Bố cục SOTA cho Tiếng Việt
v5.0 - Integrated SOTA Layout Engine (pdf2zh / DocLayout-YOLO) + PyMuPDF fallback
"""
import os, sys, re, io, json, time, subprocess, shutil
import urllib.request, urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
import pymupdf
from docx import Document

# ─── SOTA ENGINE INTEGRATION (pdf2zh) ─────────────────────────────────────────
def is_pdf2zh_available() -> bool:
    """Kiểm tra xem engine pdf2zh có sẵn trên hệ thống không."""
    return shutil.which("pdf2zh") is not None or shutil.which("pdf2zh.exe") is not None

def translate_pdf_sota(
    pdf_path: str,
    output_pdf_path: str = None,
    service: str = 'google',
    lang_in: str = 'en',
    lang_out: str = 'vi',
    thread: int = 4
) -> str:
    """
    Dịch PDF bằng engine pdf2zh (DocLayout-YOLO):
    Giữ 100% bố cục, font chữ, hình ảnh, bảng biểu & công thức toán.
    """
    p = Path(pdf_path).resolve()
    if output_pdf_path is None:
        output_pdf_path = str(p.with_name(f"{p.stem}_TiengViet.pdf"))

    print(f"\n🚀 [SOTA Engine: pdf2zh + DocLayout-YOLO] Đang dịch: {p.name}")
    print(f"   Service: {service.upper()} | Ngôn ngữ: {lang_in} -> {lang_out}")

    cmd = [
        "pdf2zh",
        str(p),
        "-li", lang_in,
        "-lo", lang_out,
        "-s", service,
        "-t", str(thread)
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # pdf2zh generates files with suffix e.g. filename.mono.pdf or filename.dual.pdf
        # Let's find generated output file in the same directory
        stem = p.stem
        parent = p.parent
        possible_outputs = [
            parent / f"{stem}.mono.pdf",
            parent / f"{stem}_mono.pdf",
            parent / f"{stem}.dual.pdf",
        ]

        found_out = None
        for po in possible_outputs:
            if po.exists():
                found_out = po
                break

        if not found_out:
            # Search for newest created pdf with stem in name
            matched = list(parent.glob(f"{stem}*.pdf"))
            matched = [f for f in matched if f.resolve() != p]
            if matched:
                found_out = max(matched, key=lambda f: f.stat().st_mtime)

        if found_out:
            shutil.move(str(found_out), output_pdf_path)
            print(f"✅ Đã tạo PDF bản dịch chuẩn SOTA: {output_pdf_path}\n")
            return output_pdf_path
        else:
            print("⚠️ Không tìm thấy file đầu ra từ pdf2zh, chuyển sang fallback engine...", file=sys.stderr)
            return translate_pdf_fallback(pdf_path, output_pdf_path)

    except Exception as e:
        print(f"⚠️ Lỗi khi chạy pdf2zh ({e}). Đang chuyển sang Fallback engine (PyMuPDF)...", file=sys.stderr)
        return translate_pdf_fallback(pdf_path, output_pdf_path)


# ─── FALLBACK ENGINE (PyMuPDF Custom Overlay) ─────────────────────────────────
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

_CHORD_RE = re.compile(r'^[A-G][b#]?(maj7?|min7?|m7?|dim7?|aug|sus[24]?|add\d|7|9|11|13)?(\/[A-G][b#]?)?$', re.I)
_PAGE_NUM_RE = re.compile(r'^\d{1,4}(-\d{1,4})?$')

def _skip(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if t.isdigit() or _PAGE_NUM_RE.match(t):
        return True
    if len(t) <= 7 and _CHORD_RE.match(t):
        return True
    if all(c in '©®™°•·-–—_|/\\' for c in t):
        return True
    return False

_trans_cache: dict = {}
_DELIM = "\n|||SPLIT|||\n"

def _gtx_raw(text: str, target: str = 'vi') -> str:
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=auto&tl={target}&dt=t&q={urllib.parse.quote(text)}"
        )
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read().decode('utf-8'))
            return "".join([item[0] for item in res[0] if item[0]])
    except Exception:
        return text

def _gtx(text: str, target: str = 'vi') -> str:
    t = text.strip()
    if _skip(t):
        return text
    if t in _trans_cache:
        return _trans_cache[t]
    result = _gtx_raw(t, target)
    _trans_cache[t] = result
    return result

def batch_translate(texts: list, target: str = 'vi') -> list:
    if not texts:
        return []
    results = [None] * len(texts)
    need_idx, need_txt = [], []
    for i, t in enumerate(texts):
        if _skip(t):
            results[i] = t
        elif t.strip() in _trans_cache:
            results[i] = _trans_cache[t.strip()]
        else:
            need_idx.append(i)
            need_txt.append(t)

    CHUNK = 40
    for cs in range(0, len(need_txt), CHUNK):
        chunk = need_txt[cs:cs + CHUNK]
        combined = _gtx_raw(_DELIM.join(chunk), target)
        parts = combined.split(_DELIM)
        if len(parts) == len(chunk):
            for j, tr in enumerate(parts):
                idx = need_idx[cs + j]
                results[idx] = tr.strip()
                _trans_cache[need_txt[cs + j].strip()] = tr.strip()
        else:
            for j, orig in enumerate(chunk):
                idx = need_idx[cs + j]
                results[idx] = _gtx(orig, target)
        if cs + CHUNK < len(need_txt):
            time.sleep(0.08)

    return results

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

def render_page(page: pymupdf.Page, page_idx: int, total: int, zoom: float = 2.5, target: str = 'vi') -> io.BytesIO:
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
        img.save(buf, format="JPEG", quality=93)
        buf.seek(0)
        return buf

    translated = batch_translate([ln.text for ln in lines], target=target)
    for ln, tr in zip(lines, translated):
        ln.translated = tr or ln.text

    lines.sort(key=lambda ln: (ln.y0, ln.x0))
    for ln in lines:
        draw_translated_block(draw, img, ln.x0, ln.y0, ln.x1, ln.y1, ln.translated, ln.size, ln.bold, ln.italic, ln.rgb, ln.line_h)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=93)
    buf.seek(0)
    return buf

def translate_pdf_fallback(pdf_path: str, output_pdf_path: str = None, workers: int = 3) -> str:
    p = Path(pdf_path)
    if output_pdf_path is None:
        output_pdf_path = str(p.with_name(p.stem + "_TiengViet.pdf"))

    doc = pymupdf.open(pdf_path)
    total = len(doc)
    print(f"\n📄 [Fallback Engine: PyMuPDF] {p.name} ({total} trang)")
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
    print(f"✅ Đã tạo: {output_pdf_path}\n")
    return output_pdf_path

def translate_pdf_file(pdf_path: str, output_pdf_path: str = None, service: str = 'google') -> str:
    if is_pdf2zh_available():
        return translate_pdf_sota(pdf_path, output_pdf_path, service=service)
    else:
        return translate_pdf_fallback(pdf_path, output_pdf_path)

# ─── DOCX TRANSLATOR ─────────────────────────────────────────────────────────
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

# ─── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) > 1:
        fp = sys.argv[1]
        svc = sys.argv[2] if len(sys.argv) > 2 else 'google'
        if fp.lower().endswith('.pdf'):
            translate_pdf_file(fp, service=svc)
        elif fp.lower().endswith('.docx'):
            translate_docx_file(fp)
        else:
            print("❌ Chỉ hỗ trợ .pdf hoặc .docx")
    else:
        print("Sử dụng: python3 doc_translator.py <path_to_pdf_or_docx> [service_name]")
