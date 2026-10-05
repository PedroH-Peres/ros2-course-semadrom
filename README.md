# Minicurso de ROS 2: futebol de robôs 2D

Minicurso de 1h45 (teoria + prática ao vivo) que ensina os conceitos básicos de ROS 2 usando um futebol de robôs simulado. Tudo roda no seu computador, sem hardware.

O cenário é um campo de 9x6 m, como o da RoboCup Humanoid KidSize. Um robô procura a bola, contorna, alinha com o gol e chuta. A simulação é feita em Python com Tkinter, sem nenhuma dependência além do ROS 2 (`rclpy` e mensagens padrão).

O campo tem a origem no centro, com x de -4,5 a +4,5 m e y de -3 a +3 m. O gol azul fica em x = +4,5 e o amarelo em x = -4,5. Por padrão o robô ataca o gol amarelo.

## Duas versões do mesmo projeto

- **`sem_ros/`**: Python puro, um único processo. O `mundo.py` guarda a física e o desenho, o `cerebro.py` guarda a decisão e o `main.py` liga os dois por chamadas de função.
- **`com_ros/`**: o mesmo projeto dividido em dois nós ROS 2, `simulador` e `cerebro`, que conversam por tópicos e serviços. O `mundo.py` é idêntico ao da versão sem ROS (o pacote fica em `com_ros/src/futebol_robo/`).

A ideia do curso é mostrar o que muda quando as chamadas de função viram mensagens.

## Requisitos

- Ubuntu com ROS 2 Humble ou Jazzy (testado no Humble)
- `python3-tk`
- `ros-$ROS_DISTRO-teleop-twist-keyboard`
- `rqt_graph` (pacote `ros-$ROS_DISTRO-rqt-graph`)

```bash
sudo apt install python3-tk ros-$ROS_DISTRO-teleop-twist-keyboard ros-$ROS_DISTRO-rqt-graph
```

## Como rodar

Versão sem ROS:

```bash
cd sem_ros
python3 main.py
```

Clique no campo para mover a bola.

Versão com ROS:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd com_ros
colcon build --symlink-install
source install/setup.bash
ros2 launch futebol_robo futebol.launch.py
```

O build mostra avisos de `setup.py` e `easy_install` obsoletos. Eles vêm do setuptools e podem ser ignorados.

Ctrl+C no terminal encerra os dois nós. Fechar a janela do simulador também encerra tudo.

## Interface ROS

| Nome | Tipo | Quem publica / oferece |
|------|------|------------------------|
| `/robo/pose` | `geometry_msgs/Pose` | simulador |
| `/bola/posicao` | `geometry_msgs/Point` | simulador |
| `/cmd_vel` | `geometry_msgs/Twist` | cérebro (ou teleop) |
| `/estado` | `std_msgs/String` | cérebro |
| `/chutar` | `std_srvs/Trigger` | simulador |
| `/resetar_bola` | `std_srvs/Trigger` | simulador |

Parâmetros do nó `cerebro`: `velocidade_maxima` (1,0 m/s), `ganho_angular` (2,0), `distancia_atras` (0,5 m) e `gol_alvo` (`amarelo` ou `azul`). Eles valem a qualquer momento: `ros2 param set /cerebro gol_alvo azul` muda o ataque na hora. Os valores iniciais ficam em `config/params.yaml`.

O simulador tem um watchdog: se ficar 0,5 s sem receber `/cmd_vel`, o robô para. Por isso, se o cérebro cair, o robô não sai andando sozinho.

## Comandos úteis para testar

```bash
ros2 topic list
ros2 topic hz /robo/pose
ros2 service call /resetar_bola std_srvs/srv/Trigger
ros2 param set /cerebro gol_alvo azul
ros2 run teleop_twist_keyboard teleop_twist_keyboard
rqt_graph
```

## Etapas da rosificação ao vivo

A pasta `etapas/` guarda checkpoints para acompanhar a construção passo a passo. Cada etapa é um workspace completo, que compila e roda sozinho. Se algo der errado ao vivo, é só entrar na pasta da etapa e rodar `colcon build --symlink-install`. Cada uma tem um `ETAPA.md` com o que mudou e os comandos de teste.

1. `01_simulador_topicos`: só o simulador, com a assinatura de `/cmd_vel` e as publicações das posições.
2. `02_cerebro`: entra o nó cerebro, com constantes fixas e ainda sem chute.
3. `03_servicos`: entram os serviços `/chutar` e `/resetar_bola` e o cliente assíncrono.
4. `04_parametros`: as constantes viram parâmetros.
5. `05_launch`: launch file e `params.yaml`, igual ao `com_ros` final.

Para usar uma etapa:

```bash
cd etapas/03_servicos
colcon build --symlink-install
source install/setup.bash
ros2 run futebol_robo simulador   # e, em outro terminal, o cerebro
```

## Exercícios

1. **Goleiro.** Crie um nó que defende o gol azul. Ele assina `/bola/posicao` e publica em `/cmd_vel` para manter o robô perto do gol azul, na altura y da bola. Rode o simulador e o seu nó, sem o cérebro, e clique no campo para lançar a bola. Dica: o robô só anda para a frente e gira, então para se deslocar em y ele precisa virar para o lado, andar e voltar a olhar para o campo.
2. **Placar.** Faça o simulador publicar um tópico `/placar` com os gols de cada lado. O `mundo.py` já conta os gols em `gols_azul` e `gols_amarelo`; falta publicar. Escolha o tipo de mensagem (por exemplo `std_msgs/Int32MultiArray`) e confira com `ros2 topic echo /placar`. Não mude o `mundo.py`.
3. **Distância percorrida.** Crie um nó que assina `/robo/pose`, soma a distância entre posições consecutivas e escreve o total no log uma vez por segundo. Dica: use `math.hypot` e guarde a posição anterior.

## Estrutura do repositório

```
sem_ros/   versão em Python puro
com_ros/   versão com dois nós ROS 2
etapas/    checkpoints da rosificação (01 a 05)
```
