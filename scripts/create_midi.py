from music21 import converter, tempo, instrument, metadata
from glob import glob
from lxml import etree
from collections import Counter
from tqdm import tqdm
import os

def purify(fname):
    return os.path.splitext(os.path.basename(fname))[0]

def save_midi(score, folder, new_tempo, pure_fname):
    score.metadata = metadata.Metadata()
    song_no = pure_fname.lstrip("0")
    if folder == "organ":
        score.metadata.title = f"Doprovod k písni {song_no}"
        score.metadata.composer = (
            "Varhanní doprovod k mešním zpěvům, k hymnům pro denní modlitbu církve"
            "a ke zpěvům s odpovědí lidu; Česká liturgická komise, Praha 1990"
        )
    else:
        score.metadata.title = f"Píseň {song_no}"
    new_tempo = tempo.MetronomeMark(number=new_tempo)
    new_instrument = instrument.PipeOrgan() if folder == "organ" else instrument.Choir()
    for part in score.parts:
        for instr in part.recurse().getElementsByClass(instrument.Instrument):
            part.remove(instr)
        part.insert(0, new_instrument)
    score.insert(0, new_tempo)
    score.write("midi", fp=f"../midi_{folder}/{pure_fname}_{folder}.mid")

for fname in tqdm(glob("../musicxml/*.musicxml")):
    pure_fname = purify(fname)

    tree = etree.parse(fname)
    root = tree.getroot()

    note_counter = Counter()

    for note in root.iter("note"):
        if (note.findtext("voice") == "1") and (note.find("rest") is None):
            note_counter[note.findtext("type")] += 1

    if note_counter["eighth"] > note_counter["quarter"]:
        new_tempo = 70
    else:
        new_tempo = 100

    score = converter.parse(fname)
    save_midi(score, "organ", new_tempo, pure_fname)

    for el in root.iter("note", "backup"):
        if (voice := el.find("voice")) is not None:
            if voice.text == "1":
                continue
        el.getparent().remove(el)

    staves = root.find(".//staves")
    staves.text = "1"

    xml_string = etree.tostring(tree, encoding="utf-8", xml_declaration=True)
    score = converter.parse(xml_string, format='musicxml')

    save_midi(score, "voice", new_tempo, pure_fname)