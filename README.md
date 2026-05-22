# SmartFarm Mini Project with ROS2 & Docker
ROS2(Jazzy) 기반으로 구동되는 소형 스마트 팜 모니터링 및 질병 진단 시스템입니다.
센서 데이터 수집(시리얼 통신), OpenCV 기반의 생장 프로세싱, PyTorch(ResNet50) 기반의 식물 질병 추론, 그리고 실시간 경고 시스템이 유기적으로 연동되어 있습니다.

# 시스템 아키텍처 및 토픽 흐름
본 프로젝트는 각 노드가 독립적으로 구동되며, ROS2 토픽을 통해 데이터를 주고받습니다.

## 주요 노드 역할
- sensor_node: 아두이노와 시리얼 통신을 통해 온/습도, 토양 수분 데이터를 수집하여 MariaDB 및 CSV에 저장하고 토픽을 발행합니다.

- vision_node: USB 카메라로부터 영상을 받아 실시간으로 왜곡 보정(Calibration) 및 HSV 초록색 마스킹을 수행하여 식물의 생장률을 모니터링합니다. 스케줄러 트리거에 따라 이미지를 저장합니다.

- scheduler_node: 지정된 주기(3시간 간격)마다 촬영 트리거 메시지를 발행하여 시스템의 불필요한 리소스 낭비를 방지합니다.

- ai_node: 저장된 최신 식물 이미지를 로드하여 ResNet50 모델을 통해 질병 유무를 추론합니다. (라즈베리파이 3 리소스 제한을 고려하여 단일 스레드로 최적화)

- alert_node: 환경 데이터와 질병 진단 결과를 실시간으로 모니터링하여 임계치 초과나 질병 발생 시 CRITICAL/WARNING 알림을 발행합니다.

# 기술 스택 및 환경
- 주요 언어: Python, C++(Arduino)

- 핵심 프레임워크/라이브러리: ROS2 Jazzy, OpenCV 4.13, PyTorch 2.12 (CPU), ResNet50 

- 데이터베이스: MariaDB, CSV Log Files

- 하드웨어: Raspberry Pi 3, Arduino Uno, USB 웹 카메라

- OS / 컨테이너: Raspberry Pi OS + Docker

# 디렉토리 구조
아두이노 펌웨어 소스 코드(`smartfarm_ard`)와 ROS2 Jazzy 워크스페이스(`ros2_ws`)로 분리되어 관리됩니다.

```text
smartfarm/
├── smartfarm_ard/                  # 아두이노 펌웨어 디렉터리
│   └── smartfarm_ard.ino           # 센서 데이터 수집 및 팬 제어 아두이노 소스 파일
│
└── ros2_ws/                        # ROS2 워크스페이스
    └── src/
        └── smartfarm/              # smartfarm ROS2 패키지
            ├── launch/
            │   └── smartfarm.launch.py   # 5개 노드 일괄 실행을 위한 런치 파일
            │
            ├── smartfarm/          # ROS2 파이썬 노드 소스코드 디렉터리
            │   ├── __init__.py
            │   ├── ai_node.py       # PyTorch 기반 식물 질병 추론 노드
            │   ├── alert_node.py    # 위험 임계치 모니터링 및 실시간 경고 노드
            │   ├── scheduler_node.py # 정기 촬영(3시간 주기) 트리거 발행 노드
            │   ├── sensor_node.py   # 시리얼 데이터 수집 및 DB/CSV 저장 노드
            │   └── vision_node.py   # OpenCV 기반 생장률 분석 및 이미지 저장 노드
            │
            ├── resource/           # 패키지 리소스 디렉터리
            ├── package.xml         # 패키지 메타데이터 및 의존성 정의 파일
            ├── setup.cfg           # 스크립트 및 환경 설정 파일
            └── setup.py            # 패키지 빌드 및 진입점(Entry Points) 정의 파일
``` 

# 아두이노 연결

* **Arduino 5V** ──► 브레드보드 전원 라인 (+)
* **Arduino GND** ──► 브레드보드 접지 라인 (-)

* **DHT11 (온습도 센서 모듈)**
  * `+` 또는 `VCC` (가운데 핀) ──► 브레드보드 (+)
  * `-` 또는 `GND` (우측 핀) ──► 브레드보드 (-)
  * `S` 또는 `OUT` (데이터 핀) ──► 아두이노 **Digital 8 (D8)**
* **토양 수분 센서 (Soil Moisture)**
  * `VCC` ──► 브레드보드 (+)
  * `GND` ──► 브레드보드 (-)
  * `AOUT` (아날로그 출력) ──► 아두이노 **Analog 0 (A0)**

* **L9110S (모터 드라이버 - 팬 제어)**
  * `VCC` ──► 브레드보드 (+)
  * `GND` ──► 브레드보드 (-)
  * `A-1A` (제어 신호) ──► 아두이노 **Digital 9 (D9)** *(PWM 제어 가능)*
  * `A-1B` (방향 기준) ──► 브레드보드 (-) *(GND 고정)*
  * `MOTOR A` 단자 ──► DC 팬(Fan) 양단 연결


