#!/usr/bin/env bash

# Note: this script assumes you have PNG sources in ./subset1
#
# Make sure ./output is empty; this script doesn't delete it
# (for safety), but bad things happen if it isn't.
#
# Obviously, all these programs should be their latest versions
# and somewhere on your $PATH.

# step 1: build other format sources
for file in subset1/*.png; do 
    ffmpeg -n -i $file ${file%.png}.y4m;
    ffmpeg -n -i $file ${file%.png}.ppm;
done

# step 2: generate images
# note: this will take a very long time!
python compare.py subset1

# step 3: create PNG for non-jpeg output
cd output
for file in */AV1/*.ivf; do
    aomdec $file -o $file.y4m;
    ffmpeg -i $file.y4m ${file%.ivf}.png;
    rm $file.y4m;
    # also put AV1 in standard container 
    MP4Box -add-image $file:primary -ab avif -ab miaf -new ${file%.ivf}.avif;
    rm $file;
done
for file in */BPG/*.bpg; do
    bpgdec -o ${file%.bpg}.png $file;
done
for file in */FLIF/*.flif; do
    flif $file ${file%.flif}.png;
done
for file in */JPEGXL/*.jxl; do
    djpegxl $file ${file%.flif}.png;
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
