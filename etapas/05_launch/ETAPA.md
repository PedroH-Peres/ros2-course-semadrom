# Etapa 05: launch file e params.yaml

Esta etapa é igual ao `com_ros/` final.

## O que mudou em relação à etapa 04

- `launch/futebol.launch.py` sobe os dois nós com um comando só. Se a janela do simulador for fechada, o launch encerra o resto.
- `config/params.yaml` guarda os parâmetros do cérebro.
- `setup.py` instala as pastas `launch/` e `config/`.

## Como testar

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch futebol_robo futebol.launch.py
```

```bash
ros2 node list
ros2 param get /cerebro gol_alvo          # vem do params.yaml
ros2 param set /cerebro gol_alvo azul
rqt_graph
```

Edite o `config/params.yaml` e rode o launch de novo para ver o novo valor.
