from lxml import etree
from collections import deque
import re

voices = [1, 2, 5, 6]
voice_names = ["soprano", "alto", "tenor", "bass"]

octave_marks = [",,,", ",,", ",", "", "'", "''", "'''"]
note_lens = {"16th": "16", "eighth": "8", "quarter": "4", "half": "2", "whole": "1"}
keys = {0: "c", 1: "g", 2: "d", 3: "a", 4: "e", 5: "b", -1: "f", -2: "bes", -3: "es", -4: "as", -5: "des"}

def note_to_ly(note):
    if (pitch := note.find("pitch")) is not None:
        note_str = pitch.findtext("step").lower()
        if (alter := pitch.find("alter")) is not None:
            note_str += "is" if alter.text == "1" else "es"
        note_str += octave_marks[int(pitch.findtext("octave"))]
        if (accidental := note.find("accidental")) is not None:
            if accidental.get("parentheses") == "yes":
                note_str += "?"
            else:
                note_str += "!"
    else:
        note_str = "r"
    note_str += note_lens[note.findtext("type")]
    if note.find("dot") is not None:
        note_str += "."
    return note_str

with open("template.ly", "r", encoding="utf-8") as f:
    template = f.read()


def musicxml_to_ly(xml_file):
    xml = etree.parse(xml_file)

    root = xml.getroot()
    part = root.find("part")

    measures = []
    for measure in part.iterchildren("measure"):
        if measure.get("number").startswith("X"):
            prev_measure = measures[-1]
            for el in measure.iterchildren():
                prev_measure.append(el)
            part.remove(measure)
        else:
            measures.append(measure)

    attributes = measures[0].find("attributes")

    divisions = int(attributes.findtext("divisions"))
    if (key_el := attributes.find("key")) is not None:
        key_fifths = int(key_el.findtext("fifths"))
        key = keys[key_fifths] + " \\major"
    else:
        key = "c \\major"

    free_time = attributes.find("time") is None

    voice_total_str = ""

    for voice, vname in zip(voices, voice_names):
        repeat_open = False
        add_starting_repeat = False
        voice_output = []
        for measure in measures:
            measure_duration = 0
            measure_els = deque()
            tags_to_iterate = ["note"]
            if voice == 1:
                tags_to_iterate.append("barline")
                if not free_time:
                    tags_to_iterate.append("attributes")
            for el in measure.iterchildren(*tags_to_iterate):
                if el.tag == "note":
                    if int(el.findtext("voice")) != voice:
                        continue
                    note_str = note_to_ly(el)

                    if el.find("chord") is None:
                        measure_duration += int(el.findtext("duration"))
                        measure_els.append(note_str)
                    else:
                        intermediate_stuff = deque()
                        prev_note = measure_els.pop()
                        while (len_match := re.search(r"\d+\.?", prev_note)) is None:
                            intermediate_stuff.appendleft(prev_note)
                            prev_note = measure_els.pop()
                        prev_note, note_str = (re.sub(r"\d+\.?", "", n) for n in [prev_note, note_str])
                        measure_els.extend(["<", prev_note, note_str, ">"+len_match[0]])
                        measure_els.extend(intermediate_stuff)

                    if (beam := el.find("beam")) is not None:
                        if beam.text == "begin":
                            measure_els.append("[")
                        elif beam.text == "end":
                            measure_els.append("]")

                    if (notations := el.find("notations")) is not None:
                        if notations.find("fermata") is not None:
                            measure_els.append("\\fermata")
                        if (tied := notations.find("tied")) is not None:
                            if tied.get("type") != "stop":
                                measure_els.append("~")
                        if (slur := notations.find("slur")) is not None:
                            slur_type = slur.get("type")
                            if slur_type == "start":
                                measure_els.append("(")
                            elif slur_type == "stop":
                                measure_els.append(")")
                        if notations.find(".//breath-mark") is not None:
                            measure_els.append("\\breathe")

                elif el.tag == "barline":
                    if (repeat := el.find("repeat")) is not None:
                        if repeat.get("direction") == "forward":
                            measure_els.append("\\repeat volta 2 {")
                            repeat_open = True
                        else:
                            measure_els.append("}")
                            if not repeat_open:
                                add_starting_repeat = True
                            repeat_open = False
                    else:
                        if el.findtext("bar-style") == "light-light":
                            measure_els.append('\\bar "||"')

                elif el.tag == "attributes":
                    if (time_el := el.find("time")) is not None:
                        time_sig = time_el.findtext("beats") + "/" + time_el.findtext("beat-type")
                        measure_els.append("\\time " + time_sig)

            sixteens = str((4*measure_duration) // divisions)
            if free_time:
                measure_els.appendleft("\\time " + sixteens + "/16")
            elif measure.get("number") == "0":
                measure_els.appendleft("\\partial 16*" + sixteens)
            voice_output.append(measure_els)

        if add_starting_repeat:
            voice_output[0].appendleft("\\repeat volta 2 {")

        voice_start_els = []

        voice_start_els.append("\\clef " + ('"bass"' if voice > 2 else '"treble"'))
        voice_start_els.append("\\key " + key)
        voice_start = " ".join(voice_start_els)

        voice_str = " |\n".join((" ".join(m) for m in voice_output))

        voice_total_str += vname + " = {\n" + voice_start + "\n" + voice_str + ' \\bar "|."\n}\n\n\n'

    ly_output = template.replace("% VOICES", voice_total_str, 1)
    ly_output = ly_output.replace('"TITLE"', '"'+root.find("work").findtext("work-number")+'"', 1)
    if free_time:
        ly_output = ly_output.replace("% TIME", "\\omit TimeSignature", 1)

    return ly_output