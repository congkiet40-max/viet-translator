#!/usr/bin/env python3
"""
sub_doc_app.py - GUI dịch phụ đề & tài liệu sang Tiếng Việt
v4.0 - Integrated Engine Selector (Google / Gemini Cloud API / Local AI), Progress Bar, SOTA Layout
"""
import os, sys, glob, subprocess, threading, json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sub_translator import translate_srt_file
from doc_translator import translate_pdf_file, translate_docx_file

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_PATH = Path.home() / ".config" / "viet-translator" / "config.json"

def load_config() -> dict:
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"engine": "gemini", "gemini_key": ""}

def save_config(cfg: dict):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Bộ Dịch Phụ Đề & Sách Ngoại Văn (Eng/Rus ➔ Tiếng Việt)")
        self.geometry("820x720")
        self.minsize(720, 620)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cfg = load_config()

        # ── Header ──────────────────────────────────────────────────────────
        hf = ctk.CTkFrame(self, corner_radius=12)
        hf.pack(padx=20, pady=(15, 5), fill="x")
        ctk.CTkLabel(hf, text="🎬 BỘ DỊCH PHỤ ĐỀ & SÁCH NGOẠI VĂN SANG TIẾNG VIỆT",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(hf, text="SOTA Layout (pdf2zh + DocLayout-YOLO) · Phụ đề .srt · .docx  |  Chế độ Dịch Sách Cao Cấp",
                     font=ctk.CTkFont(size=12), text_color="gray70").pack(pady=(0, 10))

        # ── Engine Selection Frame ─────────────────────────────────────────
        ef = ctk.CTkFrame(self, corner_radius=10, fg_color="#1e222a")
        ef.pack(padx=20, pady=5, fill="x")

        ctk.CTkLabel(ef, text="⚙️ LỰA CHỌN ENGINE DỊCH (Tự do tùy chọn trước mỗi lượt dịch):",
                     font=ctk.CTkFont(size=12, weight="bold"), text_color="#38d9a9").pack(anchor="w", padx=12, pady=(8, 4))

        radio_frame = ctk.CTkFrame(ef, fg_color="transparent")
        radio_frame.pack(fill="x", padx=10, pady=2)

        self.engine_var = tk.StringVar(value=self.cfg.get("engine", "google"))

        r1 = ctk.CTkRadioButton(
            radio_frame, text="⚡ Google Translate (Miễn phí - Nhanh, không cần Key)",
            variable=self.engine_var, value="google", command=self._on_engine_change
        )
        r1.pack(side="left", padx=10, pady=4)

        r2 = ctk.CTkRadioButton(
            radio_frame, text="🔑 Gemini Cloud API (Dịch Sách Cao Cấp - Chuẩn mượt)",
            variable=self.engine_var, value="gemini", command=self._on_engine_change
        )
        r2.pack(side="left", padx=10, pady=4)

        r3 = ctk.CTkRadioButton(
            radio_frame, text="🔒 Local AI / Ollama (Offline)",
            variable=self.engine_var, value="ollama", command=self._on_engine_change
        )
        r3.pack(side="left", padx=10, pady=4)

        # API Key Entry Row (collapsible / enabled when Gemini chosen)
        self.key_frame = ctk.CTkFrame(ef, fg_color="transparent")
        self.key_frame.pack(fill="x", padx=12, pady=(2, 8))

        ctk.CTkLabel(self.key_frame, text="🔑 Gemini API Key:", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
        self.key_entry = ctk.CTkEntry(self.key_frame, placeholder_text="Nhập API Key miễn phí từ Google...", width=320)
        self.key_entry.insert(0, self.cfg.get("gemini_key", ""))
        self.key_entry.pack(side="left", padx=4)

        btn_get_key = ctk.CTkButton(
            self.key_frame, text="🔗 Lấy Key Miễn Phí (1-Click)", width=170,
            fg_color="#0c8599", hover_color="#0b7285", font=ctk.CTkFont(size=11),
            command=self._open_gemini_key_page
        )
        btn_get_key.pack(side="left", padx=6)

        self._on_engine_change()

        # ── Progress bar (always visible below header) ───────────────────────
        self._progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self, variable=self._progress_var, height=10)
        self.progress_bar.pack(padx=20, pady=(4, 0), fill="x")
        self._progress_label = ctk.CTkLabel(self, text="Sẵn sàng", font=ctk.CTkFont(size=11), text_color="gray60")
        self._progress_label.pack(anchor="e", padx=22, pady=(2, 0))

        # ── Tabs ─────────────────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=6, fill="both", expand=True)

        self._setup_batch_tab(self.tabview.add("📂 Dịch Phụ Đề Thư Mục"))
        self._setup_file_tab(self.tabview.add("📄 Dịch 1 File (Sub / PDF / Sách / Word)"))
        self._setup_pdf_batch_tab(self.tabview.add("📋 Dịch PDF / Sách Thư Mục"))
        self._setup_play_tab(self.tabview.add("▶️ Xem Video Kèm Sub"))

        # ── Log box ──────────────────────────────────────────────────────────
        lf = ctk.CTkFrame(self, corner_radius=8)
        lf.pack(padx=20, pady=(4, 14), fill="x")
        ctk.CTkLabel(lf, text="Nhật ký tiến trình:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(6, 0))
        self.log_box = ctk.CTkTextbox(lf, height=100, font=ctk.CTkFont(family="monospace", size=11))
        self.log_box.pack(padx=10, pady=6, fill="x")

    def _open_gemini_key_page(self):
        try:
            subprocess.Popen(["xdg-open", "https://aistudio.google.com/app/apikey"])
        except Exception:
            pass

    def _on_engine_change(self):
        eng = self.engine_var.get()
        self.cfg["engine"] = eng
        save_config(self.cfg)
        if eng == "gemini":
            self.key_entry.configure(state="normal")
        else:
            # Leave entry readable
            self.key_entry.configure(state="normal")

    def get_selected_service(self) -> str:
        eng = self.engine_var.get()
        key = self.key_entry.get().strip()
        if key:
            os.environ["GEMINI_API_KEY"] = key
            self.cfg["gemini_key"] = key
            save_config(self.cfg)
        return eng

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _on_close(self):
        self.destroy(); sys.exit(0)

    def log(self, msg: str):
        def _do():
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        self.after(0, _do)

    def set_progress(self, value: float, label: str = ""):
        def _do():
            self._progress_var.set(value)
            if label:
                self._progress_label.configure(text=label)
        self.after(0, _do)

    def _open_file(self, path: str):
        try:
            subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.log(f"⚠️ Không thể mở file: {e}")

    def _result_banner(self, parent, text, path, fg="#2b8a3e"):
        def _do():
            if hasattr(self, '_result_frame') and self._result_frame.winfo_exists():
                self._result_frame.destroy()
            rf = ctk.CTkFrame(parent, fg_color=fg, corner_radius=8)
            rf.pack(padx=15, pady=8, fill="x")
            ctk.CTkLabel(rf, text=text, text_color="white", wraplength=580,
                         font=ctk.CTkFont(size=12)).pack(side="left", padx=12, pady=8, fill="x", expand=True)
            ctk.CTkButton(rf, text="Mở File", width=80, fg_color="white", text_color=fg,
                          command=lambda: self._open_file(path)).pack(side="right", padx=10, pady=6)
            self._result_frame = rf
        self.after(0, _do)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: Batch Subtitle
    # ════════════════════════════════════════════════════════════════════════
    def _setup_batch_tab(self, tab):
        ctk.CTkLabel(tab, text="Chọn thư mục chứa phụ đề (.srt) của khóa học/phim:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(15, 4))

        ff = ctk.CTkFrame(tab)
        ff.pack(fill="x", padx=15, pady=4)
        self.folder_entry = ctk.CTkEntry(ff, placeholder_text="Đường dẫn thư mục...")
        self.folder_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        default = os.path.expanduser("~/Bản tải về/UDEMY Pianoforall Incredible New Way To Learn Piano Keyboard 2026")
        if os.path.exists(default):
            self.folder_entry.insert(0, default)
        ctk.CTkButton(ff, text="📁 Duyệt", command=self._browse_folder, width=100).pack(side="right", padx=8, pady=10)

        self.btn_batch = ctk.CTkButton(
            tab, text="🚀 BẮT ĐẦU DỊCH TOÀN BỘ PHỤ ĐỀ (.SRT) SANG TIẾNG VIỆT",
            fg_color="#1f538d", hover_color="#14375e",
            font=ctk.CTkFont(size=14, weight="bold"), height=44,
            command=self._start_batch_srt)
        self.btn_batch.pack(padx=15, pady=20, fill="x")

    def _browse_folder(self):
        d = filedialog.askdirectory(initialdir=os.path.expanduser("~/Bản tải về"))
        if d:
            self.folder_entry.delete(0, "end"); self.folder_entry.insert(0, d)

    def _start_batch_srt(self):
        folder = self.folder_entry.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục hợp lệ!"); return
        self.btn_batch.configure(state="disabled")
        threading.Thread(target=self._run_batch_srt, args=(folder,), daemon=True).start()

    def _run_batch_srt(self, folder):
        files = [f for f in glob.glob(os.path.join(folder, "**", "*.srt"), recursive=True)
                 if not f.endswith(".vi.srt")]
        if not files:
            self.log("⚠️ Không tìm thấy file .srt nào!")
            self.after(0, lambda: self.btn_batch.configure(state="normal")); return

        self.log(f"📌 Tìm thấy {len(files)} file .srt → bắt đầu dịch...")
        ok = 0
        for i, path in enumerate(files, 1):
            try:
                self.set_progress(i / len(files), f"Phụ đề {i}/{len(files)}: {os.path.basename(path)}")
                self.log(f"[{i}/{len(files)}] {os.path.basename(path)}")
                translate_srt_file(path, target_lang='vi')
                ok += 1
            except Exception as e:
                self.log(f"  ❌ Lỗi: {e}")

        self.set_progress(1.0, f"Hoàn tất {ok}/{len(files)} file phụ đề")
        self.log(f"🎉 Xong! Đã dịch {ok}/{len(files)} file phụ đề Tiếng Việt.")
        self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã dịch xong {ok} file phụ đề!"))
        self.after(0, lambda: self.btn_batch.configure(state="normal"))

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: Single File
    # ════════════════════════════════════════════════════════════════════════
    def _setup_file_tab(self, tab):
        ctk.CTkLabel(tab, text="Chọn 1 file để dịch (PDF / Phụ đề / Sách / Word):",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(15, 4))

        ff = ctk.CTkFrame(tab)
        ff.pack(fill="x", padx=15, pady=4)
        self.file_entry = ctk.CTkEntry(ff, placeholder_text="Chưa chọn file...")
        self.file_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        ctk.CTkButton(ff, text="📂 Chọn File", command=self._browse_file, width=120).pack(side="right", padx=8, pady=10)

        self.btn_file = ctk.CTkButton(
            tab, text="✨ DỊCH FILE NÀY SANG TIẾNG VIỆT (SOTA LAYOUT ENGINE)",
            fg_color="#2b8a3e", hover_color="#1b5e28",
            font=ctk.CTkFont(size=14, weight="bold"), height=44,
            command=self._start_file_translation)
        self.btn_file.pack(padx=15, pady=15, fill="x")

        self._file_tab_ref = tab

    def _browse_file(self):
        fp = filedialog.askopenfilename(
            initialdir=os.path.expanduser("~/Bản tải về"),
            filetypes=[("Tất cả hỗ trợ", "*.srt *.vtt *.pdf *.docx"),
                       ("PDF", "*.pdf"), ("Phụ đề", "*.srt *.vtt"), ("Word", "*.docx")])
        if fp:
            self.file_entry.delete(0, "end"); self.file_entry.insert(0, fp)

    def _start_file_translation(self):
        fp = self.file_entry.get().strip()
        if not fp or not os.path.exists(fp):
            messagebox.showerror("Lỗi", "Vui lòng chọn file hợp lệ!"); return
        svc = self.get_selected_service()
        self.btn_file.configure(state="disabled")
        threading.Thread(target=self._run_file_translation, args=(fp, svc), daemon=True).start()

    def _run_file_translation(self, fp, svc):
        try:
            self.set_progress(0.1, f"Đang xử lý: {os.path.basename(fp)}")
            self.log(f"✨ Bắt đầu dịch ({svc.upper()} Engine): {fp}")
            ext = fp.lower()
            if ext.endswith(".srt") or ext.endswith(".vtt"):
                out = translate_srt_file(fp)
                msg = f"Đã dịch xong phụ đề!\nFile lưu tại:\n{out}"
            elif ext.endswith(".pdf"):
                out = translate_pdf_file(fp, service=svc)
                msg = f"Đã dịch xong PDF (SOTA Layout)!\nFile lưu tại:\n{out}"
            elif ext.endswith(".docx"):
                out = translate_docx_file(fp)
                msg = f"Đã dịch xong Word!\nFile lưu tại:\n{out}"
            else:
                raise ValueError("Định dạng không được hỗ trợ")

            self.set_progress(1.0, "Hoàn tất!")
            self.log(f"✅ Đã tạo: {out}")
            self._result_banner(self._file_tab_ref, f"✅ {msg}", out)
            self.after(0, lambda: messagebox.showinfo("Thành công", msg))
        except Exception as e:
            self.set_progress(0.0, "Lỗi!")
            self.log(f"❌ Lỗi: {e}")
            self.after(0, lambda: messagebox.showerror("Lỗi", str(e)))
        finally:
            self.after(0, lambda: self.btn_file.configure(state="normal"))

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: Batch PDF
    # ════════════════════════════════════════════════════════════════════════
    def _setup_pdf_batch_tab(self, tab):
        ctk.CTkLabel(tab, text="Chọn thư mục chứa các file PDF/Sách muốn dịch:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(15, 4))

        ff = ctk.CTkFrame(tab)
        ff.pack(fill="x", padx=15, pady=4)
        self.pdf_folder_entry = ctk.CTkEntry(ff, placeholder_text="Đường dẫn thư mục PDF...")
        self.pdf_folder_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        default = os.path.expanduser("~/Bản tải về/UDEMY Pianoforall Incredible New Way To Learn Piano Keyboard 2026")
        if os.path.exists(default):
            self.pdf_folder_entry.insert(0, default)
        ctk.CTkButton(ff, text="📁 Duyệt", command=self._browse_pdf_folder, width=100).pack(side="right", padx=8, pady=10)

        ctk.CTkLabel(tab, text="⚠️  Chỉ dịch file PDF chưa được dịch (bỏ qua file *_TiengViet.pdf)",
                     font=ctk.CTkFont(size=11), text_color="gray60").pack(anchor="w", padx=15)

        self.btn_pdf_batch = ctk.CTkButton(
            tab, text="📋 DỊCH TOÀN BỘ FILE PDF SANG TIẾNG VIỆT",
            fg_color="#7b2d8b", hover_color="#4a1a55",
            font=ctk.CTkFont(size=14, weight="bold"), height=44,
            command=self._start_batch_pdf)
        self.btn_pdf_batch.pack(padx=15, pady=20, fill="x")

    def _browse_pdf_folder(self):
        d = filedialog.askdirectory(initialdir=os.path.expanduser("~/Bản tải về"))
        if d:
            self.pdf_folder_entry.delete(0, "end"); self.pdf_folder_entry.insert(0, d)

    def _start_batch_pdf(self):
        folder = self.pdf_folder_entry.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục hợp lệ!"); return
        svc = self.get_selected_service()
        self.btn_pdf_batch.configure(state="disabled")
        threading.Thread(target=self._run_batch_pdf, args=(folder, svc), daemon=True).start()

    def _run_batch_pdf(self, folder, svc):
        files = [f for f in glob.glob(os.path.join(folder, "**", "*.pdf"), recursive=True)
                 if "_TiengViet" not in f and not f.endswith(".mono.pdf") and not f.endswith(".dual.pdf")]
        if not files:
            self.log("⚠️ Không tìm thấy file PDF nào cần dịch!")
            self.after(0, lambda: self.btn_pdf_batch.configure(state="normal")); return

        self.log(f"📌 Tìm thấy {len(files)} file PDF → bắt đầu dịch ({svc.upper()})...")
        ok = 0
        for i, path in enumerate(files, 1):
            try:
                self.set_progress(i / len(files), f"PDF {i}/{len(files)}: {os.path.basename(path)}")
                self.log(f"[{i}/{len(files)}] {os.path.basename(path)}")
                translate_pdf_file(path, service=svc)
                ok += 1
            except Exception as e:
                self.log(f"  ❌ Lỗi: {e}")

        self.set_progress(1.0, f"Hoàn tất {ok}/{len(files)} file PDF")
        self.log(f"🎉 Xong! Đã dịch {ok}/{len(files)} file PDF Tiếng Việt.")
        self.after(0, lambda: messagebox.showinfo("Thành công", f"Đã dịch xong {ok} file PDF Tiếng Việt!"))
        self.after(0, lambda: self.btn_pdf_batch.configure(state="normal"))

    # ════════════════════════════════════════════════════════════════════════
    # TAB 4: Play Video
    # ════════════════════════════════════════════════════════════════════════
    def _setup_play_tab(self, tab):
        ctk.CTkLabel(tab, text="Chọn video MP4/MKV để xem kèm Phụ Đề Tiếng Việt:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(15, 4))

        vf = ctk.CTkFrame(tab)
        vf.pack(fill="x", padx=15, pady=4)
        self.video_entry = ctk.CTkEntry(vf, placeholder_text="Chưa chọn video...")
        self.video_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        ctk.CTkButton(vf, text="🎬 Chọn Video", command=self._browse_video, width=130).pack(side="right", padx=8, pady=10)

        ctk.CTkButton(tab, text="▶️  MỞ VIDEO BẰNG VLC PLAYER",
                      fg_color="#e65100", hover_color="#b23c00",
                      font=ctk.CTkFont(size=14, weight="bold"), height=40,
                      command=lambda: self._play("vlc")).pack(padx=15, pady=(15, 6), fill="x")

        ctk.CTkButton(tab, text="⏯️  MỞ VIDEO BẰNG MPV PLAYER",
                      fg_color="#333333", hover_color="#555555",
                      font=ctk.CTkFont(size=14, weight="bold"), height=40,
                      command=lambda: self._play("mpv")).pack(padx=15, pady=6, fill="x")

    def _browse_video(self):
        fp = filedialog.askopenfilename(
            initialdir=os.path.expanduser("~/Bản tải về"),
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")])
        if fp:
            self.video_entry.delete(0, "end"); self.video_entry.insert(0, fp)

    def _play(self, player: str):
        vp = self.video_entry.get().strip()
        if not vp or not os.path.exists(vp):
            messagebox.showerror("Lỗi", "Vui lòng chọn file video hợp lệ!"); return

        base = os.path.splitext(vp)[0]
        sub = None
        for cand in [base + ".vi.srt", base + ".srt"]:
            if os.path.exists(cand):
                sub = cand; break
        if not sub:
            matches = glob.glob(base + "*.srt")
            sub = matches[0] if matches else None

        self.log(f"🎬 Mở: {os.path.basename(vp)}" + (f"  💬 Sub: {os.path.basename(sub)}" if sub else "  ⚠️ Không tìm thấy sub"))
        try:
            if player == "vlc":
                cmd = ["flatpak", "run", "org.videolan.VLC", vp]
                if sub: cmd += ["--sub-file", sub]
            else:
                cmd = ["mpv", vp]
                if sub: cmd.append(f"--sub-file={sub}")
            subprocess.Popen(cmd)
        except Exception as e:
            self.log(f"❌ Không mở me: {e}")


if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
