"""O mundo do jogo: guarda onde estão o robô e a bola, faz a física e desenha.

Este arquivo é igual na versão sem ROS e na com ROS. Ele não sabe o que é ROS.

Unidades: metros, segundos e radianos.
O centro do campo é o (0, 0). O gol azul fica em x = +4.5 e o amarelo em x = -4.5.
Quando theta = 0 o robô está olhando para o gol azul.
"""

import math
import tkinter as tk

# Tamanho do campo (o da RoboCup Humanoid KidSize)
COMPRIMENTO = 9.0
LARGURA = 6.0
LARGURA_GOL = 2.6

# Robô e bola
RAIO_ROBO = 0.20
RAIO_BOLA = 0.08
VEL_LINEAR_MAX = 1.5      # m/s
VEL_ANGULAR_MAX = 3.0     # rad/s

# Bola
ATRITO_BOLA = 0.6         # quanto ela perde de velocidade por segundo (m/s²)
VEL_CHUTE = 3.0           # m/s
ALCANCE_CHUTE = 0.45      # a bola tem que estar a no máximo essa distância
ANGULO_CHUTE = math.radians(35)  # e mais ou menos na frente do robô

# Desenho
ESCALA = 100              # pixels por metro
MARGEM = 50               # espaço em volta do campo, em pixels


def normalizar_angulo(a):
    """Deixa o ângulo entre -pi e pi (assim 350° vira -10°)."""
    return math.atan2(math.sin(a), math.cos(a))


