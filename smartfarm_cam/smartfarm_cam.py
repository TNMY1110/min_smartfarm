import cv2
import numpy as np
import csv
import os
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# 설정
CAMERA_INDEX = 0
CSV_FILE = 'growth_log.csv'
SAVE_DIR = 'plant_images'
ROI_X, ROI_Y, ROI_W, ROI_H = 100, 50, 440, 380  # ROI 영역 (필요시 조정)

# 카메라 캘리브레이션 파라미터 (calibrate.py 실행 후 값 교체)
# 없으면 None으로 두면 캘리브레이션 없이 동작
CAMERA_MATRIX = None
DIST_COEFFS = None

# 실제 면적 환산 상수 (캘리브레이션 후 설정)
# 예: 1픽셀 = 0.1cm 이면 PIXEL_TO_CM = 0.1
PIXEL_TO_CM = 0.0032  # 캘리브레이션 값

os.makedirs(SAVE_DIR, exist_ok=True)

# CSV 초기화
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'green_ratio', 'green_pixels',
                        'green_area_cm2', 'total_pixels', 'avg_fps'])

def save_snapshot(frame, mask, green_ratio, green_pixels, total_pixels, avg_fps):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    filename = os.path.join(SAVE_DIR, f"plant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
    cv2.imwrite(filename, frame)

    # 실제 면적 환산 (픽셀 → cm²)
    green_area_cm2 = round(green_pixels * (PIXEL_TO_CM ** 2), 2)

    # CSV 저장
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, green_ratio, green_pixels,
                         green_area_cm2, total_pixels, round(avg_fps, 1)])

    print(f"[{timestamp}] 자동 저장 완료")
    print(f"  Green: {green_ratio}% / 면적: {green_area_cm2}cm² / FPS: {avg_fps:.1f}")
    print(f"  파일: {filename}")

# 스케줄러용 전역 변수
latest_data = {
    'frame': None,
    'mask': None,
    'green_ratio': 0,
    'green_pixels': 0,
    'total_pixels': 0,
    'avg_fps': 0
}

def scheduled_save():
    if latest_data['frame'] is not None:
        save_snapshot(
            latest_data['frame'],
            latest_data['mask'],
            latest_data['green_ratio'],
            latest_data['green_pixels'],
            latest_data['total_pixels'],
            latest_data['avg_fps']
        )

# 스케줄러 설정 (매일 07:00, 19:00)
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_save, 'cron', hour='7,19', minute=0)
scheduler.start()

# 카메라 초기화
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("=== 식물 성장 모니터링 시작 ===")
print("q: 종료 / s: 즉시 저장 테스트")

# FPS 평균 변수
FPS_SAMPLE = 30
frame_count = 0
fps_sum = 0
avg_fps = 0
prev_time = time.time()

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] 카메라 읽기 실패")
        break

    # 캘리브레이션 적용
    if CAMERA_MATRIX is not None and DIST_COEFFS is not None:
        frame = cv2.undistort(frame, CAMERA_MATRIX, DIST_COEFFS)

    # ROI 적용 (최적화)
    roi = frame[ROI_Y:ROI_Y+ROI_H, ROI_X:ROI_X+ROI_W]

    # FPS 계산 (30프레임 평균)
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time
    fps_sum += fps
    frame_count += 1
    if frame_count >= FPS_SAMPLE:
        avg_fps = fps_sum / FPS_SAMPLE
        fps_sum = 0
        frame_count = 0

    # 노이즈 제거
    blurred = cv2.GaussianBlur(roi, (5, 5), 0)

    # HSV 변환 및 초록 마스킹
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # morphology 처리
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 초록 영역 비율 계산
    total_pixels = roi.shape[0] * roi.shape[1]
    green_pixels = cv2.countNonZero(mask)
    green_ratio = round((green_pixels / total_pixels) * 100, 2)

    # 초록 영역 시각화
    green_area = cv2.bitwise_and(roi, roi, mask=mask)

    # ROI 박스 표시
    cv2.rectangle(frame, (ROI_X, ROI_Y),
                  (ROI_X+ROI_W, ROI_Y+ROI_H), (255, 0, 0), 2)

    # 정보 표시
    cv2.putText(frame, f'FPS: {avg_fps:.1f}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f'Green: {green_ratio}%', (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(frame, f'Area: {round(green_pixels*(PIXEL_TO_CM**2),2)}cm2', (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

    # 최신 데이터 업데이트
    latest_data.update({
        'frame': frame.copy(),
        'mask': mask.copy(),
        'green_ratio': green_ratio,
        'green_pixels': green_pixels,
        'total_pixels': total_pixels,
        'avg_fps': avg_fps
    })

    # 화면 출력
    cv2.imshow('Smart Farm', frame)
    cv2.imshow('Green Mask', mask)
    cv2.imshow('Green Area', green_area)

    # 키 입력
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        scheduled_save()  # 즉시 저장 테스트

scheduler.shutdown()
cap.release()
cv2.destroyAllWindows()