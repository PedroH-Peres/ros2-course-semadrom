"""Versão SEM ROS: tudo roda em um programa só.

A cada 20 ms acontece o seguinte:
  1. o cérebro olha o mundo e decide o que fazer (chamada de função)
  2. a decisão é passada para o mundo (outra chamada de função)
  3. o mundo faz a física andar um pouquinho e se redesenha
"""

import signal
import tkinter as tk

from cerebro import Cerebro
from mundo import Mundo

PERIODO_MS = 20


def main():
    raiz = tk.Tk()
    mundo = Mundo(raiz)
    cerebro = Cerebro()

    def tick():
        velocidade, giro, chutar = cerebro.decidir(
            mundo.robo_x, mundo.robo_y, mundo.robo_theta,
            mundo.bola_x, mundo.bola_y)
        mundo.aplicar_velocidade(velocidade, giro)
        if chutar:
            mundo.chutar()
        mundo.estado = cerebro.estado
        mundo.passo(PERIODO_MS / 1000)
        mundo.desenhar()
        raiz.after(PERIODO_MS, tick)   # agenda o próximo tick

    # Sem isso o Tkinter ignora o Ctrl+C e o terminal fica preso.
    signal.signal(signal.SIGINT, lambda *args: raiz.quit())

    raiz.after(PERIODO_MS, tick)
    raiz.mainloop()


if __name__ == "__main__":
    main()
