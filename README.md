# Minicurso de ROS 2: futebol de robôs 2D

> **Projeto em andamento.** O material ainda está sendo construído e pode ter falhas, erros de texto ou partes que não funcionam no seu computador. Se achar algo errado, qualquer correção é bem-vinda: abra uma issue ou mande um pull request.

Este projeto é o material de um minicurso de ROS 2 de 1h45. A gente começa com um jogo de futebol de robôs em Python puro e, ao vivo, transforma o jogo em um sistema ROS 2 com dois programas conversando entre si. Tudo roda no seu computador, sem robô de verdade e sem hardware.

Você não precisa saber ROS para começar. Se ainda não sabe o que ele é, leia o [EXPLICACAO.md](EXPLICACAO.md), que explica os conceitos usando este mesmo projeto.

## O que tem aqui

Um robô vermelho joga num campo de 9 x 6 metros (o tamanho do campo da RoboCup Humanoid KidSize). Ele procura a bola, dá a volta até ficar atrás dela, aponta para o gol e chuta. Você pode clicar no campo para mudar a bola de lugar e ver o robô se virando.

O projeto vem em duas versões do mesmo jogo:

- **`sem_ros/`**: Python puro, tudo num programa só. Serve para entender o jogo antes de ver o ROS.
- **`com_ros/`**: o mesmo jogo dividido em dois programas (nós ROS 2): o `simulador`, que cuida do campo, e o `cerebro`, que decide o que o robô faz. Eles trocam mensagens pelo ROS.

Além disso, a pasta **`etapas/`** guarda 5 passos intermediários para construir a versão com ROS aos poucos.

```
sem_ros/                       jogo em Python puro
  mundo.py                     campo, física e desenho
  cerebro.py                   decisão do robô
  main.py                      junta as duas partes e roda
com_ros/src/futebol_robo/      pacote ROS 2
  futebol_robo/mundo.py        o mesmo mundo.py de cima
  futebol_robo/simulador.py    nó do simulador
  futebol_robo/cerebro.py      nó do cérebro
  launch/futebol.launch.py     liga os dois nós de uma vez
  config/params.yaml           valores dos parâmetros do cérebro
etapas/                        5 checkpoints da versão com ROS
EXPLICACAO.md                  o que é ROS e como o código funciona
```

## Como o jogo funciona

O campo tem o centro em (0, 0). O eixo x vai de -4,5 a +4,5 metros e o y vai de -3 a +3. O gol azul fica do lado direito (x = +4,5) e o amarelo do lado esquerdo (x = -4,5). Por padrão o robô ataca o gol amarelo.

O cérebro do robô passa por quatro estados, sempre nesta ordem:

1. **PROCURAR**: gira parado até enxergar a bola.
2. **CONTORNAR**: anda até um ponto logo atrás da bola, na linha entre a bola e o gol. Se estiver do lado do gol, dá a volta por fora para não empurrar a bola para trás.
3. **ALINHAR**: gira no lugar até ficar apontado para o gol.
4. **CHUTAR**: anda até a bola e chuta. Depois volta para PROCURAR.

No fim você vê o placar subindo na tela.

### Como as duas versões se parecem

A lógica do jogo é a mesma. O que muda é como as partes conversam:

| Versão sem ROS | Versão com ROS |
|---|---|
| o cérebro lê as posições direto do mundo | o simulador publica `/robo/pose` e `/bola/posicao`, e o cérebro assina |
| o cérebro chama `mundo.aplicar_velocidade()` | o cérebro publica `/cmd_vel`, e o simulador assina |
| o cérebro chama `mundo.chutar()` | o cérebro chama o serviço `/chutar` |
| as constantes ficam no código | viram parâmetros do nó |

### As mensagens na versão com ROS

| Nome | Tipo | Quem manda |
|------|------|------------|
| `/robo/pose` | `geometry_msgs/Pose` | simulador |
| `/bola/posicao` | `geometry_msgs/Point` | simulador |
| `/cmd_vel` | `geometry_msgs/Twist` | cérebro (ou o teleop, se você quiser dirigir) |
| `/estado` | `std_msgs/String` | cérebro (é só o texto que aparece na tela) |
| `/chutar` | `std_srvs/Trigger` | serviço do simulador |
| `/resetar_bola` | `std_srvs/Trigger` | serviço do simulador |

