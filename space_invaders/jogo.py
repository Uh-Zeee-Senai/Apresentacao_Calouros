import pygame
import random

def rodar_jogo(tela, relogio, arduino, ler_hardware):
    LARGURA, ALTURA = 800, 600
    jogador_x = LARGURA // 2
    tiros = []
    aliens = [{"x": random.randint(50, LARGURA-50), "y": random.randint(30, 150)} for _ in range(5)]
    
    rodando = True
    ultimo_btn_tiro = 1

    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

        # Usa a função de leitura que o Main emprestou para o jogo
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware()

        # CONDIÇÃO GLOBAL DE SAÍDA: Apertou o clique do analógico, volta pro Launcher!
        if btn_menu == 0:
            rodando = False
            pygame.time.wait(300)
            break

        # Logica do Space Invaders
        if joy_x < 300: jogador_x = max(25, jogador_x - 7)
        elif joy_x > 700: jogador_x = min(LARGURA - 25, jogador_x + 7)

        if btn_tiro == 0 and ultimo_btn_tiro == 1:
            tiros.append({"x": jogador_x, "y": ALTURA - 60})
            if arduino: arduino.write(b'T') # Envia som de tiro pro Arduino

        ultimo_btn_tiro = btn_tiro

        # Atualiza Tiros e Aliens
        for t in tiros[:]:
            t['y'] -= 10
            if t['y'] < 0: tiros.remove(t)

        for a in aliens[:]:
            a['y'] += 1
            if a['y'] > ALTURA: a['y'] = 0
            for t in tiros[:]:
                if a['x']-20 < t['x'] < a['x']+20 and a['y'] < t['y'] < a['y']+25:
                    aliens.remove(a)
                    if t in tiros: tiros.remove(t)
                    if arduino: arduino.write(b'M') # Som de morte
                    aliens.append({"x": random.randint(50, LARGURA-50), "y": random.randint(30, 150)})

        # Desenhar na tela
        tela.fill((0, 0, 0))
        pygame.draw.rect(tela, (0, 255, 0), (jogador_x - 25, ALTURA - 50, 50, 15)) # Jogador
        for t in tiros: pygame.draw.circle(tela, (255, 255, 0), (t['x'], t['y']), 4) # Tiros
        for a in aliens: pygame.draw.rect(tela, (255, 50, 50), (a['x'] - 20, a['y'], 40, 25)) # Aliens
        
        pygame.display.flip()
        relogio.tick(60)
