#!/usr/bin/env python3
import os.path
import sys

# Enable running the RedBlobGreenBlob package in a non-standard location.
rgblob_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if rgblob_dir not in sys.path:
    sys.path.insert(0, rgblob_dir)

from RedBlobGreenBlob.ui import main
main()
