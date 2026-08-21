import pygame
import math
import os
import time
import random
from core.arduino_controller import enviar_comando
from core.database import obter_ou_criar_jogador, salvar_partida_adventure

def rodar_jogo(tela, relogio, arduino, ler_hardware, nome_jogador="Anônimo", nivel=2):
    LARGURA, ALTURA = 800, 600

    # Cores Clássicas Atari 2600
    COR_ATARI_BROWN = (80, 50, 20)        # Fundo Castanho
    COR_PAREDE_VERDE = (0, 140, 0)       # Paredes Verde Musgo
    COR_CASTELO_DOURADO = (220, 180, 40) # Castelo Amarelo
    COR_CASTELO_BRANCO = (200, 200, 220)  # Castelo Branco
    COR_CASTELO_NEGRO = (30, 25, 40)     # Castelo Negro
    COR_SALA_SECRETA = (40, 15, 60)      # Roxo Secreto
    COR_NEON_AZUL = (0, 240, 255)
    COR_NEON_ROSA = (255, 0, 128)
    COR_TEXTO_GOLD = (255, 215, 0)

    # --- CARREGAMENTO DE SPRITES DE ADVENTURE ---
    diretorio_sprites = os.path.join(os.path.dirname(__file__), "sprites")

    try:
        img_player = pygame.image.load(os.path.join(diretorio_sprites, "player.png")).convert_alpha()
        img_player = pygame.transform.scale(img_player, (26, 26))

        img_dragao = pygame.image.load(os.path.join(diretorio_sprites, "dragao.png")).convert_alpha()
        img_dragao_yorgle = pygame.transform.scale(img_dragao, (44, 44))
        
        # Copia e tinge dragões verde e vermelho
        img_dragao_grundle = img_dragao_yorgle.copy()
        img_dragao_grundle.fill((50, 255, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
        
        img_dragao_rhindle = img_dragao_yorgle.copy()
        img_dragao_rhindle.fill((255, 60, 60, 255), special_flags=pygame.BLEND_RGBA_MULT)

        img_chave = pygame.image.load(os.path.join(diretorio_sprites, "chave.png")).convert_alpha()
        img_chave_dourada = pygame.transform.scale(img_chave, (30, 20))
        
        img_chave_branca = img_chave_dourada.copy()
        img_chave_branca.fill((230, 230, 250, 255), special_flags=pygame.BLEND_RGBA_MULT)
        
        img_chave_negra = img_chave_dourada.copy()
        img_chave_negra.fill((100, 100, 130, 255), special_flags=pygame.BLEND_RGBA_MULT)

        img_calice = pygame.image.load(os.path.join(diretorio_sprites, "calice.png")).convert_alpha()
        img_calice = pygame.transform.scale(img_calice, (26, 32))

        # Boss Secreto ZéCreppe (Creepinho.png)
        img_boss = pygame.image.load(os.path.join(diretorio_sprites, "Creepinho.png")).convert_alpha()
        img_boss = pygame.transform.scale(img_boss, (52, 52))
    except Exception as e:
        print(f"[Adventure Error] Erro ao carregar imagens em adventure/sprites: {e}")
        return

    # --- DEFINIÇÃO DO MAPA MULTI-SALAS (ATARI 2600 KINGDOM) ---
    salas_nivel_1 = [
        'castelo_dourado_ext', 'castelo_dourado_int', 'campo_inicial',
        'floresta_leste', 'labirinto_1', 'sala_secreta_zecreppe'
    ]

    salas_nivel_2_3 = [
        'castelo_dourado_ext', 'castelo_dourado_int', 'campo_inicial',
        'floresta_leste', 'castelo_branco_ext', 'castelo_branco_int',
        'floresta_sul', 'castelo_negro_ext', 'castelo_negro_int',
        'labirinto_1', 'labirinto_2', 'labirinto_3',
        'catacumbas_1', 'catacumbas_2', 'sala_secreta_zecreppe'
    ]

    salas_disponiveis = salas_nivel_1 if nivel == 1 else salas_nivel_2_3
    sala_atual = 'castelo_dourado_ext'

    # Estado do Jogador
    px, py = 387, 450
    tamanho_jogador = 26
    item_carregado = None  # Regra original de inventário: 1 objeto por vez

    # Trancas dos Castelos
    castelo_dourado_trancado = False  # Portão Dourado começa destrancado no hub
    castelo_branco_trancado = True
    castelo_negro_trancado = True

    # Ponto Secreto no Campo Inicial (Parede Esquerda 10x10 px)
    pixel_secreto_rect = pygame.Rect(20, 280, 10, 10)
    parede_secreta_revelada = False

    # --- OBJETOS DO MUNDO (Sala -> Rect) ---
    itens = {
        'espada': {'sala': 'campo_inicial', 'rect': pygame.Rect(400, 300, 28, 28)},
        'chave_dourada': {'sala': 'floresta_leste', 'rect': pygame.Rect(600, 400, 30, 20)},
        'chave_branca': {'sala': 'labirinto_1', 'rect': pygame.Rect(500, 200, 30, 20)},
        'chave_negra': {'sala': 'catacumbas_1' if nivel > 1 else 'labirinto_1', 'rect': pygame.Rect(300, 300, 30, 20)},
        'calice': {'sala': 'castelo_negro_int' if nivel > 1 else 'labirinto_1', 'rect': pygame.Rect(387, 260, 26, 32)},
        'ponte': {'sala': 'floresta_sul' if nivel > 1 else 'campo_inicial', 'rect': pygame.Rect(250, 400, 45, 14)},
        'ima': {'sala': 'castelo_branco_int' if nivel > 1 else 'floresta_leste', 'rect': pygame.Rect(350, 350, 25, 25)}
    }

    # --- INIMIGOS: 3 DRAGÕES & MORCEGO PRETO ---
    dragões = {
        'yorgle': {'nome': 'Yorgle (Amarelo)', 'sala': 'campo_inicial', 'x': 500.0, 'y': 300.0, 'vel': 1.6, 'vivo': True, 'sprite': img_dragao_yorgle},
        'grundle': {'nome': 'Grundle (Verde)', 'sala': 'floresta_leste', 'x': 200.0, 'y': 200.0, 'vel': 2.4, 'vivo': True, 'sprite': img_dragao_grundle},
        'rhindle': {'nome': 'Rhindle (Vermelho)', 'sala': 'castelo_negro_ext' if nivel > 1 else 'labirinto_1', 'x': 400.0, 'y': 250.0, 'vel': 3.4, 'vivo': (nivel > 1), 'sprite': img_dragao_rhindle}
    }

    # Morcego Preto
    morcego_ativo = (nivel > 1)
    morcego_sala = 'floresta_leste'
    mx, my = 200.0, 150.0
    mdx, mdy = 2.5, 2.0
    morcego_item = None
    tempo_ultimo_roubo = 0.0

    # NÍVEL 3: EMBARALHAMENTO ALEATÓRIO DE ITENS E INIMIGOS A CADA PARTIDA
    if nivel == 3:
        salas_aleatorias = [s for s in salas_disponiveis if s not in ('castelo_dourado_int', 'sala_secreta_zecreppe')]
        for chave_item in itens:
            itens[chave_item]['sala'] = random.choice(salas_aleatorias)
            itens[chave_item]['rect'].x = random.randint(100, 700)
            itens[chave_item]['rect'].y = random.randint(100, 500)

        for d_key in dragões:
            dragões[d_key]['sala'] = random.choice(salas_aleatorias)

    # Boss Secreto ZéCreppe
    boss_hp = 8
    boss_max_hp = 8
    bx, by = 550.0, 260.0
    boss_vel = 2.5
    boss_derrotado = False
    tempo_invulneravel_boss = 0.0

    # Estados de Jogo e Diálogo
    em_dialogo = False
    indice_dialogo = 0
    dialogos_boss = [
        "Então você conseguiu chegar até aqui...",
        "Isso não fazia parte da aventura.",
        "Era um teste especial.",
        "Você derrotou o ZéCreppe!",
        f"Parabéns, {nome_jogador}! Você é um Vencedor Original!"
    ]
    tempo_ultimo_dialogo = 0.0

    venceu_normal = False
    venceu_secret = False
    partida_salva = False
    hero_devorado = False
    tempo_devorado = 0.0

    tempo_inicio = time.time()
    tempo_total_conclusao = 0.0
    tempo_ultimo_ataque = 0.0

    fonte_hud = pygame.font.SysFont('Consolas', 18, bold=True)
    fonte_dialogo = pygame.font.SysFont('Consolas', 20, bold=True)
    fonte_vitoria = pygame.font.SysFont('Consolas', 26, bold=True)

    rodando = True
    while rodando:
        agora = time.time()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif em_dialogo and (evento.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z)):
                    if agora - tempo_ultimo_dialogo > 0.3:
                        tempo_ultimo_dialogo = agora
                        indice_dialogo += 1
                        if indice_dialogo >= len(dialogos_boss):
                            em_dialogo = False
                            venceu_secret = True

        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0 and not em_dialogo:
            rodando = False
            pygame.time.wait(300)
            break

        if em_dialogo:
            if btn_tiro == 0 and (agora - tempo_ultimo_dialogo > 0.35):
                tempo_ultimo_dialogo = agora
                indice_dialogo += 1
                if indice_dialogo >= len(dialogos_boss):
                    em_dialogo = False
                    venceu_secret = True

        # --- SE O JOGADOR FOI DEVORADO (MECÂNICA DE RESPAWN NO CASTELO) ---
        if hero_devorado:
            tela.fill((15, 10, 20))
            txt_dev = fonte_vitoria.render("☠ VOCÊ FOI DEVORADO PELO DRAGÃO! ☠", True, (231, 76, 60))
            tela.blit(txt_dev, (LARGURA // 2 - txt_dev.get_width() // 2, 220))

            txt_resp = fonte_hud.render("Renasceu no Castelo Dourado! Pressione Botão de Tiro para continuar", True, (255, 255, 255))
            tela.blit(txt_resp, (LARGURA // 2 - txt_resp.get_width() // 2, 320))

            if btn_tiro == 0 and (agora - tempo_devorado > 1.0):
                hero_devorado = False
                sala_atual = 'castelo_dourado_ext'
                px, py = 387, 450

            pygame.display.flip()
            relogio.tick(60)
            continue

        # --- LÓGICA DE JOGO ATIVO ---
        if not venceu_normal and not venceu_secret and not em_dialogo:

            # MOVIMENTAÇÃO DO HERÓI
            antigo_x, antigo_y = px, py
            if joy_x < 300: px -= 5
            elif joy_x > 700: px += 5
            if joy_y < 300: py -= 5
            elif joy_y > 800: py += 5

            jogador_rect = pygame.Rect(px, py, tamanho_jogador, tamanho_jogador)

            # CONSTRUÇÃO DAS PAREDES DA SALA ATUAL
            paredes = [
                pygame.Rect(0, 0, LARGURA, 20),           # Topo
                pygame.Rect(0, ALTURA - 20, LARGURA, 20), # Base
                pygame.Rect(0, 0, 20, ALTURA),           # Esquerda
                pygame.Rect(LARGURA - 20, 0, 20, ALTURA)  # Direita
            ]

            is_catacumba = 'catacumbas' in sala_atual

            if sala_atual == 'castelo_dourado_ext':
                # Saída Superior (Interior do Castelo Dourado)
                paredes[0] = pygame.Rect(0, 0, 320, 20)
                paredes.append(pygame.Rect(480, 0, 320, 20))
                # Saída Inferior (Campo Inicial)
                paredes[1] = pygame.Rect(0, ALTURA - 20, 320, 20)
                paredes.append(pygame.Rect(480, ALTURA - 20, 320, 20))
                # Fachada do Castelo Dourado
                paredes.append(pygame.Rect(200, 80, 400, 280))

            elif sala_atual == 'castelo_dourado_int':
                # Saída Inferior (Exterior)
                paredes[1] = pygame.Rect(0, ALTURA - 20, 320, 20)
                paredes.append(pygame.Rect(480, ALTURA - 20, 320, 20))

            elif sala_atual == 'campo_inicial':
                # Saída Superior (Castelo Dourado Ext)
                paredes[0] = pygame.Rect(0, 0, 320, 20)
                paredes.append(pygame.Rect(480, 0, 320, 20))
                # Saída Direita (Floresta Leste)
                paredes[3] = pygame.Rect(LARGURA - 20, 0, 20, 220)
                paredes.append(pygame.Rect(LARGURA - 20, 380, 20, 220))
                # Saída Inferior (Floresta Sul)
                paredes[1] = pygame.Rect(0, ALTURA - 20, 320, 20)
                paredes.append(pygame.Rect(480, ALTURA - 20, 320, 20))

                # Passagem Secreta Esquerda
                if parede_secreta_revelada:
                    paredes[2] = pygame.Rect(0, 0, 20, 220)
                    paredes.append(pygame.Rect(0, 380, 20, 220))

            elif sala_atual == 'floresta_leste':
                # Saída Esquerda (Campo Inicial)
                paredes[2] = pygame.Rect(0, 0, 20, 220)
                paredes.append(pygame.Rect(0, 380, 20, 220))
                # Saída Superior (Castelo Branco Ext)
                if nivel > 1:
                    paredes[0] = pygame.Rect(0, 0, 320, 20)
                    paredes.append(pygame.Rect(480, 0, 320, 20))

            elif sala_atual == 'castelo_branco_ext':
                # Saída Inferior (Floresta Leste)
                paredes[1] = pygame.Rect(0, ALTURA - 20, 320, 20)
                paredes.append(pygame.Rect(480, ALTURA - 20, 320, 20))
                # Fachada e Portão Branco
                paredes.append(pygame.Rect(200, 80, 400, 280))
                if castelo_branco_trancado:
                    p_pb = pygame.Rect(350, 340, 100, 40)
                    paredes.append(p_pb)
                    if jogador_rect.colliderect(p_pb) and item_carregado == 'chave_branca':
                        castelo_branco_trancado = False
                        enviar_comando(arduino, 'E')

            elif sala_atual == 'castelo_branco_int':
                # Saída Inferior
                paredes[1] = pygame.Rect(0, ALTURA - 20, 320, 20)
                paredes.append(pygame.Rect(480, ALTURA - 20, 320, 20))

            elif sala_atual == 'floresta_sul':
                # Saída Superior (Campo Inicial)
                paredes[0] = pygame.Rect(0, 0, 320, 20)
                paredes.append(pygame.Rect(480, 0, 320, 20))
                # Saída Direita (Castelo Negro Ext)
                paredes[3] = pygame.Rect(LARGURA - 20, 0, 20, 220)
                paredes.append(pygame.Rect(LARGURA - 20, 380, 20, 220))

            elif sala_atual == 'castelo_negro_ext':
                # Saída Esquerda (Floresta Sul)
                paredes[2] = pygame.Rect(0, 0, 20, 220)
                paredes.append(pygame.Rect(0, 380, 20, 220))
                # Fachada e Portão Negro
                paredes.append(pygame.Rect(200, 80, 400, 280))
                if castelo_negro_trancado:
                    p_pn = pygame.Rect(350, 340, 100, 40)
                    paredes.append(p_pn)
                    if jogador_rect.colliderect(p_pn) and item_carregado in ('chave_negra', 'chave_dourada'):
                        castelo_negro_trancado = False
                        enviar_comando(arduino, 'E')

            elif sala_atual == 'castelo_negro_int':
                # Saída Inferior
                paredes[1] = pygame.Rect(0, ALTURA - 20, 320, 20)
                paredes.append(pygame.Rect(480, ALTURA - 20, 320, 20))

            elif 'labirinto' in sala_atual:
                # Saída Esquerda
                paredes[2] = pygame.Rect(0, 0, 20, 220)
                paredes.append(pygame.Rect(0, 380, 20, 220))
                # Estruturas de Labirinto
                paredes.append(pygame.Rect(180, 140, 20, 340))
                paredes.append(pygame.Rect(180, 140, 400, 20))
                paredes.append(pygame.Rect(380, 280, 20, 300))

            elif 'catacumbas' in sala_atual:
                # Saída Direita
                paredes[3] = pygame.Rect(LARGURA - 20, 0, 20, 220)
                paredes.append(pygame.Rect(LARGURA - 20, 380, 20, 220))

            elif sala_atual == 'sala_secreta_zecreppe':
                # Saída Direita
                paredes[3] = pygame.Rect(LARGURA - 20, 0, 20, 220)
                paredes.append(pygame.Rect(LARGURA - 20, 380, 20, 220))

            # MECÂNICA DA PONTE (SE ESTIVER NO INVENTÁRIO OU NA SALA, PERMITE ATRAVESSAR PARTE DAS PAREDES)
            for p in paredes:
                if jogador_rect.colliderect(p):
                    px, py = antigo_x, antigo_y
                    jogador_rect = pygame.Rect(px, py, tamanho_jogador, tamanho_jogador)

            # --- DETECÇÃO DO PONTO SECRETO (NA SALA INICIAL COM A CHAVE NEGRA OU DOURADA) ---
            if sala_atual == 'campo_inicial' and item_carregado in ('chave_negra', 'chave_dourada') and not parede_secreta_revelada:
                if jogador_rect.colliderect(pixel_secreto_rect):
                    parede_secreta_revelada = True
                    enviar_comando(arduino, 'E')

            # --- TRANSIÇÕES DE SALA DE ATARI ---
            if py < 10:
                if sala_atual == 'campo_inicial': sala_atual = 'castelo_dourado_ext'; py = ALTURA - 50
                elif sala_atual == 'castelo_dourado_ext': sala_atual = 'castelo_dourado_int'; py = ALTURA - 50
                elif sala_atual == 'floresta_leste' and nivel > 1: sala_atual = 'castelo_branco_ext'; py = ALTURA - 50
                elif sala_atual == 'floresta_sul': sala_atual = 'campo_inicial'; py = ALTURA - 50

            elif py > ALTURA - 30:
                if sala_atual == 'castelo_dourado_ext': sala_atual = 'campo_inicial'; py = 40
                elif sala_atual == 'castelo_dourado_int': sala_atual = 'castelo_dourado_ext'; py = 400; px = 400
                elif sala_atual == 'castelo_branco_ext': sala_atual = 'floresta_leste'; py = 40
                elif sala_atual == 'castelo_branco_int': sala_atual = 'castelo_branco_ext'; py = 400; px = 400
                elif sala_atual == 'campo_inicial': sala_atual = 'floresta_sul'; py = 40
                elif sala_atual == 'castelo_negro_int': sala_atual = 'castelo_negro_ext'; py = 400; px = 400

            elif px > LARGURA - 30:
                if sala_atual == 'campo_inicial': sala_atual = 'floresta_leste'; px = 40
                elif sala_atual == 'floresta_sul': sala_atual = 'castelo_negro_ext'; px = 40
                elif sala_atual == 'sala_secreta_zecreppe': sala_atual = 'campo_inicial'; px = 40

            elif px < 10:
                if sala_atual == 'floresta_leste': sala_atual = 'campo_inicial'; px = LARGURA - 50
                elif sala_atual == 'castelo_negro_ext': sala_atual = 'floresta_sul'; px = LARGURA - 50
                elif sala_atual == 'campo_inicial' and parede_secreta_revelada: sala_atual = 'sala_secreta_zecreppe'; px = LARGURA - 50

            # --- COLETAR ITENS (SISTEMA DE INVENTÁRIO DE 1 ITEM POR VEZ) ---
            for nome_item, info in itens.items():
                if info['sala'] == sala_atual and item_carregado != nome_item:
                    if jogador_rect.colliderect(info['rect']):
                        item_carregado = nome_item
                        enviar_comando(arduino, 'T')

            # Atualiza posição do item carregado pelo herói
            if item_carregado and item_carregado in itens:
                itens[item_carregado]['sala'] = sala_atual
                itens[item_carregado]['rect'].x = px - 3
                itens[item_carregado]['rect'].y = py - 22

            # --- MECÂNICA DO ÍMÃ (ATRAI OBJETOS PRÓXIMOS NA MESMA SALA) ---
            if item_carregado == 'ima':
                for obj_k, obj_info in itens.items():
                    if obj_k != 'ima' and obj_info['sala'] == sala_atual:
                        orx, ory = obj_info['rect'].x, obj_info['rect'].y
                        if math.hypot(orx - px, ory - py) < 220.0:
                            obj_info['rect'].x += 3 if orx < px else -3
                            obj_info['rect'].y += 3 if ory < py else -3

            # --- VITÓRIA NORMAL: LEVAR O CÁLICE AO CASTELO DOURADO ---
            if item_carregado == 'calice' and sala_atual == 'castelo_dourado_int':
                venceu_normal = True
                tempo_total_conclusao = agora - tempo_inicio
                enviar_comando(arduino, 'E')

            # --- IA DOS 3 DRAGÕES PATO ---
            for d_key, d in dragões.items():
                if d['vivo'] and d['sala'] == sala_atual:
                    dx, dy = d['x'], d['y']
                    if dx < px: dx += d['vel']
                    elif dx > px: dx -= d['vel']
                    if dy < py: dy += d['vel']
                    elif dy > py: dy -= d['vel']
                    d['x'], d['y'] = dx, dy

                    d_rect = pygame.Rect(dx, dy, 44, 44)

                    # Colisão com Espada: Mata o Dragão!
                    if item_carregado == 'espada' and jogador_rect.colliderect(d_rect):
                        d['vivo'] = False
                        enviar_comando(arduino, 'E')
                    elif jogador_rect.colliderect(d_rect):
                        # Sem espada: Herói é devorado!
                        hero_devorado = True
                        tempo_devorado = agora
                        enviar_comando(arduino, 'M')

            # --- IA DO MORCEGO PRETO (ROUBA E TROCA ITENS) ---
            if morcego_ativo:
                mx += mdx
                my += mdy
                if mx < 40 or mx > LARGURA - 40: mdx *= -1
                if my < 40 or my > ALTURA - 40: mdy *= -1

                bat_rect = pygame.Rect(int(mx), int(my), 28, 20)

                # Morcego troca de item se tocar no herói ou em objetos
                if agora - tempo_ultimo_roubo > 4.0:
                    if item_carregado and bat_rect.colliderect(jogador_rect):
                        # Morcego rouba o item do jogador!
                        morcego_item, item_carregado = item_carregado, morcego_item
                        tempo_ultimo_roubo = agora
                        enviar_comando(arduino, 'M')

            # --- LUTA CONTRA O BOSS ZÉCREPPE (SALA SECRETA) ---
            if sala_atual == 'sala_secreta_zecreppe' and not boss_derrotado:
                if bx < px: bx += boss_vel
                elif bx > px: bx -= boss_vel
                if by < py: by += boss_vel
                elif by > py: by -= boss_vel

                boss_rect = pygame.Rect(bx, by, 52, 52)
                ataque = (btn_tiro == 0) or pygame.key.get_pressed()[pygame.K_SPACE] or pygame.key.get_pressed()[pygame.K_z]
                raio_ataque = pygame.Rect(px - 20, py - 20, tamanho_jogador + 40, tamanho_jogador + 40)

                if ataque and (agora - tempo_ultimo_ataque > 0.3) and (agora > tempo_invulneravel_boss):
                    if raio_ataque.colliderect(boss_rect):
                        boss_hp -= 1
                        tempo_invulneravel_boss = agora + 0.3
                        tempo_ultimo_ataque = agora
                        enviar_comando(arduino, 'M')

                        if boss_hp <= 0:
                            boss_derrotado = True
                            em_dialogo = True
                            indice_dialogo = 0
                            tempo_ultimo_dialogo = agora
                            tempo_total_conclusao = agora - tempo_inicio
                            enviar_comando(arduino, 'E')

                if jogador_rect.colliderect(boss_rect) and not boss_derrotado:
                    px, py = 700, 300
                    enviar_comando(arduino, 'M')

        # --- SALVAMENTO NO BANCO DE DADOS ---
        if (venceu_normal or venceu_secret) and not partida_salva:
            partida_salva = True
            jogador_id = obter_ou_criar_jogador(nome_jogador)
            if jogador_id:
                salvar_partida_adventure(jogador_id, tempo_total_conclusao, derrotou_zecreppe=(1 if venceu_secret else 0), venceu=1, nivel=nivel)

        # --- RENDERIZAÇÃO GRÁFICA DAS SALAS ---
        if sala_atual == 'sala_secreta_zecreppe':
            tela.fill(COR_SALA_SECRETA)
        elif 'castelo_dourado' in sala_atual:
            tela.fill((100, 70, 30))
        elif 'castelo_branco' in sala_atual:
            tela.fill((60, 60, 80))
        elif 'castelo_negro' in sala_atual:
            tela.fill((20, 18, 30))
        else:
            tela.fill(COR_ATARI_BROWN)

        # Paredes Verde Musgo
        for p in paredes:
            pygame.draw.rect(tela, COR_PAREDE_VERDE, p)

        # Desenho dos Castelos nas suas respectivas salas
        if sala_atual == 'castelo_dourado_ext':
            pygame.draw.rect(tela, COR_CASTELO_DOURADO, (200, 80, 400, 280))
            pygame.draw.rect(tela, COR_ATARI_BROWN, (350, 260, 100, 100)) # Porta Dourada
        elif sala_atual == 'castelo_branco_ext':
            pygame.draw.rect(tela, COR_CASTELO_BRANCO, (200, 80, 400, 280))
            cor_pb = (20, 15, 10) if castelo_branco_trancado else COR_ATARI_BROWN
            pygame.draw.rect(tela, cor_pb, (350, 260, 100, 100))
        elif sala_atual == 'castelo_negro_ext':
            pygame.draw.rect(tela, COR_CASTELO_NEGRO, (200, 80, 400, 280))
            cor_pn = (10, 8, 15) if castelo_negro_trancado else COR_ATARI_BROWN
            pygame.draw.rect(tela, cor_pn, (350, 260, 100, 100))

        # Ponto Secreto de Ativação
        if sala_atual == 'campo_inicial' and not parede_secreta_revelada:
            cor_p = COR_TEXTO_GOLD if (item_carregado in ('chave_negra', 'chave_dourada') and int(agora * 4) % 2 == 0) else COR_PAREDE_VERDE
            pygame.draw.rect(tela, cor_p, pixel_secreto_rect)

        # Desenha os Objetos do Mundo na Sala Atual
        for k_item, info in itens.items():
            if info['sala'] == sala_atual:
                if k_item == 'espada':
                    pygame.draw.rect(tela, (200, 220, 255), info['rect'], border_radius=3)
                    pygame.draw.line(tela, (255, 255, 255), (info['rect'].centerx, info['rect'].top), (info['rect'].centerx, info['rect'].bottom), 3)
                elif k_item == 'chave_dourada': tela.blit(img_chave_dourada, info['rect'])
                elif k_item == 'chave_branca': tela.blit(img_chave_branca, info['rect'])
                elif k_item == 'chave_negra': tela.blit(img_chave_negra, info['rect'])
                elif k_item == 'calice': tela.blit(img_calice, info['rect'])
                elif k_item == 'ponte': pygame.draw.rect(tela, (180, 130, 70), info['rect'], border_radius=4)
                elif k_item == 'ima': pygame.draw.rect(tela, (220, 40, 40), info['rect'], border_radius=4)

        # Desenha os Dragões Pato Vivos na Sala Atual
        for d_key, d in dragões.items():
            if d['vivo'] and d['sala'] == sala_atual and not venceu_normal and not venceu_secret:
                tela.blit(d['sprite'], (int(d['x']), int(d['y'])))

        # Desenha o Morcego Preto
        if morcego_ativo and morcego_sala == sala_atual:
            pygame.draw.ellipse(tela, (20, 20, 20), (int(mx), int(my), 28, 16))
            pygame.draw.polygon(tela, (40, 40, 40), [(int(mx), int(my) + 8), (int(mx) - 8, int(my) - 4), (int(mx) + 4, int(my) + 4)])
            pygame.draw.polygon(tela, (40, 40, 40), [(int(mx) + 28, int(my) + 8), (int(mx) + 36, int(my) - 4), (int(mx) + 24, int(my) + 4)])

        # Desenha o Boss ZéCreppe
        if sala_atual == 'sala_secreta_zecreppe' and not boss_derrotado:
            if agora < tempo_invulneravel_boss:
                s_boss = img_boss.copy()
                s_boss.fill((255, 100, 100, 180), special_flags=pygame.BLEND_RGBA_MULT)
                tela.blit(s_boss, (int(bx), int(by)))
            else:
                tela.blit(img_boss, (int(bx), int(by)))

            # Barra de HP ZéCreppe
            hp_w = 60
            hp_x = int(bx) - 4
            hp_y = int(by) - 12
            pygame.draw.rect(tela, (40, 20, 20), (hp_x, hp_y, hp_w, 7), border_radius=3)
            fill_w = int(hp_w * (boss_hp / float(boss_max_hp)))
            if fill_w > 0:
                pygame.draw.rect(tela, COR_NEON_ROSA, (hp_x, hp_y, fill_w, 7), border_radius=3)
            pygame.draw.rect(tela, (255, 255, 255), (hp_x, hp_y, hp_w, 7), width=1, border_radius=3)

        # ILUMINAÇÃO PARCIAL / SPOTLIGHT NAS CATACUMBAS (FOG OF WAR RETRO)
        if is_catacumba:
            fog_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            fog_surf.fill((5, 5, 10, 240))
            pygame.draw.circle(fog_surf, (0, 0, 0, 0), (px + 13, py + 13), 130)
            tela.blit(fog_surf, (0, 0))

        # Desenha o Herói (Quadrado Retro Atari)
        tela.blit(img_player, (px, py))

        # HUD Superior com Nível e Tempo
        tempo_dec = agora - tempo_inicio if (not venceu_normal and not venceu_secret) else tempo_total_conclusao
        txt_hud = fonte_hud.render(f"NÍVEL {nivel}  |  {nome_jogador[:10]}  |  SALA: {sala_atual.upper()}  |  TEMPO: {tempo_dec:.1f}s", True, (255, 255, 255))
        tela.blit(txt_hud, (25, 25))

        # DIÁLOGOS PÓS-BOSS ZÉCREPPE
        if em_dialogo:
            dialogo_box = pygame.Rect(60, 380, 680, 160)
            pygame.draw.rect(tela, (14, 12, 28), dialogo_box, border_radius=10)
            pygame.draw.rect(tela, COR_TEXTO_GOLD, dialogo_box, width=3, border_radius=10)

            txt_d_autor = fonte_dialogo.render("👾 ZÉCREPPE (BOSS SECRETO):", True, COR_NEON_ROSA)
            tela.blit(txt_d_autor, (85, 395))

            if indice_dialogo < len(dialogos_boss):
                txt_d_conteudo = fonte_dialogo.render(f'"{dialogos_boss[indice_dialogo]}"', True, (255, 255, 255))
                tela.blit(txt_d_conteudo, (85, 440))

            txt_d_avanco = fonte_hud.render("► PRESSIONE AÇÃO / ESPAÇO PARA CONTINUAR ◄", True, COR_TEXTO_GOLD)
            tela.blit(txt_d_avanco, (LARGURA // 2 - txt_d_avanco.get_width() // 2, 500))

        # TELAS DE VITÓRIA
        if venceu_secret:
            tela.fill((10, 8, 20))
            tempo_pisca = int(agora * 4) % 2
            cor_secreta = COR_TEXTO_GOLD if tempo_pisca == 0 else COR_NEON_AZUL

            txt1 = fonte_vitoria.render("🏆 VENCEDOR ORIGINAL — ADVENTURE 🏆", True, cor_secreta)
            txt2 = fonte_vitoria.render(f"PARABÉNS, {nome_jogador.upper()}!", True, (255, 255, 255))
            txt3 = fonte_dialogo.render("VOCÊ DERROTOU O ZÉCREPPE E COMPLETOU O DESAFIO!", True, COR_NEON_ROSA)
            txt4 = fonte_hud.render(f"NÍVEL {nivel}  |  TEMPO FINAL: {tempo_total_conclusao:.2f}s  |  REGISTRADO NO RANKING!", True, COR_TEXTO_GOLD)

            tela.blit(txt1, (LARGURA//2 - txt1.get_width()//2, 160))
            tela.blit(txt2, (LARGURA//2 - txt2.get_width()//2, 230))
            tela.blit(txt3, (LARGURA//2 - txt3.get_width()//2, 300))
            tela.blit(txt4, (LARGURA//2 - txt4.get_width()//2, 360))

            txt_voltar = fonte_dialogo.render("PRESSIONE BOTÃO DE TIRO / ESC PARA VOLTAR AO MENU", True, (160, 170, 190))
            tela.blit(txt_voltar, (LARGURA//2 - txt_voltar.get_width()//2, 480))

            if btn_tiro == 0 and (agora - tempo_ultimo_dialogo > 0.4):
                rodando = False

        elif venceu_normal:
            txt_vitoria = fonte_vitoria.render("🏆 CÁLICE RECUPERADO! VOCÊ VENCEU! 🏆", True, COR_TEXTO_GOLD)
            tela.blit(txt_vitoria, (LARGURA//2 - txt_vitoria.get_width()//2, ALTURA//2 - 40))

            txt_tempo = fonte_hud.render(f"NÍVEL {nivel}  |  TEMPO DE CONCLUSÃO: {tempo_total_conclusao:.2f}s", True, (255, 255, 255))
            tela.blit(txt_tempo, (LARGURA//2 - txt_tempo.get_width()//2, ALTURA//2 + 20))

            txt_voltar = fonte_dialogo.render("PRESSIONE BOTÃO DE TIRO / ESC PARA VOLTAR AO LAUNCHER", True, (160, 170, 190))
            tela.blit(txt_voltar, (LARGURA//2 - txt_voltar.get_width()//2, ALTURA - 80))

            if btn_tiro == 0:
                pygame.time.wait(300)
                rodando = False

        pygame.display.flip()
        relogio.tick(60)

    return
