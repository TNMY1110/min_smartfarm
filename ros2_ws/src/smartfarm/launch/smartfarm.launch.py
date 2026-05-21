from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='smartfarm',
            executable='sensor_node',
            name='sensor_node',
            output='screen'
        ),
        Node(
            package='smartfarm',
            executable='vision_node',
            name='vision_node',
            output='screen'
        ),
        Node(
            package='smartfarm',
            executable='ai_node',
            name='ai_node',
            output='screen'
        ),
        Node(
            package='smartfarm',
            executable='alert_node',
            name='alert_node',
            output='screen'
        ),
        Node(
            package='smartfarm',
            executable='scheduler_node',
            name='scheduler_node',
            output='screen'
        ),
    ])