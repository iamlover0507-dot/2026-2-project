# Navigation Baseline Experiments

B1 and CorrMatchNet closed-loop navigation evaluation results.

## 1. 실험 목적

기존 B1 모델과 CorrMatchNet의 항법 성능을 비교하기 위해 동일한 평가 조건에서 폐루프(Closed-loop) 항법 실험을 수행하였다.

평가 대상 도시는 Singapore와 San Francisco(SF)이며, 동일한 시작 조건과 궤적을 사용하여 두 모델의 항법 성공률, 실패 원인 및 통계적 유의성을 비교하였다.

본 실험은 `capstone1 phase0`의 **2D 위성 지도 기반 항법 결과**이다.

## 2. 실험 설정

| 항목 | 설정 |
|---|---|
| 평가 모델 | B1, CorrMatchNet |
| 평가 도시 | Singapore, San Francisco |
| Seed | 7 |
| 도시별 궤적 수 | 32개 |
| 모델별 총 평가 궤적 | 64개 |
| 항법 방식 | Closed-loop navigation |
| Step당 이동 거리 | 15 m |
| 도착 판정 거리 | 20 m |
| 초기 Heading | 90° |
| 평가 환경 | Kaggle GPU (Tesla T4) |

두 모델은 동일한 seed로 생성한 궤적을 사용하였다. 각 도시에서 32개 궤적의 시작 위치와 초기 블록 위치가 일치하는 것을 확인하였다.

**입력 데이터 관련 주의사항**

이번 T5 실험에서는 3D-view 체크포인트 및 메타데이터를 선택했지만, 실제 항법 입력은 각 시점의 2D 위성 지도 Crop이었다. 따라서 이 결과는 실제 3D UAV 영상 입력을 이용한 항법 성능으로 해석할 수 없다.

## 3. 실험 결과

### 3.1 도시별 항법 성공률

| 도시 | 모델 | 성공률 | 성공 궤적 | 실행 시간 |
|---|---|---:|---:|---:|
| Singapore | B1 | 18.8% | 6/32 | 35.5초 |
| Singapore | CorrMatchNet | 100.0% | 32/32 | 50.7초 |
| SF | B1 | 40.6% | 13/32 | 29.0초 |
| SF | CorrMatchNet | 100.0% | 32/32 | 52.4초 |

### 3.2 성공률의 95% 신뢰구간

| 도시 | 모델 | 95% 신뢰구간 |
|---|---|---:|
| Singapore | B1 | 8.9–35.3% |
| Singapore | CorrMatchNet | 89.3–100.0% |
| SF | B1 | 25.5–57.7% |
| SF | CorrMatchNet | 89.3–100.0% |

### 3.3 실패 원인 분석

B1 모델의 실패 원인을 확인한 결과 다음과 같이 나타났다.

- Singapore: 26개 궤적에서 `out_of_map` 발생
- SF: 19개 궤적에서 `out_of_map` 발생

반면 CorrMatchNet은 두 도시 모두에서 32개 궤적이 `arrived_ok`로 종료되었다.

이번 평가에서는 B1의 주요 실패 양상이 지도 영역을 벗어나는 문제로 나타났으며, CorrMatchNet은 평가한 모든 궤적에서 도착 조건을 만족하였다.

## 4. 궤적별 쌍체 비교 및 통계검정

동일한 시작 조건을 가진 궤적끼리 비교하기 위해 각 모델의 궤적별 최종 성공 여부를 기준으로 쌍체 비교를 수행하였다.

| 도시 | 둘 다 성공 | B1만 성공 | CorrMatchNet만 성공 | 둘 다 실패 | p-value |
|---|---:|---:|---:|---:|---:|
| Singapore | 6 | 0 | 26 | 0 | 2.98 × 10⁻⁸ |
| SF | 13 | 0 | 19 | 0 | 3.81 × 10⁻⁶ |

불일치 쌍에 대해 정확 이항검정(Exact Binomial Test)을 수행하였다. 이는 불일치 쌍을 대상으로 하는 정확 McNemar 검정과 동등한 방식이다.