O cérebro tem quatro parâmetros: `velocidade_maxima` (1,0 m/s), `ganho_angular` (2,0), `distancia_atras` (0,5 m) e `gol_alvo` (`amarelo` ou `azul`).

O simulador também tem um watchdog: se ele ficar meio segundo sem receber `/cmd_vel`, o robô para. Assim, se o cérebro for fechado, o robô não sai andando sozinho.

## Requisitos

- **Sistema:** Ubuntu 22.04 com ROS 2 Humble, ou Ubuntu 24.04 com ROS 2 Jazzy. O projeto foi testado no Humble. No Jazzy ele deve funcionar, mas não foi testado.
- **Uma tela:** os dois programas abrem uma janela, então não funciona por SSH sem interface gráfica.

O que precisa estar instalado depende da versão que você quer rodar:

| Para rodar | Precisa de |
|---|---|
| só `sem_ros/` | `python3` e `python3-tk` (não precisa de ROS) |
| `com_ros/` e `etapas/` | ROS 2 (de preferência `ros-$ROS_DISTRO-desktop`), `python3-tk`, `colcon`, `teleop_twist_keyboard` e `rqt_graph` |

### Instalando o ROS 2

Siga o guia oficial para a sua versão do Ubuntu:

- Humble (Ubuntu 22.04): <https://docs.ros.org/en/humble/Installation.html>
- Jazzy (Ubuntu 24.04): <https://docs.ros.org/en/jazzy/Installation.html>

Instale a variante `desktop`, que já traz o `rqt_graph`, o `rclpy` e o sistema de launch.

### Instalando o resto

Com o ROS instalado e carregado (`source /opt/ros/$ROS_DISTRO/setup.bash`), rode:

```bash
sudo apt update
sudo apt install python3-tk python3-colcon-common-extensions \
    ros-$ROS_DISTRO-teleop-twist-keyboard ros-$ROS_DISTRO-rqt-graph
```

`$ROS_DISTRO` é uma variável que o próprio `source` do ROS cria (vale `humble` ou `jazzy`). Para conferir se deu certo:

```bash
echo $ROS_DISTRO                       # humble ou jazzy
python3 -c "import tkinter"            # não pode dar erro
ros2 pkg list | grep teleop_twist      # deve aparecer teleop_twist_keyboard
colcon --help | head -1                # deve mostrar a ajuda do colcon
```

Não é preciso instalar nada com `pip`: o projeto usa só o Python do sistema, o Tkinter e o ROS.

## Baixando o projeto

Com git:

```bash
git clone https://github.com/SEU-USUARIO/ros2-course-semadrom.git
cd ros2-course-semadrom
```

Troque `SEU-USUARIO` pelo usuário do GitHub onde o repositório está publicado. Sem git, use o botão **Code > Download ZIP** na página do repositório e descompacte.

## Rodando a versão sem ROS

```bash
cd sem_ros
python3 main.py
```

Uma janela com o campo abre e o robô começa a jogar. Clique em qualquer ponto do campo para colocar a bola lá. Para sair, feche a janela ou aperte `Ctrl+C` no terminal.

## Rodando a versão com ROS

