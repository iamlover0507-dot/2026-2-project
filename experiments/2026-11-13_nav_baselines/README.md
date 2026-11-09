# Navigation Baseline Experiments

B1 and CorrMatchNet evaluation results.


# B1 and CorrMatchNet Evaluation Results

## 1. 실험 목적

기존 B1 모델과 CorrMatchNet의 항법 성능을 비교하기 위해 두 모델을 동일한 환경에서 평가하였다. Singapore와 San Francisco(SF) 두 도시를 대상으로 폐루프(Closed-loop) 항법 실험을 수행하고, 궤적별 성공률과 통계적 유의성을 분석하였다.

## 2. 실험 설정

| 항목         | 설정                       |
| ---------- | ------------------------ |
| 평가 모델      | B1, CorrMatchNet         |
| 평가 도시      | Singapore, San Francisco |
| Seed       | 7                        |
| 도시별 궤적 수   | 32개                      |
| 총 평가 궤적    | 모델별 64개                  |
| 항법 방식      | Closed-loop navigation   |
| 이동 거리      | Step당 15m                |
| 도착 판정 거리   | 20m                      |
| 초기 Heading | 90°                      |
| 평가 환경      | Kaggle GPU (T4)          |

두 모델은 동일한 seed로 생성한 궤적을 사용하였다. 각 도시에서 32개 궤적의 시작 위치와 초기 블록 위치가 일치하는 것도 확인하였다.

**평가 환경 관련 주의:** 이번 T5 실험은 3D-view 체크포인트 및 메타데이터를 선택했지만, 실제 입력은 각 시점의 2D 위성 지도 Crop을 사용하는 방식이다. 따라서 실제 3D UAV 영상 입력 실험으로 해석해서는 안 된다.

## 3. 실험 결과

### 3.1 도시별 항법 성공률

| 도시        | 모델           | 성공률    | 성공 궤적 | 실행 시간 |
| --------- | ------------ | ------ | ----- | ----- |
| Singapore | B1           | 18.8%  | 6/32  | 35.5초 |
| Singapore | CorrMatchNet | 100.0% | 32/32 | 50.7초 |
| SF        | B1           | 40.6%  | 13/32 | 29.0초 |
| SF        | CorrMatchNet | 100.0% | 32/32 | 52.4초 |

성공률의 95% 신뢰구간은 다음과 같다.

- Singapore B1: 8.9–35.3%
- Singapore CorrMatchNet: 89.3–100.0%
- SF B1: 25.5–57.7%
- SF CorrMatchNet: 89.3–100.0%

### 3.2 실패 원인

B1 모델의 실패 원인을 확인한 결과 다음과 같았다.

- Singapore: 26개 궤적에서 `out_of_map` 발생
- SF: 19개 궤적에서 `out_of_map` 발생

반면 CorrMatchNet은 두 도시에서 모두 32개 궤적이 `arrived_ok`로 종료되었다.

## 4. 궤적별 쌍체 비교 및 통계검정

동일한 시작 조건을 가진 궤적끼리 비교하기 위해 각 모델의 궤적별 최종 성공 여부를 기준으로 쌍체 비교를 수행하였다.

| 도시        | 둘 다 성공 | B1만 성공 | CorrMatchNet만 성공 | 둘 다 실패 | p-value     |
| --------- | ------ | ------ | ---------------- | ------ | ----------- |
| Singapore | 6      | 0      | 26               | 0      | 2.98 × 10⁻⁸ |
| SF        | 13     | 0      | 19               | 0      | 3.81 × 10⁻⁶ |

불일치 쌍에 대한 정확 이항검정(Exact Binomial Test)을 수행하였다. 이는 정확 McNemar 검정과 동등한 방식이다.

두 도시 모두 p < 0.05로 통계적으로 유의한 차이가 확인되었다.

## 5. 종합 분석

CorrMatchNet은 Singapore와 SF 두 도시에서 모두 100%의 항법 성공률을 달성하였다. 반면 B1은 Singapore에서 18.8%, SF에서 40.6%의 성공률을 기록하였다.

동일한 시작 조건을 가진 궤적별 비교에서도 CorrMatchNet만 성공한 궤적이 Singapore 26개, SF 19개였으며, B1만 성공한 궤적은 두 도시 모두 없었다.

이 결과는 이번 실험 조건에서 CorrMatchNet이 B1보다 높은 폐루프 항법 성공률을 보였음을 나타낸다. 다만 실험은 seed 7과 도시별 32개 궤적을 기준으로 수행되었으므로, 일반화 가능성을 확인하려면 추가 seed와 더 많은 궤적에 대한 평가가 필요하다.

## 6. 결과 파일

실험 결과는 다음 구조로 정리하였다.

```
experiments/
└── 2026-11-13_nav_baselines/
    ├── B1/
    │   ├── SF_result.json
    │   ├── SF_steps.csv
    │   ├── Singapore_result.json
    │   ├── Singapore_steps.csv
    │   └── summary.csv
    ├── CorrMatchNet/
    │   ├── SF_result.json
    │   ├── SF_steps.csv
    │   ├── Singapore_result.json
    │   ├── Singapore_steps.csv
    │   └── summary.csv
    ├── summary.csv
    ├── comparison.md
    └── paired_comparison.csv
```

**최종 결론:** 이번 seed 7 기반 T5 평가에서 CorrMatchNet은 B1보다 두 도시 모두에서 높은 항법 성공률을 기록했으며, 궤적별 쌍체 비교에서도 통계적으로 유의한 차이를 보였다.

## 핵심 결과만 다시 보면

## CorrMatchNet 항법 성공률

Singapore

# 100%

32 / 32

B1: 18.8%

San Francisco

# 100%

32 / 32

B1: 40.6%

통계검정

- Singapore: p = 2.98 × 10⁻⁸
- SF: p = 3.81 × 10⁻⁶

주의할 점: 이번 결과는 seed 7의 32개 궤적씩을 평가한 결과야. CorrMatchNet의 100% 성공률을 모든 환경에서 보장되는 성능으로 표현하면 안 돼.

다음으로 이 내용을 바탕으로 교수님 제출용 실험 결과 표와 분석 문단까지 정리할 수 있어.
