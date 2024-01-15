from lxml import etree
from collections import deque
from breath_marks import add_breath_marks, get_omr_tree
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("xml_file", type=argparse.FileType("r", encoding="utf-8"))
parser.add_argument("omr_file", type=argparse.FileType("rb"))
args = parser.parse_args()

xml_parser = etree.XMLParser(remove_blank_text=True)

fname = args.xml_file.name

xml_tree = etree.parse(args.xml_file, xml_parser)
args.xml_file.close()

omr_tree = get_omr_tree(args.omr_file, xml_parser)
args.omr_file.close()

add_breath_marks(xml_tree, omr_tree)

xml_tree.write(fname, pretty_print=True, xml_declaration=True, encoding="utf-8")