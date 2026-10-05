from glob import glob

from setuptools import setup

package_name = 'futebol_robo'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Pedro Peres',
    maintainer_email='pedrohperescode@gmail.com',
    description='Futebol de robôs 2D para o minicurso de ROS 2',
    license='MIT',
    entry_points={
        'console_scripts': [
            'simulador = futebol_robo.simulador:main',
            'cerebro = futebol_robo.cerebro:main',
        ],
    },
)
