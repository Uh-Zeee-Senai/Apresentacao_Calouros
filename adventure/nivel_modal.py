import pygame
import time

def selecionar_nivel_adventure(tela, relogio, arduino, ler_hardware):
    """
    Exibe a modal retro para seleção do Nível de Dificuldade do Adventure (1, 2 ou 3).
    - Nível 1: Introdução (Reino menor, 2 dragões, sem morcego, objetos fixos)
    - Nível 2: Adventure Completo (3 castelos, 3 dragões, morcego, ponte, ímã, ZéCreppe)
    - Nível 3: Adventure Aleatório (Mesmo reino do nível 2 com itens e inimigos embaralhados)
    """
    LARGURA, ALTURA = 800, 600

    COR_MODAL_BG = (18, 16, 32)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_VERDE = (0, 255, 120)
    COR_NEON_AMARELO = (255, 230, 0)
    COR_TEXTO_MUTED = (140, 150, 180)

    fonte_titulo = pygame.font.SysFont('Consolas', 24, bold=True)
    fonte_opcao_tit = pygame.font.SysFont('Consolas', 18, bold=True)
    fonte_opcao_desc = pygame.font.SysFont('Consolas', 12)
    fonte_sub = pygame.font.SysFont('Consolas', 13)

    opcoes_nivel = [
        {
            'nivel': 1,
            'titulo': 'NÍVEL 1 — INTRODUÇÃO',
            'desc': 'Reino menor, 2 dragões (Yorgle & Grundle), sem morcego, itens em posições fixas.'
        },
        {
            'nivel': 2,
            'titulo': 'NÍVEL 2 — ADVENTURE COMPLETO',
            'desc': 'Mundo completo (3 Castelos, 3 Dragões, Morcego, Ponte, Ímã, ZéCreppe Easter Egg).'
        },
        {
            'nivel': 3,
            'titulo': 'NÍVEL 3 — ALEATÓRIO (HARDCORE)',
            'desc': 'Mundo completo com itens, dragões e morcego em posições 100% aleatórias!'
        }
    ]

    opcao_selecionada = 1  # Padrão: Nível 2 (Adventure Completo)
    tempo_ultimo_input = time.time()

    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    rodando = True

    while rodando:
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return None
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_UP, pygame.K_w):
                    opcao_selecionada = (opcao_selecionada - 1) % len(opcoes_nivel)
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    opcao_selecionada = (opcao_selecionada + 1) % len(opcoes_nivel)
                elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return opcoes_nivel[opcao_selecionada]['nivel']
                elif evento.key == pygame.K_ESCAPE:
                    return None

        # Lê hardware
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0 and (agora - tempo_ultimo_input > 0.3):
            return None

        if agora - tempo_ultimo_input > 0.22:
            if joy_y < 300:
                opcao_selecionada = (opcao_selecionada - 1) % len(opcoes_nivel)
                tempo_ultimo_input = agora
            elif joy_y > 700:
                opcao_selecionada = (opcao_selecionada + 1) % len(opcoes_nivel)
                tempo_ultimo_input = agora

        if btn_tiro == 0 and (agora - tempo_ultimo_input > 0.3):
            tempo_ultimo_input = agora
            return opcoes_nivel[opcao_selecionada]['nivel']

        # --- RENDERIZAÇÃO RETRO ---
        overlay.fill((0, 0, 0, 195))
        tela.blit(overlay, (0, 0))

        modal_rect = pygame.Rect(110, 80, 580, 440)
        pygame.draw.rect(tela, COR_MODAL_BG, modal_rect, border_radius=12)
        pygame.draw.rect(tela, COR_NEON_AZUL, modal_rect, width=3, border_radius=12)
        pygame.draw.rect(tela, COR_NEON_ROSA, (115, 85, 570, 430), width=1, border_radius=10)

        # Cabeçalho
        txt_tit = fonte_titulo.render("⚔️ SELECIONE A DIFICULDADE (ATARI 2600) ⚔️", True, COR_NEON_AMARELO)
        tela.blit(txt_tit, (LARGURA // 2 - txt_tit.get_width() // 2, 105))

        txt_dica1 = fonte_sub.render("Escolha o nível de exploração e desafio do reino", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica1, (LARGURA // 2 - txt_dica1.get_width() // 2, 140))

        # Lista de Cards dos Níveis
        y_base = 175
        card_w, card_h = 520, 85

        for i, opt in enumerate(opcoes_nivel):
            y_pos = y_base + i * 95
            selecionado = (i == opcao_selecionada)

            card_x = LARGURA // 2 - card_w // 2
            card_rect = pygame.Rect(card_x, y_pos, card_w, card_h)

            if selecionado:
                cor_bg = (38, 22, 58)
                cor_borda = COR_NEON_VERDE
                cor_txt_t = COR_NEON_VERDE
                cor_txt_d = (220, 240, 220)
            else:
                cor_bg = (14, 12, 26)
                cor_borda = (50, 45, 75)
                cor_txt_t = (210, 215, 230)
                cor_txt_d = COR_TEXTO_MUTED

            pygame.draw.rect(tela, cor_bg, card_rect, border_radius=8)
            pygame.draw.rect(tela, cor_borda, card_rect, width=2 if selecionado else 1, border_radius=8)

            txt_ot = fonte_opcao_tit.render(opt['titulo'], True, cor_txt_t)
            txt_od = fonte_opcao_desc.render(opt['desc'], True, cor_txt_d)

            tela.blit(txt_ot, (card_x + 20, y_pos + 14))
            tela.blit(txt_od, (card_x + 20, y_pos + 46))

        txt_instrucao = fonte_sub.render("JOYSTICK Y / W-S: NAVEGAR  |  BOTÃO DE TIRO / ENTER: SELECIONAR", True, COR_NEON_AMARELO)
        tela.blit(txt_instrucao, (LARGURA // 2 - txt_instrucao.get_width() // 2, 475))

        pygame.display.flip()
        relogio.tick(60)

    return None
