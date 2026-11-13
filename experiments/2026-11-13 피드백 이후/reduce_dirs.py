"""Recompute results from the 8-direction run (_angles.csv) for fewer directions and early stop.
Walk angles in order, stop at the first angle with n_inl >= stop, add up time until then.
  python scripts/reduce_dirs.py outputs/vis8/loma_s1.csv
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from imatch import geometry  # noqa: E402
from imatch.metrics import errors  # noqa: E402

SUBSETS = {
    '8dir': [0, 45, 90, 135, 180, 225, 270, 315],
    '4dir': [0, 90, 180, 270],
}
STOPS = [0, 15]  # 0 = no early stop (full search)


def pick(a, angs, stop):
    tried = []
    for ang in angs:
        r = a[a.a == ang]
        if r.empty:
            continue
        r = r.iloc[0]
        tried.append(r)
        if stop > 0 and pd.notna(r.px) and r.n_inl >= stop:
            break
    ok = [r for r in tried if pd.notna(r.px)]
    best = max(ok, key=lambda r: r.n_inl) if ok else None
    return best, sum(r.sec for r in tried), len(tried)


def main():
    f = sys.argv[1]
    R = pd.read_csv(f)
    A = pd.read_csv(f.replace('.csv', '_angles.csv'))
    A['a'] = A.angle.round(1) % 360
    if 'dx' in A:
        A = A[(A.dx == 0) & (A.dy == 0)]
    print('| dirs | stop | set | n | within10m | mean_err | median_err | fail | head_err_median | sec_per_sample | n_angles |')
    print('| --- ' * 11 + '|')
    for st, g in R.groupby('set'):
        r = g.drop_duplicates('k').set_index('k').sort_index()
        Ag = {k: d for k, d in A[A.set == st].groupby('k')}
        for name, angs in SUBSETS.items():
            for stop in STOPS:
                rows = {}
                for k in r.index:
                    if k not in Ag:
                        rows[k] = dict(px=np.nan, py=np.nan, head=np.nan, sec=0.0, nt=0)
                        continue
                    best, sec, nt = pick(Ag[k], angs, stop)
                    rows[k] = dict(px=best.px if best is not None else np.nan,
                                   py=best.py if best is not None else np.nan,
                                   head=best['head'] if best is not None else np.nan, sec=sec, nt=nt)
                P = pd.DataFrame.from_dict(rows, orient='index').reindex(r.index)
                e, fail = errors(P.px, P.py, r.gt_x, r.gt_y)
                he = np.nanmedian(np.abs(geometry.wrap((P['head'] - r.gt_theta).to_numpy(dtype=float))))
                lab = 'none' if stop == 0 else f'inl{stop}'
                print(f"| {name} | {lab} | {st} | {len(r)} | {(e < 10).mean()*100:.1f}% | {e.mean():.2f} m "
                      f"| {np.median(e):.2f} m | {fail.mean()*100:.0f}% | {he:.1f} | {P.sec.mean():.2f} | {P.nt.mean():.1f} |")


if __name__ == '__main__':
    main()