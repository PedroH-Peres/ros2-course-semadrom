"""Nó cérebro: decide a velocidade do robô.

Assina:
  /robo/pose      (geometry_msgs/Pose)
  /bola/posicao   (geometry_msgs/Point)
Publica:
  /cmd_vel        (geometry_msgs/Twist)
  /estado         (std_msgs/String)
Chama o serviço:
  /chutar         (std_srvs/Trigger)

Máquina de estados: PROCURAR -> CONTORNAR -> ALINHAR -> CHUTAR.
"""

import math
import signal

import rclpy
from geometry_msgs.msg import Point, Pose, Twist
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from futebol_robo.mundo import normalizar_angulo

VELOCIDADE_ANGULAR_MAXIMA = 2.0
CAMPO_DE_VISAO = math.radians(70)   # o robô só enxerga a bola 70° para cada lado
DISTANCIA_DO_CHUTE = 0.38           # distância da bola para dar o chute
PERIODO = 0.05                      # o cérebro decide 20 vezes por segundo

# Constantes do comportamento (na etapa 04 viram parâmetros)
VELOCIDADE_MAXIMA = 1.0     # m/s
GANHO_ANGULAR = 2.0         # quanto maior, mais rápido o robô gira
DISTANCIA_ATRAS = 0.5       # distância da bola de onde o robô chuta
GOL_ALVO = 'amarelo'        # 'amarelo' (x = -4.5) ou 'azul' (x = +4.5)


