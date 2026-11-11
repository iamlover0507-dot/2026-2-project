# C5 External Dataset Evaluation

UAV-VisLoc Example의 Sequence 03을 이용해 기존 Trone-iMatch 파이프라인의 외부 데이터 성능을 평가했다.

- 평가 데이터: 260개 표본
- 모델: LoMa-B128, LoMa-B
- 탐색 방식: 8방향
- 위성 지도: 512×512, 0.25m/px, GPS 중심
- UAV 영상: 중앙 568px 크롭 후 256×256으로 변환
- UAV 영상 GSD: 연속 프레임 14쌍으로 추정한 중앙값 0.1128m/px
- Heading 변환: `theta = (-Phi1 + 6) mod 360`
- 평가 환경: Kaggle Tesla T4


## 2. 실행 명령어

### 데이터 변환

실험 당시 실제 사용한 변환 스크립트는 `export_external_v5.py`이다. 

**실제 실행 명령**

```bash
python /kaggle/working/export_external_v5.py \
  --root "<UAV_VisLoc_example (1)>" \
  --out /kaggle/working/data_uavvisloc_v5_260
```

위 명령은 다음 기본 인자를 사용한다.

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `--n` | 260 | 변환할 표본 수 |
| `--uav-gsd` | 0.1128 | UAV 영상 GSD 추정값 (m/px) |
| `--theta-sign` | -1.0 | Phi1 부호 |
| `--theta-offset` | 6.0 | Heading 보정 각도 |

**변환 과정**

1. UAV-VisLoc Example의 `03/03.csv`에서 표본을 선택한다.
2. `03/satellite03.tif`의 GeoTIFF 정보를 읽고 GPS 좌표를 위성 지도 픽셀 좌표로 변환한다.
3. GPS를 중심으로 700×700px 위성 지도 영역을 읽는다.
4. 원본 지도 축척을 고려해 512×512px, 128m 영역으로 변환한다.
5. 드론 영상의 중앙 568×568px 영역을 자르고 256×256px로 리사이즈한다.
6. Heading을 `theta = (-Phi1 + 6) mod 360`으로 변환한다.
7. UAV 영상, 지도 블록, `samples.csv`를 출력한다.


최종 저장소의 변환 스크립트 경로는 `scripts/export_external.py`이다. 다만 위 실행 명령은 실험 당시 사용한 `/kaggle/working/export_external_v5.py`의 실행 이력을 기록한 것이며, 최종 저장소 파일명으로 실행한 명령은 아니다.


## 3. Evaluate 결과

260개 전체 표본 기준이며, 실패 표본은 성공으로 계산하지 않았다.

| Metric | LoMa-B128 | LoMa-B |
|---|---:|---:|
| Found | 251/260 | 257/260 |
| 10m 이내 | 12.3% | 14.6% |
| 20m 이내 | 48.1% | 47.7% |
| 32m 이내 | 80.8% | 82.3% |
| 유효 예측 기준 10m 이내 | 12.7% | 14.8% |
| Unknown (Inlier < 15) | 43 (17%) | 39 (15%) |
| 답한 표본 기준 10m 이내 | 13.8% | 15.8% |
| Heading 중앙값 | -1.6° | -2.0° |
| Heading MAD | 2.9° | 2.7° |
| 180° 뒤집힘 | 1 | 0 |
| Inlier 중앙값 | 114 | 129 |
| 초/샘플 | 1.66 | 2.55 |

### Heading 검증

Heading 변환 규칙 설정에 사용하지 않은 새 표본 38개에서 다음 결과를 확인했다.

| Metric | Result |
|---|---:|
| Heading 오차 중앙값 | -2.6° |
| MAD | 3.0° |
| 15° 이내 비율 | 96% |

무작위 방향의 90° 오차 기준보다 일관되게 작은 오차를 보였다. 다만 GPS 및 지도 좌표계의 절대 정확성까지 독립적으로 검증한 결과는 아니다.

### 모델 간 쌍체 비교

프로젝트 공통 평가 규칙에 따라 정규화 좌표의 각 축에 ±1 clip을 적용한 위치 오차를 계산한 뒤, 동일 표본의 성공 여부를 기준으로 McNemar exact test를 수행했다. 총 260개 표본을 비교했으며, 예측 좌표가 없는 표본은 실패로 처리했다.

| 기준 | B128만 성공 | LoMa-B만 성공 | p-value |
|---|---:|---:|---:|
| 10m | 2 | 8 | 0.109375 |
| 20m | 8 | 7 | 1.000000 |
| 32m | 8 | 12 | 0.503444 |


세 기준 모두 p-value가 0.05보다 크므로, 위치 정확도에서 두 모델 사이의 통계적으로 유의한 차이는 확인되지 않았다.

## 4. 결과 해석 및 제한사항

- 위성 지도는 프로젝트 기준인 0.25m/px로 변환했다.
- UAV 영상의 0.1128m/px는 연속 프레임으로 추정한 GSD이며, 카메라 보정으로 검증된 값은 아니다.
- `Inlier < 15`는 Unknown으로 집계했지만 파이프라인 전체의 거절 동작으로 완전히 통합하지는 않았다.
- 인접 프레임이 포함되어 있어 260개 표본이 완전히 독립적이지 않다.
- 정답 위치와 추정 위치의 NCC 차이 및 비행 줄별 위치 편향이 관찰되었다. GPS 또는 지도 georeferencing 오차 가능성이 있으나 원인은 확정되지 않았다.

## 5. 결과 파일

다음 파일에 평가 결과를 CSV로 보관한다.

```text
experiments/2026-11-13_external/
├── README.md
├── LoMa-B128/
│   ├── loma-b128-v5_b128_s1.csv
│   ├── loma-b128-v5_b128_s1_angles.csv
│   └── summary.csv
├── LoMa-B/
│   ├── loma-v5_loma_s1.csv
│   ├── loma-v5_loma_s1_angles.csv
│   └── summary.csv
└── label_check_v5_loma.csv
```

## 6. 결론 한 줄

UAV-VisLoc 260개 표본에서 Heading은 새 표본 기준 15° 이내 96%였고, LoMa-B128의 10m 이내 성공률은 12.3%, 32m 이내 성공률은 80.8%였으나 GPS/georeferencing 오차 가능성으로 절대 위치 정확도 해석에는 주의가 필요하다.
