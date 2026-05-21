from setuptools import find_packages, setup

package_name = 'smartfarm'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    ('share/' + package_name + '/launch', ['launch/smartfarm.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pi',
    maintainer_email='pi@todo.todo',
    description='Smart Farm ROS2 Package',
    license='MIT',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'sensor_node = smartfarm.sensor_node:main',
            'vision_node = smartfarm.vision_node:main',
            'ai_node = smartfarm.ai_node:main',
            'alert_node = smartfarm.alert_node:main',
            'scheduler_node = smartfarm.scheduler_node:main',
        ],
    },
)