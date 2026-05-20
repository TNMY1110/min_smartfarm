#!/bin/bash
apt-get update -q
apt-get install -y python3-pip
pip3 install pyserial mysql-connector-python --break-system-packages --target /usr/lib/python3/dist-packages
pip3 install opencv-python-headless --break-system-packages --target /usr/lib/python3/dist-packages
pip3 install torch torchvision --break-system-packages --target /smartfarm/torch_libs
source /opt/ros/jazzy/setup.bash
source /smartfarm/ros2_ws/install/setup.bash
echo "=== 설정 완료 ==="
