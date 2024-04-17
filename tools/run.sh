#!/usr/bin/env bash

# Note: this script assumes you have PNG sources in ./subset1
#
# Make sure ./output is empty; this script doesn't delete it
# (for safety), but bad things happen if it isn't.
#
# Obviously, all these programs should be their latest versions
# and somewhere on your $PATH.

set -e

# step 1: build other format sources
for file in subset1/*.png; do 
    # errors here are intended if the file already exists
    ffmpeg -loglevel 31 -n -i $file ${file%.png}.ppm || true;
done

# step 2: generate images
# note: this will take a very long time!
python compare.py subset1

# step 3: create PNG for non-jpeg output
cd output
for file in */AV1/*.avif; do
    avifdec -d 8 $file ${file%.avif}.png;
done
for file in */FLIF/*.flif; do
    flif $file ${file%.flif}.png;
done
for file in */HEIF/*.bpg; do
    heif-convert $file ${file%.heif}.png;
done
for file in */JPEGXL/*.jxl; do
    djxl $file ${file%.jxl}.png;
done
for file in */JPEGXR/*.jxr; do
    JxrDecApp -o $file.bmp -i $file;
    ffmpeg -i $file.bmp ${file%.jxr}.png;
    rm $file.bmp;
done

# step 4: recompress PNG for web upload
parallel ect --strict -9 ::: */*/*.png

# step 5 (currently manual):
# 1. move the contents of the output folder to the correct location
# in the image-format-comparisons project.
# 2. Make sure imagecomparisons.json contains the correct metadata
# for all the files.
