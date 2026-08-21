import pygame
import time

def solicitar_nome_jogador(tela, relogio, arduino, ler_hardware, nome_anterior=""):
    """
    Exibe a modal retro para o jogador digitar seu nome antes de iniciar a partida.
    - O campo SEMPRE começa 100% VAZIO ("") a cada nova chamada.
    - Limite absoluto de 10 caracteres.
    - O botão [JOGAR] permanece bloqueado enquanto o campo estiver vazio ou > 10 caracteres.
    - Pressionar ESC/Menu retorna None (cancelando a inicialização do jogo).
    """
    LARGURA, ALTURA = 800, 600

    # SEMPRE RESETAR O NOME PARA VAZIO
    nome = ""

    COR_MODAL_BG = (18, 16, 32)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_VERDE = (0, 255, 120)
    COR_NEON_AMARELO = (255, 230, 0)
    COR_TEXTO_MUTED = (140, 150, 180)
    COR_TEXTO_DESABILITADO = (80, 85, 100)

    fonte_titulo = pygame.font.SysFont('Consolas', 26, bold=True)
    fonte_input = pygame.font.SysFont('Consolas', 30, bold=True)
    fonte_btn = pygame.font.SysFont('Consolas', 22, bold=True)
    fonte_sub = pygame.font.SysFont('Consolas', 14)

    tempo_ultimo_input = time.time()
    opcao_selecionada = 0 # 0 = Campo Texto, 1 = Botão Jogar

    pygame.key.start_text_input()

    rodando = True
    resultado_nome = None

    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

    while rodando:
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.key.stop_text_input()
                return None

            elif evento.type == pygame.TEXTINPUT:
                # LIMITE ABSOLUTO DE 10 CARACTERES
                if len(nome) < 10 and opcao_selecionada == 0:
                    char = evento.text
                    if char.isalnum() or char in (' ', '_', '-'):
                        nome += char

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_BACKSPACE:
                    nome = nome[:-1]
                elif evento.key == pygame.K_ESCAPE:
                    pygame.key.stop_text_input()
                    return None
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if 1 <= len(nome.strip()) <= 10:
                        resultado_nome = nome.strip()
                        rodando = False
                elif evento.key in (pygame.K_DOWN, pygame.K_TAB):
                    opcao_selecionada = 1
                elif evento.key == pygame.K_UP:
                    opcao_selecionada = 0

        # Lê entradas de Hardware (Joystick / Botões Arcade)
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0 and (agora - tempo_ultimo_input > 0.3):
            pygame.key.stop_text_input()
            return None

        if agora - tempo_ultimo_input > 0.22:
            if joy_y > 700:
                opcao_selecionada = 1
                tempo_ultimo_input = agora
            elif joy_y < 300:
                opcao_selecionada = 0
                tempo_ultimo_input = agora

        if btn_tiro == 0 and (agora - tempo_ultimo_input > 0.3):
            tempo_ultimo_input = agora
            if opcao_selecionada == 1 and (1 <= len(nome.strip()) <= 10):
                resultado_nome = nome.strip()
                rodando = False

        # --- RENDERIZAÇÃO RETRO ---
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))

        modal_rect = pygame.Rect(160, 110, 480, 380)
        pygame.draw.rect(tela, COR_MODAL_BG, modal_rect, border_radius=12)
        pygame.draw.rect(tela, COR_NEON_AZUL, modal_rect, width=3, border_radius=12)
        pygame.draw.rect(tela, COR_NEON_ROSA, (165, 115, 470, 370), width=1, border_radius=10)

        # Cabeçalho
        txt_tit = fonte_titulo.render("★ DIGITE SEU NOME ★", True, COR_NEON_AMARELO)
        tela.blit(txt_tit, (LARGURA // 2 - txt_tit.get_width() // 2, 135))

        txt_dica1 = fonte_sub.render("NOME OBRIGATÓRIO (MÁXIMO 10 CARACTERES)", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica1, (LARGURA // 2 - txt_dica1.get_width() // 2, 172))

        # Campo Input
        input_rect = pygame.Rect(210, 210, 380, 58)
        cor_borda_input = COR_NEON_VERDE if opcao_selecionada == 0 else COR_TEXTO_MUTED
        pygame.draw.rect(tela, (10, 8, 20), input_rect, border_radius=8)
        pygame.draw.rect(tela, cor_borda_input, input_rect, width=2, border_radius=8)

        # Texto do Nome + Cursor
        texto_exibido = nome + ("_" if (int(agora * 2.5) % 2 == 0 and opcao_selecionada == 0) else "")
        txt_nome = fonte_input.render(texto_exibido if texto_exibido else "_", True, (255, 255, 255) if nome else COR_TEXTO_MUTED)
        tela.blit(txt_nome, (input_rect.x + 20, input_rect.y + 12))

        # Indicador de Caracteres (ex: 5/10)
        txt_counter = fonte_sub.render(f"{len(nome)}/10", True, COR_NEON_AMARELO if len(nome) == 10 else COR_TEXTO_MUTED)
        tela.blit(txt_counter, (input_rect.right - 45, input_rect.bottom + 6))

        # Botão [ JOGAR ]
        pode_jogar = (1 <= len(nome.strip()) <= 10)
        btn_rect = pygame.Rect(260, 310, 280, 55)

        if pode_jogar:
            if opcao_selecionada == 1:
                cor_btn_bg = (0, 180, 90)
                cor_btn_borda = COR_NEON_VERDE
                cor_btn_txt = (255, 255, 255)
            else:
                cor_btn_bg = (20, 80, 40)
                cor_btn_borda = COR_NEON_VERDE
                cor_btn_txt = COR_NEON_VERDE
        else:
            cor_btn_bg = (25, 25, 35)
            cor_btn_borda = COR_TEXTO_DESABILITADO
            cor_btn_txt = COR_TEXTO_DESABILITADO

        pygame.draw.rect(tela, cor_btn_bg, btn_rect, border_radius=8)
        pygame.draw.rect(tela, cor_btn_borda, btn_rect, width=2, border_radius=8)

        txt_btn = fonte_btn.render("🎮  INICIAR JOGO", True, cor_btn_txt)
        tela.blit(txt_btn, (LARGURA // 2 - txt_btn.get_width() // 2, btn_rect.y + 14))

        # Dica / Status
        if not pode_jogar:
            txt_bloqueio = fonte_sub.render("⚠️ DIGITE DE 1 A 10 CARACTERES PARA LIBERAR", True, COR_NEON_ROSA)
            tela.blit(txt_bloqueio, (LARGURA // 2 - txt_bloqueio.get_width() // 2, 385))
        else:
            txt_ok = fonte_sub.render("PRESSIONE ENTER OU BOTÃO DE TIRO PARA JOGAR", True, COR_NEON_VERDE)
            tela.blit(txt_ok, (LARGURA // 2 - txt_ok.get_width() // 2, 385))

        txt_esc = fonte_sub.render("[ESC / MENU] VOLTAR AO LAUNCHER", True, COR_TEXTO_MUTED)
        tela.blit(txt_esc, (LARGURA // 2 - txt_esc.get_width() // 2, 435))

        pygame.display.flip()
        relogio.tick(60)

    pygame.key.stop_text_input()
    return resultado_nome
