# 🇻🇳 Viet Translator — Dịch Phụ Đề & Tài Liệu sang Tiếng Việt

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
  <img src="https://img.shields.io/badge/Platform-Linux-orange?logo=linux" />
  <img src="https://img.shields.io/badge/Dịch%20tự%20động-Google%20Translate-red?logo=googletranslate" />
  <img src="https://img.shields.io/badge/Miễn%20phí-Không%20cần%20API%20Key-brightgreen" />
</p>

<p align="center">
  <b>Xem phim nước ngoài kèm phụ đề Tiếng Việt · Đọc sách/tài liệu PDF giữ nguyên hình ảnh · Hoàn toàn miễn phí</b>
</p>

---

## 🤔 Công cụ này dùng để làm gì?

Bạn có bao giờ gặp những tình huống này không?

- 📺 **Tải phim / khóa học nước ngoài** về nhưng phụ đề chỉ có tiếng Anh hoặc tiếng Nga
- 📚 **Có file PDF sách / tài liệu** tiếng nước ngoài muốn đọc bằng tiếng Việt nhưng dịch xong thì mất hết hình ảnh, sơ đồ
- 📖 **Tải ebook, giáo trình** muốn dịch nhưng các công cụ online chỉ cho dịch text, không giữ được bố cục

**Viet Translator giải quyết đúng 3 vấn đề đó:**

| Bạn có | Bạn nhận được |
|--------|--------------|
| `video.srt` (phụ đề Anh/Nga) | `video.vi.srt` (phụ đề Tiếng Việt, đúng thời điểm) |
| `sachgiao.pdf` (tiếng Anh, có hình) | `sachgiao_TiengViet.pdf` (tiếng Việt, **giữ nguyên toàn bộ hình ảnh & bố cục**) |
| `baocao.docx` (tiếng Anh) | `baocao_TiengViet.docx` (tiếng Việt) |

---

## 🎯 Ai nên dùng?

- 🎓 **Học viên khóa học online** (Udemy, Coursera...) — dịch phụ đề + tài liệu PDF kèm theo
- 🎬 **Người xem phim/series nước ngoài** — tự tạo phụ đề Tiếng Việt từ file `.srt` có sẵn
- 📖 **Người đọc sách ngoại văn** — dịch PDF giữ nguyên hình minh hoạ, sơ đồ, bảng biểu
- 🎵 **Học nhạc** — dịch giáo trình nhạc lý, giữ nguyên ký hiệu hợp âm (C, Am, G7...)
- 👨‍💻 **Người dùng Linux** muốn tool dịch offline không phụ thuộc web

---

## ✨ Tính Năng Nổi Bật

### 📄 Dịch PDF — Điểm khác biệt lớn nhất

Hầu hết công cụ dịch PDF sẽ:
- ❌ Mất hình ảnh, đồ thị, sơ đồ
- ❌ Vỡ bố cục, chữ chạy loạn
- ❌ Mất màu sắc, định dạng

Viet Translator:
- ✅ **Giữ nguyên 100% hình ảnh** — chỉ thay phần chữ
- ✅ **Giữ màu chữ gốc** — chữ đỏ vẫn đỏ, in đậm vẫn đậm
- ✅ **Tự co font / xuống dòng** khi tiếng Việt dài hơn tiếng Anh
- ✅ **Nhận biết ký hiệu nhạc** (Am, G7, Cmaj7...) và KHÔNG dịch chúng

### 🎬 Dịch Phụ Đề `.srt`
- ✅ Giữ nguyên toàn bộ timestamp (không bao giờ bị lệch)
- ✅ Dịch hàng loạt cả thư mục (hàng trăm file một lúc)
- ✅ Tự tạo file `video.vi.srt` cùng thư mục với video

### ⚡ Hiệu suất
- Dùng **Google Translate miễn phí** — không cần tạo tài khoản, không cần API key
- **Batch translation**: gom nhiều dòng vào 1 request → nhanh gấp 10-40x so với dịch từng dòng
- **Xử lý song song** nhiều trang PDF cùng lúc
- **Cache thông minh**: không dịch lại text đã dịch

---

## 🖥️ Giao Diện

App desktop dark mode, chạy ngay trên Linux:

