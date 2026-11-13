"""매칭 실행: data/<set>/k###_uav.jpg, k###_block.jpg 샘플마다 위치·heading을 추정해 CSV로 저장한다.

  python scripts/run.py --data data/im_t1_3d_1000 --out outputs/loma_8dir --matchers loma --angles 8
  python scripts/run.py --data data/im_t1_3d_1000 --out outputs/sift_test --matchers cv-sift --n 5 --device cpu
  python scripts/run.py --data data/im_t1_3d_1000 --out outputs/blk3 --matchers loma --angles 1 --block-radius 1

--block-radius 1이면 주변 3x3 후보 블록을 모두 매칭한다 (scripts/export_block_index.py로 만든 파일이 필요).
이때 샘플별 CSV에는 정답 블록의 결과만 들어가고, 후보별 결과는 _angles.csv의 dx, dy 열로 남는다.
후보 중 고르는 일은 scripts/select_block.py가 한다.

출력 (--out 폴더)
  <matcher><tag>_s<scale>.csv          샘플당 1행: 추정 위치·heading, 오차, inlier 수, 시간
  <matcher><tag>_s<scale>_angles.csv   샘플 × 각도마다 1행 (방향 수를 줄인 결과를 다시 계산할 때 사용)
  summary.csv                           도시별 요약
"""
import argparse
import os
import sys

