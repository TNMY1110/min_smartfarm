import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import torch
import torchvision.models as models
import torchvision.transforms as transforms
import torch.nn as nn
from PIL import Image
import json
import os
import time
from datetime import datetime

MODEL_PATH = '/smartfarm/best_model_resnet50_85.pth'
IMAGE_DIR  = '/smartfarm/plant_images'
CLASS_NAMES = ["정상", "잎곰팡이병", "황화잎말이바이러스"]
CONFIDENCE_THRESHOLD = 0.7

class AiNode(Node):
    def __init__(self):
        super().__init__('ai_node')
        self.publisher = self.create_publisher(String, '/farm/disease', 10)

        self.get_logger().info('모델 로드 중...')
        start = time.time()

        # 라즈베리파이 메모리 최적화
        torch.set_num_threads(1)

        self.model = models.resnet50()
        self.model.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(self.model.fc.in_features, 3)
        )
        self.model.load_state_dict(
            torch.load(MODEL_PATH, map_location='cpu')
        )
        self.model.eval()
        self.get_logger().info(f'모델 로드 완료 ({time.time()-start:.1f}초)')

        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406],
                                 [0.229, 0.224, 0.225]),
        ])

        self.timer = self.create_timer(30.0, self.run_inference)
        self.get_logger().info('ai_node 시작')

    def get_latest_image(self):
        if not os.path.exists(IMAGE_DIR):
            return None
        images = sorted([
            os.path.join(IMAGE_DIR, f)
            for f in os.listdir(IMAGE_DIR)
            if f.endswith('.jpg')
        ])
        return images[-1] if images else None

    def run_inference(self):
        img_path = self.get_latest_image()
        if img_path is None:
            self.get_logger().warn('추론할 이미지 없음')
            return

        try:
            start = time.time()
            img = Image.open(img_path).convert('RGB')
            tensor = self.transform(img).unsqueeze(0)

            with torch.no_grad():
                output = self.model(tensor)
                probs = torch.softmax(output, dim=1)[0]
                pred = probs.argmax().item()
                confidence = probs[pred].item()

            elapsed = time.time() - start
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            result = {
                'timestamp': timestamp,
                'image': os.path.basename(img_path),
                'prediction': CLASS_NAMES[pred],
                'confidence': round(confidence * 100, 1),
                'elapsed': round(elapsed, 2),
                'is_disease': pred != 0,
                'probabilities': {
                    name: round(probs[i].item() * 100, 1)
                    for i, name in enumerate(CLASS_NAMES)
                }
            }

            self.publisher.publish(String(data=json.dumps(result)))
            self.get_logger().info(
                f'추론 완료 - {CLASS_NAMES[pred]} ({confidence*100:.1f}%) / {elapsed:.2f}초'
            )

            if pred != 0:
                self.get_logger().warn(f'⚠️  질병 감지: {CLASS_NAMES[pred]}')

        except Exception as e:
            self.get_logger().error(f'[ERROR] {e}')

    def destroy_node(self):
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = AiNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()