```
┌─────────────────────────────────────────────────────┐
│  🎬 BỘ DỊCH PHỤ ĐỀ & TÀI LIỆU SANG TIẾNG VIỆT      │
├──────────────┬──────────────┬──────────┬────────────┤
│ 📂 Dịch Toàn │ 📄 Dịch 1    │ 📋 Dịch  │ ▶️ Xem     │
│ Bộ Phụ Đề   │ File         │ Toàn Bộ  │ Video      │
│              │ Sub/PDF/Word │ PDF      │ Kèm Sub    │
├──────────────┴──────────────┴──────────┴────────────┤
│ ████████████████████░░░░  Trang 8/10: chapter3.pdf  │
├─────────────────────────────────────────────────────┤
│ Nhật ký:                                            │
│ ✅ Đã tạo: chapter3_TiengViet.pdf                   │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Cài Đặt

### Yêu cầu
- **Python 3.10+** trên **Linux**
- Kết nối Internet (để gọi Google Translate)

### Cài nhanh

```bash
# 1. Clone về máy
git clone https://github.com/congkiet40-max/viet-translator.git
cd viet-translator

# 2. Cài thư viện Python
pip install -r requirements.txt

# 3. Nếu thiếu tkinter (Fedora)
sudo dnf install python3-tkinter

# 3. Nếu thiếu tkinter (Ubuntu/Debian)
sudo apt install python3-tk
```

---

## 📖 Hướng Dẫn Sử Dụng

### 🖥️ Giao diện GUI (dễ nhất)

```bash
python3 sub_doc_app.py
```

**Tab "Dịch 1 File"** → Chọn file → Bấm Dịch → Xong!

Hỗ trợ kéo thả hoặc duyệt file `.srt`, `.pdf`, `.docx`

---

### ⌨️ Dòng lệnh (CLI)

```bash
# Dịch phụ đề (tạo file .vi.srt)
python3 sub_translator.py "Phim.Hay.srt"

# Dịch PDF giữ hình & bố cục
python3 doc_translator.py "GiaoTrinh.pdf"

# Dịch file Word
python3 doc_translator.py "TaiLieu.docx"

# Dịch hàng loạt phụ đề trong thư mục
python3 sub_translator.py --batch "/path/to/folder"
```

---

### ▶️ Xem video kèm phụ đề Tiếng Việt

1. Dịch file `.srt` của video → được file `.vi.srt`
2. Mở tab **"Xem Video Kèm Sub"** → Chọn video → Bấm **Mở VLC**
3. VLC tự gắn phụ đề Tiếng Việt vào video

Hoặc dùng lệnh:
```bash
vlc video.mp4 --sub-file video.vi.srt
mpv video.mp4 --sub-file=video.vi.srt
```

---

## 📂 Cấu Trúc Project

```
viet-translator/
├── sub_doc_app.py      # 🖥️  GUI app chính (4 tab)
├── doc_translator.py   # 📄  Engine dịch PDF + DOCX
├── sub_translator.py   # 🎬  Engine dịch SRT phụ đề
├── requirements.txt    # 📦  Danh sách thư viện cần cài
├── LICENSE             # ⚖️  MIT License
└── README.md
```

---

## ⚙️ Cách Hoạt Động (cho người tò mò)

### PDF Translation Engine

```
File PDF gốc
  │
  ▼ PyMuPDF đọc + render thành ảnh độ phân giải cao (2.5x)
  │
  ▼ Trích xuất vị trí từng dòng chữ (bounding box)
  │
  ▼ Gom tất cả dòng → gửi 1 request Google Translate (batch)
  │
  ▼ Lấy màu nền thực tế bằng pixel sampling → xóa chữ cũ
  │
  ▼ Vẽ chữ Việt đúng màu, đúng cỡ, tự xuống dòng nếu cần
  │
  ▼ Xuất PDF mới (giữ nguyên ảnh, sơ đồ, ký hiệu nhạc)
```

### Subtitle Engine

```
File .srt → Parse timestamp + text → Dịch text → Ghép lại → .vi.srt
```

---

## ⚠️ Giới Hạn & Lưu Ý

- Chất lượng dịch phụ thuộc **Google Translate** — tốt với Anh→Việt, khá với Nga→Việt
- PDF dạng **scan (ảnh chụp)** không dịch được — chỉ dịch được PDF có text thực (digital PDF)
- Không phù hợp với tài liệu cần dịch **chuyên ngành y/pháp/kỹ thuật** độ chính xác cao
- Cần **kết nối internet** để gọi Google Translate

---

## 🙏 Thư Viện Sử Dụng

| Thư viện | Vai trò |
|----------|---------|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | Đọc & render PDF thành ảnh |
| [Pillow](https://python-pillow.org/) | Xử lý ảnh, vẽ chữ lên ảnh |
| [srt](https://github.com/cdown/srt) | Parse & ghi file phụ đề .srt |
| [python-docx](https://github.com/python-openxml/python-docx) | Đọc/ghi file Word .docx |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | GUI dark mode đẹp |
| Google Translate (free) | Dịch thuật tự động |

---

## 📄 License

[MIT](LICENSE) © 2026 — Tự do sử dụng, chỉnh sửa, chia sẻ.
