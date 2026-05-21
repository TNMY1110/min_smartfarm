import paho.mqtt.client as mqtt
import json
import signal
import sys

MQTT_BROKER = 'localhost'
MQTT_TOPIC = 'smartfarm/sensors'

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("=== MQTT 브로커 연결 성공 ===")
        client.subscribe(MQTT_TOPIC)
        print(f"구독 시작: {MQTT_TOPIC}")
    else:
        print(f"연결 실패: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        timestamp = payload['timestamp']
        temp = payload['temperature']
        humid = payload['humidity']
        soil = payload['soil']
        fan = payload['fan']

        print(f"\n[{timestamp}]")
        print(f"  온도     : {temp}°C")
        print(f"  습도     : {humid}%")
        print(f"  토양수분 : {soil}%")
        print(f"  팬 속도  : {fan}/255")

        if humid >= 70:
            print("  ⚠️  경고: 습도 높음 → 팬 최대 가동")
        if soil <= 20:
            print("  ⚠️  경고: 토양 건조")
        if temp >= 35:
            print("  ⚠️  경고: 온도 높음")

    except Exception as e:
        print(f"[ERROR] {e}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"[WARN] 예상치 못한 연결 끊김 (rc={rc})")
    else:
        print("브로커 연결 해제 완료")

# ─────────────────────────────────────────────
# Ctrl+C 핸들러
# ─────────────────────────────────────────────
def shutdown(sig, frame):
    print("\n\n[종료 중] MQTT 연결 해제 중...")
    client.unsubscribe(MQTT_TOPIC)   # 구독 해제
    client.disconnect()              # 브로커에 DISCONNECT 패킷 전송
    client.loop_stop()               # 내부 네트워크 루프 정리
    print("[종료 완료]")
    sys.exit(0)

signal.signal(signal.SIGINT,  shutdown)   # Ctrl+C
signal.signal(signal.SIGTERM, shutdown)   # kill 명령 대응

# ─────────────────────────────────────────────
# 클라이언트 시작
# ─────────────────────────────────────────────
client = mqtt.Client()
client.on_connect    = on_connect
client.on_message    = on_message
client.on_disconnect = on_disconnect

client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()