import pygame
import sys
import time
from core.arduino_controller import conectar_arduino, ler_hardware, enviar_comando

def rodar_teste():
    pygame.init()
    LARGURA, ALTURA = 900, 650
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("TESTADOR DE CONTROLES - ARDUINO & PYTHON")
    relogio = pygame.time.Clock()

    # Tenta conectar ao Arduino
    arduino = conectar_arduino()

    # Cores (Palette dark moderna)
    COR_FUNDO = (18, 20, 28)
    COR_CARD = (28, 32, 45)
    COR_BORDA = (45, 52, 70)
    COR_TEXTO = (230, 235, 245)
    COR_SUBTEXTO = (150, 160, 180)
    COR_VERDE = (46, 204, 113)
    COR_VERMELHO = (231, 76, 60)
    COR_AZUL = (52, 152, 219)
    COR_AMARELO = (241, 196, 15)

    fonte_titulo = pygame.font.SysFont('Consolas', 26, bold=True)
    fonte_sub = pygame.font.SysFont('Consolas', 18, bold=True)
    fonte_normal = pygame.font.SysFont('Consolas', 15)

    btn_t_rect = pygame.Rect(50, 520, 240, 50)
    btn_m_rect = pygame.Rect(330, 520, 240, 50)
    btn_e_rect = pygame.Rect(610, 520, 240, 50)

    ultimo_log = "Eixos X e Y trocados para corresponder ao alinhamento físico do Joystick."

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif evento.key == pygame.K_t:
                    enviar_comando(arduino, 'T')
                    ultimo_log = "Comando 'T' enviado (Som de Tiro)."
                elif evento.key == pygame.K_m:
                    enviar_comando(arduino, 'M')
                    ultimo_log = "Comando 'M' enviado (Acende LED + Som Morte)."
                elif evento.key == pygame.K_e:
                    enviar_comando(arduino, 'E')
                    ultimo_log = "Comando 'E' enviado (Fanfarra Vitória + LED)."
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if btn_t_rect.collidepoint(evento.pos):
                    enviar_comando(arduino, 'T')
                    ultimo_log = "Clique: Comando 'T' (Som Tiro)."
                elif btn_m_rect.collidepoint(evento.pos):
                    enviar_comando(arduino, 'M')
                    ultimo_log = "Clique: Comando 'M' (Acende LED + Som Morte)."
                elif btn_e_rect.collidepoint(evento.pos):
                    enviar_comando(arduino, 'E')
                    ultimo_log = "Clique: Comando 'E' (Fanfarra Vitória)."

        # Leitura dos dados de controle (Eixos X/Y invertidos)
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        tela.fill(COR_FUNDO)

        # Header
        pygame.draw.rect(tela, COR_CARD, (30, 20, 840, 70), border_radius=10)
        pygame.draw.rect(tela, COR_BORDA, (30, 20, 840, 70), width=2, border_radius=10)

        txt_titulo = fonte_titulo.render("TESTADOR DE CONTROLES ARCADE", True, COR_TEXTO)
        tela.blit(txt_titulo, (50, 32))

        if arduino:
            txt_status = fonte_sub.render(f"● CONECTADO ({arduino.port})", True, COR_VERDE)
        else:
            txt_status = fonte_sub.render("● EMULAÇÃO (TECLADO)", True, COR_AMARELO)
        tela.blit(txt_status, (600, 42))

        # CARD 1: VISUALIZADOR DO JOYSTICK
        pygame.draw.rect(tela, COR_CARD, (30, 110, 400, 380), border_radius=10)
        pygame.draw.rect(tela, COR_BORDA, (30, 110, 400, 380), width=2, border_radius=10)

        lbl_joy = fonte_sub.render("JOYSTICK (EIXOS X/Y INVERTIDOS)", True, COR_AZUL)
        tela.blit(lbl_joy, (50, 125))

        box_cx, box_cy = 230, 290
        box_tam = 200
        pygame.draw.rect(tela, (15, 18, 25), (box_cx - box_tam//2, box_cy - box_tam//2, box_tam, box_tam), border_radius=8)
        pygame.draw.rect(tela, COR_BORDA, (box_cx - box_tam//2, box_cy - box_tam//2, box_tam, box_tam), width=1, border_radius=8)
        
        pygame.draw.line(tela, (40, 45, 60), (box_cx, box_cy - box_tam//2), (box_cx, box_cy + box_tam//2), 1)
        pygame.draw.line(tela, (40, 45, 60), (box_cx - box_tam//2, box_cy), (box_cx + box_tam//2, box_cy), 1)

        dot_x = box_cx - box_tam//2 + int((joy_x / 1023.0) * box_tam)
        dot_y = box_cy - box_tam//2 + int((joy_y / 1023.0) * box_tam)
        dot_x = max(box_cx - box_tam//2 + 5, min(box_cx + box_tam//2 - 5, dot_x))
        dot_y = max(box_cy - box_tam//2 + 5, min(box_cy + box_tam//2 - 5, dot_y))

        pygame.draw.circle(tela, COR_VERDE, (dot_x, dot_y), 10)
        pygame.draw.circle(tela, (255, 255, 255), (dot_x, dot_y), 4)

        dir_x = "ESQUERDA" if joy_x < 300 else ("DIREITA" if joy_x > 700 else "CENTRO")
        dir_y = "CIMA" if joy_y < 300 else ("BAIXO" if joy_y > 700 else "CENTRO")

        txt_val_x = fonte_normal.render(f"Eixo X (Mapped): {joy_x:4d} [{dir_x}]", True, COR_TEXTO)
        txt_val_y = fonte_normal.render(f"Eixo Y (Mapped): {joy_y:4d} [{dir_y}]", True, COR_TEXTO)
        tela.blit(txt_val_x, (50, 415))
        tela.blit(txt_val_y, (50, 445))

        # CARD 2: BOTÕES DIGITAIS
        pygame.draw.rect(tela, COR_CARD, (450, 110, 420, 380), border_radius=10)
        pygame.draw.rect(tela, COR_BORDA, (450, 110, 420, 380), width=2, border_radius=10)

        lbl_btn = fonte_sub.render("BOTÕES DIGITAIS", True, COR_AZUL)
        tela.blit(lbl_btn, (470, 125))

        tiro_press = (btn_tiro == 0)
        cor_tiro = COR_VERDE if tiro_press else (60, 65, 80)
        pygame.draw.rect(tela, (20, 24, 35), (470, 165, 380, 110), border_radius=8)
        pygame.draw.circle(tela, cor_tiro, (510, 220), 24)
        lbl_tiro_name = fonte_sub.render("BOTÃO DE TIRO (Pino D3)", True, COR_TEXTO)
        lbl_tiro_st = fonte_normal.render(f"Estado: {'PRESSIONADO (0)' if tiro_press else 'SOLTO (1)'}", True, COR_VERDE if tiro_press else COR_SUBTEXTO)
        lbl_tiro_keys = fonte_normal.render("Teclado: ESPAÇO / ENTER / Z", True, COR_SUBTEXTO)
        tela.blit(lbl_tiro_name, (550, 180))
        tela.blit(lbl_tiro_st, (550, 205))
        tela.blit(lbl_tiro_keys, (550, 230))

        menu_press = (btn_menu == 0)
        cor_menu = COR_VERMELHO if menu_press else (60, 65, 80)
        pygame.draw.rect(tela, (20, 24, 35), (470, 300, 380, 110), border_radius=8)
        pygame.draw.circle(tela, cor_menu, (510, 355), 24)
        lbl_menu_name = fonte_sub.render("BOTÃO MENU / SW (Pino D2)", True, COR_TEXTO)
        lbl_menu_st = fonte_normal.render(f"Estado: {'PRESSIONADO (0)' if menu_press else 'SOLTO (1)'}", True, COR_VERMELHO if menu_press else COR_SUBTEXTO)
        lbl_menu_keys = fonte_normal.render("Teclado: ESC / BACKSPACE", True, COR_SUBTEXTO)
        tela.blit(lbl_menu_name, (550, 315))
        tela.blit(lbl_menu_st, (550, 340))
        tela.blit(lbl_menu_keys, (550, 365))

        # CARD 3: TESTAR SAÍDAS
        pygame.draw.rect(tela, COR_CARD, (30, 505, 840, 80), border_radius=10)
        pygame.draw.rect(tela, COR_BORDA, (30, 505, 840, 80), width=2, border_radius=10)

        pygame.draw.rect(tela, COR_AZUL, btn_t_rect, border_radius=6)
        txt_btn_t = fonte_normal.render("[T] TESTAR TIRO", True, COR_TEXTO)
        tela.blit(txt_btn_t, (btn_t_rect.centerx - txt_btn_t.get_width()//2, btn_t_rect.centery - 8))

        pygame.draw.rect(tela, COR_AMARELO, btn_m_rect, border_radius=6)
        txt_btn_m = fonte_normal.render("[M] IMPACTO (LED)", True, (20, 20, 20))
        tela.blit(txt_btn_m, (btn_m_rect.centerx - txt_btn_m.get_width()//2, btn_m_rect.centery - 8))

        pygame.draw.rect(tela, COR_VERDE, btn_e_rect, border_radius=6)
        txt_btn_e = fonte_normal.render("[E] TESTAR VI TÓRIA", True, (20, 20, 20))
        tela.blit(txt_btn_e, (btn_e_rect.centerx - txt_btn_e.get_width()//2, btn_e_rect.centery - 8))

        txt_log = fonte_normal.render(f"Log: {ultimo_log}", True, COR_SUBTEXTO)
        tela.blit(txt_log, (40, 600))

        pygame.display.flip()
        relogio.tick(60)

    if arduino:
        arduino.close()
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    rodar_teste()
