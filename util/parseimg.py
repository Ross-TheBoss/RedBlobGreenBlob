#!/usr/bin/env python3
import PIL
import argparse

from PIL import Image

def hex_to_rgb(s):
    return tuple(int(s[1:][x:x+2],base=16) for x in range(0,6,2))

with open("palette.txt","r") as p:
    colours = list(map(hex_to_rgb,p.readlines()))

# Realistic Palette
CHARS = "45 1     23  " + \
        "6     0      " + \
        "             " + \
        "             " + \
        "             " + \
        " ) * (       "

PALETTE = dict(zip(colours,CHARS))
IPALETTE = dict(zip(CHARS,colours))

parser = argparse.ArgumentParser()
parser.add_argument("file",help="the image")
parser.add_argument("destination",help="the level file")
parser.add_argument("-i",action="store_true",help="perform the reverse process")

args = parser.parse_args()

BG = (255,255,255)

if not args.i:
    img = Image.open(args.file)

    data = list(img.getdata())
    level = ""
    for i,pix in enumerate(data,start=1):
        if i % img.width == 0:
            level += "\n"
        elif pix == BG:
            level += " "
        else:
            level += PALETTE[pix]

    with open(args.destination,"w") as f:
        f.write(level)
else:
    with open(args.file,"r") as f:
        content = f.read()

    width = content.index("\n")
    height = content.count("\n")

    print(width,height)

    img = PIL.Image.new("RGB",(width,height),"white") 
    for i,ch in enumerate(content):
        print(ch,end="")

        if not ch in ["\n"," "]:
            img.putpixel((i % (width + 1),i // (width + 1)),IPALETTE[ch])

    img.save("test.png","PNG")

    
            
        
