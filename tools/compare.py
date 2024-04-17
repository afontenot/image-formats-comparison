import os
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from glob import glob
from multiprocessing import Pool
from shutil import copy, rmtree


jxl_size_cmd = "cjxl --disable_output --resampling 1 -e 9 {0}"
jxl_size_regex = re.compile("Compressed to ([.0-9]+) (\w+)")
jxl_size_abbr = {"bytes": 1, "kB": 1024, "MB": 1024 ** 2}


codecs = {
    "jpegxl": {
        "ext": ".jxl",
        "input_ext": ".png",
        "cmd": "cjxl --resampling 1 -e 9 -d {0} {1} {2}",
        "low_q": 0,
        "high_q": 250,
        "frac": 10,
        "quantizer": True
    },
    "jpegli": {
        "ext": ".jpg",
        "input_ext": ".png",
        "cmd": "cjpegli --chroma_subsampling=444 -d {0} {1} {2}",
        "low_q": 0,
        "high_q": 250,
        "frac": 10,
        "quantizer": True
    },
    "av1": {
        "ext": ".avif",
        "input_ext": ".png",
        "cmd": 'avifenc --depth 10 --yuv 444 --range full --speed 0 -c aom --min {0} --max {0} {1} {2}',
        "low_q": 0,
        "high_q": 63,
        "quantizer": True
    },
    "heif": {
        "ext": ".heif",
        "input_ext": ".png",
        "cmd": "heif-enc -p chroma=444 -p x265:p=veryslow -q {0} -o {2} {1}",
        "low_q": 0,
        "high_q": 100,
        "quantizer": False
    },
    "flif": {
        "ext": ".flif",
        "input_ext": ".png",
        "cmd": "flif -E 95 -Q {0} {1} {2}",
        "low_q": -329,
        "high_q": 79,
        "quantizer": False
    },
    "jpegxr": {
        "ext": ".jxr",
        "input_ext": ".ppm",
        "cmd": "JxrEncApp -d 3 -q {0} -o {2} -i {1}",
        "low_q": 1,
        "high_q": 255,
        "quantizer": True
    },
    "mozjpeg": {
        "ext": ".jpg",
        "input_ext": ".png",
        "cmd": "mozjpeg -sample 1x1 -quality {0} -outfile {2} {1}",
        "low_q": 5,
        "high_q": 95,
        "quantizer": False
    }
}


def mkdir(directory):
    try:
        os.mkdir(directory)
    except FileExistsError:
        pass


def split(cmd):
    lex = shlex.shlex(cmd)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)


def run_external_cmd(cmd):
    rv = subprocess.run(split(cmd), capture_output=True)
    if rv.returncode != 0:
        print("\nERROR:", cmd)
        print(rv.stderr)
        return None
    return rv


# not thread safe, but we don't care about a little jank
def update_progress(i, end, codec, path):
    pct = i * 100 // end
    line = "\r\x1b[0K" + f"[{pct:3}%] <{codec}> {path}"
    print(line[:80], end="")


def get_target_size(image):
    line = "\r\x1b[0K" + f"Getting size for {image}"
    print(line[:80], end="")
    cmd = jxl_size_cmd.format(image + ".png")
    rv = run_external_cmd(cmd)
    res = jxl_size_regex.search(rv.stderr.decode("utf-8")).groups()
    return float(res[0]) * jxl_size_abbr[res[1]]


def get_target_sizes(images):
    with Pool(8) as p:
        return p.map(get_target_size, images, chunksize=1)


def convert(codec, image_src, q):
    image_src_name = os.path.basename(image_src)
    ext = codecs[codec]["ext"]
    image_out = f"/tmp/{codec}_{image_src_name}/{codec}_{image_src_name}_{q}{ext}"
    image_src += codecs[codec]["input_ext"]
    cmd = codecs[codec]["cmd"].format(q, image_src, image_out)
    rv = run_external_cmd(cmd)
    sz = os.path.getsize(image_out)
    return image_out, sz


def search(args):
    index, count, codec, image_src, target_sizes, size_names = args
    image_src_name = os.path.basename(image_src)
    update_progress(index, count, codec, image_src_name)
    mkdir(f"/tmp/{codec}_{image_src_name}/")
    cache = defaultdict(None)
    for target_size, sz_n in zip(target_sizes, size_names):
        exact = codecs[codec].get("exact")
        # codec has built-in ability to target a bitrate, no search
        if exact is not None:
            if exact == "sz":
                image, sz = convert(codec, image_src, target_size)
            copy(image, f"output/{sz_n}/{codec.upper()}/{image_src_name}{ext}")
        else:
            low, high = codecs[codec]["low_q"], codecs[codec]["high_q"]
            best = low + (high - low) // 2
            while low <= high:
                middle = low + (high - low) // 2
                if not cache.get(middle):
                    # some codecs *require* support for fractional q
                    # this is an ugly hack to support this
                    quality = middle
                    frac = codecs[codec].get("frac")
                    if frac is not None:
                        quality /= frac
                    cache[middle] = convert(codec, image_src, quality)
                fn, sz = cache[middle]
                # special cases for reversed (quantizer) mode
                if sz < target_size:
                    if codecs[codec]["quantizer"]:
                        high = middle - 1
                    else:
                        low = middle + 1
                elif sz > target_size:
                    if codecs[codec]["quantizer"]:
                        low = middle + 1
                    else:
                        high = middle - 1
                else:
                    best = middle
                    break
                if abs(sz - target_size) < abs(cache[best][1] - target_size):
                    best = middle
            ext = codecs[codec]["ext"]
            copy(cache[best][0], f"output/{sz_n}/{codec.upper()}/{image_src_name}{ext}")
    rmtree(f"/tmp/{codec}_{image_src_name}/")


if __name__ == "__main__":
    args = sys.argv
    if len(args) < 2:
        print(f"Usage: {args[0]} path_to_images")
        sys.exit()

    path_to_images = args[1]
    base_files = glob(path_to_images + "/*.ppm")
    images = [fn[:-4] for fn in base_files]
    print("Getting target size for large image variants...")
    target_sizes = get_target_sizes(images)

    # stage zero: set up dirs
    print("\n\nSetting up search jobs...")
    size_names = ["large", "medium", "small", "tiny"]
    mkdir("output")
    for sz_n in size_names:
        mkdir("output/" + sz_n)
        for codec in codecs.keys():
            mkdir(f"output/{sz_n}/{codec.upper()}/")

    # stage one: build job pool
    jobs = []
    job_count = len(images) * len(codecs)
    idx = 0
    for image, sz in zip(images, target_sizes):
        for codec in codecs.keys():
            idx += 1
            jobs.append([idx, job_count, codec, image, [sz, sz // 2, sz // 3, sz // 4], size_names])

    # stage 2: run jobs
    print("Running search jobs...")
    with Pool() as p:
        p.map(search, jobs, chunksize=1)

