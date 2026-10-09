"""Sobe o simulador e o cérebro juntos, com um comando só."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node


def generate_launch_description():
    # procura o params.yaml dentro do pacote instalado
    params = os.path.join(
        get_package_share_directory('futebol_robo'), 'config', 'params.yaml')

    simulador = Node(
        package='futebol_robo',
        executable='simulador',
        name='simulador',
        output='screen',
    )
    cerebro = Node(
        package='futebol_robo',
        executable='cerebro',
        name='cerebro',
        output='screen',
        parameters=[params],
    )

    # se fecharem a janela do simulador, derruba o cérebro também
    fechar_tudo = RegisterEventHandler(
        OnProcessExit(
            target_action=simulador,
            on_exit=[EmitEvent(event=Shutdown())],
        )
    )

    return LaunchDescription([simulador, cerebro, fechar_tudo])