class Cerebro(Node):
    def __init__(self):
        super().__init__('cerebro')

        self.estado = 'PROCURAR'
        self.pose = None
        self.bola = None
        self.chute_pendente = False

        # Assinaturas
        self.create_subscription(Pose, '/robo/pose', self.ao_receber_pose, 10)
        self.create_subscription(
            Point, '/bola/posicao', self.ao_receber_bola, 10)

        # Publicadores
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)
        self.pub_estado = self.create_publisher(String, '/estado', 10)

        # Cliente do serviço de chute
        self.cli_chutar = self.create_client(Trigger, '/chutar')

        self.create_timer(PERIODO, self.ciclo)
        self.get_logger().info('Cérebro pronto.')

    # --- Entradas ---
    def ao_receber_pose(self, msg):
        self.pose = msg

    def ao_receber_bola(self, msg):
        self.bola = msg

    # --- Ciclo principal ---
    def ciclo(self):
        if self.pose is None or self.bola is None:
            return  # ainda não recebemos nada do simulador

        robo_x = self.pose.position.x
        robo_y = self.pose.position.y
        # Quaternion só com rotação em z: yaw = 2 * atan2(z, w)
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
        """Devolve (velocidade_linear, velocidade_angular, chutar)."""
        velocidade_maxima = VELOCIDADE_MAXIMA
        ganho_angular = GANHO_ANGULAR
        distancia_atras_da_bola = DISTANCIA_ATRAS
        gol_alvo = GOL_ALVO

        gol_x = 4.5 if gol_alvo == 'azul' else -4.5

        # Direção da bola até o gol (vetor de tamanho 1).
        dx, dy = gol_x - bola_x, 0.0 - bola_y
        tamanho = math.hypot(dx, dy)
        dir_x, dir_y = dx / tamanho, dy / tamanho
        angulo_do_gol = math.atan2(dir_y, dir_x)

        # Ponto atrás da bola, na linha que liga o gol à bola.
        atras_x = bola_x - dir_x * distancia_atras_da_bola
        atras_y = bola_y - dir_y * distancia_atras_da_bola
        atras_x = max(-4.25, min(4.25, atras_x))
        atras_y = max(-2.75, min(2.75, atras_y))

        distancia_bola = math.hypot(bola_x - robo_x, bola_y - robo_y)
        angulo_bola = normalizar_angulo(
            math.atan2(bola_y - robo_y, bola_x - robo_x) - robo_yaw)
        distancia_atras = math.hypot(atras_x - robo_x, atras_y - robo_y)
        erro_alinhamento = normalizar_angulo(angulo_do_gol - robo_yaw)

        velocidade, giro, chutar = 0.0, 0.0, False

        if self.estado == 'PROCURAR':
            giro = VELOCIDADE_ANGULAR_MAXIMA
            if abs(angulo_bola) < CAMPO_DE_VISAO:
                self.estado = 'CONTORNAR'

        elif self.estado == 'CONTORNAR':
            # Se o robô está do lado do gol, ele passa pela lateral da bola
            # em vez de atravessar a bola.
            rel_x, rel_y = robo_x - bola_x, robo_y - bola_y
            na_frente = rel_x * dir_x + rel_y * dir_y
            alvo_x, alvo_y = atras_x, atras_y
            if na_frente > 0:
                lado = 1.0 if (-rel_x * dir_y + rel_y * dir_x) >= 0 else -1.0
                alvo_x = bola_x - lado * dir_y * 0.8 - dir_x * 0.2
                alvo_y = bola_y + lado * dir_x * 0.8 - dir_y * 0.2
            velocidade, giro = self.ir_para(
                robo_x, robo_y, robo_yaw, alvo_x, alvo_y,
                velocidade_maxima, ganho_angular)
            if distancia_atras < 0.15:
                self.estado = 'ALINHAR'

        elif self.estado == 'ALINHAR':
            giro = self.limitar_giro(ganho_angular * erro_alinhamento)
            if distancia_atras > 0.4:
                self.estado = 'CONTORNAR'
            elif abs(erro_alinhamento) < 0.08:
                self.estado = 'CHUTAR'

        elif self.estado == 'CHUTAR':
            velocidade = 0.5 * velocidade_maxima
            giro = self.limitar_giro(ganho_angular * angulo_bola)
            if distancia_bola > 1.0 or abs(erro_alinhamento) > 0.35:
                self.estado = 'CONTORNAR'
            elif distancia_bola < DISTANCIA_DO_CHUTE and abs(angulo_bola) < 0.3:
                chutar = True
                velocidade, giro = 0.0, 0.0
                self.estado = 'PROCURAR'

        return velocidade, giro, chutar

    def ir_para(self, robo_x, robo_y, robo_yaw, alvo_x, alvo_y,
                velocidade_maxima, ganho_angular):
        """Controle simples para ir até um ponto: gira para ele e avança."""
        distancia = math.hypot(alvo_x - robo_x, alvo_y - robo_y)
        erro = normalizar_angulo(
            math.atan2(alvo_y - robo_y, alvo_x - robo_x) - robo_yaw)
        giro = self.limitar_giro(ganho_angular * erro)
        # Só anda para a frente se estiver mais ou menos apontado para o alvo.
        velocidade = (min(velocidade_maxima, 1.5 * distancia)
                      * max(0.0, math.cos(erro)))
        return velocidade, giro

    def limitar_giro(self, giro):
        return max(-VELOCIDADE_ANGULAR_MAXIMA,
                   min(VELOCIDADE_ANGULAR_MAXIMA, giro))

    # --- Chute pelo serviço ---
    def pedir_chute(self):
        if self.chute_pendente or not self.cli_chutar.service_is_ready():
            return
        self.chute_pendente = True
        # call_async não trava: a resposta chega depois, no callback.
        futuro = self.cli_chutar.call_async(Trigger.Request())
        futuro.add_done_callback(self.ao_responder_chute)

    def ao_responder_chute(self, futuro):
        self.chute_pendente = False
        resposta = futuro.result()
        self.get_logger().info(f'Chute: {resposta.message}')


def main(args=None):
    rclpy.init(args=args)
    no = Cerebro()
    try:
        rclpy.spin(no)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # O Ctrl+C no terminal chega duas vezes (do terminal e do launch);
        # ignora a segunda para não interromper a limpeza.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        no.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
