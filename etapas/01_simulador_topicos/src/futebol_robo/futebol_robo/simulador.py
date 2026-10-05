"""Nó simulador: dono do mundo (física e desenho).

Publica:
  /robo/pose      (geometry_msgs/Pose)   posição do robô; yaw em quaternion
  /bola/posicao   (geometry_msgs/Point)  posição da bola
Assina:
  /cmd_vel        (geometry_msgs/Twist)  velocidade que o robô deve seguir
"""

import math
import signal
import time
import tkinter as tk

import rclpy
from geometry_msgs.msg import Point, Pose, Twist
from rclpy.node import Node

from futebol_robo.mundo import Mundo

PERIODO_MS = 20
# Se ninguém mandar /cmd_vel por este tempo, o robô para (segurança).
TEMPO_WATCHDOG = 0.5


class Simulador(Node):
    def __init__(self, mundo):
        super().__init__('simulador')
        self.mundo = mundo
        self.ultimo_cmd_vel = time.monotonic()

        # Publicadores
        self.pub_pose = self.create_publisher(Pose, '/robo/pose', 10)
        self.pub_bola = self.create_publisher(Point, '/bola/posicao', 10)

        # Assinaturas
        self.create_subscription(Twist, '/cmd_vel', self.ao_receber_cmd_vel, 10)

        self.get_logger().info('Simulador pronto.')

    # --- Callbacks ---
    def ao_receber_cmd_vel(self, msg):
        self.ultimo_cmd_vel = time.monotonic()
        self.mundo.aplicar_velocidade(msg.linear.x, msg.angular.z)

    # --- Chamado a cada ciclo do loop do Tkinter ---
    def atualizar(self, dt):
        # Watchdog: sem comandos recentes, para o robô.
        if time.monotonic() - self.ultimo_cmd_vel > TEMPO_WATCHDOG:
            self.mundo.aplicar_velocidade(0.0, 0.0)

        self.mundo.passo(dt)
        self.publicar()
        self.mundo.desenhar()

    def publicar(self):
        pose = Pose()
        pose.position.x = self.mundo.robo_x
        pose.position.y = self.mundo.robo_y
        # Rotação só em torno de z: quaternion = (0, 0, sen(yaw/2), cos(yaw/2))
        pose.orientation.z = math.sin(self.mundo.robo_theta / 2)
        pose.orientation.w = math.cos(self.mundo.robo_theta / 2)
        self.pub_pose.publish(pose)

        bola = Point()
        bola.x = self.mundo.bola_x
        bola.y = self.mundo.bola_y
        self.pub_bola.publish(bola)


def main(args=None):
    rclpy.init(args=args)
    raiz = tk.Tk()
    mundo = Mundo(raiz)
    no = Simulador(mundo)
    ultimo_tick = time.monotonic()

    def tick():
        nonlocal ultimo_tick
        # Ctrl+C (ou o launch encerrando) deixa o rclpy "não ok".
        if not rclpy.ok():
            raiz.quit()
            return
        agora = time.monotonic()
        dt = min(agora - ultimo_tick, 0.1)
        ultimo_tick = agora
        # Processa mensagens e serviços que chegaram, sem esperar.
        rclpy.spin_once(no, timeout_sec=0)
        no.atualizar(dt)
        raiz.after(PERIODO_MS, tick)

    # Ctrl+C fecha a janela (sem isso o Tkinter engole o sinal).
    signal.signal(signal.SIGINT, lambda *args: raiz.quit())
    # Fechar a janela também encerra o nó.
    raiz.protocol('WM_DELETE_WINDOW', raiz.quit)
    raiz.after(PERIODO_MS, tick)
    try:
        raiz.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        no.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        try:
            raiz.destroy()
        except tk.TclError:
            pass


if __name__ == '__main__':
    main()
