import os
import sys
from lxml import etree
import argparse
from itertools import islice, chain
from collections import Counter
from numpy import gcd
import re

def measure_duration(measure, voice):
    return sum(int(n.findtext("duration")) for n in measure.iterchildren("note") if (n.find("chord") is None) and (n.findtext("voice") == voice))

def add_next(el, tag):
    el.addnext(etree.Element(tag))
    return el.getnext()

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--force", action=argparse.BooleanOptionalAction)
parser.add_argument("-N", "--no_breath_marks", action=argparse.BooleanOptionalAction)
parser.add_argument("files", nargs="*", type=argparse.FileType("r", encoding="utf-8"), default=sys.stdin)
args = parser.parse_args()

bad_elements = ["miscellaneous", "defaults", "supports", "print", "direction", "volume", "midi-program", "staff-details", "display-step", "display-octave", "work", "rights", "part-group", "virtual-instrument", "mode", "instrument"]
bad_attributes = ["width", "default-x", "default-y", "bezier-x", "bezier-y", "color", "print-object"]

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
    part = root.find("part")
    measures = list(part.iterchildren("measure"))

    # remove bad elements
    for el in chain(root.iter(*bad_elements), islice(root.iter("attributes"), 1, None)):
        el.getparent().remove(el)

    # remove bad attributes
    for el in root.iter():
        for attr in bad_attributes:
            if attr in el.attrib:
                del el.attrib[attr]

    # common data
    work = etree.Element("work")
    work_number = etree.SubElement(work, "work-number")
    work_number.text = base_fname_noext.lstrip("0")
    root.insert(0, work)

    score_part = root.find(".//score-part")
    part_name = score_part.find("part-name")
    part_name.text = "Organ"
    add_next(part_name, "part-abbreviation").text = "Organ"
    score_instrument = score_part.find("score-instrument")
    score_instrument.find("instrument-name").text = "Organ"
    midi_instrument = add_next(score_instrument, "midi-instrument")
    midi_instrument.set("id", "P1-I1")
    midi_name = etree.SubElement(midi_instrument, "midi-name")
    midi_name.text = "Church Organ"
    midi_bank = etree.SubElement(midi_instrument, "midi-bank")
    midi_bank.text = "20"

    encoding = root.find(".//encoding")
    for tag in ["accidental", "beam", "stem"]:
        etree.SubElement(encoding, "supports", element=tag, type="yes")

    add_next(encoding, "source").text = "Varhanní doprovod k mešním zpěvům, k hymnům pro denní modlitbu církve a ke zpěvům s odpovědí lidu; Česká liturgická komise, Praha 1990"


    # normalize voices
    for voice in part.iter("voice"):
        if voice.text == "3":
            voice.text = "5"
        elif voice.text == "4":
            voice.text = "6"

    # assign voices to chord notes
    for chord in part.iter("chord"):
        chord_note = chord.getparent()
        if chord_note.find("voice") is None:
            voice = etree.Element("voice")
            prev_note = chord_note.getprevious()
            voice.text = prev_note.findtext("voice")
            chord_note.find("type").addprevious(voice)

    # minimize durations
    divisions = root.find(".//divisions")
    div_val = int(divisions.text)
    durations = list(root.iter("duration"))
    dur_values = [int(d.text) for d in durations]
    dur_values.append(div_val)
    dur_gcd = gcd.reduce(dur_values)
    # print(dur_gcd)
    if dur_gcd != 1:
        for duration, val in zip(durations, dur_values):
            duration.text = str(val // dur_gcd)
        divisions.text = str(div_val // dur_gcd)

    # add final barline
    final_measure = measures[-1]
    final_barline = etree.SubElement(final_measure, "barline", location="right")
    etree.SubElement(final_barline, "bar-style").text = "light-heavy"

    # MusicXML version
    root.set("version", "4.0.2")
    xml.docinfo.public_id = "-//Recordare//DTD MusicXML 4.0.2 Partwise//EN"

    # check breath marks
    for bm in root.iter("breath-mark"):
        note = bm.getparent().getparent().getparent()
        if note.findtext("voice") not in ["1", "5"]:
            print(fname + ": breath mark in wrong voice in measure " + note.getparent().get("number"))

    # check measure durations
    for measure in measures:
        voice_durations = Counter()
        for n in measure.iterchildren("note"):
            if (n.find("chord") is not None):
                continue
            voice = n.findtext("voice")
            voice_durations[voice] += int(n.findtext("duration"))
        if len(set(voice_durations.values())) != 1:
            print(fname + ": different voice durations in measure " + measure.get("number"))

    # renumber if pickup measure
    first_measure = measures[0]
    if first_measure.find("attributes").find("time") is not None:
        second_measure = measures[1]
        first_duration, second_duration = (measure_duration(m, "1") for m in (first_measure, second_measure))
        if first_duration != second_duration:
            for i, measure in enumerate(measures):
                measure.set("number", str(i))
                if not i:
                    measure.set("implicit", "yes")
            for i, comment in enumerate(part.iterchildren(etree.Comment)):
                comment.text = re.sub(r" \d+ ", " "+str(i)+" ", comment.text, count=1)


    xml.write(fname_new, pretty_print=True, xml_declaration=True, encoding="utf-8")