# Explicação: o que é ROS 2 e como este projeto funciona

Este arquivo tem duas partes. A primeira explica o que é o ROS 2, do zero. A segunda mostra como o código deste projeto usa cada conceito. Para instalar e rodar, veja o [README](README.md).

## Parte 1: o que é ROS 2

### O que é e para que serve

ROS significa *Robot Operating System*, mas ele não é um sistema operacional. É um conjunto de bibliotecas e ferramentas, gratuitas e de código aberto, para programar robôs. Ele roda em cima de um sistema que você já tem, como o Ubuntu.

A ideia principal é esta: em vez de fazer um programa gigante que lê sensores, decide e move os motores, você divide o robô em vários programas pequenos que conversam entre si. Cada programa faz uma coisa só. Isso traz algumas vantagens:

- **Troca de peças.** O programa que decide não precisa saber se quem recebe a ordem é um simulador ou um robô de verdade. Neste curso, o `simulador` poderia ser trocado pelo programa de um robô real sem mexer no `cerebro`.
- **Reuso.** Muita coisa já vem pronta: leitura de câmera, navegação, visualização, gravação de dados.
- **Vários computadores.** Os programas podem rodar em máquinas diferentes e ainda assim se enxergar pela rede.
- **Ferramentas.** Dá para espiar a conversa entre os programas e desenhar o grafo do sistema sem mudar uma linha de código.

O "2" quer dizer a segunda geração, que substituiu o ROS 1. Cada lançamento do ROS 2 é uma *distribuição* com nome de letra: o **Humble** (2022) roda no Ubuntu 22.04, e o **Jazzy** (2024) roda no Ubuntu 24.04. Os dois têm suporte de longo prazo, e este projeto foi escrito para funcionar nos dois.

### Os conceitos que importam

**Nó.** É um programa que faz uma tarefa. Neste projeto são dois: `simulador` e `cerebro`. Em um robô de verdade seriam dezenas (câmera, motores, planejador...). Em Python, um nó é uma classe que herda de `rclpy.node.Node`.

**Tópico e mensagem.** Um tópico é um canal de comunicação com nome, como `/cmd_vel`. Quem quer enviar dados *publica* no tópico, e quem quer receber *assina* o tópico. O publicador não sabe quem está ouvindo, e quem ouve não sabe quem está falando. Pode haver vários publicadores e vários assinantes no mesmo tópico.

O que trafega no tópico é uma *mensagem*, e cada tópico tem um tipo fixo de mensagem. Os tipos usados aqui são:

| Tipo | O que tem dentro |
|---|---|
| `geometry_msgs/Twist` | velocidade: `linear.x` (para a frente, em m/s) e `angular.z` (giro, em rad/s) |
| `geometry_msgs/Pose` | posição (`position.x/y/z`) e direção (`orientation`, um quaternion) |
| `geometry_msgs/Point` | só um ponto: `x`, `y`, `z` |
| `std_msgs/String` | um texto em `data` |

Tópicos servem para fluxos contínuos: posição do robô 50 vezes por segundo, comandos de velocidade, leituras de sensor.

**Serviço.** É uma pergunta com resposta. Um nó *cliente* faz um pedido (*request*) e o nó *servidor* responde (*response*). Serve para ações pontuais, como "chuta agora" ou "põe a bola no centro". Este projeto usa o tipo `std_srvs/Trigger`: o pedido vem vazio, e a resposta tem `success` (verdadeiro ou falso) e `message` (um texto).

A diferença prática: um tópico é um fluxo que não espera resposta, e um serviço é um pedido que volta com resultado.

**Parâmetro.** É uma configuração de um nó, como a velocidade máxima ou qual gol atacar. Cada parâmetro tem nome, tipo e valor, e pode ser lido e mudado com o programa rodando (`ros2 param get` e `ros2 param set`) ou definido num arquivo YAML.

**Launch file.** Um arquivo Python que sobe vários nós de uma vez, já com os parâmetros certos. Evita abrir um terminal para cada programa.

**Pacote, workspace e colcon.** O código ROS é organizado em *pacotes* (aqui, o `futebol_robo`). Uma pasta com pacotes dentro de `src/` é um *workspace*. O `colcon build` compila o workspace e cria as pastas `build/`, `install/` e `log/`. Depois, o `source install/setup.bash` avisa o terminal de que esses pacotes existem. Esse `source` precisa ser feito em cada terminal novo.

### Como os nós se encontram

No ROS 2 não existe um programa central coordenando tudo. Quando um nó sobe, ele se anuncia na rede local, e os outros nós descobrem a existência dele sozinhos. Por baixo, o ROS 2 usa um padrão de comunicação chamado DDS para isso.

Todos os nós que estão no mesmo *domínio* se enxergam. O domínio é um número (a variável `ROS_DOMAIN_ID`, que vale 0 se não estiver definida). Dois computadores na mesma rede com o mesmo número se enxergam. Isso é útil para separar grupos numa sala de aula: cada grupo usa um número diferente.

### Ferramentas de linha de comando

