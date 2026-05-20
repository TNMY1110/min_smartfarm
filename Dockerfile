FROM arm64v8/ros:jazzy-ros-base

RUN apt-get update && apt-get install -y python3-pip && apt-get clean

RUN pip3 install pyserial mysql-connector-python opencv-python-headless --break-system-packages --ignore-installed numpy --no-cache-dir

SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc

CMD ["/bin/bash"]