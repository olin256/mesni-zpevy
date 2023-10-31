import glob
import os
import subprocess
import json

def pure_fname(fname):
    return os.path.splitext(os.path.basename(fname))[0]

musescore_exe = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"

# two runs because MuseScore cannot use styles when exporting to PDF
# https://musescore.org/en/node/102421

job_mscz = [{"in": fname, "out": "../mscz/"+pure_fname(fname)+".mscz"} for fname in glob.iglob("../musicxml/*.musicxml")]
job_pdf = [{"in": "../mscz/"+fname+".mscz", "out": "../pdf/"+fname+".pdf"} for fname in map(pure_fname, glob.iglob("../musicxml/*.musicxml"))]

with open("job_mscz.json", "w") as f:
    json.dump(job_mscz, f)

with open("job_pdf.json", "w") as f:
    json.dump(job_pdf, f)

subprocess.run([musescore_exe, "-S", os.path.abspath("plain.mss"), "-j", "job_mscz.json"])
subprocess.run([musescore_exe, "-j", "job_pdf.json"])