class Mundo:
    def __init__(self, raiz):
        self.raiz = raiz
        raiz.title("Futebol de robôs 2D")

        largura_px = int(COMPRIMENTO * ESCALA + 2 * MARGEM)
        altura_px = int(LARGURA * ESCALA + 2 * MARGEM)
        self.canvas = tk.Canvas(raiz, width=largura_px, height=altura_px,
                                bg="#2e7d32", highlightthickness=0)
        self.canvas.pack()
        # clicou no campo: a bola vai pra lá
        self.canvas.bind("<Button-1>", self._ao_clicar)

        # robô
        self.robo_x = -2.0
        self.robo_y = 1.0
        self.robo_theta = 0.0
        self.vel_linear = 0.0
        self.vel_angular = 0.0

        # bola
        self.bola_x = 0.0
        self.bola_y = 0.0
        self.bola_vx = 0.0
        self.bola_vy = 0.0

        # placar: quantos gols foram marcados em cada gol
        self.gols_azul = 0
        self.gols_amarelo = 0

        # texto que aparece no canto da tela (quem controla o robô escreve aqui)
        self.estado = "-"

        self._desenhar_campo()
        self._criar_objetos()
        self.desenhar()

    # ----- comandos -----

    def aplicar_velocidade(self, linear, angular):
        """Diz ao robô quão rápido andar (m/s) e girar (rad/s)."""
        self.vel_linear = max(-VEL_LINEAR_MAX, min(VEL_LINEAR_MAX, linear))
        self.vel_angular = max(-VEL_ANGULAR_MAX, min(VEL_ANGULAR_MAX, angular))

    def chutar(self):
        """Chuta a bola se ela estiver perto e na frente. Retorna True se chutou."""
        dx = self.bola_x - self.robo_x
        dy = self.bola_y - self.robo_y
        distancia = math.hypot(dx, dy)
        angulo = normalizar_angulo(math.atan2(dy, dx) - self.robo_theta)
        if distancia > ALCANCE_CHUTE or abs(angulo) > ANGULO_CHUTE:
            return False
        self.bola_vx = VEL_CHUTE * math.cos(self.robo_theta)
        self.bola_vy = VEL_CHUTE * math.sin(self.robo_theta)
        return True

    def resetar_bola(self):
        """Põe a bola parada no meio do campo."""
        self.mover_bola(0.0, 0.0)

    def mover_bola(self, x, y):
        """Põe a bola parada em (x, y)."""
        self.bola_x = max(-COMPRIMENTO / 2, min(COMPRIMENTO / 2, x))
        self.bola_y = max(-LARGURA / 2, min(LARGURA / 2, y))
        self.bola_vx = 0.0
        self.bola_vy = 0.0

    # ----- física -----

    def passo(self, dt):
        """Faz o tempo andar dt segundos."""
        self._mover_robo(dt)
        self._mover_bola(dt)
        self._colisao_robo_bola()

    def _mover_robo(self, dt):
        self.robo_theta = normalizar_angulo(
            self.robo_theta + self.vel_angular * dt)
        self.robo_x += self.vel_linear * math.cos(self.robo_theta) * dt
        self.robo_y += self.vel_linear * math.sin(self.robo_theta) * dt
        # o robô não sai do campo
        limite_x = COMPRIMENTO / 2 - RAIO_ROBO
        limite_y = LARGURA / 2 - RAIO_ROBO
        self.robo_x = max(-limite_x, min(limite_x, self.robo_x))
        self.robo_y = max(-limite_y, min(limite_y, self.robo_y))

    def _mover_bola(self, dt):
        # atrito: a bola vai ficando mais lenta até parar
        velocidade = math.hypot(self.bola_vx, self.bola_vy)
        if velocidade > 0:
            nova = max(0.0, velocidade - ATRITO_BOLA * dt)
            fator = nova / velocidade
            self.bola_vx *= fator
            self.bola_vy *= fator

        self.bola_x += self.bola_vx * dt
        self.bola_y += self.bola_vy * dt

        meio_x = COMPRIMENTO / 2
        meio_y = LARGURA / 2

        # nas laterais a bola quica
        if abs(self.bola_y) > meio_y:
            self.bola_y = math.copysign(meio_y, self.bola_y)
            self.bola_vy = -self.bola_vy

        # na linha de fundo: se passou pelo gol é gol, senão quica
        if abs(self.bola_x) > meio_x:
            if abs(self.bola_y) < LARGURA_GOL / 2:
                if self.bola_x > 0:
                    self.gols_azul += 1
                else:
                    self.gols_amarelo += 1
                self.resetar_bola()
            else:
                self.bola_x = math.copysign(meio_x, self.bola_x)
                self.bola_vx = -self.bola_vx

    def _colisao_robo_bola(self):
        """Se o robô encosta na bola, ele empurra."""
        dx = self.bola_x - self.robo_x
        dy = self.bola_y - self.robo_y
        distancia = math.hypot(dx, dy)
        minimo = RAIO_ROBO + RAIO_BOLA
        if distancia >= minimo or distancia == 0:
            return
        # (nx, ny) aponta do robô para a bola
        nx, ny = dx / distancia, dy / distancia
        # tira a bola de dentro do robô
        self.bola_x = self.robo_x + nx * minimo
        self.bola_y = self.robo_y + ny * minimo
        # a bola ganha a velocidade do robô naquela direção
        vx = self.vel_linear * math.cos(self.robo_theta)
        vy = self.vel_linear * math.sin(self.robo_theta)
        empurrao = vx * nx + vy * ny
        if empurrao > 0:
            self.bola_vx = nx * empurrao * 1.3
            self.bola_vy = ny * empurrao * 1.3

    # ----- desenho -----

    def _px(self, x, y):
        """Converte metros em pixels (no Tkinter o y cresce para baixo)."""
        return (MARGEM + (x + COMPRIMENTO / 2) * ESCALA,
                MARGEM + (LARGURA / 2 - y) * ESCALA)

    def _retangulo(self, x1, y1, x2, y2, **opcoes):
        a = self._px(x1, y1)
        b = self._px(x2, y2)
        return self.canvas.create_rectangle(*a, *b, **opcoes)

    def _desenhar_campo(self):
        meio_x = COMPRIMENTO / 2
        meio_y = LARGURA / 2
        branco = "white"
        self._retangulo(-meio_x, -meio_y, meio_x, meio_y,
                        outline=branco, width=3)
        # linha do meio e círculo central
        a = self._px(0, -meio_y)
        b = self._px(0, meio_y)
        self.canvas.create_line(*a, *b, fill=branco, width=3)
        c1 = self._px(-0.75, 0.75)
        c2 = self._px(0.75, -0.75)
        self.canvas.create_oval(*c1, *c2, outline=branco, width=3)
        # gols (ficam um pouco para fora do campo)
        meio_gol = LARGURA_GOL / 2
        profundidade = 0.4
        self._retangulo(-meio_x - profundidade, -meio_gol, -meio_x, meio_gol,
                        outline="#fdd835", width=4)
        self._retangulo(meio_x, -meio_gol, meio_x + profundidade, meio_gol,
                        outline="#1e88e5", width=4)

    def _criar_objetos(self):
        self.id_robo = self.canvas.create_oval(0, 0, 0, 0, fill="#e53935",
                                               outline="white", width=2)
        self.id_direcao = self.canvas.create_line(0, 0, 0, 0, fill="white",
                                                  width=3)
        self.id_bola = self.canvas.create_oval(0, 0, 0, 0, fill="#ff9800",
                                               outline="black")
        self.id_placar = self.canvas.create_text(
            MARGEM, 15, anchor="w", fill="white", font=("Arial", 14, "bold"))
        self.id_estado = self.canvas.create_text(
            MARGEM + COMPRIMENTO * ESCALA, 15, anchor="e", fill="white",
            font=("Arial", 14))
        self.canvas.create_text(
            MARGEM, MARGEM + LARGURA * ESCALA + 22, anchor="w", fill="white",
            text="Clique no campo para mover a bola")

    def _circulo(self, id_, x, y, raio):
        cx, cy = self._px(x, y)
        r = raio * ESCALA
        self.canvas.coords(id_, cx - r, cy - r, cx + r, cy + r)

    def desenhar(self):
        """Redesenha o robô, a bola, o placar e o estado."""
        self._circulo(self.id_robo, self.robo_x, self.robo_y, RAIO_ROBO)
        self._circulo(self.id_bola, self.bola_x, self.bola_y, RAIO_BOLA)
        # o risquinho branco mostra para onde o robô está olhando
        x0, y0 = self._px(self.robo_x, self.robo_y)
        x1, y1 = self._px(
            self.robo_x + 1.6 * RAIO_ROBO * math.cos(self.robo_theta),
            self.robo_y + 1.6 * RAIO_ROBO * math.sin(self.robo_theta))
        self.canvas.coords(self.id_direcao, x0, y0, x1, y1)
        self.canvas.itemconfigure(
            self.id_placar,
            text=f"Gols no amarelo: {self.gols_amarelo}   "
                 f"Gols no azul: {self.gols_azul}")
        self.canvas.itemconfigure(self.id_estado,
                                  text=f"Estado: {self.estado}")

    def _ao_clicar(self, evento):
        x = (evento.x - MARGEM) / ESCALA - COMPRIMENTO / 2
        y = LARGURA / 2 - (evento.y - MARGEM) / ESCALA
        self.mover_bola(x, y)
