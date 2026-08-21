import pygame
import time
from core.database import (
    obter_ranking_space_invaders,
    obter_vencedores_originais_adventure,
    obter_vencedores_normais_adventure
)

def exibir_rankings(tela, relogio, arduino, ler_hardware):
    """
    Exibe a tela de Rankings com abas interativas no estilo Arcade Retro Neon 80s:
    1. 🏆 Vencedores Originais (Adventure - Boss ZéCreppe)
    2. 🚀 Space Invaders (Top 20 Pontuação)
    3. 🐉 Adventure (Vitórias Normais)
    """
    LARGURA, ALTURA = 800, 600

    COR_FUNDO = (10, 8, 20)
    COR_NEON_ROSA = (255, 0, 128)
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_AMARELO = (255, 215, 0)
    COR_NEON_VERDE = (0, 255, 120)
    COR_TEXTO_MUTED = (140, 150, 180)
    COR_TAB_INATIVA = (25, 20, 40)

    fonte_titulo = pygame.font.SysFont('Consolas', 26, bold=True)
    fonte_tab = pygame.font.SysFont('Consolas', 15, bold=True)
    fonte_cabecalho = pygame.font.SysFont('Consolas', 16, bold=True)
    fonte_linha = pygame.font.SysFont('Consolas', 15)
    fonte_sub = pygame.font.SysFont('Consolas', 13)

    aba_atual = 0  # 0 = Vencedores Originais, 1 = Space Invaders, 2 = Adventure Normal
    abas = [
        "🏆 VENCEDORES ORIGINAIS (BOSS ZÉCREPPE)",
        "🚀 SPACE INVADERS (TOP 20)",
        "🐉 ADVENTURE (NORMAL)"
    ]

    tempo_ultima_troca = time.time()
    rodando = True

    while rodando:
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    rodando = False
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    aba_atual = (aba_atual - 1) % len(abas)
                elif evento.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                    aba_atual = (aba_atual + 1) % len(abas)

        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0 and (agora - tempo_ultima_troca > 0.3):
            rodando = False
            break

        # Troca de Abas pelo Joystick X
        if agora - tempo_ultima_troca > 0.25:
            if joy_x < 300:
                aba_atual = (aba_atual - 1) % len(abas)
                tempo_ultima_troca = agora
            elif joy_x > 700:
                aba_atual = (aba_atual + 1) % len(abas)
                tempo_ultima_troca = agora

        # --- RENDERIZAÇÃO RETRO CRT ---
        tela.fill(COR_FUNDO)

        # Scanlines
        for y in range(0, ALTURA, 4):
            pygame.draw.line(tela, (16, 14, 30), (0, y), (LARGURA, y), 1)

        # Moldura Externa Retro
        pygame.draw.rect(tela, COR_NEON_ROSA, (15, 12, 770, 576), width=2, border_radius=6)
        pygame.draw.rect(tela, COR_NEON_AZUL, (20, 17, 760, 566), width=1, border_radius=4)

        # Banner do Título
        txt_titulo = fonte_titulo.render("🏆 HALL DA FAMA & RANKINGS 🏆", True, COR_NEON_AMARELO)
        tela.blit(txt_titulo, (LARGURA // 2 - txt_titulo.get_width() // 2, 28))

        # --- DESENHO DAS ABAS ---
        largura_tab = 240
        x_inicio_tabs = 35

        for i, tab_nome in enumerate(abas):
            x_tab = x_inicio_tabs + i * 248
            y_tab = 70
            ativa = (i == aba_atual)

            if ativa:
                cor_bg = (40, 25, 60)
                cor_borda = COR_NEON_AMARELO if i == 0 else COR_NEON_AZUL
                cor_txt = COR_NEON_AMARELO if i == 0 else COR_NEON_AZUL
            else:
                cor_bg = COR_TAB_INATIVA
                cor_borda = (50, 45, 70)
                cor_txt = COR_TEXTO_MUTED

            pygame.draw.rect(tela, cor_bg, (x_tab, y_tab, largura_tab, 38), border_radius=6)
            pygame.draw.rect(tela, cor_borda, (x_tab, y_tab, largura_tab, 38), width=2 if ativa else 1, border_radius=6)

            txt_t = fonte_tab.render(tab_nome, True, cor_txt)
            tela.blit(txt_t, (x_tab + largura_tab // 2 - txt_t.get_width() // 2, y_tab + 10))

        # --- CONTEÚDO DA TABELA ---
        painel_rect = pygame.Rect(35, 120, 730, 400)
        pygame.draw.rect(tela, (14, 12, 24), painel_rect, border_radius=8)
        pygame.draw.rect(tela, COR_NEON_AZUL, painel_rect, width=1, border_radius=8)

        # Cabeçalho da Tabela
        pygame.draw.rect(tela, (25, 20, 42), (35, 120, 730, 36), border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.line(tela, COR_NEON_ROSA, (35, 156), (765, 156), 2)

        if aba_atual == 0:
            col1, col2, col3, col4 = "POS", "VENCEDOR ORIGINAL", "TEMPO", "DATA / HORA"
            dados = obter_vencedores_originais_adventure(limit=10)
        elif aba_atual == 1:
            col1, col2, col3, col4 = "POS", "JOGADOR", "PONTUAÇÃO", "DATA / HORA"
            dados = obter_ranking_space_invaders(limit=20)
        else:
            col1, col2, col3, col4 = "POS", "JOGADOR", "TEMPO", "DATA / HORA"
            dados = obter_vencedores_normais_adventure(limit=10)

        txt_c1 = fonte_cabecalho.render(col1, True, COR_NEON_VERDE)
        txt_c2 = fonte_cabecalho.render(col2, True, COR_NEON_VERDE)
        txt_c3 = fonte_cabecalho.render(col3, True, COR_NEON_VERDE)
        txt_c4 = fonte_cabecalho.render(col4, True, COR_NEON_VERDE)

        tela.blit(txt_c1, (60, 128))
        tela.blit(txt_c2, (150, 128))
        tela.blit(txt_c3, (440, 128))
        tela.blit(txt_c4, (600, 128))

        # Linhas de Registros
        if not dados:
            txt_vazio = fonte_linha.render("NENHUM REGISTRO ENCONTRADO AINDA. SEJA O PRIMEIRA A JOGAR!", True, COR_TEXTO_MUTED)
            tela.blit(txt_vazio, (LARGURA // 2 - txt_vazio.get_width() // 2, 280))
        else:
            y_linha = 170
            for item in dados[:10]: # Exibe até 10 por página visível
                pos = item['posicao']
                nome = item['nome']
                val_col3 = str(item.get('pontuacao') if aba_atual == 1 else item.get('tempo'))
                data_str = item['data']

                # Cor da Posição
                if pos == 1:
                    cor_pos = COR_NEON_AMARELO
                    badge = "🥇 "
                elif pos == 2:
                    cor_pos = (220, 220, 220)
                    badge = "🥈 "
                elif pos == 3:
                    cor_pos = (205, 127, 50)
                    badge = "🥉 "
                else:
                    cor_pos = COR_TEXTO_MUTED
                    badge = "   "

                if aba_atual == 0:
                    cor_nome = COR_NEON_AMARELO
                else:
                    cor_nome = (255, 255, 255)

                t_pos = fonte_linha.render(f"{badge}{pos}º", True, cor_pos)
                t_nome = fonte_linha.render(nome[:18], True, cor_nome)
                t_val = fonte_linha.render(val_col3, True, COR_NEON_VERDE if aba_atual == 1 else COR_NEON_AZUL)
                t_data = fonte_sub.render(data_str[:16], True, COR_TEXTO_MUTED)

                tela.blit(t_pos, (55, y_linha))
                tela.blit(t_nome, (150, y_linha))
                tela.blit(t_val, (440, y_linha))
                tela.blit(t_data, (600, y_linha + 2))

                # Linha divisória sutil
                pygame.draw.line(tela, (25, 22, 45), (45, y_linha + 28), (755, y_linha + 28), 1)
                y_linha += 34

        # Rodapé de Instruções
        txt_dica = fonte_sub.render("JOYSTICK X / ◄ ►: ALTERNAR ABAS  |  ESC / MENU: VOLTAR AO LAUNCHER", True, COR_TEXTO_MUTED)
        tela.blit(txt_dica, (LARGURA // 2 - txt_dica.get_width() // 2, 540))

        pygame.display.flip()
        relogio.tick(60)
