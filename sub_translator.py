#!/usr/bin/env python3
import os
import sys
import re
import time
import json
import urllib.request
import urllib.parse
import srt
from pathlib import Path

def translate_text_gtx(text, src='auto', target='vi'):
    if not text.strip():
        return text
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={target}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode('utf-8'))
            translated = "".join([item[0] for item in res[0] if item[0]])
            return translated
    except Exception as e:
        print(f"Error translating text: {e}", file=sys.stderr)
        return text

def translate_srt_file(file_path, target_lang='vi', output_path=None):
    p = Path(file_path)
    dir_path = p.parent

    # Find matching mp4 if any
    stem_clean = p.stem.replace(" RUS", "").strip()
    matching_mp4 = None
    for f in os.listdir(dir_path):
        if f.endswith('.mp4'):
            num_f = f.split('-')[0] if '-' in f else ''
            num_p = stem_clean.split('-')[0] if '-' in stem_clean else ''
            if (num_f and num_f == num_p) or (stem_clean.lower().replace('_', ' ') in f.lower()):
                matching_mp4 = Path(f).stem
                break

    if output_path is None:
        if matching_mp4:
            output_path = os.path.join(dir_path, f"{matching_mp4}.srt")
            alt_path = os.path.join(dir_path, f"{matching_mp4}.vi.srt")
        else:
            output_path = os.path.join(dir_path, f"{stem_clean}.srt")
            alt_path = os.path.join(dir_path, f"{stem_clean}.vi.srt")

    print(f"Dịch file: {file_path} -> {output_path}")

    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
        content = f.read()

    try:
        subs = list(srt.parse(content))
    except Exception as e:
        print(f"Lỗi parse SRT: {e}, thử dịch từng dòng...", file=sys.stderr)
        subs = None

    if subs:
        batch_size = 30
        for i in range(0, len(subs), batch_size):
            batch = subs[i:i+batch_size]
            combined_text = "\n===SUB_DELIM===\n".join([s.content for s in batch])
            translated_combined = translate_text_gtx(combined_text, target=target_lang)
            translated_lines = translated_combined.split("\n===SUB_DELIM===\n")

            if len(translated_lines) == len(batch):
                for sub_obj, trans in zip(batch, translated_lines):
                    sub_obj.content = trans.strip()
            else:
                for sub_obj in batch:
                    sub_obj.content = translate_text_gtx(sub_obj.content, target=target_lang).strip()

            time.sleep(0.1)

        translated_srt = srt.compose(subs)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_srt)
        if 'alt_path' in locals() and alt_path != output_path:
            with open(alt_path, 'w', encoding='utf-8') as f:
                f.write(translated_srt)

        print(f"✅ Đã tạo phụ đề Tiếng Việt: {output_path}")
        return output_path
    return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        translate_srt_file(sys.argv[1])
    else:
        print("Sử dụng: python3 sub_translator.py <path_to_srt_file>")
