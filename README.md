# 🎬 Viet Translator — Dịch Phụ Đề & Tài Liệu sang Tiếng Việt

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/badge/Platform-Linux-orange?logo=linux" />
  <img src="https://img.shields.io/badge/Google%20Translate-Free%20API-red?logo=googletranslate" />
</p>

Công cụ dịch **phụ đề `.srt`**, **tài liệu `.pdf`** (giữ nguyên hình ảnh & bố cục), và **file `.docx`** sang **Tiếng Việt** — hoàn toàn miễn phí, không cần API key, có giao diện đồ họa (GUI) và chạy được trên **Linux**.

---

## ✨ Tính Năng

| Tính năng | Mô tả |
|-----------|-------|
| 🎬 **Dịch phụ đề .srt** | Dịch hàng loạt toàn bộ file .srt trong thư mục, tự tạo file `.vi.srt` |
| 📄 **Dịch PDF giữ bố cục** | Dịch text trực tiếp lên ảnh PDF, giữ nguyên hình vẽ, ký hiệu nhạc, sơ đồ |
| 📝 **Dịch Word .docx** | Dịch nhanh file Word, giữ cấu trúc đoạn văn |
| 🖥️ **Giao diện GUI** | App desktop bằng `customtkinter`, dark mode, progress bar |
| ⚡ **Batch + MultiThread** | Dịch nhiều trang PDF song song, batch HTTP request giảm latency |
| 🧠 **Translation Cache** | Không dịch lại text trùng lặp giữa các trang |
| 🎼 **Bảo toàn ký hiệu nhạc** | Tự nhận biết hợp âm piano (C, Am, G7...) và KHÔNG dịch |
| 🎨 **Smart Layout** | Tự co font / word-wrap khi text dịch dài hơn gốc |
| 🖌️ **Giữ màu chữ & font** | Red text → vẫn đỏ, bold → vẫn đậm, italic → vẫn nghiêng |

---

## 📸 Demo

| Trang gốc (Tiếng Anh) | Sau khi dịch (Tiếng Việt) |
|---|---|
| Hình ảnh, chord, lyrics | Chord giữ nguyên, lyrics dịch, hình giữ nguyên |

---

## 🚀 Cài Đặt

### Yêu cầu
- **Python 3.10+**
- **Linux** (Fedora / Ubuntu / Debian / Arch)

### Bước 1: Clone repo

```bash
git clone https://github.com/<your-username>/viet-translator.git
cd viet-translator
```

### Bước 2: Cài dependencies

```bash
pip install -r requirements.txt
```

Nếu thiếu `tkinter`:
```bash
# Fedora
sudo dnf install python3-tkinter

# Ubuntu/Debian
sudo apt install python3-tk
```

---

## 🖥️ Sử Dụng

### Cách 1: Giao diện GUI (khuyến nghị)

```bash
python3 sub_doc_app.py
```

App có 4 tab:
- **📂 Dịch Toàn Bộ Phụ Đề Thư Mục** — chọn thư mục khóa học, dịch tất cả `.srt`
- **📄 Dịch 1 File** — dịch một file `.srt` / `.pdf` / `.docx`
- **📋 Dịch Toàn Bộ PDF Thư Mục** — dịch hàng loạt PDF
- **▶️ Xem Video Kèm Sub** — mở VLC / MPV kèm phụ đề Tiếng Việt

### Cách 2: Dòng lệnh (CLI)

**Dịch file phụ đề .srt:**
```bash
python3 sub_translator.py "video.srt"
# → Tạo ra: video.vi.srt
```

**Dịch PDF (giữ hình ảnh & bố cục):**
```bash
python3 doc_translator.py "TaiLieu.pdf"
# → Tạo ra: TaiLieu_TiengViet.pdf
```

**Dịch file Word:**
```bash
python3 doc_translator.py "BaoCao.docx"
# → Tạo ra: BaoCao_TiengViet.docx
```

---

## 📂 Cấu Trúc Project

```
viet-translator/
├── sub_doc_app.py      # 🖥️  GUI app chính (4 tab)
├── doc_translator.py   # 📄  Engine dịch PDF + DOCX
├── sub_translator.py   # 🎬  Engine dịch SRT phụ đề
├── requirements.txt    # 📦  Python dependencies
├── LICENSE             # ⚖️  MIT License
└── README.md
```

---

## ⚙️ Kỹ Thuật

### PDF Translation Engine (`doc_translator.py`)

```
PDF gốc
  ↓ PyMuPDF rasterize → ảnh 2.5x zoom (high-res)
  ↓ Trích xuất text block + bounding box từng dòng
  ↓ Batch translate (gom 40 dòng → 1 HTTP request)
  ↓ Background color sampling (4-strip average)
  ↓ Erase vùng text gốc với đúng màu nền
  ↓ Vẽ text dịch: auto word-wrap / shrink font nếu quá dài
  ↓ Lưu lại thành PDF mới
```

**Các tối ưu nổi bật:**
- `ThreadPoolExecutor` (3 luồng) — xử lý song song nhiều trang
- `_trans_cache` dict — cache in-memory tránh dịch lại text trùng
- Nhận diện chord nhạc bằng regex, không dịch `C, Am7, G/B...`
- `line_height detection` từ khoảng cách dòng kế tiếp
- Smart wrap: 1 dòng → ≤3 dòng → shrink font (fallback)

### Subtitle Engine (`sub_translator.py`)
- Parse `.srt` / `.vtt` bằng thư viện `srt`
- Giữ nguyên timestamp, chỉ dịch text
- Tự ghép file `.vi.srt` cùng thư mục với video

---

## 🔒 Bảo mật & Giới hạn

- Dùng **Google Translate unofficial API** (`gtx` endpoint) — miễn phí nhưng không có SLA
- Không gửi file lên server — mọi xử lý ảnh/PDF đều local
- Rate limit nhẹ: pause `80ms` giữa các chunk để tránh bị block

---

## 🙏 Thư viện sử dụng

| Thư viện | Mục đích |
|----------|----------|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Đọc & render PDF |
| [Pillow](https://python-pillow.org/) | Xử lý ảnh, vẽ text |
| [srt](https://github.com/cdown/srt) | Parse file phụ đề |
| [python-docx](https://github.com/python-openxml/python-docx) | Đọc/ghi Word |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | GUI dark mode |

---

## 📄 License

[MIT](LICENSE) © 2026
