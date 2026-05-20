import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import cv2
import numpy as np
import csv
import os
import json
import pickle
from datetime import datetime

CSV_FILE = '/smartfarm/growth_log.csv'
SAVE_DIR = '/smartfarm/plant_images'
CALIB_FILE = '/smartfarm/camera_calibration.pkl'

ROI_X, ROI_Y, ROI_W, ROI_H = 100, 50, 440, 380
PIXEL_TO_CM = 0.003244
FPS_SAMPLE = 30

class VisionNode(Node):
    def __init__(self):
        super().__init__('vision_node')
        self.publisher = self.create_publisher(String, '/farm/growth', 10)

        os.makedirs(SAVE_DIR, exist_ok=True)

        # CSV 초기화
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'green_ratio', 'green_pixels',
                                 'green_area_cm2', 'total_pixels', 'avg_fps'])

        # 캘리브레이션 로드
        self.camera_matrix = None
        self.dist_coeffs = None
        if os.path.exists(CALIB_FILE):
            with open(CALIB_FILE, 'rb') as f:
                calib = pickle.load(f)
                self.camera_matrix = calib['camera_matrix']
                self.dist_coeffs = calib['dist_coeffs']
            self.get_logger().info('캘리브레이션 로드 완료')

        # 카메라 초기화
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # FPS 변수
        self.frame_count = 0
        self.fps_sum = 0.0
        self.avg_fps = 0.0
        self.prev_time = self.get_clock().now()

        # 최신 데이터
        self.latest_frame = None
        self.latest_green_ratio = 0.0
        self.latest_green_pixels = 0
        self.latest_total_pixels = 0

        # 타이머
        self.frame_timer = self.create_timer(0.1, self.process_frame)
        self.save_timer = self.create_timer(60.0, self.scheduled_save)

        self.get_logger().info('vision_node 시작')

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn('카메라 읽기 실패')
            return

        if self.camera_matrix is not None:
            frame = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs)

        roi = frame[ROI_Y:ROI_Y+ROI_H, ROI_X:ROI_X+ROI_W]

        # FPS 계산
        curr_time = self.get_clock().now()
        dt = (curr_time - self.prev_time).nanoseconds / 1e9
        if dt > 0:
            fps = 1.0 / dt
            self.fps_sum += fps
            self.frame_count += 1
            if self.frame_count >= FPS_SAMPLE:
                self.avg_fps = self.fps_sum / FPS_SAMPLE
                self.fps_sum = 0.0
                self.frame_count = 0
        self.prev_time = curr_time

        # 초록 마스킹
        blurred = cv2.GaussianBlur(roi, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 50, 50])
        upper_green = np.array([90, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        total_pixels = roi.shape[0] * roi.shape[1]
        green_pixels = cv2.countNonZero(mask)
        green_ratio = round((green_pixels / total_pixels) * 100, 2)

        self.latest_frame = frame.copy()
        self.latest_green_ratio = green_ratio
        self.latest_green_pixels = green_pixels
        self.latest_total_pixels = total_pixels

        payload = json.dumps({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'green_ratio': green_ratio,
            'green_pixels': green_pixels,
            'green_area_cm2': round(green_pixels * (PIXEL_TO_CM ** 2), 2),
            'avg_fps': round(self.avg_fps, 1)
        })
        self.publisher.publish(String(data=payload))

    def scheduled_save(self):
        if self.latest_frame is None:
            return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.join(SAVE_DIR, f"plant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        cv2.imwrite(filename, self.latest_frame)

        green_area_cm2 = round(self.latest_green_pixels * (PIXEL_TO_CM ** 2), 2)

        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, self.latest_green_ratio, self.latest_green_pixels,
                             green_area_cm2, self.latest_total_pixels, round(self.avg_fps, 1)])

        self.get_logger().info(f'저장 완료 - Green: {self.latest_green_ratio}% / 파일: {filename}')

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()