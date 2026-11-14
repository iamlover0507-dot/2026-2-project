"""Recompute results from the 8-direction run (_angles.csv) for fewer directions and early stop.
Walk angles in order, stop at the first angle with n_inl >= stop, add up time until then.
  python scripts/reduce_dirs.py outputs/visloc-8dir/out/loma_s1.csv            (all flights pooled)
  python scripts/reduce_dirs.py outputs/visloc-8dir/out/loma_s1.csv flights    (also per flight)
"""
import math
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
THS = [10, 20, 32]
PAIRS = [
    (('4dir', 15), ('8dir', 15)),
    (('4dir', 0), ('8dir', 0)),
    (('8dir', 15), ('8dir', 0)),
    (('4dir', 15), ('4dir', 0)),
]


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


def mcnemar_p(b, c):
    """exact two-sided McNemar test"""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def lab(stop):
    return 'none' if stop == 0 else f'inl{stop}'


def row(name, stop, D, tag):
    w = ' | '.join(f'{(D.e < t).mean() * 100:.1f}%' for t in THS)
    he = np.nanmedian(D.he) if D.he.notna().any() else float('nan')
    print(f"| {name} | {lab(stop)} | {tag} | {len(D)} | {w} | {D.e.median():.2f} m | {D.fail.mean() * 100:.0f}% "
          f"| {he:.1f} | {D.sec.mean():.2f} | {D.nt.mean():.1f} |")


def header():
    print('| dirs | stop | flights | n | within10m | within20m | within32m | median_err | fail | head_err_median '
          '| sec_per_sample | n_angles |')
    print('| --- ' * 12 + '|')


def main():
    f = sys.argv[1]
    by_flight = len(sys.argv) > 2 and sys.argv[2] == 'flights'
    R = pd.read_csv(f)
    A = pd.read_csv(f.replace('.csv', '_angles.csv'))
    A['a'] = A.angle.round(1) % 360
    if 'dx' in A:
        A = A[(A.dx == 0) & (A.dy == 0)]
    res = {}
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
                he = np.abs(geometry.wrap((P['head'] - r.gt_theta).to_numpy(dtype=float)))
                D = pd.DataFrame(dict(set=st, k=r.index.to_numpy(), e=np.asarray(e, float),
                                      fail=np.asarray(fail, bool), he=he, sec=P.sec.to_numpy(), nt=P.nt.to_numpy()))
                res.setdefault((name, stop), []).append(D)
    tab = {key: pd.concat(v, ignore_index=True) for key, v in res.items()}

    print('\n## All flights pooled\n')
    header()
    for name in SUBSETS:
        for stop in STOPS:
            row(name, stop, tab[(name, stop)], 'ALL')

    print('\n## Paired comparison (McNemar exact, same samples): A_only / B_only / p\n')
    print('| A | B | threshold | A_only | B_only | p |')
    print('| --- | --- | --- | --- | --- | --- |')
    for ka, kb in PAIRS:
        for t in THS:
            oa, ob = tab[ka].e < t, tab[kb].e < t
            b, c = int((oa & ~ob).sum()), int((~oa & ob).sum())
            print(f'| {ka[0]}-{lab(ka[1])} | {kb[0]}-{lab(kb[1])} | {t} m | {b} | {c} | {mcnemar_p(b, c):.3f} |')

    if by_flight:
        print('\n## Per flight\n')
        header()
        for st in sorted(R.set.unique()):
            for name in SUBSETS:
                for stop in STOPS:
                    D = tab[(name, stop)]
                    row(name, stop, D[D.set == st], st.replace('visloc_', ''))


if __name__ == '__main__':
    main()