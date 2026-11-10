import sys, argparse, csv, math
from pathlib import Path
sys.path.insert(0, "/kaggle/working")
import numpy as np
from PIL import Image
import tifffile
from export_external_v3 import (read_geotiff_tags, source_px_size_m,
    geo_to_pixel_float, read_tiled_crop, make_block, select_even_rows)

WIN = 700
ap = argparse.ArgumentParser()
ap.add_argument("--root", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--n", type=int, default=260)
ap.add_argument("--uav-gsd", type=float, default=0.1128)   # 추정값
ap.add_argument("--theta-sign", type=float, default=-1.0)
ap.add_argument("--theta-offset", type=float, default=6.0)
a = ap.parse_args()

crop = 2 * round(256 * 0.25 / a.uav_gsd / 2)               # 568
seq = Path(a.root) / "03"
rows = list(csv.DictReader(open(seq/"03.csv", newline="", encoding="utf-8-sig")))
sel = select_even_rows(rows, a.n)
out = Path(a.out); sd = out/"uavvisloc_03"; sd.mkdir(parents=True, exist_ok=True)
tif = seq/"satellite03.tif"
with tifffile.TiffFile(str(tif)) as t:
    pg = t.pages[0]; geo = read_geotiff_tags(pg)
    mw, mh = int(pg.imagewidth), int(pg.imagelength)

recs, skipped = [], []
for ri, row in sel:
    cx, cy = geo_to_pixel_float(row["lon"], row["lat"], geo)
    x0 = int(math.floor(cx)) - WIN//2; y0 = int(math.floor(cy)) - WIN//2
    if x0 < 0 or y0 < 0 or x0+WIN > mw or y0+WIN > mh:
        skipped.append(row["filename"]); continue
    pe, pn = source_px_size_m(geo, row["lat"])
    blk = make_block(read_tiled_crop(tif, x0, y0, WIN, WIN), x0, y0, cx, cy, pe, pn, size=512)
    with Image.open(seq/"drone"/row["filename"]) as im:
        im = im.convert("RGB"); w, h = im.size
        l, tp = (w-crop)//2, (h-crop)//2
        u = im.crop((l, tp, l+crop, tp+crop)).resize((256, 256), Image.Resampling.LANCZOS)
    k = len(recs) + 1
    u.save(sd/f"k{k:03d}_uav.jpg", quality=95)
    Image.fromarray(blk, mode="RGB").save(sd/f"k{k:03d}_block.jpg", quality=95)
    th = (a.theta_sign*float(row["Phi1"]) + a.theta_offset) % 360
    recs.append(dict(set="uavvisloc_03", k=k, row=ri, x_norm=0.0, y_norm=0.0, theta=th,
        source_filename=row["filename"], lat=row["lat"], lon=row["lon"], height=row["height"],
        Phi1=row["Phi1"], Phi2=row["Phi2"], src_px_e_m=round(pe,5), src_px_n_m=round(pn,5),
        uav_crop_px=crop))

with open(out/"samples.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(recs[0].keys())); w.writeheader(); w.writerows(recs)
print(f"EXPORT: {len(recs)} ok, {len(skipped)} skipped | block 512 (128 m), uav crop {crop}px "
      f"-> 256 (64 m), theta={a.theta_sign:+.0f}*Phi1{a.theta_offset:+.0f}")
