# 헤딩 탐색: 8방향 vs 4방향 (분담 6)

드론 사진을 8방향(45° 간격) 또는 4방향(90° 간격)으로 돌려 보며 inlier 15개가 나오면 멈출 때("멈추기"), 걸음당 시간과 정답률이 어떻게 달라지는지 재고 어느 쪽을 쓸지 정한다.

**결론 한 줄**: 정답률은 네 설정에서 차이가 없고(10 m 13.9~14.0%), 걸음당 시간은 4방향 + 멈추기 15가 0.83초로 8방향 전체 탐색(2.42초)의 약 34%다. 한 장 비교 기준으로 4방향 + 멈추기 15를 쓴다.

## 1. 데이터와 설정

- 데이터: UAV-VisLoc `single_eval` (`heeyunju/visloc-single-eval`), 10개 비행(07 제외), 1,738장. GPS를 그대로 정답으로 썼다.
- 매처: LoMa, 스케일 1. Kaggle 커널은 `build_kernel.py`가 묶은 `scripts/run.py`를 실행한다(4절 참고).
- GPU: Kaggle T4, 커널을 하나씩 차례로 실행

| 커널 | 방향 | 멈추기 |
| --- | --- | --- |
| visloc-8dir | 8 | 없음 |
| visloc-4dir | 4 | 없음 |
| visloc-8dir-stop | 8 | inlier ≥ 15 |
| visloc-4dir-stop | 4 | inlier ≥ 15 |

## 2. 명령어

저장소 최상위에서 실행한다.

```
python scripts\kaggle\build_kernel.py --user jimin562 --dataset heeyunju/visloc-single-eval --slug visloc-8dir --args "--matchers loma --angles 8"
python scripts\kaggle\build_kernel.py --user jimin562 --dataset heeyunju/visloc-single-eval --slug visloc-4dir --args "--matchers loma --angles 4"
python scripts\kaggle\build_kernel.py --user jimin562 --dataset heeyunju/visloc-single-eval --slug visloc-8dir-stop --args "--matchers loma --angles 8 --stop-inl 15"
python scripts\kaggle\build_kernel.py --user jimin562 --dataset heeyunju/visloc-single-eval --slug visloc-4dir-stop --args "--matchers loma --angles 4 --stop-inl 15"
kaggle kernels push -p kaggle_kernels\<커널이름> --accelerator NvidiaTeslaT4
kaggle kernels output jimin562/<커널이름> -p outputs\<커널이름> --file-pattern "out/.*"
python scripts\reduce_dirs.py outputs\visloc-8dir\out\loma_s1.csv flights
```

build 명령의 인자는 `kaggle_kernels\<커널이름>\run.py` 2행의 `ARGS`와 대조해 확인했다. visloc-8dir은 `['--matchers', 'loma', '--angles', '8']`, visloc-4dir은 `['--matchers', 'loma', '--angles', '4']`로 위 명령과 일치한다.

## 3. 결과 (n = 1,738)

| 설정 | 10 m | 20 m | 32 m | 걸음당 시간 | 평균 시도 각도 |
| --- | --- | --- | --- | --- | --- |
| 8방향, 멈추기 없음 | 13.9% | 40.4% | 66.9% | 2.42초 | 8.0 |
| 4방향, 멈추기 없음 | 13.9% | 40.6% | 66.9% | 1.27초 | 4.0 |
| 8방향, 멈추기 15 | 14.0% | 40.3% | 66.6% | 1.43초 | 4.6 |
| 4방향, 멈추기 15 | 14.0% | 40.4% | 66.7% | 0.83초 | 2.6 |

- 시간은 각 커널 `summary.csv`의 `sec_per_sample`을 n 가중평균한 값이다.
- 정답률은 `reduce_dirs.py`가 `imatch.metrics.errors` 규칙으로 계산했다. 10 m는 라벨 오차(약 10~16 m)에 민감해서 20 m, 32 m도 같이 적는다.
- 시간 절감(8방향 전체 탐색 2.42초 대비): 8방향 + 멈추기 15 약 41%, 4방향 약 48%, 4방향 + 멈추기 15 약 66%.

### 비행별 걸음당 시간 (초, 실제 커널)

| 비행 | n | 8방향 | 4방향 | 8방향 + 멈추기 15 | 4방향 + 멈추기 15 |
| --- | --- | --- | --- | --- | --- |
| 01 | 218 | 2.410 | 1.254 | 1.407 | 0.810 |
| 02 | 288 | 2.424 | 1.265 | 1.830 | 1.004 |
| 03 | 192 | 2.435 | 1.272 | 0.651 | 0.481 |
| 04 | 186 | 2.432 | 1.273 | 0.814 | 0.562 |
| 05 | 132 | 2.436 | 1.270 | 1.802 | 0.992 |
| 06 | 96 | 2.427 | 1.268 | 1.104 | 0.671 |
| 08 | 273 | 2.423 | 1.269 | 1.894 | 1.023 |
| 09 | 170 | 2.424 | 1.271 | 1.805 | 1.015 |
| 10 | 36 | 2.417 | 1.265 | 2.200 | 1.171 |
| 11 | 147 | 2.423 | 1.273 | 0.920 | 0.612 |

