import serial
import paho.mqtt.client as mqtt
import mysql.connector
import csv
import os
import time
from datetime import datetime

# 설정
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 9600
MQTT_BROKER = 'localhost'
MQTT_TOPIC = 'smartfarm/sensors'
CSV_FILE = 'smartfarm_data.csv'

# CSV 초기화
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'temperature', 'humidity', 'soil', 'fan'])

# MySQL 연결
db = mysql.connector.connect(
    host='localhost',
    user='pi',
    password='test1234',
    database='smartfarm'
)
cursor = db.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        temperature FLOAT,
        humidity FLOAT,
        soil INT,
        fan INT
    )
''')
db.commit()

# MQTT 클라이언트 설정
client = mqtt.Client()
client.connect(MQTT_BROKER, 1883, 60)
client.loop_start()

# 시리얼 연결
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

print("=== 스마트팜 데이터 수신 시작 ===")

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if not line or ':' not in line:
            continue

        # 파싱
        data = {}
        for item in line.split(','):
            key, value = item.split(':')
            data[key] = value

        temp = float(data['TEMP'])
        humid = float(data['HUMID'])
        soil = int(data['SOIL'])
        fan = int(data['FAN'])
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # MQTT 발행
        payload = f'{{"timestamp":"{timestamp}","temperature":{temp},"humidity":{humid},"soil":{soil},"fan":{fan}}}'
        client.publish(MQTT_TOPIC, payload)
        print(f"[{timestamp}] MQTT 발행: {payload}")

        # MySQL 저장
        cursor.execute('''
            INSERT INTO sensor_data (timestamp, temperature, humidity, soil, fan)
            VALUES (%s, %s, %s, %s, %s)
        ''', (timestamp, temp, humid, soil, fan))
        db.commit()
        print(f"MySQL 저장 완료: {timestamp}")

        # CSV 저장
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, temp, humid, soil, fan])
        print(f"CSV 저장 완료: {timestamp}")

    except KeyboardInterrupt:
        print("종료")
        break
    except Exception as e:
        print(f"[ERROR] {e}")
        continue

ser.close()
db.close()
client.loop_stop()