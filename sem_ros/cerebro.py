"""Cérebro do robô: decide para onde ir a cada instante.

É uma máquina de estados simples:

  PROCURAR   -> gira no lugar até enxergar a bola
  CONTORNAR  -> vai até um ponto atrás da bola (de costas para o nosso alvo)
  ALINHAR    -> gira até apontar para o gol
  CHUTAR     -> avança na bola e chuta

Aqui não existe ROS: o main.py chama decidir() direto, como uma função.
"""

import math

from mundo import normalizar_angulo

# --- Constantes do comportamento ---
VELOCIDADE_MAXIMA = 1.0     # m/s
GANHO_ANGULAR = 2.0         # quanto maior, mais rápido o robô gira
DISTANCIA_ATRAS = 0.5       # distância da bola até o ponto de onde vamos chutar
GOL_ALVO = "amarelo"        # "amarelo" (x = -4.5) ou "azul" (x = +4.5)

VELOCIDADE_ANGULAR_MAXIMA = 2.0
CAMPO_DE_VISAO = math.radians(70)   # o robô só enxerga a bola 70° para cada lado
DISTANCIA_DO_CHUTE = 0.38           # distância da bola para dar o chute


class Cerebro:
    def __init__(self):
        self.estado = "PROCURAR"

    def decidir(self, robo_x, robo_y, robo_yaw, bola_x, bola_y):
        """Devolve (velocidade_linear, velocidade_angular, chutar)."""
        gol_x = 4.5 if GOL_ALVO == "azul" else -4.5

        # Direção da bola até o gol (vetor de tamanho 1).
        dx, dy = gol_x - bola_x, 0.0 - bola_y
        tamanho = math.hypot(dx, dy)
        dir_x, dir_y = dx / tamanho, dy / tamanho
        angulo_do_gol = math.atan2(dir_y, dir_x)

        # Ponto atrás da bola, na linha que liga o gol à bola.
        atras_x = bola_x - dir_x * DISTANCIA_ATRAS
        atras_y = bola_y - dir_y * DISTANCIA_ATRAS
        atras_x = max(-4.25, min(4.25, atras_x))
        atras_y = max(-2.75, min(2.75, atras_y))

        distancia_bola = math.hypot(bola_x - robo_x, bola_y - robo_y)
        angulo_bola = normalizar_angulo(
            math.atan2(bola_y - robo_y, bola_x - robo_x) - robo_yaw)
        distancia_atras = math.hypot(atras_x - robo_x, atras_y - robo_y)
        erro_alinhamento = normalizar_angulo(angulo_do_gol - robo_yaw)

        velocidade, giro, chutar = 0.0, 0.0, False

        if self.estado == "PROCURAR":
            giro = VELOCIDADE_ANGULAR_MAXIMA
            if abs(angulo_bola) < CAMPO_DE_VISAO:
                self.estado = "CONTORNAR"

        elif self.estado == "CONTORNAR":
            # Se o robô está do lado do gol, ele passa pela lateral da bola
            # em vez de atravessar a bola.
            rel_x, rel_y = robo_x - bola_x, robo_y - bola_y
            na_frente = rel_x * dir_x + rel_y * dir_y
            alvo_x, alvo_y = atras_x, atras_y
            if na_frente > 0:
                lado = 1.0 if (-rel_x * dir_y + rel_y * dir_x) >= 0 else -1.0
                alvo_x = bola_x - lado * dir_y * 0.8 - dir_x * 0.2
                alvo_y = bola_y + lado * dir_x * 0.8 - dir_y * 0.2
            velocidade, giro = self.ir_para(robo_x, robo_y, robo_yaw,
                                            alvo_x, alvo_y)
            if distancia_atras < 0.15:
                self.estado = "ALINHAR"

        elif self.estado == "ALINHAR":
            giro = self.limitar_giro(GANHO_ANGULAR * erro_alinhamento)
            if distancia_atras > 0.4:
                self.estado = "CONTORNAR"
            elif abs(erro_alinhamento) < 0.08:
                self.estado = "CHUTAR"

        elif self.estado == "CHUTAR":
            velocidade = 0.5 * VELOCIDADE_MAXIMA
            giro = self.limitar_giro(GANHO_ANGULAR * angulo_bola)
            if distancia_bola > 1.0 or abs(erro_alinhamento) > 0.35:
                self.estado = "CONTORNAR"
            elif distancia_bola < DISTANCIA_DO_CHUTE and abs(angulo_bola) < 0.3:
                chutar = True
                velocidade, giro = 0.0, 0.0
                self.estado = "PROCURAR"

        return velocidade, giro, chutar

    def ir_para(self, robo_x, robo_y, robo_yaw, alvo_x, alvo_y):
        """Controle simples para ir até um ponto: gira para o ponto e avança."""
        distancia = math.hypot(alvo_x - robo_x, alvo_y - robo_y)
        erro = normalizar_angulo(
            math.atan2(alvo_y - robo_y, alvo_x - robo_x) - robo_yaw)
        giro = self.limitar_giro(GANHO_ANGULAR * erro)
        # Só anda para a frente se estiver mais ou menos apontado para o alvo.
        velocidade = min(VELOCIDADE_MAXIMA, 1.5 * distancia) * max(0.0, math.cos(erro))
        return velocidade, giro

    def limitar_giro(self, giro):
        return max(-VELOCIDADE_ANGULAR_MAXIMA,
                   min(VELOCIDADE_ANGULAR_MAXIMA, giro))