두 도시 모두 p-value가 0.05보다 작아, 이번 평가 표본에서 두 모델의 성공률 차이가 통계적으로 유의한 것으로 나타났다.

## 5. 종합 분석

CorrMatchNet은 Singapore와 SF에서 모두 100%의 항법 성공률을 기록하였다. 반면 B1은 Singapore에서 18.8%, SF에서 40.6%의 성공률을 기록하였다.

동일한 궤적을 기준으로 한 쌍체 비교에서도 CorrMatchNet만 성공한 궤적은 Singapore 26개, SF 19개였으며, B1만 성공한 궤적은 두 도시 모두 없었다.

실행 시간은 CorrMatchNet이 B1보다 길었다. Singapore에서는 B1 35.5초, CorrMatchNet 50.7초였으며, SF에서는 각각 29.0초와 52.4초였다.

따라서 이번 평가 조건에서는 CorrMatchNet이 실행 시간 증가에도 불구하고 B1보다 높은 폐루프 항법 성공률을 보였다.

다만 본 결과는 seed 7, 도시별 32개 궤적에 대한 평가이므로 모든 환경에서 동일한 성능을 보장하지 않는다. 추가 seed와 더 많은 궤적을 통한 일반화 성능 확인이 필요하다.

## 6. 3D 연속 항법 검증의 한계

Bearing_UAV_90K 데이터셋에는 실제 3D UAV 영상과 위치 및 Heading 관련 메타데이터가 존재한다. 그러나 조사한 메타데이터에는 timestamp, trajectory ID, sequence 등 연속 비행 순서를 확인할 수 있는 정보가 포함되어 있지 않았다.

따라서 현재 데이터만으로는 시간 순서가 보장된 실제 3D UAV 영상 기반 폐루프 항법 실험을 구성하고 검증하기 어렵다.

이번 실험에서는 기존 `capstone1 phase0`의 2D 항법 결과를 기준선으로 정리하였다. 따라서 B1 및 CorrMatchNet의 결과를 실제 3D 입력 기반 항법 성능으로 확대 해석하지 않는다.

## 7. 결과 파일 구성

실험 결과는 다음과 같이 정리하였다.

```text
experiments/
└── 2026-11-13_nav_baselines/
    │
    ├── README.md
    │
    ├── B1/
    │   ├── SF_result.json
    │   ├── SF_steps.csv
    │   ├── Singapore_result.json
    │   ├── Singapore_steps.csv
    │   └── summary.csv
    │
    ├── CorrMatchNet/
    │   ├── SF_result.json
    │   ├── SF_steps.csv
    │   ├── Singapore_result.json
    │   ├── Singapore_steps.csv
    │   └── summary.csv
    │
    ├── summary.csv
    ├── comparison.md
    └── paired_comparison.csv
```

| 파일 | 내용 |
|---|---|
| `README.md` | 실험 목적, 조건, 결과 및 결론 |
| `B1/` | B1 모델의 도시별 결과 및 궤적 기록 |
| `CorrMatchNet/` | CorrMatchNet의 도시별 결과 및 궤적 기록 |
| `summary.csv` | 전체 성능 요약 |
| `comparison.md` | 두 모델의 비교 분석 |
| `paired_comparison.csv` | 궤적별 쌍체 비교 및 통계검정 결과 |

## 8. 최종 결론

Seed 7 기반의 2D 폐루프 항법 평가에서 CorrMatchNet은 Singapore와 SF 두 도시 모두에서 100%의 성공률을 기록하여 B1보다 높은 성능을 보였다. 궤적별 쌍체 비교에서도 두 도시 모두 통계적으로 유의한 차이가 확인되었다.

다만 이번 결과는 2D 위성 지도 Crop을 입력으로 사용한 `capstone1 phase0` 평가이며, 실제 3D UAV 영상 기반 연속 항법 성능을 검증한 결과는 아니다.
