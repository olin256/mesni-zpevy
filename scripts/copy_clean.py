import os
import glob
import shutil

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-o", "--overwrite", action=argparse.BooleanOptionalAction)
overwrite = parser.parse_args().overwrite

for fname in glob.iglob("../xml_raw/*_clean.xml"):
    num = os.path.basename(fname)[:3]
    target = "../musicxml/"+num+".musicxml"
    if not overwrite:
        if os.path.isfile(target):
            print("skipping " + num)
            continue

    shutil.copy(fname, target)