import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import mysql.connector
import csv
import os
import json
import time
from datetime import datetime

CSV_FILE = '/smartfarm/smartfarm_data.csv'

class SensorNode(Node):
    def __init__(self):
        super().__init__('sensor_node')
        self.publisher = self.create_publisher(String, '/farm/env_data', 10)

        # CSV 초기화
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'temperature', 'humidity', 'soil', 'fan'])

        # MariaDB 연결
        self.db = mysql.connector.connect(
            host='localhost',
            user='pi',
            password='test1234',
            database='smartfarm'
        )
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                temperature FLOAT,
                humidity FLOAT,
                soil INT,
                fan INT
            )
        ''')
        self.db.commit()

        # 시리얼 연결
        self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        time.sleep(2)

        self.timer = self.create_timer(2.0, self.read_sensor)
        self.get_logger().info('sensor_node 시작')

    def read_sensor(self):
        try:
            line = self.ser.readline().decode('utf-8').strip()
            if not line or ':' not in line:
                return

            data = {}
            for item in line.split(','):
                key, value = item.split(':', 1)
                data[key] = value

            temp  = float(data['TEMP'])
            humid = float(data['HUMID'])
            soil  = int(data['SOIL'])
            fan   = int(data['FAN'])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # ROS2 토픽 발행
            payload = json.dumps({
                'timestamp': timestamp,
                'temperature': temp,
                'humidity': humid,
                'soil': soil,
                'fan': fan
            })
            self.publisher.publish(String(data=payload))
            self.get_logger().info(f'발행: {payload}')

            # MariaDB 저장
            self.cursor.execute('''
                INSERT INTO sensor_data (timestamp, temperature, humidity, soil, fan)
                VALUES (%s, %s, %s, %s, %s)
            ''', (timestamp, temp, humid, soil, fan))
            self.db.commit()

            # CSV 저장
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, temp, humid, soil, fan])

        except Exception as e:
            self.get_logger().error(f'[ERROR] {e}')

    def destroy_node(self):
        self.ser.close()
        self.db.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()