비행별 정답률은 같은 폴더의 `reduce_8dir_flights.md`(`reduce_dirs.py … flights` 출력, 8방향 기록에서 **계산한 값**)를 부록으로 첨부한다. 이 파일의 `sec_per_sample`은 8방향 한 번의 실행에서 계산한 값이라, 위 표의 실제 커널 시간과 비교하면 8방향 멈추기 없음은 같고 나머지 세 설정은 0.01~0.06초 작다.

### 통계 (McNemar 정확검정, 8방향 기록에서 계산한 값)

- 4방향 vs 8방향: p = 0.75~1.00 (멈추기 없음), p = 1.00 (멈추기 15)
- 멈추기 15 vs 없음: p = 0.29~1.00
- 어느 비교에서도 유의한 차이가 없다.

### 관찰

- 정답률은 설정 사이에 0.3%p 안쪽으로 같고, 통계적으로 차이를 검출하지 못했다.
- 시간은 방향 수를 줄이면 거의 절반이 되고, 두 방법을 합친 4방향 + 멈추기 15는 8방향 전체 탐색의 약 34%다. 멈추기는 inlier가 높은 비행(03, 04, 11)에서 크게 줄인다. 03은 2.44초에서 0.65초가 됐다.
- inlier가 낮은 비행(08, 10)은 거의 끝까지 돌아 멈추기의 절약이 작다.
- 비행 06과 10은 4방향에서 정답률이 낮아 보이지만 n=96, n=36이라 몇 장 차이다. 비행별 검정은 하지 않았으므로 단정하지 않는다.

### 한계

- 전체 정답률이 낮다(10 m 약 14%). LoMa가 08, 10 같은 비행에서 거의 맞추지 못한다.
- LoMa 한 가지 매처, 한 번의 실행 결과이고 반복 실행 간 차이는 재지 않았다.
- 시간은 T4 기준이고 첫 각도에 모델 예열이 포함된다.
- 걸음당 시간은 각도 회전과 매칭 호출 시간(`localize`의 `sec`)만이고, 이미지 읽기와 위치·heading 계산은 포함하지 않는다.
- 멈추기를 켜면 inlier가 15 이상인 첫 각도에서 끝나므로, 그 뒤 각도가 더 좋았을 수 있는 경우는 시도되지 않는다. 이번 결과에서는 정답률 차이가 검출되지 않았다.
- 한 장 비교에서 잰 결과라서, 항법(R1 + R4)에서 4방향이 정답률을 유지하는지는 확인하지 않았다.

## 4. 스크립트

### `scripts/run1113.py` (원 `run.py` 대비 변경: 조기 종료 `--stop-inl` 추가)

**`run.py`와의 관계**: Kaggle 커널은 `build_kernel.py`가 `imatch/*.py`와 `scripts/run.py`를 base64로 묶어 실행한다(`run1113.py`는 묶이지 않는다). `run1113.py`는 `run.py`에 `--stop-inl` 옵션만 추가한 11-13 시점 사본으로, 현재 `scripts/run.py`와는 `localize` 호출의 줄바꿈만 다르고(`fc`로 확인) 동작은 같다. 로컬에서 직접 돌릴 때 쓴다.

바뀐 곳은 두 군데다.

1. 인자 추가 (`--tag` 다음 줄)
   ```python
   ap.add_argument('--stop-inl', type=int, default=0,
                   help='inlier가 이 값 이상인 각도가 나오면 거기서 멈춤 (0 = 전체 탐색)')
   ```
2. `localize` 호출에 전달
   ```python
   # 원본
   cand_recs, cand_best = localize(matcher, uav, block, gt, scale,
                                   [s.theta % 360] if a.oracle_rot else angles)
   # 수정
   cand_recs, cand_best = localize(matcher, uav, block, gt, scale,
                                   [s.theta % 360] if a.oracle_rot else angles,
                                   stop_inl=a.stop_inl)
   ```

동작
- 기본값 0이면 원본과 똑같이 모든 각도를 끝까지 돈다.
- `--stop-inl 15`를 주면 각도를 순서대로 시도하다가 inlier가 15 이상인 각도에서 멈춘다. `_angles.csv`에는 멈춘 각도까지만 기록된다.
- `--block-radius 1`과 함께 쓰면 후보 블록마다 따로 멈춘다.

바뀌지 않은 것: 출력 파일 구성과 열, 위치·heading 선택 방식(inlier 최대 각도), 기록용 오차, `summary.csv` 계산.

사용 예
```
python scripts/run1113.py --data data/visloc/single_eval --out outputs/stop15 --matchers loma --angles 8 --stop-inl 15
```

**멈추는 로직의 위치**: 실제로 멈추는 코드는 `imatch/pipeline.py`의 `localize`(42행)에 있다.

```python
if stop_inl > 0 and 'px' in r and r['n_inl'] >= stop_inl:
```

