# Etapa 03: serviços

## O que mudou em relação à etapa 02

- O simulador oferece dois serviços `std_srvs/Trigger`: `/chutar` e `/resetar_bola`.
- O cérebro ganha um cliente de `/chutar` e chama com `call_async`, para não travar o ciclo de decisão. A resposta chega num callback.
- Agora o robô chuta de verdade, e o log mostra `Chute: chutou`.

## Como testar

```bash
colcon build --symlink-install
source install/setup.bash
ros2 run futebol_robo simulador      # terminal 1
ros2 run futebol_robo cerebro        # terminal 2
```

```bash
ros2 service list -t
ros2 service call /resetar_bola std_srvs/srv/Trigger
ros2 service call /chutar std_srvs/srv/Trigger   # só chuta se a bola estiver perto
```
