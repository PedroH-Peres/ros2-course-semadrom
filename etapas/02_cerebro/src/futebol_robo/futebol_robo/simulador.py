"""Nó simulador: é o dono do mundo (física e desenho).

O que ele publica:
  /robo/pose      posição e direção do robô (Pose)
  /bola/posicao   posição da bola (Point)
O que ele escuta:
  /cmd_vel        a velocidade que o robô deve seguir (Twist)
  /estado         um texto para mostrar na tela (String)
"""

import math
import signal
import time
import tkinter as tk

import rclpy
from geometry_msgs.msg import Point, Pose, Twist
from rclpy.node import Node
from std_msgs.msg import String

from futebol_robo.mundo import Mundo

PERIODO_MS = 20

# Se ficar esse tempo sem receber /cmd_vel, o robô para.
# Assim, se o cérebro travar ou for fechado, o robô não sai andando sozinho.
TEMPO_WATCHDOG = 0.5


class Simulador(Node):
    def __init__(self, mundo):
        super().__init__('simulador')
        self.mundo = mundo
        self.ultimo_cmd_vel = time.monotonic()

        # publicadores
        self.pub_pose = self.create_publisher(Pose, '/robo/pose', 10)
        self.pub_bola = self.create_publisher(Point, '/bola/posicao', 10)

        # assinaturas
        self.create_subscription(Twist, '/cmd_vel', self.ao_receber_cmd_vel, 10)
        self.create_subscription(String, '/estado', self.ao_receber_estado, 10)

        self.get_logger().info('Simulador pronto.')

    # funções chamadas quando chega uma mensagem

    def ao_receber_cmd_vel(self, msg):
        self.ultimo_cmd_vel = time.monotonic()
        self.mundo.aplicar_velocidade(msg.linear.x, msg.angular.z)

    def ao_receber_estado(self, msg):
        self.mundo.estado = msg.data

    # chamada a cada ciclo do loop do Tkinter

    def atualizar(self, dt):
        # watchdog: faz tempo que ninguém manda velocidade, então para
        if time.monotonic() - self.ultimo_cmd_vel > TEMPO_WATCHDOG:
            self.mundo.aplicar_velocidade(0.0, 0.0)

        self.mundo.passo(dt)
        self.publicar()
        self.mundo.desenhar()

    def publicar(self):
        pose = Pose()
        pose.position.x = self.mundo.robo_x
        pose.position.y = self.mundo.robo_y
        # O ROS guarda a direção como quaternion. Como o robô só gira em torno
        # do eixo z, só z e w são diferentes de zero.
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
        # o rclpy deixa de estar "ok" quando o programa é encerrado
        if not rclpy.ok():
            raiz.quit()
            return
        agora = time.monotonic()
        dt = min(agora - ultimo_tick, 0.1)
        ultimo_tick = agora
        # atende as mensagens e os serviços que chegaram, sem ficar esperando
        rclpy.spin_once(no, timeout_sec=0)
        no.atualizar(dt)
        raiz.after(PERIODO_MS, tick)

    # Sem isso o Tkinter ignora o Ctrl+C e o terminal fica preso.
    signal.signal(signal.SIGINT, lambda *args: raiz.quit())
    # fechar a janela também encerra o programa
    raiz.protocol('WM_DELETE_WINDOW', raiz.quit)
    raiz.after(PERIODO_MS, tick)
    try:
        raiz.mainloop()
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
