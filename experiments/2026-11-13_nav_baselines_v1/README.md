# Navigation Baselines: B1과 CorrMatchNet의 3D + VIO 항법 성능 비교

## 1. 실험 목적

기존 B1 및 CorrMatchNet 항법 기준선은 2D 지도 입력을 사용하므로, 우리 프로젝트의 V1 방식인 **3D 렌더링 지도 입력 + 이동 오차 기반 항법**과 직접 비교하기 어렵다.

따라서 두 기준선을 3D 지도 입력과 VIO 조건으로 실행하여, V1과 비교할 수 있는 항법 실험 환경을 구성하고자 했다.

## 2. 실험 진행 및 완료 사항

B1과 CorrMatchNet을 기존 Notebook의 `nav_run()`을 통해 각각 실행했다.

| 항목 | 실험 조건 |
|---|---|
| 지도 입력 | 3D 렌더링 지도 |
| 이동 오차 | VIO 적용 |
| 평가 지역 | San Francisco, Singapore |
| 경로 수 | 지역별 32개 |
| Seed | 7 |
| 경로 간격 | 15m |
| 도착 판정 반경 | 20m |
| 목표 경로 길이 | 1,000m |
| VIO 설정 | bias 3°, heading 오차 2°, scale 0.05 |

두 모델에 대해 SF와 Singapore 실험을 수행하고 결과 CSV를 생성했다.

### 완료된 작업

- B1의 3D 지도 입력 및 VIO 조건 실험
- CorrMatchNet의 3D 지도 입력 및 VIO 조건 실험
- SF 및 Singapore 지역별 성능 비교
- 팀 공통 10m 위치 오차 평가 기준 적용
- 모델별 paired comparison 수행
- 경로별 및 스텝별 결과 CSV 저장

## 3. 주요 실험 결과

### 3.1 항법 도착 성공률

| 지역 | 모델 | 도착 성공 |
|---|---|---:|
| SF | B1 | 8/32 (25.00%) |
| SF | CorrMatchNet | 5/32 (15.62%) |
| Singapore | B1 | 9/32 (28.12%) |
| Singapore | CorrMatchNet | 8/32 (25.00%) |

### 3.2 공통 10m 위치 오차 평가

팀의 공통 평가 기준에 따라 추정 좌표를 ±1 범위로 클리핑하고, 위치 오차가 10m 이하인 경우를 성공으로 계산했다.

| 지역 | 모델 | 10m 성공률 | 평균 위치 오차 |
|---|---|---:|---:|
| SF | B1 | 0.76% | 458.11m |
| SF | CorrMatchNet | 1.51% | 309.89m |
| Singapore | B1 | 0.75% | 479.50m |
| Singapore | CorrMatchNet | 1.56% | 333.37m |

공통 10m 평가에서는 CorrMatchNet이 두 지역 모두 B1보다 높은 성공률과 낮은 평균 위치 오차를 보였다. 다만 절대적인 10m 성공률은 두 모델 모두 낮으므로 결과 해석에 주의해야 한다.

### 3.3 Paired Comparison

공통 `(trajectory, step)` 기준으로 비교한 결과, 두 지역 통합 분석에서 CorrMatchNet의 10m 성공이 더 많았다.

- B1만 성공: 30
- CorrMatchNet만 성공: 65
- 두 모델 모두 성공: 4
- 두 모델 모두 실패: 4,276
- McNemar 검정 p-value: 0.000425

단, 동일 경로 내 스텝들은 서로 독립적이지 않으므로 스텝 단위 검정은 탐색적 결과로 해석한다. 경로 단위 분석에서는 두 지역 각각의 차이가 통계적으로 유의하지 않았으며, 통합 분석에서는 유의한 차이가 관찰되었다.

## 4. 결과 해석 및 한계

이번 실험을 통해 기존 2D 항법 기준선인 B1과 CorrMatchNet을 3D 지도 입력 및 VIO 조건으로 실행하고, V1과 비교하기 위한 실험 결과를 확보했다.

공통 10m 평가에서는 CorrMatchNet이 B1보다 상대적으로 좋은 결과를 보였다. 그러나 두 모델 모두 절대적인 10m 성공률이 낮아, 현재 결과만으로 실제 항법 성능이 충분하다고 판단할 수는 없다.

또한 이번 실험은 Notebook에서 `nav_run()`을 개별 호출하여 수행한 것이다. 독립 실행 스크립트인 `scripts/run_nav.py`에 두 모델이 통합되었는지는 아직 확인되지 않았다.

## 5. 현재 작업 상태

| 작업 | 상태 |
|---|---|
| B1 3D + VIO 실험 | 완료 |
| CorrMatchNet 3D + VIO 실험 | 완료 |
| SF·Singapore 비교 | 완료 |
| 공통 10m 평가 | 완료 |
| Paired comparison | 완료 |
| 실험 결과 CSV 생성 | 완료 |
| `scripts/run_nav.py` 통합 여부 확인 | 미확인 |
| `--frames 3d --odo vio` CLI 실행 검증 | 미완료 |
| 독립 실행 및 재현성 검증 | 미완료 |

## 6. 후속 작업

Kaggle GPU 사용량 초기화 전까지는 GPU 추론 실험을 진행하지 않는다.

GPU 없이 가능한 작업:
1. 기존 B1 및 CorrMatchNet 실행 코드 구조 확인
2. `scripts/run_nav.py` 통합 코드 작성
3. CLI 인자 및 모델 선택 로직 정리
4. 코드 문법 및 정적 검토
5. README와 실험 결과 문서 정리

Kaggle GPU 사용량 초기화 후 진행할 작업:
1. `scripts/run_nav.py`에서 B1 및 CorrMatchNet 실행
2. `--frames 3d --odo vio` CLI 실행 확인
3. 기존 Notebook 실험과 결과 재현성 확인

**최종 정리:** B1과 CorrMatchNet의 3D + VIO 조건 비교 실험은 완료했다. 다만 이를 독립 실행형 `scripts/run_nav.py`로 통합하고 CLI 실행까지 검증하는 작업은 별도로 남아 있다.
