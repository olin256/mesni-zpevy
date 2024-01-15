import os
import sys
from lxml import etree
import argparse
from itertools import islice, chain
from breath_marks import add_breath_marks, get_omr_tree

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--force", action=argparse.BooleanOptionalAction)
parser.add_argument("-N", "--no_breath_marks", action=argparse.BooleanOptionalAction)
parser.add_argument("files", nargs="*", type=argparse.FileType("r", encoding="utf-8"), default=sys.stdin)
args = parser.parse_args()

bad_elements = ["miscellaneous", "defaults", "supports", "print", "direction", "volume", "midi-program", "staff-details", "display-step", "display-octave"]
bad_attributes = ["width", "default-x", "default-y", "bezier-x", "bezier-y"]

parser = etree.XMLParser(remove_blank_text=True)

for f in args.files:
    fname = f.name
    fname_noext, ext = os.path.splitext(fname)
    base_fname_noext = os.path.basename(fname_noext)
    if not args.force:
        if fname_noext.endswith("_clean"):
            print("skipping " + fname)
            f.close()
            continue

    fname_new = fname_noext + "_clean" + ext
    xml = etree.parse(f, parser)
    f.close()

    root = xml.getroot()

    # remove bad elements
    for el in chain(root.iter(*bad_elements), islice(root.iter("attributes"), 1, None)):
        el.getparent().remove(el)

    # remove bad attributes
    for el in root.iter():
        for attr in bad_attributes:
            if attr in el.attrib:
                del el.attrib[attr]

    root.find(".//source").text = "Varhanní doprovod k mešním zpěvům, k hymnům pro denní modlitbu církve a ke zpěvům s odpovědí lidu; Česká liturgická komise, Praha 1990"

    work = etree.Element("work")
    work_number = etree.SubElement(work, "work-number")
    work_number.text = base_fname_noext.lstrip("0")
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

    encoding = root.find(".//encoding")
    for tag in ["accidental", "beam", "stem"]:
        etree.SubElement(encoding, "supports", element=tag, type="yes")

    # add breath marks, if possible
    if not args.no_breath_marks:
        omr_path = os.path.dirname(os.path.abspath(fname)) + "\\..\\omr\\" + base_fname_noext + ".omr"
        if os.path.isfile(omr_path):
            with open(omr_path, "rb") as omrf:
                omr_tree = get_omr_tree(omrf, parser)

            add_breath_marks(xml, omr_tree)
        else:
            print(fname + ": no omr file")


    xml.write(fname_new, pretty_print=True, xml_declaration=True, encoding="utf-8")