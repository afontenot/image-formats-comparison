image-formats-comparison
==================
http://afontenot.github.io/image-formats-comparison/

This is a clean fork of [the version by WyohKnott](https://github.com/WyohKnott/image-formats-comparison), removing unnecessary files and the large git history.

The following changes have been made to the previous version:

 * Instead of using the original Daala test images, which are 4:2:0 subsampled, I recreated the image set from the original high-res sources, downscaling to the same sized source images as the Daala set, but not subsampled (4:4:4).
 * I wrote my own script for generating the comparison images, which uses a binary search to quickly find the quality level that generates the image with the closest file size to the target. You can find my work in the `tools` directory.
 * All images that can't be rendered by the browser are now served as PNGs, instead of trying (in some cases) to decode with Javascript. The images were heavily compressed (losslessly) to take up less space, and this requires less decoding power on the viewer end.
 * A number of codecs from the previous version were dropped. These are Daala, KDU (JPEG2000), OpenJpeg (JPEG2000), PIK, VP9, and WebP. WebP was dropped because it doesn't support unsubsampled images, making it a bad candidate for a high quality photography codec. PIK was dropped because I couldn't get it running on my computer; I think it might require newer CPU features. I'd like to add it back in the future if possible. OpenJpeg was removed because the results seemed to be fairly low quality. KDU was removed because it crashed on input images with certain characters in the filename. I might work on adding it back later. As for Daala and VP9, I think their features have been mostly subsumed into newer codecs that current development effort is focused on.
 * **JPEGXL** was added to the comparison.
 * All codecs were updated to their latest available releases, see below.
 * I fixed a bug where the settings weren't restored from the URL when refreshing or sharing a link.
 * I fixed a bug where the image loaded first when the image was changed would have an incorrect bits / pixel calculation.

The fork currently has the following flaws:

 * Some codecs you might be interested in are missing, currently (see above). I tried to add Guetzli, but couldn't get it working — below a certain quality level the output file is always the same size (even after you remove the check for quality >= 84).
 * My repository doesn't have the generated [report](https://wyohknott.github.io/image-formats-comparison/report.html) that the original has. The biggest reason is that because I'm using a binary search to find the closest matching file size, I don't generate as many data points for the graphs. (The full report takes forever.) But also, I think objective metrics are not very useful. Even Netflix's state of the art VMAF shows KDU supposedly blowing the competition away, but I think this is very clearly not the case. (At best, KDU is competitive with other top codecs and interestingly different from them.) I recommend using your eyes; after all, that's what this comparison tool is for!
 * Subset2 is entirely missing right now. I haven't recreated the image set from the sources yet.
