import os
import sys
from lxml import etree
import argparse
from itertools import islice, chain
from copy import deepcopy
from collections import Counter
from breath_marks import add_breath_marks, get_omr_tree

def measure_duration(voice):
    return sum(int(n.findtext("duration")) for n in measure.iterchildren("note") if (n.find("chord") is None) and (n.findtext("voice") == voice))

complementary_voice = {"1": "2", "2": "1", "5": "6", "6": "5"}

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

    # common data

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

    # add matching rests

    measures_to_fix = set()

    existing_rests = list(root.iter("rest"))
    for rest in existing_rests:
        rest_note = rest.getparent()
        voice = rest_note.findtext("voice")
        measure = rest_note.getparent()

        prev_duration = 0
        for note in measure.iterchildren("note"):
            if note is rest_note:
                break
            elif (note.findtext("voice") == voice) and (note.find("chord") is None):
                prev_duration += int(note.findtext("duration"))

        comp_voice = complementary_voice[voice]
        comp_duration = 0
        overflow = False
        last_comp_note = None
        for note in filter(lambda n: n.findtext("voice") == comp_voice, measure.iterchildren("note")):
            # if (note.findtext("voice") == comp_voice) and (note.find("chord") is None):
            if note.find("chord") is None:
                comp_duration += int(note.findtext("duration"))
                if comp_duration > prev_duration:
                    overflow = True
                    break

        if (not overflow) and (comp_duration < prev_duration):
            print(fname + ": non-matching rest in measure " + measure.get("number"))
            continue

        if (not overflow) or (note.find("rest") is None):
            if overflow:
                note = note.getprevious()
            new_rest_note = deepcopy(rest_note)
            new_rest_note.find("voice").text = comp_voice
            note.addnext(new_rest_note)
            measures_to_fix.add(measure)


    # fix measures where rests were added
    for measure in measures_to_fix:
        total_duration = str(measure_duration("1"))
        for backup in measure.iterchildren("backup"):
            backup.find("duration").text = total_duration


    # check measure durations
    for measure in root.find("part").iterchildren("measure"):
        voice_durations = Counter()
        for n in measure.iterchildren("note"):
            if (n.find("chord") is not None):
                continue
            voice = n.findtext("voice")
            voice_durations[voice] += int(n.findtext("duration"))
        if len(set(voice_durations.values())) != 1:
            print(fname + ": different voice durations in measure " + measure.get("number"))


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