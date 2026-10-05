# Etapa 02: nó cérebro

## O que mudou em relação à etapa 01

- Novo nó `cerebro` (`cerebro.py`) com a máquina de estados PROCURAR, CONTORNAR, ALINHAR e CHUTAR.
- Ele assina `/robo/pose` e `/bola/posicao`, e publica `/cmd_vel` e `/estado`.
- As constantes (velocidade máxima, ganho, distância atrás da bola, gol alvo) estão fixas no topo do arquivo.
- O chute ainda não existe: ao chegar na hora de chutar, o cérebro só escreve no log `Chutaria agora!`. O robô empurra a bola só por contato.
- O simulador passa a assinar `/estado` e mostra o estado na janela.
- `setup.py` ganha o executável `cerebro`.

## Como testar

```bash
colcon build --symlink-install
source install/setup.bash
ros2 run futebol_robo simulador      # terminal 1
ros2 run futebol_robo cerebro        # terminal 2
```

```bash
ros2 topic echo /estado
ros2 topic echo /cmd_vel
rqt_graph
```

Para ver o watchdog, feche o terminal do cérebro: o robô para.
