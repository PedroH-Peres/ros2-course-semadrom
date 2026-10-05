# Etapa 01: simulador com tópicos

Primeira etapa: só existe o nó `simulador`. O `mundo.py` entra pronto, igual ao da versão sem ROS.

## O que tem de novo

- `simulador.py`: um nó que embute o Tkinter. A cada 20 ms ele roda `rclpy.spin_once`, avança a física e desenha.
- Assina `/cmd_vel` (`Twist`): usa `linear.x` e `angular.z`.
- Publica `/robo/pose` (`Pose`, com o yaw em quaternion) e `/bola/posicao` (`Point`).
- Watchdog: se passar 0,5 s sem `/cmd_vel`, o robô para.

## Como testar

```bash
colcon build --symlink-install
source install/setup.bash
ros2 run futebol_robo simulador
```

Em outros terminais (com `source install/setup.bash`):

```bash
ros2 topic list
ros2 topic hz /robo/pose
ros2 topic echo /bola/posicao
# anda para a frente e girando; solte o comando e o robô para sozinho
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.5}}"
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Clique no campo para mover a bola.
