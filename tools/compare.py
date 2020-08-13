import os
import shlex
import subprocess
import sys
from collections import defaultdict
from glob import glob
from multiprocessing import Pool
from shutil import copy, rmtree

codecs = {
    "jpegxl": {
        "ext": ".jxl",
        "input_ext": ".png",
        "cmd": "cjpegxl -s 9 -d {0} {1} {2}",
        "low_q": 0,
        "high_q": 299,
        "quantizer": True,
        "frac": 10
        #"exact": "sz" # too slowww
    },
    "av1": {
        "ext": ".ivf",
        "input_ext": ".y4m",
        "cmd": "aomenc --i444 --passes=2 --end-usage=q --cq-level={0} --ivf -o {2} {1}",
        "low_q": 4,
        "high_q": 63,
        "quantizer": True
    },
    "bpg": {
        "ext": ".bpg",
        "input_ext": ".png",
        "cmd": "bpgenc -m 9 -f 444 -q {0} -o {2} {1}",
        "low_q": 1,
        "high_q": 51,
        "quantizer": True
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
        "cmd": "cjpeg -sample 1x1 -quality {0} -outfile {2} {1}",
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
    except Exception as e:
        return e

def split(cmd):
    lex = shlex.shlex(cmd)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)

def convert(codec, image_src, q):
    image_src_name = os.path.basename(image_src)
    ext = codecs[codec]["ext"]
    image_out = f"/tmp/{codec}_{image_src_name}/{codec}_{image_src_name}_{q}{ext}"
    image_src += codecs[codec]["input_ext"]
    cmd = codecs[codec]["cmd"].format(q, image_src, image_out)
    print("Running:", cmd)
    FNULL = open(os.devnull, 'w')
    rv = subprocess.call(split(cmd), stdout=FNULL, stderr=FNULL)
    if rv != 0:
        print("ERROR:", cmd)
        return None
    sz = os.path.getsize(image_out)
    return image_out, sz


def search(args):
    codec, image_src, target_sizes, size_names = args
    image_src_name = os.path.basename(image_src)
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
    base_files = glob(path_to_images + "/*.y4m")
    images = [(fn[:-4], os.path.getsize(fn)) for fn in base_files]
    
    # stage zero: set up dirs
    size_names = ["large", "medium", "small", "tiny"]
    mkdir("output")
    for sz_n in size_names:
        mkdir("output/" + sz_n)
        for codec in codecs.keys():
            mkdir(f"output/{sz_n}/{codec.upper()}/")

    # stage one: build job pool
    jobs = []
    for image in images:
        src = image[0]
        sz = image[1]
        for codec in codecs.keys():
            jobs.append([codec, src, [sz // 20, sz // 40, sz // 80, sz // 160], size_names])

    # stage 2: run jobs
    with Pool(8) as p:
        p.map(search, jobs, chunksize=1)

