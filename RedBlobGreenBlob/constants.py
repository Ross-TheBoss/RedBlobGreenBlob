"""
Provides global constant values for RedBlobGreenBlob.
"""
import os.path

# Directories

ROOTDIR = os.path.dirname(__file__)

SOUNDDIR = os.path.join(ROOTDIR,"sounds")
IMGDIR = os.path.join(ROOTDIR,"images")
LEVELDIR = os.path.join(ROOTDIR,"levels")

# Sounds

# 8-bit Platformer SFX commissioned by Mark McCorkle for OpenGameArt.org ( http://opengameart.org )
JUMPSOUNDFILE = os.path.join(SOUNDDIR,"jump.ogg")
SELECTSOUNDFILE = os.path.join(SOUNDDIR,"select.ogg")
POWERUPSOUNDFILE = os.path.join(SOUNDDIR,"powerup.ogg")
DESTROYSOUNDFILE = os.path.join(SOUNDDIR,"destroy.ogg") # Orginally Explosion.wav
