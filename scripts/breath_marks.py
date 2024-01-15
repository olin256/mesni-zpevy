from lxml import etree
from collections import deque
from zipfile import ZipFile

def get_omr_tree(omr_file, xml_parser):
    with ZipFile(omr_file) as zip:
        with zip.open("sheet#1/sheet#1.xml") as f:
            omr_tree = etree.parse(f, xml_parser)
    return omr_tree


def add_breath_marks(xml_tree, omr_tree):
    xml_root = xml_tree.getroot()
    omr_root = omr_tree.getroot()

    head_chords = {hch.get("id"): int(hch.find("bounds").get("x")) for hch in omr_root.iter("head-chord")}

    xml_notes = [n for n in xml_root.iter("note") if not n.xpath("rest|chord")]

    for voice, staff in [("1", 1), ("5", 0)]:
        voice_notes = [n for n in xml_notes if n.findtext("voice") == voice]

        skips = []
        last_segment = 0

        for system in omr_root.iter("system"):
            system_notes = []
            for measure in system.iter("measure"):
                curr_voice = next(v for v in measure.iterchildren("voice") if v.get("id") == voice)
                for vl in curr_voice.iter("value"):
                    chord_x = head_chords.get(vl.get("chord"))
                    if (chord_x is not None) and (vl.get("status") == "BEGIN"):
                        system_notes.append(chord_x)

            system_notes.sort()
            system_notes = deque(system_notes)
            system_notes.append(65535) # infty

            inters = system.find("sig").find("inters")
            breath_marks = [int(bm.find("bounds").get("x")) for bm in inters.iterchildren("breath-mark") if (int(bm.get("staff")) % 2) == staff]
            breath_marks.sort()
            breath_marks = deque(breath_marks)

            curr_skip = last_segment
            while breath_marks:
                bm_x = breath_marks.popleft()
                while (note_x := system_notes.popleft()) < bm_x:
                    curr_skip += 1
                skips.append(curr_skip)
                system_notes.appendleft(note_x)
                curr_skip = 0

            last_segment = len(system_notes) - 1

        if not skips:
            continue

        skips = deque(skips)

        curr_skip = skips.popleft()
        for note in voice_notes:
            if curr_skip == 1:
                notations = note.find("notations")
                if notations is None:
                    notations = etree.SubElement(note, "notations")
                articulations = etree.SubElement(notations, "articulations")
                etree.SubElement(articulations, "breath-mark")
                if skips:
                    curr_skip = skips.popleft()
                else:
                    break
            else:
                curr_skip -= 1