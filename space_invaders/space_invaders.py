import pygame
import serial
import sys
import random

# --- CONFIGURAÇÃO DA PORTA SERIAL DO ARDUINO ---
# IMPORTANTE: Mude para a porta correta que aparece na IDE do Arduino (Ex: 'COM3')
PORTA_SERIAL = 'COM3' 
VELOCIDADE_BAUD = 115200

try:
    arduino = serial.Serial(PORTA_SERIAL, VELOCIDADE_BAUD, timeout=0.01)
    print(f"Sucesso: Conectado ao hardware na porta {PORTA_SERIAL}!")
except Exception as erro:
    print(f"Erro ao conectar na porta {PORTA_SERIAL}: {erro}")
    print("O jogo rodará em modo de emulação de teclado para testes.")
    arduino = None

# --- INICIALIZAÇÃO DA GAME ENGINE (PYGAME) ---
pygame.init()
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Space Invaders Lab - Apresentação Acadêmica")
relogio = pygame.time.Clock()

# Variáveis globais para armazenamento dos estados dos sensores
joy_x, joy_y, btn_menu, btn_tiro = 512, 512, 1, 1
ultimo_estado_botao_tiro = 1

def processar_dados_hardware():
    """Lê as informações da porta serial e atualiza os comandos lógicos do jogo."""
    global joy_x, joy_y, btn_menu, btn_tiro, ultimo_estado_botao_tiro
    
    if arduino and arduino.in_waiting > 0:
        try:
            # Captura a linha de texto bruta enviada pelo Arduino
            linha = arduino.readline().decode('utf-8').strip()
            dados = linha.split(',')
            if len(dados) == 4:
                joy_x = int(dados[0])
                joy_y = int(dados[1])
                btn_menu = int(dados[2])
                ultimo_estado_botao_tiro = btn_tiro
                btn_tiro = int(dados[3])
        except Exception:
            pass # Ignora erros de leitura de pacotes incompletos

def notificar_hardware(comando):
    """Envia um byte de instrução de volta para o Arduino executar som/luz."""
    if arduino:
        try:
            arduino.write(comando.encode())
        except Exception:
            pass

# --- ENTIDADES E CONFIGURAÇÃO DO JOGO ---
# Jogador (Canhão de Defesa)
jogador_x = LARGURA // 2
jogador_y = ALTURA - 50
velocidade_jogador = 8

# Vetores de gerenciamento de objetos em cena
tiros_jogador = []
aliens = []
pontuacao = 0

def criar_novo_alien():
    """Gera uma nova coordenada aleatória no topo da tela para um inimigo."""
    return {"x": random.randint(50, LARGURA - 50), "y": random.randint(30, 150), "velocidade": random.choice([1, 2])}

# Inicializa os primeiros 5 invasores na matriz espacial
for _ in range(5):
    aliens.append(criar_novo_alien())

# --- LOOP PRINCIPAL DO JOGO (60 FPS) ---
jogando = True
while jogando:
    # Gerenciamento de eventos de fechamento de janela
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            jogando = False

    # Executa a atualização dos dados do controle físico
    processar_dados_hardware()

    # --- PROCESSAMENTO LOGICO DOS COMANDOS DO JOYSTICK ---
    # Centralizado fica em torno de 512. Menor que 300 = Esquerda. Maior que 700 = Direita.
    if joy_x < 300:
        jogador_x = max(25, jogador_x - velocidade_jogador)
    elif joy_x > 700:
        jogador_x = min(LARGURA - 25, jogador_x + velocidade_jogador)

    # Lógica de Gatilho de Tiro de Borda de Descida (Apenas um tiro por clique físico)
    # Lembrar que o botão físico usa PULLUP, ou seja, 0 significa pressionado.
    if btn_tiro == 0 and ultimo_estado_botao_tiro == 1:
        tiros_jogador.append({"x": jogador_x, "y": jogador_y - 15})
        notificar_hardware('T') # Manda o sinal 'T' imediatamente para o Arduino apitar/piscar

    # --- ATUALIZAÇÃO DA FÍSICA DOS OBJETOS ---
    # Movimentação dos tiros para cima
    for tiro in tiros_jogador[:]:
        tiro['y'] -= 12
        if tiro['y'] < 0:
            tiros_jogador.remove(tiro)

    # Movimentação e colisão dos invasores
    for alien in aliens[:]:
        # Deslocamento progressivo para baixo
        alien['y'] += alien['velocidade']
        
        # Se algum invasor atingir a linha de defesa, reseta sua posição no topo
        if alien['y'] > ALTURA - 30:
            alien['y'] = random.randint(30, 100)

        # Checagem de colisões (Tiro vs Invasor) através de caixas delimitadoras (Bounding Box)
        for tiro in tiros_jogador[:]:
            if (alien['x'] - 20 < tiro['x'] < alien['x'] + 20) and (alien['y'] < tiro['y'] < alien['y'] + 25):
                # Detecção positiva de colisão
                notificar_hardware('M') # Manda sinal de explosão 'M' para o som de colisão do Arduino
                pontuacao += 10
                aliens.remove(alien)
                if tiro in tiros_jogador:
                    tiros_jogador.remove(tiro)
                aliens.append(criar_novo_alien()) # Repovoa o cenário espacial
                break

    # --- RENDERIZAÇÃO GRÁFICA NA TELA ---
    tela.fill((10, 10, 20)) # Fundo Espacial Escuro

    # Desenha o Canhão do Jogador (Retângulo Verde Clássico)
    pygame.draw.rect(tela, (0, 255, 0), (jogador_x - 25, jogador_y, 50, 15), border_radius=3)
    pygame.draw.rect(tela, (0, 255, 0), (jogador_x - 6, jogador_y - 10, 12, 10))

    # Desenha os Tiros Ativos
    for tiro in tiros_jogador:
        pygame.draw.circle(tela, (255, 255, 0), (tiro['x'], tiro['y']), 4)

    # Desenha os Invasores (Blocos Vermelhos de Ameaça)
    for alien in aliens:
        pygame.draw.rect(tela, (255, 50, 50), (alien['x'] - 20, alien['y'], 40, 25), border_radius=4)
        # Detalhe visual dos olhos mecânicos dos aliens
        pygame.draw.circle(tela, (255, 255, 255), (alien['x'] - 8, alien['y'] + 10), 3)
        pygame.draw.circle(tela, (255, 255, 255), (alien['x'] + 8, alien['y'] + 10), 3)

    # Exibição do Placar de Pontuação na Apresentação
    fonte = pygame.font.SysFont('Consolas', 28)
    texto_placar = fonte.render(f"SCORE: {pontuacao:05d}", True, (255, 255, 255))
    tela.blit(texto_placar, (20, 20))

    # Atualiza o frame atual e sincroniza a 60 quadros por segundo
    pygame.display.flip()
    relogio.tick(60)

# Finaliza conexões e encerra o sistema limpando recursos
if arduino:
    arduino.close()
pygame.quit()
sys.exit()
