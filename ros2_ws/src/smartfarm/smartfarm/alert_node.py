import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
from datetime import datetime

# 임계값 설정
HUMID_HIGH = 70.0
TEMP_HIGH  = 35.0
SOIL_DRY   = 20

class AlertNode(Node):
    def __init__(self):
        super().__init__('alert_node')

        # 구독
        self.sub_env = self.create_subscription(
            String, '/farm/env_data', self.env_callback, 10)
        self.sub_growth = self.create_subscription(
            String, '/farm/growth', self.growth_callback, 10)
        self.sub_disease = self.create_subscription(
            String, '/farm/disease', self.disease_callback, 10)

        # 경고 발행
        self.publisher = self.create_publisher(String, '/farm/alert', 10)

        self.get_logger().info('alert_node 시작')

    def publish_alert(self, level, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        payload = json.dumps({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        self.publisher.publish(String(data=payload))
        self.get_logger().warn(f'[{level}] {message}')

    def env_callback(self, msg):
        try:
            data = json.loads(msg.data)
            temp  = data['temperature']
            humid = data['humidity']
            soil  = data['soil']

            if humid >= HUMID_HIGH:
                self.publish_alert('WARNING', f'습도 높음: {humid}% → 팬 가동')
            if temp >= TEMP_HIGH:
                self.publish_alert('WARNING', f'온도 높음: {temp}°C')
            if soil <= SOIL_DRY:
                self.publish_alert('WARNING', f'토양 건조: {soil}%')

        except Exception as e:
            self.get_logger().error(f'[ERROR] {e}')

    def growth_callback(self, msg):
        try:
            data = json.loads(msg.data)
            green_ratio = data['green_ratio']

            if green_ratio < 5.0:
                self.publish_alert('WARNING', f'초록 영역 감소: {green_ratio}%')

        except Exception as e:
            self.get_logger().error(f'[ERROR] {e}')

    def disease_callback(self, msg):
        try:
            data = json.loads(msg.data)
            if data['is_disease']:
                self.publish_alert(
                    'CRITICAL',
                    f"질병 감지: {data['prediction']} ({data['confidence']}%)"
                )

        except Exception as e:
            self.get_logger().error(f'[ERROR] {e}')

def main(args=None):
    rclpy.init(args=args)
    node = AlertNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()