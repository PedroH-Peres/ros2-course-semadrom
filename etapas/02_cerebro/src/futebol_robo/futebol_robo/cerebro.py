"""Nó cérebro: decide a velocidade do robô.

O que ele escuta:
  /robo/pose      onde o robô está (Pose)
  /bola/posicao   onde a bola está (Point)
O que ele publica:
  /cmd_vel        a velocidade que o robô deve seguir (Twist)
  /estado         o estado atual, só para mostrar na tela (String)

A lógica é a mesma da versão sem ROS: PROCURAR, CONTORNAR, ALINHAR e CHUTAR.
"""

import math
import signal

import rclpy
from geometry_msgs.msg import Point, Pose, Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from futebol_robo.mundo import normalizar_angulo

VELOCIDADE_ANGULAR_MAXIMA = 2.0
CAMPO_DE_VISAO = math.radians(70)   # ele só enxerga a bola até 70° para cada lado
DISTANCIA_DO_CHUTE = 0.38           # chuta quando chegar nessa distância da bola
PERIODO = 0.05                      # decide 20 vezes por segundo

# valores fixos por enquanto (na etapa 04 viram parâmetros)
VELOCIDADE_MAXIMA = 1.0     # m/s
GANHO_ANGULAR = 2.0         # quanto maior, mais rápido ele gira para corrigir a direção
DISTANCIA_ATRAS = 0.5       # o robô se posiciona a essa distância atrás da bola
GOL_ALVO = 'amarelo'        # 'amarelo' (x = -4.5) ou 'azul' (x = +4.5)


