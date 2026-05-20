import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
from datetime import datetime

class SchedulerNode(Node):
    def __init__(self):
        super().__init__('scheduler_node')
        self.publisher = self.create_publisher(String, '/farm/capture_trigger', 10)

        # 1분마다 시간 체크
        self.timer = self.create_timer(60.0, self.check_schedule)
        self.get_logger().info('scheduler_node 시작')

    def check_schedule(self):
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        # 매일 07:00, 19:00에 트리거 발행
        if minute == 0 and hour in [7, 19]:
            timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
            payload = json.dumps({
                'timestamp': timestamp,
                'trigger': 'scheduled_capture',
                'hour': hour
            })
            self.publisher.publish(String(data=payload))
            self.get_logger().info(f'촬영 트리거 발행: {timestamp}')

def main(args=None):
    rclpy.init(args=args)
    node = SchedulerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()