import cv2
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from imatch import geometry, get_matcher, localize  # noqa: E402
from imatch.blocks import UNITS_PER_BLOCK, crop_block, neighbors  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True, help='samples.csv가 있는 폴더')
    ap.add_argument('--out', required=True)
    ap.add_argument('--matchers', default='cv-sift', help='쉼표로 여러 개: loma,romav2,sift-lightglue,cv-sift')
    ap.add_argument('--scales', default='1', help='영상 확대 배율, 쉼표로 여러 개')
    ap.add_argument('--angles', type=int, default=8, help='회전 탐색 방향 수 (1 = 탐색 없음)')
    ap.add_argument('--oracle-rot', action='store_true',
                    help='정답 heading 한 방향만 돌려 매칭 (회전을 완벽히 맞췄을 때의 상한 실험용, 실제 방법 아님)')
    ap.add_argument('--angle-offset', type=float, default=0.0, help='모든 방향에 더할 각도. 예: 8방향 + 22.5 = 기존 8방향 사이')
    ap.add_argument('--sets', default='', help='3d_ho38bc(SF), 3d_ho37bc(Singapore). 비우면 전부')
    ap.add_argument('--n', type=int, default=0, help='k < n 샘플만 (0 = 전부)')
    ap.add_argument('--kmin', type=int, default=0, help='k >= kmin 샘플만')
    ap.add_argument('--device', default='cuda')
    ap.add_argument('--ransac-px', type=float, default=3.0)
    ap.add_argument('--block-radius', type=int, default=0, help='0 = 정답 블록만, 1 = 주변 3x3 후보 블록')
    ap.add_argument('--tag', default='', help='출력 파일 이름 뒤에 붙일 말. 예: --tag=-1dir')
    ap.add_argument('--stop-inl', type=int, default=0, help='inlier가 이 값 이상인 각도가 나오면 거기서 멈춤 (0 = 전체 탐색)')
    a = ap.parse_args(argv)
    geometry.set_ransac_px(a.ransac_px)
    os.makedirs(a.out, exist_ok=True)
    df = pd.read_csv(os.path.join(a.data, 'samples.csv'))
    if a.sets: df = df[df.set.isin(a.sets.split(','))]
    if a.n: df = df[df.k < a.n]
    if a.kmin: df = df[df.k >= a.kmin]
    if a.block_radius:
        df = df.merge(pd.read_csv(os.path.join(a.data, 'block_index.csv')), on=['set', 'k'])
        city = {st: cv2.cvtColor(cv2.imread(os.path.join(a.data, 'maps', f'{st}.jpg')), cv2.COLOR_BGR2RGB)
                for st in df.set.unique()}
    angles = list(np.arange(0, 360, 360 / a.angles) + a.angle_offset)
    summ = []
    for mname in a.matchers.split(','):
        try:
            matcher = get_matcher(mname, a.device)
        except Exception as e:
            print('LOAD FAIL', mname, repr(e), flush=True); summ.append(dict(matcher=mname, error=repr(e)[:300])); continue
        for scale in [float(s) for s in a.scales.split(',')]:
            rows, per_angle = [], []
            for s in df.itertuples():
                d = os.path.join(a.data, s.set)
                rd = lambda f: cv2.cvtColor(cv2.imread(os.path.join(d, f)), cv2.COLOR_BGR2RGB)
                recs, best = [], None
                try:
                    uav = rd(f'k{s.k:03d}_uav.jpg')
                    # 후보 블록은 정답 블록까지 모두 지도에서 같은 방식으로 자른다
                    cands = [(dx, dy, crop_block(city[s.set], s.block_x + dx, s.block_y + dy))
                             for dx, dy in neighbors(s.block_x, s.block_y, a.block_radius)] if a.block_radius \
                        else [(0, 0, rd(f'k{s.k:03d}_block.jpg'))]
                    for dx, dy, block in cands:
                        gt = (s.x_norm - UNITS_PER_BLOCK * dx, s.y_norm - UNITS_PER_BLOCK * dy, s.theta)
                        cand_recs, cand_best = localize(matcher, uav, block, gt, scale, [s.theta % 360] if a.oracle_rot else angles, stop_inl=a.stop_inl)
                        where = dict(dx=dx, dy=dy) if a.block_radius else {}
                        for r in cand_recs: per_angle.append(dict(matcher=mname, scale=scale, set=s.set, k=s.k, **where, **r))
                        if dx == 0 and dy == 0: recs, best = cand_recs, cand_best
                except Exception as e:
                    print('RUN FAIL', mname, scale, s.set, s.k, repr(e)[:200], flush=True); recs, best = [], None
                row = dict(matcher=mname, scale=scale, set=s.set, k=s.k, gt_x=s.x_norm, gt_y=s.y_norm, gt_theta=s.theta,
                           sec=sum(r['sec'] for r in recs))
                if best:
                    row.update(pred_x=best['px'], pred_y=best['py'], pred_theta=best['head'], angle=best['angle'],
                               n_inl=best['n_inl'], n_match=best['n_match'], good_match=best['good_match'],
                               good_inl=best['good_inl'], scale_est=best['scale_est'])
                rows.append(row)
                if len(rows) % 20 == 0:
                    print(f'  {mname} s{scale:g} {len(rows)}/{len(df)} samples, {row["sec"]:.2f} s/sample', flush=True)
            R = pd.DataFrame(rows)
            if 'pred_x' not in R: R['pred_x'] = np.nan; R['pred_y'] = np.nan; R['pred_theta'] = np.nan; R['n_inl'] = 0
            # 원래 기록용 오차 (clip 없음, 추정 없으면 블록 중심). 표의 숫자는 scripts/evaluate.py 규칙으로 다시 계산한다
            px, py = R.pred_x.fillna(0), R.pred_y.fillna(0)
            R['err_m'] = np.hypot(px - R.gt_x, py - R.gt_y) * geometry.M_PER_UNIT
            R['head_err'] = geometry.wrap(R.pred_theta.fillna(0) - R.gt_theta)
            tag = f'{mname}{a.tag}_s{scale:g}'
            R.to_csv(os.path.join(a.out, f'{tag}.csv'), index=False)
            pd.DataFrame(per_angle).to_csv(os.path.join(a.out, f'{tag}_angles.csv'), index=False)
            for st, g in R.groupby('set'):
                summ.append(dict(matcher=mname, scale=scale, set=st, n=len(g), found=round(float(g.pred_x.notna().mean() * 100), 1),
                                 MLE=round(float(g.err_m.mean()), 2), medLE=round(float(g.err_m.median()), 2),
                                 LSR10=round(float((g.err_m < 10).mean() * 100), 1), MHE=round(float(g.head_err.mean()), 2),
                                 medHE=round(float(g.head_err.median()), 2), inl_med=float(g.n_inl.fillna(0).median()),
                                 good_inl=round(float(g.get('good_inl', pd.Series(dtype=float)).mean() * 100), 1),
                                 good_match=round(float(g.get('good_match', pd.Series(dtype=float)).mean() * 100), 1),
                                 sec_per_sample=round(float(g.sec.mean()), 3)))
                print(summ[-1], flush=True)
            pd.DataFrame(summ).to_csv(os.path.join(a.out, 'summary.csv'), index=False)


if __name__ == '__main__':
    main()