class Cerebro(Node):
    def __init__(self):
        super().__init__('cerebro')

        self.estado = 'PROCURAR'
        self.pose = None
        self.bola = None

        # assinaturas
        self.create_subscription(Pose, '/robo/pose', self.ao_receber_pose, 10)
        self.create_subscription(
            Point, '/bola/posicao', self.ao_receber_bola, 10)

        # publicadores
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_estado = self.create_publisher(String, '/estado', 10)

        # a cada PERIODO segundos o ROS chama self.ciclo
        self.create_timer(PERIODO, self.ciclo)
        self.get_logger().info('Cérebro pronto.')

    # mensagens que chegam

    def ao_receber_pose(self, msg):
        self.pose = msg

    def ao_receber_bola(self, msg):
        self.bola = msg

    # o que acontece a cada ciclo

    def ciclo(self):
        if self.pose is None or self.bola is None:
            return  # o simulador ainda não mandou nada

        robo_x = self.pose.position.x
        robo_y = self.pose.position.y
        # desfaz o quaternion para voltar a ter um ângulo simples (yaw)
        robo_yaw = 2 * math.atan2(self.pose.orientation.z,
                                  self.pose.orientation.w)

        velocidade, giro, chutar = self.decidir(
            robo_x, robo_y, robo_yaw, self.bola.x, self.bola.y)

        cmd = Twist()
        cmd.linear.x = velocidade
        cmd.angular.z = giro
        self.pub_cmd_vel.publish(cmd)

        estado = String()
        estado.data = self.estado
        self.pub_estado.publish(estado)

        if chutar:
            self.pedir_chute()

    def decidir(self, robo_x, robo_y, robo_yaw, bola_x, bola_y):
        """Recebe as posições e responde com (velocidade, giro, chutar)."""
        velocidade_maxima = VELOCIDADE_MAXIMA
        ganho_angular = GANHO_ANGULAR
        distancia_atras_da_bola = DISTANCIA_ATRAS
        gol_alvo = GOL_ALVO

        gol_x = 4.5 if gol_alvo == 'azul' else -4.5

        # direção da bola até o gol (um vetor de tamanho 1)
        dx = gol_x - bola_x
        dy = 0.0 - bola_y
        tamanho = math.hypot(dx, dy)
        dir_x = dx / tamanho
        dir_y = dy / tamanho
        angulo_do_gol = math.atan2(dir_y, dir_x)

        # o ponto "atrás da bola": de lá o chute sai na direção do gol
        atras_x = bola_x - dir_x * distancia_atras_da_bola
        atras_y = bola_y - dir_y * distancia_atras_da_bola
        atras_x = max(-4.25, min(4.25, atras_x))   # não deixa sair do campo
        atras_y = max(-2.75, min(2.75, atras_y))

        distancia_bola = math.hypot(bola_x - robo_x, bola_y - robo_y)
        angulo_bola = normalizar_angulo(
            math.atan2(bola_y - robo_y, bola_x - robo_x) - robo_yaw)
        distancia_ponto = math.hypot(atras_x - robo_x, atras_y - robo_y)
        erro_alinhamento = normalizar_angulo(angulo_do_gol - robo_yaw)

        velocidade = 0.0
        giro = 0.0
        chutar = False

        if self.estado == 'PROCURAR':
            # gira parado até ver a bola
            giro = VELOCIDADE_ANGULAR_MAXIMA
            if abs(angulo_bola) < CAMPO_DE_VISAO:
                self.estado = 'CONTORNAR'

        elif self.estado == 'CONTORNAR':
            # por padrão vai direto para o ponto atrás da bola
            alvo_x = atras_x
            alvo_y = atras_y
            # mas se o robô está do lado do gol, ele dá a volta pela lateral
            # (senão ia passar por cima da bola e empurrar para o lado errado)
            rel_x = robo_x - bola_x
            rel_y = robo_y - bola_y
            na_frente = rel_x * dir_x + rel_y * dir_y
            if na_frente > 0:
                if -rel_x * dir_y + rel_y * dir_x >= 0:
                    lado = 1.0
                else:
                    lado = -1.0
                alvo_x = bola_x - lado * dir_y * 0.8 - dir_x * 0.2
                alvo_y = bola_y + lado * dir_x * 0.8 - dir_y * 0.2
            velocidade, giro = self.ir_para(
                robo_x, robo_y, robo_yaw, alvo_x, alvo_y,
                velocidade_maxima, ganho_angular)
            if distancia_ponto < 0.15:
                self.estado = 'ALINHAR'

        elif self.estado == 'ALINHAR':
            # gira no lugar até apontar para o gol
            giro = self.limitar_giro(ganho_angular * erro_alinhamento)
            if distancia_ponto > 0.4:
                self.estado = 'CONTORNAR'      # se afastou do ponto, volta a contornar
            elif abs(erro_alinhamento) < 0.08:
                self.estado = 'CHUTAR'

        elif self.estado == 'CHUTAR':
            # anda devagar até a bola, sempre olhando para ela
            velocidade = 0.5 * velocidade_maxima
            giro = self.limitar_giro(ganho_angular * angulo_bola)
            if distancia_bola > 1.0 or abs(erro_alinhamento) > 0.35:
                self.estado = 'CONTORNAR'      # a bola fugiu, começa de novo
            elif distancia_bola < DISTANCIA_DO_CHUTE and abs(angulo_bola) < 0.3:
                chutar = True
                velocidade = 0.0
                giro = 0.0
                self.estado = 'PROCURAR'

        return velocidade, giro, chutar

    def ir_para(self, robo_x, robo_y, robo_yaw, alvo_x, alvo_y,
                velocidade_maxima, ganho_angular):
        """Gira para o alvo e anda até ele. Retorna (velocidade, giro)."""
        distancia = math.hypot(alvo_x - robo_x, alvo_y - robo_y)
        erro = normalizar_angulo(
            math.atan2(alvo_y - robo_y, alvo_x - robo_x) - robo_yaw)
        giro = self.limitar_giro(ganho_angular * erro)
        # quanto mais virado para o lado, mais devagar ele anda (de costas, não anda)
        velocidade = (min(velocidade_maxima, 1.5 * distancia)
                      * max(0.0, math.cos(erro)))
        return velocidade, giro

    def limitar_giro(self, giro):
        return max(-VELOCIDADE_ANGULAR_MAXIMA,
                   min(VELOCIDADE_ANGULAR_MAXIMA, giro))

    # chute (ainda sem serviço)

    def pedir_chute(self):
        # na etapa 03 isto vira uma chamada ao serviço /chutar
        self.get_logger().info('Chutaria agora! (o serviço /chutar ainda não existe)')


def main(args=None):
    rclpy.init(args=args)
    no = Cerebro()
    try:
        rclpy.spin(no)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # O Ctrl+C no terminal chega duas vezes (uma do terminal e outra do
        # launch). Ignoramos a segunda para não atrapalhar o encerramento.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        no.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
