import pygame
import sys
import os
import time
import math
from core.arduino_controller import conectar_arduino, ler_hardware, enviar_comando
from core import teste_controle
from core.database import init_db
from core.nome_modal import solicitar_nome_jogador
from core import rankings_ui
from space_invaders import jogo as space_invaders_jogo
from adventure import jogo as adventure_jogo
from adventure.nivel_modal import selecionar_nivel_adventure

def main():
    pygame.init()
    init_db()  # Inicializa o banco de dados SQLite (arcade.db)

    LARGURA, ALTURA = 800, 600
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("RETRO ARCADE CABINET - ROBOCORE KIT")
    relogio = pygame.time.Clock()

    # Conecta ao Arduino se disponível
    arduino = conectar_arduino()

    opcao_menu = 0
    opcoes = [
        {"icon": "🚀", "titulo": "SPACE INVADERS", "sub": "RETRO 5-COL ARCADE SHOOTER"},
        {"icon": "🐉", "titulo": "ADVENTURE ATARI 2600", "sub": "MAPA COMPLETO, 3 CASTELOS & BOSS ZÉCREPPE"},
        {"icon": "🏆", "titulo": "HALL DA FAMA", "sub": "VENCEDORES ORIGINAIS & TOP 20"},
        {"icon": "⚙️", "titulo": "HARDWARE DIAGNOSTIC", "sub": "TESTE DE JOYSTICK E BOTÕES"},
        {"icon": "❌", "titulo": "SAIR DO LAUNCHER", "sub": "ENCERRAR O SISTEMA ARCADE"}
    ]

    # Cores Anos 80 Neon CRT
    COR_FUNDO = (10, 8, 22)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_AMARELO = (255, 230, 0)
    COR_NEON_VERDE = (0, 255, 120)
    COR_TEXTO_MUTED = (140, 150, 180)
    COR_CARD_BG = (18, 16, 32)
    COR_CARD_SEL = (35, 20, 55)

    fonte_titulo_lg = pygame.font.SysFont('Consolas', 30, bold=True)
    fonte_card_tit = pygame.font.SysFont('Consolas', 18, bold=True)
    fonte_card_sub = pygame.font.SysFont('Consolas', 12)
    fonte_arcade_sm = pygame.font.SysFont('Consolas', 13, bold=True)

    tempo_ultima_navegacao = 0
    ultimo_nome = ""

    # Fundo Estelar Discreto do Launcher
    estrelas_launcher = [
        {"x": (i * 97) % LARGURA, "y": (i * 53) % ALTURA, "tam": (i % 2) + 1, "vel": 0.4 + (i % 3) * 0.2}
        for i in range(40)
    ]

    rodando = True
    frame_count = 0

    def executar_opcao(idx):
        nonlocal ultimo_nome, rodando
        if idx == 0:
            nome = solicitar_nome_jogador(tela, relogio, arduino, ler_hardware, ultimo_nome)
            if nome:
                ultimo_nome = nome
                space_invaders_jogo.rodar_jogo(tela, relogio, arduino, ler_hardware, nome)
        elif idx == 1:
            nome = solicitar_nome_jogador(tela, relogio, arduino, ler_hardware, ultimo_nome)
            if nome:
                ultimo_nome = nome
                nivel = selecionar_nivel_adventure(tela, relogio, arduino, ler_hardware)
                if nivel:
                    adventure_jogo.rodar_jogo(tela, relogio, arduino, ler_hardware, nome, nivel)
        elif idx == 2:
            rankings_ui.exibir_rankings(tela, relogio, arduino, ler_hardware)
        elif idx == 3:
            teste_controle.rodar_teste()
        elif idx == 4:
            rodando = False

    while rodando:
        frame_count += 1
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    opcao_menu = (opcao_menu - 1) % len(opcoes)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    opcao_menu = (opcao_menu + 1) % len(opcoes)
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    executar_opcao(opcao_menu)

        # Lê os dados do hardware
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        # Navegação no Menu por Joystick Y
        if agora - tempo_ultima_navegacao > 0.22:
            if joy_y < 300:
                opcao_menu = (opcao_menu - 1) % len(opcoes)
                tempo_ultima_navegacao = agora
            elif joy_y > 700:
                opcao_menu = (opcao_menu + 1) % len(opcoes)
                tempo_ultima_navegacao = agora

        # Seleção por Botão de Tiro
        if btn_tiro == 0 and (agora - tempo_ultima_navegacao > 0.3):
            tempo_ultima_navegacao = agora
            executar_opcao(opcao_menu)

        # --- RENDERIZAÇÃO RETRO ARCADE ---
        tela.fill(COR_FUNDO)

        # Animação de estrelas no fundo
        for est in estrelas_launcher:
            est['y'] = (est['y'] + est['vel']) % ALTURA
            pygame.draw.circle(tela, (70, 75, 110), (int(est['x']), int(est['y'])), est['tam'])

        # Scanlines CRT
        for y in range(0, ALTURA, 4):
            pygame.draw.line(tela, (14, 12, 28), (0, y), (LARGURA, y), 1)

        # Molduras Duplas Neon
        pygame.draw.rect(tela, COR_NEON_ROSA, (15, 10, 770, 580), width=3, border_radius=8)
        pygame.draw.rect(tela, COR_NEON_AZUL, (21, 16, 758, 568), width=1, border_radius=6)

        # Header Superior
        nome_exibido = f"JOGADOR ATIVO: {ultimo_nome}" if ultimo_nome else "JOGADOR: ANÔNIMO"
        txt_hi = fonte_arcade_sm.render(f"ARCADE CABINET SYSTEM   |   {nome_exibido}", True, COR_NEON_AMARELO)
        tela.blit(txt_hi, (LARGURA // 2 - txt_hi.get_width() // 2, 24))

        # Banner do Título Principal Neon
        pygame.draw.rect(tela, (22, 14, 38), (60, 48, 680, 68), border_radius=8)
        pygame.draw.rect(tela, COR_NEON_AZUL, (60, 48, 680, 68), width=2, border_radius=8)

        pulso_titulo = math.sin(agora * 3) * 20
        cor_tit_glow = (min(255, max(0, int(0 + pulso_titulo))), 240, 255)
        txt_titulo = fonte_titulo_lg.render("★ RETRO ARCADE CLASSICS ★", True, cor_tit_glow)
        tela.blit(txt_titulo, (LARGURA // 2 - txt_titulo.get_width() // 2, 54))

        txt_sub = fonte_arcade_sm.render("ROBOCORE BLACKBOARD - LAUNCHER EDITIONS", True, COR_NEON_ROSA)
        tela.blit(txt_sub, (LARGURA // 2 - txt_sub.get_width() // 2, 92))

        # Status de Hardware
        if arduino:
            status_txt = f"● ARDUINO ONLINE ({arduino.port})"
            cor_st = COR_NEON_VERDE
        else:
            status_txt = "● MODO TECLADO (WASD / TECLAS DIRECIONAIS)"
            cor_st = COR_NEON_AMARELO

        txt_st = fonte_arcade_sm.render(status_txt, True, cor_st)
        tela.blit(txt_st, (LARGURA // 2 - txt_st.get_width() // 2, 126))

        # --- CARDS DO MENU ---
        y_base = 154
        card_w, card_h = 520, 56
        espacamento = 64

        for i, item in enumerate(opcoes):
            y_pos = y_base + i * espacamento
            selecionado = (i == opcao_menu)

            card_x = LARGURA // 2 - card_w // 2
            card_rect = pygame.Rect(card_x, y_pos, card_w, card_h)

            if selecionado:
                cor_bg = COR_CARD_SEL
                cor_borda = COR_NEON_VERDE
                cor_tit = COR_NEON_VERDE
                cor_sub = (200, 240, 210)

                pygame.draw.polygon(tela, COR_NEON_VERDE, [(card_x - 30, y_pos + 18), (card_x - 30, y_pos + 38), (card_x - 12, y_pos + 28)])
                pygame.draw.polygon(tela, COR_NEON_VERDE, [(card_x + card_w + 30, y_pos + 18), (card_x + card_w + 30, y_pos + 38), (card_x + card_w + 12, y_pos + 28)])
            else:
                cor_bg = COR_CARD_BG
                cor_borda = (50, 45, 75)
                cor_tit = (220, 225, 240)
                cor_sub = COR_TEXTO_MUTED

            pygame.draw.rect(tela, cor_bg, card_rect, border_radius=8)
            pygame.draw.rect(tela, cor_borda, card_rect, width=2 if selecionado else 1, border_radius=8)

            txt_ic = fonte_card_tit.render(item['icon'], True, (255, 255, 255))
            txt_t = fonte_card_tit.render(item['titulo'], True, cor_tit)
            txt_s = fonte_card_sub.render(item['sub'], True, cor_sub)

            tela.blit(txt_ic, (card_x + 18, y_pos + 16))
            tela.blit(txt_t, (card_x + 55, y_pos + 11))
            tela.blit(txt_s, (card_x + 55, y_pos + 32))

        if (frame_count // 25) % 2 == 0:
            txt_start = fonte_card_tit.render("► PRESSIONE BOTÃO DE TIRO / ENTER PARA SELECIONAR ◄", True, COR_NEON_AMARELO)
            tela.blit(txt_start, (LARGURA // 2 - txt_start.get_width() // 2, 492))

        txt_dica = fonte_arcade_sm.render("JOYSTICK Y / W-S: NAVEGAR  |  BOTÃO DE TIRO / ESPAÇO: CONFIRMAR", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica, (LARGURA // 2 - txt_dica.get_width() // 2, 545))

        pygame.display.flip()
        relogio.tick(60)

    if arduino:
        arduino.close()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
