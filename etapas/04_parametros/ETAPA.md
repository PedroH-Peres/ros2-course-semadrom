# Etapa 04: parâmetros

## O que mudou em relação à etapa 03

- As quatro constantes do cérebro viram parâmetros: `velocidade_maxima`, `ganho_angular`, `distancia_atras` e `gol_alvo`.
- Elas são lidas com `get_parameter` a cada ciclo, então mudam em tempo de execução.
- Um callback recusa valores inválidos de `gol_alvo`.

## Como testar

```bash
colcon build --symlink-install
source install/setup.bash
ros2 run futebol_robo simulador      # terminal 1
ros2 run futebol_robo cerebro        # terminal 2
```

```bash
ros2 param list /cerebro
ros2 param get /cerebro gol_alvo
ros2 param set /cerebro gol_alvo azul      # o robô passa a atacar o gol azul
ros2 param set /cerebro gol_alvo verde     # recusado
ros2 param set /cerebro velocidade_maxima 0.4
```

Também dá para passar o valor ao iniciar:

```bash
ros2 run futebol_robo cerebro --ros-args -p gol_alvo:=azul
```
