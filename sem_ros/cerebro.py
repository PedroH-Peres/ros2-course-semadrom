"""O cérebro do robô: olha onde estão o robô e a bola e decide o que fazer.

Ele funciona como uma máquina de estados, sempre em um destes estados:
PROCURAR, CONTORNAR, ALINHAR e CHUTAR (depois do chute, volta para PROCURAR).

Aqui não tem ROS: o main.py chama o decidir() como uma função normal.
"""

import math

from mundo import normalizar_angulo

# Valores que a gente pode mexer para mudar o jeito do robô jogar
VELOCIDADE_MAXIMA = 1.0     # m/s
GANHO_ANGULAR = 2.0         # quanto maior, mais rápido ele gira para corrigir a direção
DISTANCIA_ATRAS = 0.5       # o robô se posiciona a essa distância atrás da bola
GOL_ALVO = "amarelo"        # "amarelo" (x = -4.5) ou "azul" (x = +4.5)

VELOCIDADE_ANGULAR_MAXIMA = 2.0
CAMPO_DE_VISAO = math.radians(70)   # ele só enxerga a bola até 70° para cada lado
DISTANCIA_DO_CHUTE = 0.38           # chuta quando chegar nessa distância da bola


class Cerebro:
    def __init__(self):
        self.estado = "PROCURAR"

    def decidir(self, robo_x, robo_y, robo_yaw, bola_x, bola_y):
        """Recebe as posições e responde com (velocidade, giro, chutar)."""
        gol_x = 4.5 if GOL_ALVO == "azul" else -4.5

        # direção da bola até o gol (um vetor de tamanho 1)
        dx = gol_x - bola_x
        dy = 0.0 - bola_y
        tamanho = math.hypot(dx, dy)
        dir_x = dx / tamanho
        dir_y = dy / tamanho
        angulo_do_gol = math.atan2(dir_y, dir_x)

        # o ponto "atrás da bola": de lá o chute sai na direção do gol
        atras_x = bola_x - dir_x * DISTANCIA_ATRAS
        atras_y = bola_y - dir_y * DISTANCIA_ATRAS
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

        if self.estado == "PROCURAR":
            # gira parado até ver a bola
            giro = VELOCIDADE_ANGULAR_MAXIMA
            if abs(angulo_bola) < CAMPO_DE_VISAO:
                self.estado = "CONTORNAR"

        elif self.estado == "CONTORNAR":
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
            velocidade, giro = self.ir_para(robo_x, robo_y, robo_yaw,
                                            alvo_x, alvo_y)
            if distancia_ponto < 0.15:
                self.estado = "ALINHAR"

        elif self.estado == "ALINHAR":
            # gira no lugar até apontar para o gol
            giro = self.limitar_giro(GANHO_ANGULAR * erro_alinhamento)
            if distancia_ponto > 0.4:
                self.estado = "CONTORNAR"      # se afastou do ponto, volta a contornar
            elif abs(erro_alinhamento) < 0.08:
                self.estado = "CHUTAR"

        elif self.estado == "CHUTAR":
            # anda devagar até a bola, sempre olhando para ela
            velocidade = 0.5 * VELOCIDADE_MAXIMA
            giro = self.limitar_giro(GANHO_ANGULAR * angulo_bola)
            if distancia_bola > 1.0 or abs(erro_alinhamento) > 0.35:
                self.estado = "CONTORNAR"      # a bola fugiu, começa de novo
            elif distancia_bola < DISTANCIA_DO_CHUTE and abs(angulo_bola) < 0.3:
                chutar = True
                velocidade = 0.0
                giro = 0.0
                self.estado = "PROCURAR"

        return velocidade, giro, chutar

    def ir_para(self, robo_x, robo_y, robo_yaw, alvo_x, alvo_y):
        """Gira para o alvo e anda até ele. Retorna (velocidade, giro)."""
        distancia = math.hypot(alvo_x - robo_x, alvo_y - robo_y)
        erro = normalizar_angulo(
            math.atan2(alvo_y - robo_y, alvo_x - robo_x) - robo_yaw)
        giro = self.limitar_giro(GANHO_ANGULAR * erro)
        # quanto mais virado para o lado, mais devagar ele anda (de costas, não anda)
        velocidade = min(VELOCIDADE_MAXIMA, 1.5 * distancia) * max(0.0, math.cos(erro))
        return velocidade, giro

    def limitar_giro(self, giro):
        return max(-VELOCIDADE_ANGULAR_MAXIMA,
                   min(VELOCIDADE_ANGULAR_MAXIMA, giro))