`localize`가 각도를 차례로 매칭하다가, 위치 추정(`px`)이 있고 inlier 수가 `stop_inl` 이상이면 그 각도에서 탐색을 끝낸다. 기본값 0이면 멈추기가 꺼져 모든 각도를 시도한다. `imatch/nav.py`의 `stop_inl` 인자(77, 79, 93행)는 이 값을 `localize`로 전달하기만 한다.

### `scripts/reduce_dirs.py` (분석)

**역할**: 멈추기 없이 8방향을 끝까지 돌린 기록(`_angles.csv`)만 읽어서, 매칭을 새로 돌리지 않고 네 설정(8/4방향 × 멈추기 없음/inlier 15)의 정확도와 시간을 다시 계산한다. 4방향(0/90/180/270°)은 8방향의 부분집합이라 같은 기록에서 뽑는다.

```
python scripts\reduce_dirs.py outputs\visloc-8dir\out\loma_s1.csv            # 전체 비행 합산
python scripts\reduce_dirs.py outputs\visloc-8dir\out\loma_s1.csv flights    # 비행별 표도 출력
```

- 입력은 `loma_s1.csv`이고 같은 폴더의 `loma_s1_angles.csv`를 자동으로 함께 읽는다. `--help`는 없다.
- 파일로 저장하려면 끝에 `> 출력파일.md`를 붙인다.

계산 방식
1. 샘플마다 각도를 순서대로 훑는다. 멈추기가 켜져 있으면 위치가 있고 `n_inl >= 15`인 첫 각도에서 멈춘다.
2. 시도한 각도 중 위치가 있는 것 가운데 inlier가 가장 많은 각도의 위치와 heading을 답으로 쓴다.
3. 시간은 시도한 각도들의 `sec` 합이다.
4. 오차는 팀 공통 규칙 `imatch.metrics.errors`로 계산한다(추정을 블록 안으로 clip, 추정이 없으면 블록 중심).

출력: 전체 합산 표(10/20/32 m 이내, 중앙값 오차, 실패율, heading 오차 중앙값, 걸음당 시간, 평균 시도 각도), 짝 비교 표(McNemar), 비행별 표(`flights`).

해석 주의
- 입력은 반드시 멈추기 없이 돌린 8방향 기록이어야 한다. 4방향 커널이나 stop 커널의 기록에서는 일부 행이 의미 없다.
- 시간은 8방향 실행의 각도별 `sec` 합이다. `sec`는 `localize`에서 각도 회전과 매칭 호출에 걸린 시간만 잰 값이라(이미지 읽기·후처리 제외) 실제 커널도 같은 정의이고, 별도로 돌린 커널과는 실행 간 속도 차이로 전체 합산 기준 0.03~0.06초 다르다. 최종 시간은 실제 커널의 `summary.csv`를 쓴다.
- `fail`은 "추정 없음 또는 블록 밖으로 3.2 m 넘게 나감"이다. 틀린 위치를 답했지만 블록 안이면 fail이 아니다.

**검증**: 4방향(멈추기 없음), 8방향 + 멈추기 15, 4방향 + 멈추기 15 모두 실제 커널과 정답률(10/20/32 m)이 일치했고, 멈추기 설정은 평균 시도 각도(4.6, 2.6)도 일치했다. 시간은 전체 합산 기준 계산값이 실제보다 0.03~0.06초 작다(둘 다 같은 `sec` 합이라 정의는 같고, 별도 커널 실행 간 속도 차이로 설명된다).

계산값(`reduce_dirs.py`)과 실제 커널 측정값의 비교 (전체 합산, n = 1,738). 실제 정답률은 각 커널의 `loma_s1.csv`를 `reduce_dirs.py`에 넣어 해당 설정 행을 읽은 값이고, 실제 시간은 `summary.csv`의 `sec_per_sample`이다. 8방향 멈추기 없음은 계산의 원본 기록(visloc-8dir 커널 결과)이라 기준 행이다. 비행별 비교는 하지 않았다.

| 설정 | 10 m (계산 / 실제) | 20 m (계산 / 실제) | 32 m (계산 / 실제) | 걸음당 시간 (계산 → 실제) | 평균 시도 각도 (계산 / 실제) |
| --- | --- | --- | --- | --- | --- |
| 8방향, 멈추기 없음 (기준) | 13.9% / 13.9% | 40.4% / 40.4% | 66.9% / 66.9% | 2.42초 → 2.42초 | 8.0 / 8.0 |
| 4방향, 멈추기 없음 | 13.9% / 13.9% | 40.6% / 40.6% | 66.9% / 66.9% | 1.21초 → 1.27초 | 4.0 / 4.0 |
| 8방향, 멈추기 15 | 14.0% / 14.0% | 40.3% / 40.3% | 66.6% / 66.6% | 1.40초 → 1.43초 | 4.6 / 4.6 |
| 4방향, 멈추기 15 | 14.0% / 14.0% | 40.4% / 40.4% | 66.7% / 66.7% | 0.79초 → 0.83초 | 2.6 / 2.6 |