# 실행 방법

## 1. 사전 준비
**아두이노 펌웨어 업로드**: 
   `smartfarm_ard/smartfarm_ard.ino` 파일을 Arduino IDE로 열어 보드에 업로드합니다.

**하드웨어 연결**: 
   업로드가 완료된 아두이노와 USB 웹캠을 라즈베리파이(또는 PC)에 연결합니다.

**디바이스 권한 부여**:
   시리얼 및 카메라 디바이스가 정상 인식되도록 권한을 설정합니다.

``` bash
# 시리얼 및 카메라 디바이스 권한 부여
sudo chmod 666 /dev/ttyUSB0
sudo chmod 666 /dev/video*
```
## 2. 환경별 실행 방법
### 2-1. Docker 환경에서 실행하는 경우
Docker를 사용하면 ROS2 Jazzy 및 PyTorch, OpenCV 등의 복잡한 의존성 설정을 생략하고 즉시 구동할 수 있습니다.

1. 도커 컨테이너 실행

호스트의 프로젝트 디렉터리를 컨테이너 내부의 /smartfarm 경로로 마운트하여 실행합니다.
``` bash
docker run -it \
  --network host \
  --privileged \
  -v ~/projects/smartfarm:/smartfarm \
  smartfarm-ros:with-torch
```

2. (선택) 추가 터미널에서 컨테이너 접속

토픽 모니터링이나 개별 노드 테스트를 위해 추가 터미널을 열 때 사용합니다.
``` bash
# 실행 중인 컨테이너 ID 확인
docker ps
# 특정 컨테이너 접속
docker exec -it [컨테이너ID] bash
```

3. 컨테이너 내부에서 ROS2 패키지 빌드

``` bash
# ROS2 언더레이 환경 로드 및 이동
source /opt/ros/jazzy/setup.bash
cd /smartfarm/ros2_ws

# smartfarm 패키지 지정 빌드
colcon build --packages-select smartfarm
source install/setup.bash
```

4. 전체 시스템 실행 (Launch)
``` bash
ros2 launch smartfarm smartfarm.launch.py
```

사용하지 않는 도커 컨테이너 정리

테스트 후 찌꺼기 컨테이너를 강제로 일괄 삭제하여 저장 공간을 확보합니다.
``` bash
docker container prune -f
```
### 2-2 로컬 환경에서 실행하는 경우 (Docker 미사용)
호스트 OS에 ROS2 Jazzy가 기본 설치되어 있고, 파이썬 의존성 패키지가 구성된 환경에서의 실행 방법입니다.

1. 필수 의존성 패키지 설치
``` bash
pip install torch torchvision numpy opencv-python-headless mysql-connector-python pyserial pillow
```

2. ROS2 패키지 빌드
``` bash
# ROS2 환경 로드
source /opt/ros/jazzy/setup.bash

# 프로젝트의 ros2_ws 경로로 이동
cd ~/projects/smartfarm/ros2_ws
colcon build --packages-select smartfarm
source install/setup.bash
```
3. 전체 시스템 실행 (Launch)
``` bash
ros2 launch smartfarm smartfarm.launch.py
```

## 3. 디버깅 및 토픽 테스트
시스템이 정상 작동하는지 확인하기 위해 추가 터미널(또는 docker exec 세션)을 열고 아래 명령어를 수행할 수 있습니다.

1. 개별 노드 수동 실행 (디버깅용)

런치 파일을 쓰지 않고 특정 노드의 로그만 집중적으로 확인하고 싶을 때 사용합니다.

``` bash
ros2 run smartfarm sensor_node   # 센서 데이터 수집 노드
ros2 run smartfarm vision_node   # 비전 프로세싱 노드
ros2 run smartfarm ai_node       # AI 질병 추론 노드
ros2 run smartfarm alert_node    # 경고 및 알림 노드
```

2. 실시간 토픽 모니터링
발행되는 센서 데이터와 비전 분석 데이터를 실시간으로 모니터링합니다.

``` bash
# 센서 및 팬 상태 데이터 확인
ros2 topic echo /farm/env_data

# 식물 생장률(초록 영역 비율) 및 FPS 확인
ros2 topic echo /farm/growth
```

3. 수동 촬영 및 추론 테스트 트리거

스케줄러 노드는 3시간 주기로 촬영을 요청하므로, 테스트 목적으로 즉시 촬영 및 AI 추론을 수행하고 싶을 때 아래 토픽을 수동으로 발행합니다.

``` bash
ros2 topic pub /farm/capture_trigger std_msgs/msg/String "data: 'test'" --once
```

# 데이터 저장 스펙
1. MariaDB (smartfarm 데이터베이스)

sensor_node 실행 시 자동으로 테이블이 생성되며 데이터가 누적됩니다.

