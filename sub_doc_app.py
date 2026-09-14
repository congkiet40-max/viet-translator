#!/usr/bin/env python3
"""
sub_doc_app.py - GUI dịch phụ đề & tài liệu sang Tiếng Việt
Phiên bản 3.0 - Tối ưu: Progress bar, mở file đầu ra, batch PDF, canh chỉnh font
"""
import os, sys, glob, subprocess, threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sub_translator import translate_srt_file
from doc_translator import translate_pdf_file, translate_docx_file

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class TranslatorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Bộ Dịch Phụ Đề & Tài Liệu (Eng/Rus ➔ Tiếng Việt)")
        self.geometry("800x650")
        self.minsize(700, 580)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Header ──────────────────────────────────────────────────────────
        hf = ctk.CTkFrame(self, corner_radius=12)
        hf.pack(padx=20, pady=(15, 5), fill="x")
        ctk.CTkLabel(hf, text="🎬 BỘ DỊCH PHỤ ĐỀ & TÀI LIỆU SANG TIẾNG VIỆT",
                     font=ctk.CTkFont(size=19, weight="bold")).pack(pady=(10, 2))
        ctk.CTkLabel(hf, text="Tự động dịch .srt · .pdf (giữ hình ảnh + bố cục) · .docx  |  Xem video kèm sub Tiếng Việt",
                     font=ctk.CTkFont(size=12), text_color="gray70").pack(pady=(0, 10))

        # ── Progress bar (always visible below header) ───────────────────────
        self._progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(self, variable=self._progress_var, height=10)
        self.progress_bar.pack(padx=20, pady=(4, 0), fill="x")
        self._progress_label = ctk.CTkLabel(self, text="Sẵn sàng", font=ctk.CTkFont(size=11), text_color="gray60")
        self._progress_label.pack(anchor="e", padx=22, pady=(2, 0))

        # ── Tabs ─────────────────────────────────────────────────────────────
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=6, fill="both", expand=True)

        self._setup_batch_tab(self.tabview.add("📂 Dịch Toàn Bộ Phụ Đề Thư Mục"))
        self._setup_file_tab(self.tabview.add("📄 Dịch 1 File (Sub / PDF / Word)"))
        self._setup_pdf_batch_tab(self.tabview.add("📋 Dịch Toàn Bộ PDF Thư Mục"))
        self._setup_play_tab(self.tabview.add("▶️ Xem Video Kèm Sub"))

        # ── Log box ──────────────────────────────────────────────────────────
        lf = ctk.CTkFrame(self, corner_radius=8)
        lf.pack(padx=20, pady=(4, 14), fill="x")
        ctk.CTkLabel(lf, text="Nhật ký tiến trình:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=10, pady=(6, 0))
        self.log_box = ctk.CTkTextbox(lf, height=110, font=ctk.CTkFont(family="monospace", size=11))
        self.log_box.pack(padx=10, pady=6, fill="x")

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _on_close(self):
        self.destroy(); sys.exit(0)

    def log(self, msg: str):
        def _do():
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
        self.after(0, _do)

    def set_progress(self, value: float, label: str = ""):
        """value: 0.0 – 1.0"""
        def _do():
            self._progress_var.set(value)
            if label:
                self._progress_label.configure(text=label)
        self.after(0, _do)

    def _open_file(self, path: str):
        """Open a file with the system default app."""
        try:
            subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self.log(f"⚠️ Không thể mở file: {e}")

    def _result_banner(self, parent, text, path, fg="#2b8a3e"):
        """Show a success banner with Open button."""
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
        ctk.CTkLabel(tab, text="Chọn thư mục chứa phụ đề (.srt) của khóa học:",
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
        ctk.CTkLabel(tab, text="Chọn 1 file để dịch:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(15, 4))

        ff = ctk.CTkFrame(tab)
        ff.pack(fill="x", padx=15, pady=4)
        self.file_entry = ctk.CTkEntry(ff, placeholder_text="Chưa chọn file...")
        self.file_entry.pack(side="left", fill="x", expand=True, padx=10, pady=10)
        ctk.CTkButton(ff, text="📂 Chọn File", command=self._browse_file, width=120).pack(side="right", padx=8, pady=10)

        self.btn_file = ctk.CTkButton(
            tab, text="✨ DỊCH FILE NÀY SANG TIẾNG VIỆT (GIỮ HÌNH ẢNH & BỐ CỤC)",
            fg_color="#2b8a3e", hover_color="#1b5e28",
            font=ctk.CTkFont(size=14, weight="bold"), height=44,
            command=self._start_file_translation)
        self.btn_file.pack(padx=15, pady=15, fill="x")

        self._file_tab_ref = tab  # save ref for result banner

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
        self.btn_file.configure(state="disabled")
        threading.Thread(target=self._run_file_translation, args=(fp,), daemon=True).start()

    def _run_file_translation(self, fp):
        try:
            self.set_progress(0.1, f"Đang xử lý: {os.path.basename(fp)}")
            self.log(f"✨ Bắt đầu dịch: {fp}")
            ext = fp.lower()
            if ext.endswith(".srt") or ext.endswith(".vtt"):
                out = translate_srt_file(fp)
                msg = f"Đã dịch xong phụ đề!\nFile lưu tại:\n{out}"
            elif ext.endswith(".pdf"):
                out = translate_pdf_file(fp)
                msg = f"Đã dịch xong PDF!\nFile lưu tại:\n{out}"
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
        ctk.CTkLabel(tab, text="Chọn thư mục chứa các file PDF muốn dịch:",
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
        self.btn_pdf_batch.configure(state="disabled")
        threading.Thread(target=self._run_batch_pdf, args=(folder,), daemon=True).start()

    def _run_batch_pdf(self, folder):
        files = [f for f in glob.glob(os.path.join(folder, "**", "*.pdf"), recursive=True)
                 if "_TiengViet" not in f]
        if not files:
            self.log("⚠️ Không tìm thấy file PDF nào cần dịch!")
            self.after(0, lambda: self.btn_pdf_batch.configure(state="normal")); return

        self.log(f"📌 Tìm thấy {len(files)} file PDF → bắt đầu dịch...")
        ok = 0
        for i, path in enumerate(files, 1):
            try:
                self.set_progress(i / len(files), f"PDF {i}/{len(files)}: {os.path.basename(path)}")
                self.log(f"[{i}/{len(files)}] {os.path.basename(path)}")
                translate_pdf_file(path)
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
            self.log(f"❌ Không mở được trình phát: {e}")


if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()
