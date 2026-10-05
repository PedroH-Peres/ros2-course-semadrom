"""Versão SEM ROS: tudo em um processo só.

O loop abaixo faz, a cada 20 ms:
  1. o cérebro olha o mundo e decide a velocidade (chamada de função);
  2. a velocidade é entregue ao mundo (chamada de função);
  3. o mundo avança a física e se redesenha.
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
        raiz.after(PERIODO_MS, tick)

    # Ctrl+C no terminal fecha a janela (sem isso o Tkinter engole o sinal).
    signal.signal(signal.SIGINT, lambda *args: raiz.quit())

    raiz.after(PERIODO_MS, tick)
    raiz.mainloop()


if __name__ == "__main__":
    main()