Estas são as que usamos na aula:

| Comando | Para que serve |
|---|---|
| `ros2 node list` | lista os nós que estão rodando |
| `ros2 topic list` | lista os tópicos |
| `ros2 topic echo /nome` | mostra as mensagens de um tópico |
| `ros2 topic hz /nome` | mede a frequência de um tópico |
| `ros2 topic pub /nome tipo "{...}"` | publica uma mensagem na mão |
| `ros2 service list` / `call` | lista e chama serviços |
| `ros2 param list` / `get` / `set` | mexe nos parâmetros |
| `ros2 run pacote executavel` | roda um nó |
| `ros2 launch pacote arquivo` | roda um launch file |
| `rqt_graph` | desenha os nós e os tópicos entre eles |

## Parte 2: como o projeto funciona

### O desenho geral

```
simulador --- /robo/pose ---------> cerebro
simulador --- /bola/posicao ------> cerebro
cerebro   --- /cmd_vel ----------> simulador
cerebro   --- /estado ------------> simulador
cerebro   --- serviço /chutar ----> simulador
```

O simulador diz onde estão o robô e a bola. O cérebro decide e responde com a velocidade (`/cmd_vel`), com um texto de estado (`/estado`) e, na hora de chutar, com um pedido ao serviço `/chutar`. O serviço `/resetar_bola` fica disponível para quem quiser chamar de fora.

### Onde cada conceito aparece no código

| Conceito | Onde |
|---|---|
| nó | `class Simulador(Node)` e `class Cerebro(Node)` |
| publicar | `self.create_publisher(...)` e `.publish(...)` |
| assinar | `self.create_subscription(...)` |
| serviço (servidor) | `self.create_service(Trigger, '/chutar', ...)` no simulador |
| serviço (cliente) | `self.create_client(Trigger, '/chutar')` e `call_async` no cérebro |
| parâmetro | `self.declare_parameter(...)` e `self.get_parameter(...)` no cérebro |
| launch | `launch/futebol.launch.py` |
| arquivo de parâmetros | `config/params.yaml` |

### O mundo (`mundo.py`)

Este arquivo não sabe nada de ROS. Ele guarda onde estão o robô e a bola, faz a física e desenha com o Tkinter. É igual nas duas versões, e é por isso que dá para mostrar que só a "cola" mudou.

- O robô é um robô diferencial: ele só anda para a frente (`vel_linear`) e gira (`vel_angular`). Não anda de lado.
- A bola perde velocidade com o atrito e quica nas paredes.
- Se o robô encosta na bola, ele a empurra.
- O chute dá 3 m/s à bola, mas só funciona se ela estiver a menos de 0,45 m e mais ou menos na frente do robô.
- Se a bola cruza a linha de fundo dentro do gol, conta o gol e a bola volta ao centro.
- Clicar no campo põe a bola no ponto clicado.

### O cérebro

Ele recebe a posição do robô e da bola e devolve três coisas: a velocidade para a frente, o giro e se deve chutar. Por dentro é uma máquina de estados, ou seja, uma variável `estado` que diz o que o robô está fazendo agora, e um `if` para cada estado:

1. **PROCURAR**: gira até a bola estar a menos de 70° da frente.
2. **CONTORNAR**: vai até o ponto atrás da bola. Esse ponto fica na linha que liga o gol à bola, `distancia_atras` metros antes da bola. Se o robô está do lado do gol, ele primeiro vai para um ponto ao lado da bola, para não atravessá-la.
3. **ALINHAR**: gira até apontar para o gol (erro menor que 0,08 rad, uns 5°). Se se afastar do ponto, volta para CONTORNAR.
4. **CHUTAR**: anda devagar até a bola. A menos de 0,38 m e bem apontado, pede o chute e volta para PROCURAR.

Para ir até um ponto, a função `ir_para` calcula o ângulo até o alvo, gira proporcionalmente ao erro (esse é o `ganho_angular`) e anda para a frente na velocidade máxima, mais devagar quando está perto. A velocidade é multiplicada pelo cosseno do erro, então o robô quase não anda enquanto está virado para o lado errado.

### O nó simulador

- Cria o `Mundo` dentro do nó. O Tkinter e o ROS precisam rodar juntos, e os dois querem controlar o laço principal do programa. A solução é deixar o Tkinter mandar: a cada 20 ms ele chama `tick()`, que faz um `rclpy.spin_once(no, timeout_sec=0)` (atende o que chegou sem esperar), avança a física, publica as posições e redesenha.
- A direção do robô sai como quaternion. Como o robô só gira em torno do eixo z, basta `z = sen(yaw/2)` e `w = cos(yaw/2)`. O cérebro desfaz com `yaw = 2 * atan2(z, w)`.
- O watchdog guarda a hora do último `/cmd_vel`. Se passar 0,5 s sem receber nada, a velocidade vai a zero. Pelo mesmo motivo, um robô de verdade pararia se o programa que decide travasse.

### O nó cérebro

