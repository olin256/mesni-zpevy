import os
import subprocess
import json
from glob import iglob
from musicxml_to_ly import musicxml_to_ly

def pure_fname(fname):
    return os.path.splitext(os.path.basename(fname))[0]

def path_fname_short(fname, ext):
    return "../" + ext + "/" + fname

def path_fname(fname, ext):
    return path_fname_short(fname, ext) + "." + ext

def star_path(ext):
    return "../" + ext + "/*." + ext

available_pdf = set(map(pure_fname, iglob(star_path("pdf"))))
available_musicxml = [fname for fname in map(pure_fname, iglob(star_path("musicxml"))) if fname not in available_pdf]

print(", ".join(available_musicxml))

for fname in available_musicxml:
    out_fn = path_fname(fname, "ly")
    with open(path_fname(fname, "musicxml"), "r", encoding="utf-8") as f:
        ly_source = musicxml_to_ly(f)
    res = subprocess.run(["lilypond", "-o", path_fname_short(fname, "pdf"), "-"], shell=True, input=ly_source, text=True, encoding="utf-8", capture_output = True)
    stderr = res.stderr.lower()
    if ("varov" in stderr) or ("chyba" in stderr):
        print(fname + " bad")
        with open(path_fname(fname, "ly"), "w", encoding="utf-8") as f:
            f.write(ly_source)
        with open(path_fname(fname, "log"), "w", encoding="utf-8") as f:
            f.write(res.stderr)