> ⚠️ **[중요] 데이터베이스 연결 설정 주의사항**
> * `sensor_node.py` 소스 코드 내부에는 MariaDB 접근 계정이 다음과 같이 고정되어 있습니다:
>   * `host='localhost'`, `user='pi'`, `password='test1234'`, `database='smartfarm'`
> * **Docker 환경을 사용하는 경우**: MariaDB가 라즈베리파이 호스트(Host OS)에 설치되어 있다면, 컨테이너 내부에서 호스트의 DB로 접근하기 위해 `host='localhost'` 설정을 **`host='127.0.0.1'`** 또는 도커 브리지 IP인 **`host='172.17.0.1'`**로 수정해야 할 수 있습니다. 
> * 본인의 데이터베이스 구축 환경(계정명, 비밀번호, 호스트 IP)에 맞게 소스 코드를 반드시 수정 후 빌드하여 사용하세요.

Table: sensor_data

Columns: id (PK), timestamp, temperature, humidity, soil, fan

2. CSV 로그 파일

데이터 수집 및 분석을 위해 실시간 데이터가 타임스탬프와 함께 지정된 경로에 기록됩니다.

센서 로그 (/smartfarm/smartfarm_data.csv): timestamp, temperature, humidity, soil, fan

비전 생장 로그 (/smartfarm/growth_log.csv): timestamp, green_ratio, green_pixels, green_area_cm2, total_pixels, avg_fps


# 실시간 모니터링 및 위험 알림 기준
`alert_node`는 각 토픽의 데이터를 모니터링하여 아래 조건 발생 시 /farm/alert 토픽으로 알림을 퍼블리시합니다.

| 모니터링 대상 | 임계값 (Threshold) | 알림 레벨 | 대응 액션 / 메시지 |
| :--- | :--- | :--- | :--- |
| **습도 (Humidity)** | 70.0% 이상 | WARNING | 습도 높음 → 팬 가동 유도 |
| **온도 (Temperature)** | 35.0°C 이상 | WARNING | 온도 높음 경고 |
| **토양 수분 (Soil)** | 20% 이하 | WARNING | 토양 건조 경고 |
| **초록 영역 비율** | 5.0% 미만 | WARNING | 초록 영역 감소 (생장 부진 또는 잎 탈락) |
| **AI 질병 진단** | 잎곰팡이병, 황화잎말이바이러스 | CRITICAL | 질병 이름 및 추론 신뢰도(%) 출력 |

# AI Model & Inference Details
## 1. 대상 작물 및 학습 데이터

### 학습 데이터셋
- **데이터셋명**: 시설 작물 질병 진단 이미지
- **출처**: AI Hub (한국지능정보사회진흥원)
- **링크**: https://aihub.or.kr/aihubdata/data/view.do?currMenu=115&topMenu=100&aihubDataSe=data&dataSetSn=153
- **활용 클래스**: 토마토 정상 / 잎곰팡이병 / 황화잎말이바이러스(TYLCV) 3종

### 대상 작물: 토마토 (Tomato Only)
- 본 프로젝트의 ai_node에 탑재된 모델은 토마토 단일 작물만을 타깃으로 학습되었습니다. 토마토 이외의 타 작물이나 이물질을 촬영할 경우 올바른 추론을 수행하지 않습니다.

### 학습 및 분류 클래스 (3 Classes):

`정상 (Normal)`: 건강한 토마토 잎

`잎곰팡이병 (Leaf Mold)`: 토마토 잎곰팡이병 증상이 발현된 잎

`황화잎말이바이러스 (TYLCV)`: 토마토황화잎말림바이러스(Yellow Leaf Curl Virus)에 감염된 잎

## 2. 추론 신뢰도(Confidence)와 실제 정확도(Accuracy)의 차이점

- **신뢰도(Confidence)의 정의**: 모델이 출력하는 신뢰도(%)는 Softmax 함수를 거쳐 나온 확률값으로, "모델이 스스로 해당 클래스라고 믿는 확신의 정도"를 나타냅니다. 

- **실제 정확도(Accuracy)와의 차이**: 신뢰도가 높다고 해서 반드시 정답을 맞췄다는 의미는 아닙니다. 예를 들어 모델이 99% 신뢰도로 "정상"이라고 판단해도 실제로는 질병일 수 있습니다. 본 모델의 검증 데이터셋 기준 실제 정확도는 약 85%입니다.

- **주의사항**: 학습에 사용된 AI Hub 데이터셋 이미지와 유사한 이미지일수록 신뢰도가 비정상적으로 높게(98% 이상) 나올 수 있습니다. 실제 환경에서 촬영한 새로운 이미지로 테스트하는 것을 권장합니다.

# 트러블슈팅
- 카메라 인식 안 될 때: 웹캠 재연결 후 컨테이너 재시작
- SSH 첫 접속 실패: 두 번째 시도하면 정상 연결됨
- torch 설치 공간 부족: CPU 전용 버전 사용 (--index-url https://download.pytorch.org/whl/cpu)