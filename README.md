image-formats-comparison
==================
http://afontenot.github.io/image-formats-comparison/

This is a clean fork of [the version by WyohKnott](https://github.com/WyohKnott/image-formats-comparison), removing unnecessary files and the large git history, along with a large number of improvements.

Changes I have made are all documented [on the main page of the app](http://afontenot.github.io/image-formats-comparison/).

The fork currently has the following flaws:

 * Some codecs you might be interested in are missing, currently (see above). I tried to add Guetzli, but couldn't get it working — below a certain quality level the output file is always the same size (even after you remove the check for quality >= 84).
 * My repository doesn't have the generated [report](https://wyohknott.github.io/image-formats-comparison/report.html) that the original has. The biggest reason is that because I'm using a binary search to find the closest matching file size, I don't generate as many data points for the graphs. (The full report takes forever.) But also, I think objective metrics are not very useful. Even Netflix's state of the art VMAF shows KDU supposedly blowing the competition away, but I think this is very clearly not the case. (At best, KDU is competitive with other top codecs and interestingly different from them.) I recommend using your eyes; after all, that's what this comparison tool is for!
 * Subset2 is entirely missing right now. I haven't recreated the image set from the sources yet.
 * The test is more geared to photography than typical web images, which are usually subsampled. An alternative comparison with subsampled images (and including webp) might be added in the future.
