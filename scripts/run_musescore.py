import os
import subprocess
import json
from updateablezipfile import UpdateableZipFile
from lxml import etree
from glob import iglob

def pure_fname(fname):
    return os.path.splitext(os.path.basename(fname))[0]

def path_fname(fname, ext):
    return "../" + ext + "/" + fname + "." + ext

def star_path(ext):
    return "../" + ext + "/*." + ext

parser = etree.XMLParser(remove_blank_text=True)

musescore_exe = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"

# two runs because MuseScore cannot use styles when exporting to PDF
# https://musescore.org/en/node/102421

available_pdf = set(map(pure_fname, iglob(star_path("pdf"))))
available_musicxml = [fname for fname in map(pure_fname, iglob(star_path("musicxml"))) if fname not in available_pdf]

print(", ".join(available_musicxml))

job_mscz = [{"in": path_fname(fname, "musicxml"), "out": path_fname(fname, "mscz")} for fname in available_musicxml]
job_pdf = [{"in": path_fname(fname, "mscz"), "out": path_fname(fname, "pdf")} for fname in available_musicxml]

with open("job_mscz.json", "w") as f:
    json.dump(job_mscz, f)

with open("job_pdf.json", "w") as f:
    json.dump(job_pdf, f)

subprocess.run([musescore_exe, "-S", os.path.abspath("plain.mss"), "-j", "job_mscz.json"])

for fname in available_musicxml:
    mscz_fn = path_fname(fname, "mscz")
    mscx_fn = fname + ".mscx"
    with UpdateableZipFile(mscz_fn, "r") as zip:
        with zip.open(mscx_fn, "r") as f:
            xml = etree.parse(f, parser)
    root = xml.getroot()
    part = root.find(".//Part")
    for staff in part.iterfind("Staff"):
        etree.SubElement(staff, "mergeMatchingRests").text = "1"
    with UpdateableZipFile(mscz_fn, "a") as zip:
        zip.remove_file(mscx_fn)
        with zip.open(mscx_fn, "w") as f:
            xml.write(f, pretty_print=True, xml_declaration=True, encoding="utf-8")

subprocess.run([musescore_exe, "-j", "job_pdf.json"])