- Guarda a última pose e a última posição da bola que chegaram.
- Um timer chama `ciclo()` 20 vezes por segundo: decide, publica `/cmd_vel` e `/estado`, e pede o chute se for o caso.
- O chute usa `call_async`. Se o cérebro esperasse a resposta parado, o programa inteiro travaria até ela chegar. Com `call_async` o pedido sai, o programa segue, e a resposta cai na função `ao_responder_chute` quando chegar. A variável `chute_pendente` impede mandar um segundo pedido enquanto o primeiro não voltou.
- Os parâmetros são lidos a cada ciclo, então `ros2 param set` faz efeito na hora. Há uma função que o ROS chama antes de aceitar um valor novo, e ela recusa um `gol_alvo` que não seja `amarelo` ou `azul`.

### Fechando sem erro com Ctrl+C

Alguns detalhes que evitam travar a aula ao vivo:

- O Tkinter ignora o Ctrl+C. Por isso `main.py` e `simulador.py` registram um tratador de sinal que fecha a janela.
- No Humble, `rclpy.spin` levanta `ExternalShutdownException` quando o programa é encerrado. O cérebro captura essa exceção.
- O Ctrl+C chega duas vezes ao cérebro: uma direto do terminal e outra repassada pelo launch. O cérebro ignora a segunda, senão ela interromperia a limpeza e mostraria um erro.
- O launch derruba o cérebro se a janela do simulador for fechada.

## As etapas e o roteiro da aula

Cada etapa em `etapas/` é um workspace completo, gerado a partir da versão final. O `mundo.py` é igual em todas, e a `05_launch` é igual ao `com_ros/`.

| Etapa | O que muda em relação à anterior |
|---|---|
| 01 `simulador_topicos` | só o simulador, com `/cmd_vel`, as duas posições e o watchdog |
| 02 `cerebro` | entra o cérebro, com constantes fixas e `/estado`. O chute só escreve no log |
| 03 `servicos` | entram `/chutar`, `/resetar_bola` e o cliente assíncrono |
| 04 `parametros` | as constantes viram parâmetros, com validação do `gol_alvo` |
| 05 `launch` | launch file e `params.yaml` |

Um roteiro possível para os 1h45:

1. **Teoria curta.** Explique o que é ROS, nós, tópicos, serviços e parâmetros (a Parte 1 deste arquivo).
2. **Jogo sem ROS.** Rode o `sem_ros` e explique os quatro estados do cérebro. Mostre que `main.py` liga as partes com chamadas de função.
3. **Etapa 01.** Rode só o simulador e mova o robô com `ros2 topic pub` ou com o teleop. Os alunos veem um tópico funcionando.
4. **Etapa 02.** Separe o cérebro. Abra o `rqt_graph` e mostre o grafo.
5. **Etapa 03.** O chute vira serviço. Chame `/resetar_bola` pela linha de comando e explique por que o cliente é assíncrono.
6. **Etapa 04.** As constantes viram parâmetros. Rode `ros2 param set /cerebro gol_alvo azul` e veja o robô trocar de gol.
7. **Etapa 05.** O launch junta tudo. Feche o cérebro e mostre o watchdog parando o robô.
8. **Exercícios.** Os três do README.

Se errar ao vivo, entre na pasta da etapa seguinte, rode `colcon build --symlink-install` e continue.

## O que foi testado

Os testes rodaram no ROS 2 Humble, em um display virtual.

- **Sem ROS:** cerca de 58 gols em 10 minutos simulados, para os dois `gol_alvo`. O clique move a bola e o Ctrl+C encerra limpo.
- **Com ROS:** lista de tópicos, `/robo/pose` a cerca de 47 Hz, os dois serviços, `ros2 param set` (inclusive a recusa de valor inválido), o watchdog depois de matar o cérebro e o teleop. O Ctrl+C no launch encerrou limpo em todas as tentativas.
- **Etapas:** as cinco compilam, rodam e encerram sozinhas.

Limites conhecidos:

- O Jazzy não foi testado. A compatibilidade vem do uso de partes estáveis do `rclpy`.
- O exercício do goleiro é mais difícil do que parece, porque o robô é diferencial e não anda de lado.
- As etapas são cópias do `com_ros`. Se você mudar o `com_ros`, precisa atualizar as etapas à mão.

## Glossário rápido

| Termo | Significa |
|---|---|
| nó | um programa ROS que faz uma tarefa |
| tópico | canal com nome onde nós publicam e assinam mensagens |
| mensagem | o dado que passa pelo tópico, com tipo fixo |
| serviço | pedido e resposta entre dois nós |
| parâmetro | configuração de um nó, que pode mudar com ele rodando |
| launch | arquivo que sobe vários nós de uma vez |
| pacote | unidade de código ROS (aqui, `futebol_robo`) |
| workspace | pasta com pacotes dentro de `src/` |
| colcon | a ferramenta que compila o workspace |
| `source` | comando do terminal que carrega o ROS ou o seu workspace |
| quaternion | jeito de guardar uma rotação em 3D com quatro números (x, y, z, w) |
| watchdog | proteção que para o robô se os comandos pararem de chegar |