Em cada terminal novo, você precisa carregar o ROS (o `source`). Sem isso, o comando `ros2` nem existe.

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
cd com_ros
colcon build --symlink-install
source install/setup.bash
ros2 launch futebol_robo futebol.launch.py
```

O que cada comando faz:

- `source /opt/ros/$ROS_DISTRO/setup.bash` ensina o terminal a achar o ROS.
- `colcon build --symlink-install` compila o pacote. Com o `--symlink-install`, mexer nos arquivos `.py` já vale na próxima execução, sem compilar de novo. Vão aparecer três pastas novas: `build/`, `install/` e `log/` (o git ignora elas).
- `source install/setup.bash` ensina o terminal a achar o pacote `futebol_robo`.
- `ros2 launch ...` abre o simulador e o cérebro juntos.

O build mostra avisos sobre `setup.py` e `easy_install` obsoletos. Isso vem do setuptools e pode ser ignorado.

Para parar, aperte `Ctrl+C` no terminal do launch ou feche a janela do simulador. Os dois programas fecham juntos.

### Testando enquanto o jogo roda

Abra outros terminais (lembre do `source /opt/ros/$ROS_DISTRO/setup.bash` e do `source install/setup.bash` em cada um) e experimente:

```bash
ros2 node list                                   # os dois nós
ros2 topic list                                  # os tópicos
ros2 topic echo /bola/posicao                    # posição da bola ao vivo
ros2 topic hz /robo/pose                         # quantas vezes por segundo
ros2 service call /resetar_bola std_srvs/srv/Trigger     # bola volta ao centro
ros2 param get /cerebro gol_alvo                 # lê um parâmetro
ros2 param set /cerebro gol_alvo azul            # troca o gol que ele ataca
rqt_graph                                        # desenho dos nós e tópicos
```

### Dirigindo o robô com o teclado

O cérebro e o teclado mandam no mesmo tópico (`/cmd_vel`), então eles brigam. Para dirigir, rode só o simulador:

```bash
ros2 run futebol_robo simulador
```

e, em outro terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Use `i` para andar, `j` e `l` para girar, `k` para parar. O terminal do teleop precisa estar em foco.

### Testando o watchdog

Com o launch rodando, feche só o cérebro (em outro terminal: `pkill -f futebol_robo/cerebro`). O robô para em meio segundo.

## As etapas da aula

A versão com ROS é construída ao vivo, em cinco passos. A pasta `etapas/` guarda cada passo já pronto. Se algo der errado durante a aula, é só pular para a etapa seguinte. Cada etapa é um workspace completo e tem um `ETAPA.md` curto dizendo o que mudou e como testar.

| Etapa | O que ela tem |
|---|---|
| `01_simulador_topicos` | só o simulador, com os tópicos `/cmd_vel`, `/robo/pose` e `/bola/posicao` |
| `02_cerebro` | entra o cérebro. As constantes ficam fixas no código e o robô ainda não chuta de verdade |
| `03_servicos` | entram os serviços `/chutar` e `/resetar_bola`, e o chute funciona |
| `04_parametros` | as constantes viram parâmetros |
| `05_launch` | launch file e `params.yaml`. É igual ao `com_ros/` |

Para rodar uma etapa:

```bash
cd etapas/03_servicos
source /opt/ros/$ROS_DISTRO/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 run futebol_robo simulador      # terminal 1
ros2 run futebol_robo cerebro        # terminal 2 (da etapa 02 em diante)
```

## Exercícios

1. **Goleiro.** Crie um nó que defende o gol azul. Ele assina `/bola/posicao` e publica em `/cmd_vel` para manter o robô perto do gol, na altura da bola. Rode o simulador e o seu nó, sem o cérebro, e clique no campo para lançar a bola. Dica: o robô só anda para a frente e gira, então para se deslocar em y ele precisa virar para o lado, andar e voltar a olhar para o campo.
2. **Placar.** Faça o simulador publicar um tópico `/placar` com os gols de cada lado. O `mundo.py` já conta os gols em `gols_azul` e `gols_amarelo`, então falta só publicar. Escolha o tipo de mensagem (por exemplo `std_msgs/Int32MultiArray`) e confira com `ros2 topic echo /placar`. Não precisa mexer no `mundo.py`.
3. **Distância percorrida.** Crie um nó que assina `/robo/pose`, soma a distância entre as posições consecutivas e escreve o total no log uma vez por segundo. Dica: use `math.hypot` e guarde a posição anterior.

## Problemas comuns

| O que aparece | O que fazer |
|---|---|
| `ros2: command not found` | Falta o `source /opt/ros/$ROS_DISTRO/setup.bash` neste terminal. |
| `Package 'futebol_robo' not found` | Falta o `source install/setup.bash` (ou o `colcon build` ainda não foi feito). |
| `colcon: command not found` | `sudo apt install python3-colcon-common-extensions` |
| `No module named 'tkinter'` | `sudo apt install python3-tk` |
| `no display name and no $DISPLAY environment variable` | Você está sem interface gráfica (por exemplo, em SSH). Rode numa sessão com tela. |
| A janela abre, mas o robô não se mexe | Confira com `ros2 node list` se o cérebro está rodando. Se estiver usando o teleop, o cérebro precisa estar fechado. |
| Os nós não se enxergam entre terminais | Confira se `echo $ROS_DOMAIN_ID` mostra o mesmo valor em todos (ou vazio em todos). |
| Mudei o código e nada mudou | Se compilou sem `--symlink-install`, rode o `colcon build` de novo. Com ele, basta reabrir o programa. |
| Avisos de `setup.py` e `easy_install` no build | Pode ignorar. |

## Licença

MIT. Veja o arquivo [LICENSE](LICENSE).

## Contato
github.com/PedroH-Peres
