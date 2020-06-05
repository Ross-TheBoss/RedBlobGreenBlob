#!/usr/bin/env python3
import PIL
import argparse

from PIL import Image

PALETTE = {(0,0,0):"0",(255,0,0):")",(0,255,0):"("}

parser = argparse.ArgumentParser()
parser.add_argument("file",help="the image")
parser.add_argument("destination",help="the level file")

args = parser.parse_args()

BG = (255,255,255)

img = Image.open(args.file)

data = list(img.getdata())
level = ""
for i,pix in enumerate(data,start=1):
    if pix == BG:
        level += " "
    else:
        level += PALETTE[pix]
    if i % img.width == 0:
        level += "\n"

with open(args.destination,"w") as f:
    f.write(level)
