import pygame
import math
import os

def rodar_jogo(tela, relogio, arduino, ler_hardware):
    LARGURA, ALTURA = 800, 600
    
    # Cores de fundo e paredes
    COR_FUNDO = (80, 50, 20)      # Marrom Atari
    COR_PAREDE = (0, 150, 0)      # Verde musgo
    COR_CASTELO = (180, 180, 180) # Cinza
    
    # --- CARREGAMENTO DE IMAGENS PERSONALIZADAS (PNG) ---
    diretorio = os.path.dirname(__file__)
    
    try:
        img_player = pygame.image.load(os.path.join(diretorio, "player.png")).convert_alpha()
        img_player = pygame.transform.scale(img_player, (24, 24))
        
        img_dragao = pygame.image.load(os.path.join(diretorio, "dragao.png")).convert_alpha()
        img_dragao = pygame.transform.scale(img_dragao, (40, 40))
        
        img_chave = pygame.image.load(os.path.join(diretorio, "chave.png")).convert_alpha()
        img_chave = pygame.transform.scale(img_chave, (30, 20))
        
        img_calice = pygame.image.load(os.path.join(diretorio, "calice.png")).convert_alpha()
        img_calice = pygame.transform.scale(img_calice, (25, 30))
    except Exception as e:
        print(f"Erro ao carregar imagens PNG em 2_labirinto: {e}")
        print("Certifique-se de salvar os arquivos player.png, dragao.png, chave.png e calice.png na pasta.")
        return

    # Estado do Jogador
    px, py = 100, 450             
    tamanho_jogador = 24          
    tem_chave = False
    tem_calice = False
    tem_pixel_secreto = False     
    easter_egg_revelado = False
    venceu = False
    
    # Estado do Dragão (Inimigo Inteligente)
    dx, dy = 600, 400             # Posição inicial do Dragão
    vel_dragao = 2                # Velocidade de perseguição
    
    # Definição das Paredes Estáticas
    paredes = [
        pygame.Rect(0, 0, LARGURA, 20),
        pygame.Rect(0, 0, 20, ALTURA),
        pygame.Rect(0, ALTURA - 20, LARGURA, 20),
        pygame.Rect(LARGURA - 20, 0, 20, ALTURA),
        
        pygame.Rect(200, 150, 20, 450),
        pygame.Rect(200, 150, 400, 20),
        pygame.Rect(400, 300, 20, 300),
        pygame.Rect(400, 300, 250, 20),
    ]
    
    castelo_trancado = pygame.Rect(40, 100, 100, 80)
    pos_chave = pygame.Rect(700, 500, 30, 20)
    pos_calice = pygame.Rect(85, 125, 25, 30)
    pixel_secreto_rect = pygame.Rect(215, 140, 6, 6) 
    parede_falsa = pygame.Rect(650, 20, 130, 20)
    
    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware()

        if btn_menu == 0:
            rodando = False
            pygame.time.wait(300)
            break

        if not venceu:
            # --- MOVIMENTAÇÃO DO JOGADOR ---
            antigo_x, antigo_y = px, py
            if joy_x < 300: px -= 5
            elif joy_x > 700: px += 5
            if joy_y < 300: py -= 5
            elif joy_y > 800: py += 5
            
            jogador_rect = pygame.Rect(px, py, tamanho_jogador, tamanho_jogador)
            
            # Colisão Jogador vs Paredes
            for parede in paredes:
                if jogador_rect.colliderect(parede): px, py = antigo_x, antigo_y
            if not easter_egg_revelado and jogador_rect.colliderect(parede_falsa): px, py = antigo_x, antigo_y
            
            if castelo_trancado and jogador_rect.colliderect(castelo_trancado):
                if tem_chave:
                    castelo_trancado = None
                    if arduino: arduino.write(b'M')
                else: px, py = antigo_x, antigo_y
            
            jogador_rect = pygame.Rect(px, py, tamanho_jogador, tamanho_jogador)

            # --- INTELIGÊNCIA ARTIFICIAL DO DRAGÃO ---
            # O dragão persegue as coordenadas do jogador de forma suave
            antigo_dx, antiguo_dy = dx, dy
            if dx < px: dx += vel_dragao
            elif dx > px: dx -= vel_dragao
            if dy < py: dy += vel_dragao
            elif dy > py: dy -= vel_dragao
            
            dragao_rect = pygame.Rect(dx, dy, 40, 40)
            
            # O Dragão também respeita as paredes do labirinto
            for parede in paredes:
                if dragao_rect.colliderect(parede): dx, dy = antigo_dx, antiguo_dy
            if castelo_trancado and dragao_rect.colliderect(castelo_trancado): dx, dy = antigo_dx, antiguo_dy

            # Colisão fatal: Se o Dragão te pegar, você volta pro início do labirinto!
            if jogador_rect.colliderect(dragao_rect):
                px, py = 100, 450 # Reseta posição do herói
                if arduino: arduino.write(b'M') # Som de dano

            # --- COLETÁVEIS E REGRAS ---
            if not tem_chave and jogador_rect.colliderect(pos_chave):
                tem_chave = True
                if arduino: arduino.write(b'T')
                
            if castelo_trancado is None and not tem_calice and jogador_rect.colliderect(pos_calice):
                tem_calice = True
                venceu = True
                if arduino: arduino.write(b'E')
                
            if not tem_pixel_secreto and jogador_rect.colliderect(pixel_secreto_rect):
                tem_pixel_secreto = True
                if arduino: arduino.write(b'T')
                
            if tem_pixel_secreto and not easter_egg_revelado:
                distancia_corredor = math.hypot(px - 700, py - 60)
                if distancia_corredor < 60:
                    easter_egg_revelado = True
                    venceu = True
                    if arduino: arduino.write(b'E')

        # --- RENDERIZAÇÃO GRÁFICA (Sprites + Formas) ---
        tela.fill(COR_FUNDO)
        
        # Desenha estruturas de bloco
        for parede in paredes: pygame.draw.rect(tela, COR_PAREDE, parede)
        if not easter_egg_revelado: pygame.draw.rect(tela, COR_PAREDE, parede_falsa)
        if castelo_trancado:
            pygame.draw.rect(tela, COR_CASTELO, castelo_trancado)
            pygame.draw.rect(tela, COR_FUNDO, (70, 140, 40, 40)) # Porta
            
        # Desenha os Sprites PNG carregados
        if not tem_chave:
            tela.blit(img_chave, (pos_chave.x, pos_chave.y))
            
        if castelo_trancado is None and not tem_calice:
            tela.blit(img_calice, (pos_calice.x, pos_calice.y))
            
        if not venceu:
            tela.blit(img_dragao, (dx, dy)) # Desenha o dragão pato na tela
            
        if not tem_pixel_secreto:
            pygame.draw.rect(tela, COR_FUNDO, pixel_secreto_rect) # Pixel invisível
            
        # Desenha o Herói Customizado
        tela.blit(img_player, (px, py))
        
        # Efeito da chave flutuando acima do jogador
        if tem_chave and not tem_calice:
            tela.blit(img_chave, (px - 3, py - 25))

        # --- TELAS DE VITÓRIA ---
        fonte = pygame.font.SysFont('Consolas', 32, bold=True)
        if venceu:
            if easter_egg_revelado:
                tela.fill((0, 0, 0))
                tempo_pisca = pygame.time.get_ticks() // 200
                cor_secreta = (255, 215, 0) if tempo_pisca % 2 == 0 else (0, 255, 255)
                
                txt1 = fonte.render("PARABÉNS, JOGADOR NÚMERO 1!", True, cor_secreta)
                txt2 = fonte.render("VOCÊ ENCONTROU O EASTER EGG!", True, (255, 255, 255))
                txt3 = fonte.render("CRIADO POR: WARREN ROBINETT", True, (0, 255, 0))
                
                tela.blit(txt1, (LARGURA//2 - txt1.get_width()//2, 200))
                tela.blit(txt2, (LARGURA//2 - txt2.get_width()//2, 280))
                tela.blit(txt3, (LARGURA//2 - txt3.get_width()//2, 360))
            else:
                txt_vitoria = fonte.render("CÁLICE RECUPERADO! VOCÊ VENCEU!", True, (255, 215, 0))
                tela.blit(txt_vitoria, (LARGURA//2 - txt_vitoria.get_width()//2, ALTURA//2))
                
            txt_voltar = fonte.render("[CLIQUE NO ANALÓGICO PARA VOLTAR]", True, (150, 150, 150))
            tela.blit(txt_voltar, (LARGURA//2 - txt_voltar.get_width()//2, ALTURA - 80))

        pygame.display.flip()
        relogio.tick(60)
