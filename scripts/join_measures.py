import os
import sys
from lxml import etree
import argparse
from collections import deque

parser = argparse.ArgumentParser()
parser.add_argument("file", type=argparse.FileType("r", encoding="utf-8"), default=sys.stdin)
parser.add_argument("measures", nargs="*", type=int)
args = parser.parse_args()

parser = etree.XMLParser(remove_blank_text=True)

f = args.file
fname = f.name
fname_noext, ext = os.path.splitext(fname)
base_fname_noext = os.path.basename(fname_noext)

fname_new = fname_noext + "_joined" + ext
xml = etree.parse(f, parser)
f.close()

root = xml.getroot()

part = root.find("part")
measures = list(part.iterchildren("measure"))

for m_no in args.measures:
    m1 = measures[m_no-1]

    # remove comment
    part.remove(m1.getnext())

    m2 = m1.getnext()

    tot_duration = int(m1.find("backup").find("duration").text)
    tot_duration += int(m2.find("backup").find("duration").text)
    tot_duration = str(tot_duration)

    m_new = etree.Element("measure")

    qs = [deque(m1), deque(m2)]
    source = qs[0]

    while True:
        if not source:
            if source is qs[1]:
                break
            else:
                source = qs[1]
                continue
        el = source.popleft()
        if el.tag == "backup":
            if source is qs[0]:
                source = qs[1]
            else:
                source = qs[0]
                backup = etree.SubElement(m_new, "backup")
                etree.SubElement(backup, "duration").text = tot_duration
        else:
            m_new.append(el)

    part.remove(m2)
    m1.addnext(m_new)
    part.remove(m1)

for i, m in enumerate(part.iterchildren("measure"), 1):
    m.set("number", str(i))

xml.write(fname_new, pretty_print=True, xml_declaration=True, encoding="utf-8")