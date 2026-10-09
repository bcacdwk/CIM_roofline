"""Trim the empty margins around Fig. 1 without touching its content.

Transparent or near-white pixels count as background. The image is cropped to
the content bounding box plus a small padding and flattened onto white, the
paper colour. Fig1.png is never modified: re-export it, then rerun this script.

    python crop_fig1.py              # Fig1.png -> Fig1_cropped.png, 6 px padding
    python crop_fig1.py --pad 0      # tightest crop
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Crop the empty margins of Fig. 1.")
    parser.add_argument("--input", type=Path, default=HERE / "Fig1.png")
    parser.add_argument("--output", type=Path, default=HERE / "Fig1_cropped.png")
    parser.add_argument("--pad", type=int, default=6,
                        help="padding kept on every side, in source pixels")
    parser.add_argument("--threshold", type=int, default=245,
                        help="RGB level at or above which a pixel counts as white")
    args = parser.parse_args()

    source = Image.open(args.input)
    image = source.convert("RGBA")
    pixels = np.asarray(image)
    background = (pixels[..., :3].min(axis=2) >= args.threshold) | (pixels[..., 3] < 10)
    ys, xs = np.nonzero(~background)
    if xs.size == 0:
        raise SystemExit("No content found; lower --threshold.")

    width, height = image.size
    box = (max(int(xs.min()) - args.pad, 0), max(int(ys.min()) - args.pad, 0),
           min(int(xs.max()) + 1 + args.pad, width), min(int(ys.max()) + 1 + args.pad, height))
    cropped = image.crop(box)
    flat = Image.new("RGB", cropped.size, "white")
    flat.paste(cropped, mask=cropped.getchannel("A"))

    dpi = source.info.get("dpi")
    flat.save(args.output, dpi=dpi) if dpi else flat.save(args.output)
    print(f"{args.input.name} {width}x{height} -> {args.output.name} "
          f"{flat.size[0]}x{flat.size[1]}; removed L/T/R/B = "
          f"{box[0]}/{box[1]}/{width - box[2]}/{height - box[3]} px")


if __name__ == "__main__":
    main()
