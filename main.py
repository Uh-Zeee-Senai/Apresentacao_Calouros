import pygame
import sys
import os
import time
import math
from core.arduino_controller import conectar_arduino, ler_hardware, enviar_comando
from core import teste_controle
from space_invaders import jogo as space_invaders_jogo

def main():
    pygame.init()
    LARGURA, ALTURA = 800, 600
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("RETRO ARCADE CABINET - ROBOCORE KIT")
    relogio = pygame.time.Clock()

    # Tenta conectar ao Arduino
    arduino = conectar_arduino()

    opcao_menu = 0
    opcoes = [
        "1. SPACE INVADERS (RETRO 5-COL)",
        "2. HARDWARE DIAGNOSTIC PANEL",
        "3. EXIT LAUNCHER"
    ]

    # Cores no estilo Arcade Anos 80 (Neon CRT)
    COR_FUNDO = (10, 8, 20)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_AMARELO = (255, 230, 0)
    COR_NEON_VERDE = (0, 255, 120)
    COR_TEXTO_MUTED = (140, 150, 180)

    fonte_arcade_lg = pygame.font.SysFont('Consolas', 34, bold=True)
    fonte_arcade_md = pygame.font.SysFont('Consolas', 22, bold=True)
    fonte_arcade_sm = pygame.font.SysFont('Consolas', 15, bold=True)

    tempo_ultima_navegacao = 0

    rodando = True
    frame_count = 0

    while rodando:
        frame_count += 1
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_UP or evento.key == pygame.K_w:
                    opcao_menu = (opcao_menu - 1) % len(opcoes)
                elif evento.key == pygame.K_DOWN or evento.key == pygame.K_s:
                    opcao_menu = (opcao_menu + 1) % len(opcoes)
                elif evento.key == pygame.K_RETURN or evento.key == pygame.K_SPACE:
                    if opcao_menu == 0:
                        space_invaders_jogo.rodar_jogo(tela, relogio, arduino, ler_hardware)
                    elif opcao_menu == 1:
                        teste_controle.rodar_teste()
                    elif opcao_menu == 2:
                        rodando = False

        # Lê os dados do hardware (eixos X/Y invertidos)/teclado
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        # Navegação no Menu usando Eixo Y do Joystick
        agora = time.time()
        if agora - tempo_ultima_navegacao > 0.22:
            if joy_y < 300: # Para cima
                opcao_menu = (opcao_menu - 1) % len(opcoes)
                tempo_ultima_navegacao = agora
            elif joy_y > 700: # Para baixo
                opcao_menu = (opcao_menu + 1) % len(opcoes)
                tempo_ultima_navegacao = agora

        # Seleção com o Botão de Tiro
        if btn_tiro == 0 and (agora - tempo_ultima_navegacao > 0.3):
            tempo_ultima_navegacao = agora
            if opcao_menu == 0:
                space_invaders_jogo.rodar_jogo(tela, relogio, arduino, ler_hardware)
            elif opcao_menu == 1:
                teste_controle.rodar_teste()
            elif opcao_menu == 2:
                rodando = False

        # --- RENDERIZAÇÃO RETRO CRT ARCADE ---
        tela.fill(COR_FUNDO)

        # Efeito Scanlines CRT (Linhas horizontais discretas)
        for y in range(0, ALTURA, 4):
            pygame.draw.line(tela, (16, 14, 30), (0, y), (LARGURA, y), 1)

        # Moldura Externa Retro Dupla
        pygame.draw.rect(tela, COR_NEON_ROSA, (20, 15, 760, 570), width=3, border_radius=6)
        pygame.draw.rect(tela, COR_NEON_AZUL, (26, 21, 748, 558), width=1, border_radius=4)

        # High Score / Credits Header estilo 1980s
        txt_hi = fonte_arcade_sm.render("HIGH SCORE  99990    CREDIT 01", True, COR_NEON_AMARELO)
        tela.blit(txt_hi, (LARGURA // 2 - txt_hi.get_width() // 2, 35))

        # Banner Principal Neon Retro
        pygame.draw.rect(tela, (25, 15, 40), (60, 65, 680, 85), border_radius=8)
        pygame.draw.rect(tela, COR_NEON_AZUL, (60, 65, 680, 85), width=2, border_radius=8)

        txt_titulo1 = fonte_arcade_lg.render("★ ARCADE CLASSIC RETRO ★", True, COR_NEON_AZUL)
        tela.blit(txt_titulo1, (LARGURA // 2 - txt_titulo1.get_width() // 2, 75))

        txt_sub = fonte_arcade_sm.render("ROBOCORE BLACKBOARD - LAUNCHER", True, COR_NEON_ROSA)
        tela.blit(txt_sub, (LARGURA // 2 - txt_sub.get_width() // 2, 118))

        # Status de Hardware
        if arduino:
            status_txt = f"● HARDWARE ARDUINO ONLINE ({arduino.port})"
            cor_st = COR_NEON_VERDE
        else:
            status_txt = "● MODO EMULAÇÃO TECLADO (WASD / ARROWS)"
            cor_st = COR_NEON_AMARELO
            
        txt_st = fonte_arcade_sm.render(status_txt, True, cor_st)
        tela.blit(txt_st, (LARGURA // 2 - txt_st.get_width() // 2, 175))

        # Opções do Menu Estilo Arcade 80s
        for i, opt in enumerate(opcoes):
            y_pos = 230 + i * 85
            selecionado = (i == opcao_menu)

            # Efeito de brilho piscante para o item selecionado
            if selecionado:
                cor_box = (40, 20, 60)
                cor_borda = COR_NEON_VERDE
                cor_texto = COR_NEON_VERDE
                
                # Indicadores de seleção estilo seta pixel 80s `> `
                pygame.draw.polygon(tela, COR_NEON_VERDE, [(140, y_pos + 20), (140, y_pos + 45), (160, y_pos + 32)])
                pygame.draw.polygon(tela, COR_NEON_VERDE, [(660, y_pos + 20), (660, y_pos + 45), (640, y_pos + 32)])
            else:
                cor_box = (18, 16, 32)
                cor_borda = (50, 45, 80)
                cor_texto = COR_TEXTO_MUTED

            pygame.draw.rect(tela, cor_box, (175, y_pos, 450, 65), border_radius=6)
            pygame.draw.rect(tela, cor_borda, (175, y_pos, 450, 65), width=2, border_radius=6)

            txt_opt = fonte_arcade_md.render(opt, True, cor_texto)
            tela.blit(txt_opt, (LARGURA // 2 - txt_opt.get_width() // 2, y_pos + 20))

        # Texto Piscante "INSERT COIN / PRESS START"
        if (frame_count // 30) % 2 == 0:
            txt_start = fonte_arcade_md.render("► PRESS ACTION BUTTON TO START ◄", True, COR_NEON_AMARELO)
            tela.blit(txt_start, (LARGURA // 2 - txt_start.get_width() // 2, 495))

        # Instruções de navegação estilo arcade
        txt_dica = fonte_arcade_sm.render("JOYSTICK Y: MOVE SELECTION | ACTION BUTTON: SELECT", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica, (LARGURA // 2 - txt_dica.get_width() // 2, 545))

        pygame.display.flip()
        relogio.tick(60)

    if arduino:
        arduino.close()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
