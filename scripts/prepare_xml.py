import os
import sys
from lxml import etree
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--force", action=argparse.BooleanOptionalAction)
parser.add_argument("files", nargs="*", type=argparse.FileType("r", encoding="utf-8"), default=sys.stdin)
args = parser.parse_args()

bad_elements = ["miscellaneous", "defaults", "supports", "print", "direction", "volume", "midi-program"]
bad_attributes = ["width", "default-x", "default-y"]

parser = etree.XMLParser(remove_blank_text=True)

for f in args.files:
    fname_noext, ext = os.path.splitext(f.name)
    if not args.force:
        if fname_noext.endswith("_clean"):
            print("skipping " + f.name)
            f.close()
            continue

    fname_new = fname_noext + "_clean" + ext
    xml = etree.parse(f, parser)
    f.close()

    root = xml.getroot()

    # remove bad elements
    for el in root.iter(*bad_elements):
        el.getparent().remove(el)

    # remove bad attributes
    for el in root.iter():
        for attr in bad_attributes:
            if attr in el.attrib:
                del el.attrib[attr]

    root.find(".//source").text = "Varhanní doprovod k mešním zpěvům, k hymnům pro denní modlitbu církve a ke zpěvům s odpovědí lidu; Česká liturgická komise, Praha 1990"

    work = etree.Element("work")
    work_number = etree.SubElement(work, "work-number")
    work_number.text = os.path.basename(fname_noext).lstrip("0")
    root.insert(0, work)

    score_part = root.find(".//score-part")
    score_part.find("part-name").text = "Organ"
    score_part.find("part-abbreviation").text = "Organ"
    score_instrument = score_part.find("score-instrument")
    score_instrument.find("instrument-name").text = "Organ"
    instrument_sound = etree.SubElement(score_instrument, "instrument-sound")
    instrument_sound.text = "keyboard.organ.pipe"
    midi_instrument = score_part.find("midi-instrument")
    midi_name = etree.SubElement(midi_instrument, "midi-name")
    midi_name.text = "Church Organ"
    midi_bank = etree.SubElement(midi_instrument, "midi-bank")
    midi_bank.text = "20"


    xml.write(fname_new, pretty_print=True, xml_declaration=True, encoding="utf-8")