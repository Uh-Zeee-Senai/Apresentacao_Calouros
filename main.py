import pygame
import serial
import sys
import import list # Usado para importar dinamicamente os jogos das pastas

# --- CONFIGURAÇÃO DA SERIAL ---
PORTA_SERIAL = 'COM3'  # Altere para a sua porta da BlackBoard
try:
    arduino = serial.Serial(PORTA_SERIAL, 115200, timeout=0.01)
    print("Arduino Conectado com Sucesso!")
except:
    print("Arduino não encontrado. Rodando em modo de emulação.")
    arduino = None

pygame.init()
LARGURA, ALTURA = 800, 600
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("LAUNCHER ARCADE - MASTER KIT ROBOCORE")
relogio = pygame.time.Clock()

opcao_menu = 0
opcoes = ["1. Space Invaders", "2. Labirinto Easter Egg", "3. Doom Minimalista"]

def ler_hardware():
    if arduino and arduino.in_waiting > 0:
        try:
            linha = arduino.readline().decode('utf-8').strip()
            dados = [int(x) for x in linha.split(',')]
            if len(dados) == 4: return dados
        except: pass
    return [512, 512, 1, 1] # Valores padrão caso falhe ou não tenha hardware

# Importar dinamicamente os scripts das pastas
sys.path.append('1_space_invaders')
sys.path.append('2_labirinto')
sys.path.append('3_doom')

while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            if arduino: arduino.close()
            pygame.quit()
            sys.path.remove('1_space_invaders') # Limpar caminhos ao fechar
            sys.path.remove('2_labirinto')
            sys.path.remove('3_doom')
            sys.exit()

    # Coleta dados do Arduino no menu
    joy_x, joy_y, btn_menu, btn_tiro = ler_hardware()

    # Navegação no Menu usando o Eixo Y do Joystick
    if joy_y < 200:
        opcao_menu = max(0, opcao_menu - 1)
        pygame.time.wait(200) # Delay para não pular muitas opções
    elif joy_y > 800:
        opcao_menu = min(2, opcao_menu + 1)
        pygame.time.wait(200)

    # Entrar no jogo selecionado ao apertar o botão de tiro
    if btn_tiro == 0:
        pygame.time.wait(300) # Evita double-click na transição
        if opcao_menu == 0:
            import space_invaders_jogo as jogo1
            jogo1.rodar_jogo(tela, relogio, arduino, ler_hardware)
        elif opcao_menu == 1:
            import labirinto_jogo as jogo2
            jogo2.rodar_jogo(tela, relogio, arduino, ler_hardware)
        elif opcao_menu == 2:
            import doom_jogo as jogo3
            jogo3.rodar_jogo(tela, relogio, arduino, ler_hardware)

    # Renderização do Menu
    tela.fill((15, 15, 30))
    fonte_titulo = pygame.font.SysFont('Consolas', 40, bold=True)
    fonte_ops = pygame.font.SysFont('Consolas', 30)

    titulo = fonte_titulo.render("SELECIONE O JOGO", True, (255, 255, 255))
    tela.blit(titulo, (LARGURA // 2 - titulo.get_width() // 2, 100))

    for i, opt in enumerate(opcoes):
        cor = (0, 255, 0) if i == opcao_menu else (150, 150, 150)
        texto = fonte_ops.render(opt, True, cor)
        tela.blit(texto, (LARGURA // 2 - 150, 250 + i * 60))
        
    pygame.display.flip()
    relogio.tick(60)
