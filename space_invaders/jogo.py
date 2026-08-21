import pygame
import random
import time
import math
import os
from core.arduino_controller import enviar_comando

# --- CONFIGURAÇÕES E CONSTANTES (SEM NÚMEROS MÁGICOS) ---
TELEPORT_CHANCE = 0.50
FREEZE_CHANCE = 0.40

BOSS_FIRST_SPAWN_SCORE = 400
BOSS_SPAWN_CHANCE = 0.01  # Chance RARA (1% ao abrir nova vaga de spawn)
BOSS_HITS_REQUIRED = 20
BOSS_TIME_MULTIPLIER_ON_DEFEAT = 1.25
BOSS_TIME_DIVISOR_ON_ESCAPE = 1.6

CHARGED_MIN_SCORE = 500
CHARGED_SPAWN_CHANCE = 0.35
CHARGED_BUFF_DURATION = 3.5

BONUS_DURATION = 8.0
BONUS_DROP_CHANCE = 0.05 # Drop raro de item bonus.png (5%)

MAX_INIMIGOS_TELA = 15 # Limite de horda reduzido (máx 15 por vez)

# SISTEMA DE RARIDADE DE MOBS (SUBCHEFE CREEPER MAIS RARO = PESO 6)
MOB_RARITY = {
    'default':  {'nome': 'Comum',                 'peso': 45, 'pontos': 10, 'dano_fuga': 5.0},
    'verde':    {'nome': 'Creeper (Subchefe)',    'peso': 6,  'pontos': 50, 'dano_fuga': 15.0}, # Raro Subchefe (5 HP)
    'gelo':     {'nome': 'Gelo',                  'peso': 18, 'pontos': 20, 'dano_fuga': 10.0},
    'zangado':  {'nome': 'Zangado',               'peso': 15, 'pontos': 20, 'dano_fuga': 10.0},
    'teleport': {'nome': 'Teleport',              'peso': 10, 'pontos': 30, 'dano_fuga': 15.0},
    'charged':  {'nome': 'Charged',               'peso': 6,  'pontos': 35, 'dano_fuga': 15.0},
}

# --- CARREGAMENTO DE SPRITES ---
SPRITES = {}

def carregar_sprites():
    """Carrega e redimensiona os sprites da pasta 'sprites'."""
    pasta_sprites = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sprites')
    
    tamanhos = {
        'nave': (48, 48),
        'tiro': (12, 24),
        'enemy-default': (48, 48),
        'enemy-verde': (72, 72),            # Subchefe Creeper verde (72x72)
        'enemy-especial-verde': (72, 72),
        'enemy-gelo': (48, 48),
        'enemy-yellow': (48, 48),
        'enemy-charged': (48, 48),
        'charged-attack': (80, 80),         # Sprite de raio do Charged
        'enemy-teleport': (48, 48),
        'enemy-zangado': (48, 48),
        'enemy-boss-malware': (96, 96),     # Boss Malware (96x96)
        'explosion': (110, 110),
        'bonus': (32, 32)                   # Item bônus raro (bonus.png)
    }

    files = {
        'nave': 'nave.png',
        'tiro': 'tiro.png',
        'enemy-default': 'enemy-default.png',
        'enemy-verde': 'enemy-especial-verde.png',
        'enemy-especial-verde': 'enemy-especial-verde.png',
        'enemy-gelo': 'enemy-gelo.png',
        'enemy-yellow': 'enemy-yellow.png',
        'enemy-charged': 'enemy-charged.png',
        'charged-attack': 'charged-attack.png',
        'enemy-teleport': 'enemy-teleport.png',
        'enemy-zangado': 'enemy-zangado.png',
        'enemy-boss-malware': 'enemy-boss-malware.png',
        'explosion': 'explosion.gif',
        'bonus': 'bonus.png'
    }

    for key, filename in files.items():
        filepath = os.path.join(pasta_sprites, filename)
        if os.path.exists(filepath):
            try:
                img = pygame.image.load(filepath).convert_alpha()
                SPRITES[key] = pygame.transform.scale(img, tamanhos[key])
            except Exception as e:
                print(f"[Sprite Error] Erro ao carregar {filename}: {e}")
                SPRITES[key] = None
        else:
            SPRITES[key] = None

def novo_inimigo(colunas_x, tipo_forçado=None, pontuacao=0):
    """Cria um inimigo respeitando a raridade, tamanho e HP de Subchefe (Creeper Verde = 5 HP)."""
    if tipo_forçado:
        tipo = tipo_forçado
    else:
        if pontuacao >= CHARGED_MIN_SCORE and random.random() < CHARGED_SPAWN_CHANCE:
            tipo = 'charged'
        else:
            tipos_candidatos = ['default', 'verde', 'gelo', 'zangado', 'teleport']
            pesos = [MOB_RARITY[t]['peso'] for t in tipos_candidatos]
            tipo = random.choices(tipos_candidatos, weights=pesos, k=1)[0]

    col_idx = random.randint(0, len(colunas_x) - 1)
    
    is_subchefe = (tipo == 'verde')
    w = 72 if is_subchefe else 48
    h = 72 if is_subchefe else 48
    hp = 5 if is_subchefe else 1

    return {
        "tipo": tipo,
        "coluna": col_idx,
        "x": float(colunas_x[col_idx]),
        "x_base": float(colunas_x[col_idx]),
        "y": random.uniform(-160, -50),
        "dx": 0.0,
        "largura": w,
        "altura": h,
        "hp": hp,
        "hp_max": hp,
        "dash_timer": random.uniform(2.0, 4.0),
        "em_dash": False,
        "congelado_ate": 0.0
    }

def novo_boss_malware(colunas_x):
    """Cria o Boss Malware: Reúne TODAS as habilidades (dash, zig-zag, teleporte) e possui 20 HP."""
    col_idx = random.randint(0, len(colunas_x) - 1)
    return {
        "tipo": "boss_malware",
        "coluna": col_idx,
        "x": float(colunas_x[col_idx]),
        "x_base": float(colunas_x[col_idx]),
        "y": -120.0,
        "dx": 0.0,
        "largura": 96,
        "altura": 96,
        "hp": BOSS_HITS_REQUIRED,
        "hp_max": BOSS_HITS_REQUIRED,
        "dash_timer": random.uniform(2.0, 3.5),
        "em_dash": False,
        "congelado_ate": 0.0
    }

def criar_onda_inicial(colunas_x):
    """
    Onda de Apresentação Reorganizada:
    Apresenta os mobs didaticamente incluindo o Subchefe Creeper Verde (5 HP).
    """
    onda = []
    
    # Linha 1: Mobs Comuns (Default)
    for c in [1, 3]:
        o = novo_inimigo(colunas_x, tipo_forçado='default')
        o['y'] = -60.0
        o['x'] = float(colunas_x[c])
        o['coluna'] = c
        onda.append(o)

    # Linha 2: Creeper Verde (Subchefe Maior de 5 HP - Zig-zag)
    o = novo_inimigo(colunas_x, tipo_forçado='verde')
    o['y'] = -120.0
    o['x'] = float(colunas_x[2])
    o['coluna'] = 2
    onda.append(o)

    # Linha 3: Inimigo de Gelo
    o = novo_inimigo(colunas_x, tipo_forçado='gelo')
    o['y'] = -180.0
    o['x'] = float(colunas_x[0])
    o['coluna'] = 0
    onda.append(o)

    # Linha 4: Inimigo Zangado
    o = novo_inimigo(colunas_x, tipo_forçado='zangado')
    o['y'] = -240.0
    o['x'] = float(colunas_x[4])
    o['coluna'] = 4
    onda.append(o)

    # Linha 5: Inimigo Teleport
    o = novo_inimigo(colunas_x, tipo_forçado='teleport')
    o['y'] = -300.0
    o['x'] = float(colunas_x[1])
    o['coluna'] = 1
    onda.append(o)

    # Linha 6: Inimigo Charged
    o = novo_inimigo(colunas_x, tipo_forçado='charged')
    o['y'] = -360.0
    o['x'] = float(colunas_x[3])
    o['coluna'] = 3
    onda.append(o)

    return onda

def rodar_jogo(tela, relogio, arduino, ler_hardware):
    carregar_sprites()

    LARGURA, ALTURA = 800, 600
    jogador_x = LARGURA // 2
    velocidade_jogador_max = 12

    COLUNAS_X = [100, 250, 400, 550, 700]

    # CRIANTE DO FUNDO ESTELAR RETRO (ESTRELAS EM CAMADAS COM PARALAXE)
    estrelas = [
        {
            "x": random.randint(0, LARGURA),
            "y": random.randint(0, ALTURA),
            "vel": random.uniform(0.3, 1.8),
            "tam": random.choice([1, 1, 2, 2, 3]),
            "cor": random.choice([(255, 255, 255), (180, 200, 255), (255, 220, 180), (120, 140, 180)])
        }
        for _ in range(80)
    ]

    # FLUXO DA PARTIDA: ONDA INICIAL DE APRESENTAÇÃO -> JOGO NORMAL
    fase_jogo = "ONDA_INICIAL"
    aliens = criar_onda_inicial(COLUNAS_X)

    tiros = []
    explosoes = []
    popups = []
    bonuses = []
    efeitos_raio = []

    pontuacao = 0
    total_inimigos_derrotados = 0
    tempo_restante = 60.0
    TEMPO_MAXIMO_REF = 60.0

    velocidade_base_inimigo = 0.6

    buff_velocidade_inimigos_ate = 0.0
    bonus_tiro_duplo_ate = 0.0
    bonus_ataque_area_ate = 0.0

    boss_primeiro_spawnou = False
    boss_ativo = False
    boss_aura_ativo = False # AURA DO BOSS: Ativa enquanto o Boss Malware estiver em campo

    fonte_hud = pygame.font.SysFont('Consolas', 18, bold=True)
    fonte_sub = pygame.font.SysFont('Consolas', 14)
    fonte_popup = pygame.font.SysFont('Consolas', 24, bold=True)
    fonte_gameover = pygame.font.SysFont('Consolas', 36, bold=True)

    rodando = True
    game_over = False
    tempo_game_over = 0.0  # Momento em que o game over ocorreu (para cooldown de 5s)
    COOLDOWN_GAME_OVER = 5.0  # Segundos antes de redirecionar ao menu
    tempo_ultimo_tiro = 0.0
    INTERVALO_TIRO = 0.18
    tempo_anterior_frame = time.time()

    while rodando:
        agora = time.time()
        dt = agora - tempo_anterior_frame
        tempo_anterior_frame = agora

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
                elif game_over and (evento.key == pygame.K_SPACE or evento.key == pygame.K_RETURN):
                    return rodar_jogo(tela, relogio, arduino, ler_hardware)

        # Lê entradas do Hardware / Teclado
        joy_x, joy_y, btn_menu, btn_tiro = ler_hardware(arduino)

        if btn_menu == 0:
            if game_over:
                rodando = False
                break
            else:
                rodando = False
                pygame.time.wait(300)
                break

        if game_over:
            tela.fill((15, 10, 20))

            # Conta o tempo restante do cooldown
            decorrido_go = agora - tempo_game_over
            cooldown_restante = max(0.0, COOLDOWN_GAME_OVER - decorrido_go)

            # Se o cooldown expirou, volta ao menu automaticamente
            if cooldown_restante <= 0:
                rodando = False
                break

            # --- TELA DE GAME OVER ---
            txt_go = fonte_gameover.render("GAME OVER", True, (231, 76, 60))
            tela.blit(txt_go, (LARGURA // 2 - txt_go.get_width() // 2, 170))

            txt_pts = fonte_hud.render(f"PONTUAÇÃO FINAL: {pontuacao:04d}  |  ABATES: {total_inimigos_derrotados}", True, (255, 255, 255))
            tela.blit(txt_pts, (LARGURA // 2 - txt_pts.get_width() // 2, 240))

            # BARRA DE COOLDOWN (conta regressiva visual)
            bar_go_w = 340
            bar_go_x = LARGURA // 2 - bar_go_w // 2
            bar_go_y = 310
            pct_cd = cooldown_restante / COOLDOWN_GAME_OVER
            pygame.draw.rect(tela, (40, 20, 20), (bar_go_x, bar_go_y, bar_go_w, 16), border_radius=8)
            pygame.draw.rect(tela, (231, 76, 60), (bar_go_x, bar_go_y, int(bar_go_w * pct_cd), 16), border_radius=8)
            pygame.draw.rect(tela, (180, 60, 60), (bar_go_x, bar_go_y, bar_go_w, 16), width=2, border_radius=8)

            txt_cd = fonte_sub.render(f"Voltando ao menu em {cooldown_restante:.1f}s...", True, (200, 140, 140))
            tela.blit(txt_cd, (LARGURA // 2 - txt_cd.get_width() // 2, bar_go_y + 26))

            txt_reinicio = fonte_sub.render("Pressione Botão de Tiro para jogar novamente", True, (160, 170, 190))
            tela.blit(txt_reinicio, (LARGURA // 2 - txt_reinicio.get_width() // 2, 380))

            if btn_tiro == 0:
                pygame.time.wait(300)
                return rodar_jogo(tela, relogio, arduino, ler_hardware)

            pygame.display.flip()
            relogio.tick(60)
            continue

        # TEMPO CONTANDO CONTINUAMENTE
        tempo_restante -= dt
        if tempo_restante <= 0:
            tempo_restante = 0
            if not game_over:
                game_over = True
                tempo_game_over = agora  # Registra o momento exato do game over
                enviar_comando(arduino, 'M')

        # --- TRANSIÇÃO E SPAWN DO JOGO NORMAL ---
        if fase_jogo == "ONDA_INICIAL":
            if len(aliens) == 0:
                fase_jogo = "JOGO_NORMAL"
                popups.append({
                    "texto": "► JOGO NORMAL INICIADO! ◄",
                    "cor": (46, 204, 113),
                    "x": LARGURA // 2,
                    "y": 200,
                    "criado": agora
                })
        else:
            # HORDA MODERADA (MÁXIMO DE 15 INIMIGOS SIMULTÂNEOS NA TELA)
            num_inimigos_desejado = min(MAX_INIMIGOS_TELA, 3 + (pontuacao // 150))

            # AURA DO BOSS: Quando ativo, duplica a horda de inimigos invocados!
            mult_horda = 2 if boss_aura_ativo else 1
            num_horda_com_aura = min(MAX_INIMIGOS_TELA, num_inimigos_desejado * mult_horda)

            while len(aliens) < num_horda_com_aura:
                if (not boss_primeiro_spawnou) and (pontuacao >= BOSS_FIRST_SPAWN_SCORE):
                    boss_primeiro_spawnou = True
                    boss_ativo = True
                    boss_aura_ativo = True
                    aliens.append(novo_boss_malware(COLUNAS_X))
                    popups.append({
                        "texto": "☠ BOSS MALWARE DETECTADO! HORDA INVOCADA! ☠",
                        "cor": (231, 76, 60),
                        "x": LARGURA // 2,
                        "y": 180,
                        "criado": agora
                    })

                elif (boss_primeiro_spawnou) and (not boss_ativo) and (pontuacao >= BOSS_FIRST_SPAWN_SCORE) and (random.random() < BOSS_SPAWN_CHANCE):
                    boss_ativo = True
                    boss_aura_ativo = True
                    aliens.append(novo_boss_malware(COLUNAS_X))
                    popups.append({
                        "texto": "☠ BOSS MALWARE SURGIU! ☠",
                        "cor": (231, 76, 60),
                        "x": LARGURA // 2,
                        "y": 180,
                        "criado": agora
                    })
                else:
                    aliens.append(novo_inimigo(COLUNAS_X, pontuacao=pontuacao))

        # MOVIMENTAÇÃO DO JOGADOR
        MIN_X = 45
        MAX_X = LARGURA - 45

        if joy_x < 400: # Esquerda
            fator = (400.0 - joy_x) / 400.0
            vel = max(5, int(velocidade_jogador_max * fator))
            jogador_x = max(MIN_X, jogador_x - vel)
        elif joy_x > 600: # Direita
            fator = (joy_x - 600.0) / 423.0
            vel = max(5, int(velocidade_jogador_max * fator))
            jogador_x = min(MAX_X, jogador_x + vel)

        # DISPAROS DO JOGADOR
        tiro_duplo_ativo = (agora < bonus_tiro_duplo_ate)
        ataque_area_ativo = (agora < bonus_ataque_area_ate)

        if btn_tiro == 0 and (agora - tempo_ultimo_tiro >= INTERVALO_TIRO):
            if tiro_duplo_ativo:
                tiros.append({"x": jogador_x - 14, "y": ALTURA - 60, "area": ataque_area_ativo})
                tiros.append({"x": jogador_x + 14, "y": ALTURA - 60, "area": ataque_area_ativo})
            else:
                tiros.append({"x": jogador_x, "y": ALTURA - 60, "area": ataque_area_ativo})
                
            enviar_comando(arduino, 'T')
            tempo_ultimo_tiro = agora

        # Atualiza Posição dos Tiros
        for t in tiros[:]:
            t['y'] -= 15
            if t['y'] < 0:
                tiros.remove(t)

        # Atualiza Itens de Bônus Flutuantes (Usando bonus.png)
        for b in bonuses[:]:
            b['y'] += 2.0
            if (abs(b['x'] - jogador_x) < 35) and (b['y'] > ALTURA - 75):
                if b['tipo'] == 'tiro_duplo':
                    bonus_tiro_duplo_ate = agora + BONUS_DURATION
                    popups.append({"texto": "⚡ TIRO DUPLO ATIVADO!", "cor": (241, 196, 15), "x": jogador_x, "y": ALTURA - 90, "criado": agora})
                elif b['tipo'] == 'ataque_area':
                    bonus_ataque_area_ate = agora + BONUS_DURATION
                    popups.append({"texto": "💥 ATAQUE EM ÁREA ATIVADO!", "cor": (155, 89, 182), "x": jogador_x, "y": ALTURA - 90, "criado": agora})
                
                enviar_comando(arduino, 'E')
                bonuses.remove(b)
            elif b['y'] > ALTURA:
                bonuses.remove(b)

        # MOVIMENTAÇÃO DOS INIMIGOS E HABILIDADES ESPECIAIS
        buff_velocidade_ativo = (agora < buff_velocidade_inimigos_ate)

        for a in aliens[:]:
            if agora < a.get('congelado_ate', 0.0):
                continue

            mult_buff = 1.5 if buff_velocidade_ativo else 1.0
            vel_atual = velocidade_base_inimigo * mult_buff

            if a['tipo'] == 'verde': # Subchefe Creeper Verde (Movimentação Zig-Zag)
                a['y'] += vel_atual * 0.8
                a['x'] = a['x_base'] + math.sin(a['y'] * 0.04) * 80.0
            elif a['tipo'] == 'zangado':
                a['dash_timer'] -= dt
                if a['dash_timer'] <= 0:
                    a['em_dash'] = True
                    if a['dash_timer'] < -0.8:
                        a['em_dash'] = False
                        a['dash_timer'] = random.uniform(2.5, 4.5)

                if a['em_dash']:
                    a['y'] += vel_atual * 2.2
                else:
                    a['y'] += vel_atual
                a['x'] = a['x_base']
            elif a['tipo'] == 'gelo':
                a['y'] += vel_atual * 0.85
                a['x'] = a['x_base'] + math.sin(a['y'] * 0.08) * 15.0
            elif a['tipo'] == 'boss_malware':
                # BOSS FLUTUA NO TOPO: Movimentação lateral + dash, mas NUNCA desce da zona segura
                BOSS_Y_LIMITE = 220.0  # Limite inferior: boss não passa desta linha
                a['dash_timer'] -= dt
                if a['dash_timer'] <= 0:
                    a['em_dash'] = True
                    if a['dash_timer'] < -0.8:
                        a['em_dash'] = False
                        a['dash_timer'] = random.uniform(2.5, 4.0)

                # Movimento vertical suave (oscila ao redor de y=80-120)
                a['y'] = 80.0 + math.sin(agora * 0.8 + a['x_base'] * 0.01) * 40.0
                a['x'] = a['x_base'] + math.sin(agora * 1.1) * 180.0
                # Garante que nunca ultrapasse o limite inferior
                if a['y'] > BOSS_Y_LIMITE:
                    a['y'] = BOSS_Y_LIMITE
            else:
                a['y'] += vel_atual
                a['x'] = a['x_base']

            # CASO O INIMIGO PASSE PELA BORDA DE BAIXO
            # BOSS MALWARE NUNCA ESCAPA: Fica preso acima (movimento controlado acima)
            if a['y'] > ALTURA - 75 and a['tipo'] != 'boss_malware':
                dano = MOB_RARITY.get(a['tipo'], {}).get('dano_fuga', 5.0)
                # AURA DO BOSS: Inimigos comuns causam o DOBRO DO DANO de fuga!
                if boss_aura_ativo:
                    dano *= 2.0
                    popups.append({"texto": f"☠ AURA! -{int(dano)}s", "cor": (231, 76, 60), "x": a['x'], "y": ALTURA - 90, "criado": agora})
                else:
                    popups.append({"texto": f"-{int(dano)}s", "cor": (231, 76, 60), "x": a['x'], "y": ALTURA - 90, "criado": agora})
                tempo_restante -= dano

                if a in aliens:
                    aliens.remove(a)
                    if fase_jogo == "JOGO_NORMAL":
                        aliens.append(novo_inimigo(COLUNAS_X, pontuacao=pontuacao))

            # COLISÃO E PROCESSAMENTO DE DANO
            ax, ay = a['x'], a['y']
            w, h = a['largura'], a['altura']
            
            for t in tiros[:]:
                eh_tiro_area = t.get('area', False)
                dist_impacto = math.hypot(ax - t['x'], ay - t['y'])
                colidiu_direto = (ax - w//2 < t['x'] < ax + w//2) and (ay - 10 < t['y'] < ay + h + 10)

                if colidiu_direto or (eh_tiro_area and dist_impacto <= 120.0):
                    
                    # TELEPORTE (50% de chance para Teleport e Boss Malware)
                    if (a['tipo'] in ['teleport', 'boss_malware']) and random.random() < TELEPORT_CHANCE:
                        nova_col = random.randint(0, len(COLUNAS_X) - 1)
                        a['coluna'] = nova_col
                        a['x'] = float(COLUNAS_X[nova_col])
                        a['x_base'] = float(COLUNAS_X[nova_col])
                        a['y'] = max(30.0, a['y'] - random.uniform(30, 80))

                        popups.append({"texto": "🌀 TELEPORTE!", "cor": (155, 89, 182), "x": a['x'], "y": a['y'], "criado": agora})
                        if t in tiros and not eh_tiro_area:
                            tiros.remove(t)
                        continue

                    # Reduz HP
                    a['hp'] -= 1
                    if t in tiros:
                        tiros.remove(t)

                    enviar_comando(arduino, 'M')

                    # DERROTA DO INIMIGO (HP <= 0)
                    if a['hp'] <= 0:
                        pts_ganhos = 100 if a['tipo'] == 'boss_malware' else MOB_RARITY.get(a['tipo'], {}).get('pontos', 10)
                        pontuacao += pts_ganhos
                        total_inimigos_derrotados += 1
                        velocidade_base_inimigo += 0.01

                        tam_exp = 240 if a['tipo'] == 'boss_malware' else (140 if a['tipo'] == 'verde' else 110)
                        explosoes.append({"x": ax, "y": ay, "criado": agora, "tamanho": tam_exp})

                        # DROP RARO DO ITEM BÔNUS (5% de chance)
                        if random.random() < BONUS_DROP_CHANCE:
                            tipo_b = 'tiro_duplo' if random.random() < 0.5 else 'ataque_area'
                            bonuses.append({"tipo": tipo_b, "x": ax, "y": ay})

                        # HABILIDADE GELO: 40% de chance de congelar apenas inimigos próximos
                        if a['tipo'] == 'gelo' and random.random() < FREEZE_CHANCE:
                            RAIO_CONGELAMENTO = 220.0
                            for outro in aliens:
                                dist = math.hypot(outro['x'] - ax, outro['y'] - ay)
                                if dist <= RAIO_CONGELAMENTO:
                                    outro['congelado_ate'] = agora + 3.0

                            popups.append({"texto": "❄ INIMIGOS CONGELADOS! ❄", "cor": (52, 152, 219), "x": ax, "y": ay - 30, "criado": agora})

                        # HABILIDADE CHARGED: Buff de velocidade + efeito do sprite charged-attack.png
                        if a['tipo'] == 'charged':
                            buff_velocidade_inimigos_ate = agora + CHARGED_BUFF_DURATION
                            efeitos_raio.append({"x": ax, "y": ay, "criado": agora})
                            popups.append({"texto": "⚡ SURTO CHARGED!", "cor": (230, 126, 34), "x": ax, "y": ay - 20, "criado": agora})

                        # SUBCHEFE CREEPER VERDE DERROTADO: +30s LOOT + EXPLODE TODOS OS INIMIGOS (EXCETO BOSS MALWARE!)
                        if a['tipo'] == 'verde':
                            tempo_restante += 30.0
                            enviar_comando(arduino, 'E')
                            popups.append({"texto": "+30s LOOT & BOMBA TOTAL!", "cor": (46, 204, 113), "x": ax, "y": ay - 30, "criado": agora})

                            # EXPLODE INIMIGOS COMUNS (EXCETO O BOSS MALWARE!)
                            for outro in aliens[:]:
                                if outro != a and outro['tipo'] != 'boss_malware':
                                    explosoes.append({"x": outro['x'], "y": outro['y'], "criado": agora, "tamanho": 110})
                                    if outro in aliens:
                                        aliens.remove(outro)

                        # BOSS MALWARE DERROTADO: Multiplicar tempo atual por 1.25 + Aura desativada + Bomba de área gigante
                        elif a['tipo'] == 'boss_malware':
                            tempo_restante = tempo_restante * BOSS_TIME_MULTIPLIER_ON_DEFEAT
                            boss_ativo = False
                            boss_aura_ativo = False  # AURA ENCERRADA ao derrotar o Boss
                            enviar_comando(arduino, 'E')

                            popups.append({"texto": "★ BOSS DERROTADO! TEMPO x 1.25 ★", "cor": (241, 196, 15), "x": LARGURA // 2, "y": 180, "criado": agora})

                            for outro in aliens[:]:
                                if outro != a:
                                    explosoes.append({"x": outro['x'], "y": outro['y'], "criado": agora, "tamanho": 110})
                                    if outro in aliens:
                                        aliens.remove(outro)
                        else:
                            tempo_restante += 2.0
                            popups.append({"texto": "+2s", "cor": (46, 204, 113), "x": ax, "y": ay, "criado": agora})

                        if a in aliens:
                            aliens.remove(a)
                            if fase_jogo == "JOGO_NORMAL":
                                aliens.append(novo_inimigo(COLUNAS_X, pontuacao=pontuacao))

        # DESENHO NA TELA
        tela.fill((10, 12, 22))

        # FUNDO ESTELAR RETRO DINÂMICO (COM PARALAXE E DIVERSAS CORES DE ESTRELAS)
        for est in estrelas:
            est['y'] = (est['y'] + est['vel']) % ALTURA
            pygame.draw.circle(tela, est['cor'], (int(est['x']), int(est['y'])), est['tam'])

        # Linhas guia suaves das 5 Colunas
        for cx in COLUNAS_X:
            pygame.draw.line(tela, (25, 30, 48), (cx, 50), (cx, ALTURA - 20), 1)

        # NAVE DO JOGADOR
        px = jogador_x
        py = ALTURA - 50
        if SPRITES.get('nave'):
            tela.blit(SPRITES['nave'], (px - 24, py - 24))
        else:
            pygame.draw.polygon(tela, (46, 204, 113), [(px, py - 22), (px - 24, py + 10), (px + 24, py + 10)])

        # TIROS DO JOGADOR
        for t in tiros:
            cor_t = (155, 89, 182) if t.get('area', False) else (241, 196, 15)
            if SPRITES.get('tiro'):
                tela.blit(SPRITES['tiro'], (t['x'] - 6, t['y']))
            else:
                pygame.draw.rect(tela, cor_t, (t['x'] - 2, t['y'], 5, 14), border_radius=2)

        # ITENS DE BÔNUS FLUTUANTES (USANDO bonus.png)
        for b in bonuses:
            if SPRITES.get('bonus'):
                tela.blit(SPRITES['bonus'], (b['x'] - 16, b['y'] - 16))
            else:
                pygame.draw.circle(tela, (241, 196, 15), (int(b['x']), int(b['y'])), 14)

        # RENDERIZAÇÃO DO EFEITO VISUAL CHARGED-ATTACK (RAIO CHARGED)
        for ef in efeitos_raio[:]:
            if agora - ef['criado'] > 0.6:
                efeitos_raio.remove(ef)
                continue
            if SPRITES.get('charged-attack'):
                tela.blit(SPRITES['charged-attack'], (int(ef['x']) - 40, int(ef['y']) - 40))

        # INIMIGOS, SUBCHEFE E BOSS MALWARE
        for a in aliens:
            ax, ay = int(a['x']), int(a['y'])
            if ay + a['altura'] > 0:
                esta_congelado = agora < a.get('congelado_ate', 0.0)

                # Desenha Boss Malware (20 HP) ou Subchefe Creeper (5 HP)
                if a['tipo'] in ['boss_malware', 'verde']:
                    sp_key = 'enemy-boss-malware' if a['tipo'] == 'boss_malware' else 'enemy-verde'

                    # EFEITO AURA DO BOSS: Pulso vermelho brilhante ao redor do sprite
                    if a['tipo'] == 'boss_malware' and boss_aura_ativo:
                        pulso = int(20 + 15 * math.sin(agora * 6.0))
                        aura_surf = pygame.Surface((a['largura'] + pulso*2, a['altura'] + pulso*2), pygame.SRCALPHA)
                        aura_surf.fill((0, 0, 0, 0))
                        pygame.draw.ellipse(aura_surf, (200, 30, 30, 90), (0, 0, a['largura'] + pulso*2, a['altura'] + pulso*2))
                        pygame.draw.ellipse(aura_surf, (255, 80, 0, 50), (pulso//2, pulso//2, a['largura'] + pulso, a['altura'] + pulso))
                        tela.blit(aura_surf, (ax - a['largura']//2 - pulso, ay - pulso))

                    if SPRITES.get(sp_key):
                        tela.blit(SPRITES[sp_key], (ax - a['largura']//2, ay))
                    else:
                        cor_c = (231, 76, 60) if a['tipo'] == 'boss_malware' else (46, 204, 113)
                        pygame.draw.rect(tela, cor_c, (ax - a['largura']//2, ay, a['largura'], a['altura']), border_radius=12)

                    # BARRA DE VIDA DOS CHEFES / SUBCHEFES (5 HP Creeper / 20 HP Boss)
                    if a['hp_max'] > 1:
                        hp_w = 70 if a['tipo'] == 'verde' else 80
                        hp_x = ax - hp_w // 2
                        hp_y = ay - 12
                        pygame.draw.rect(tela, (40, 20, 20), (hp_x, hp_y, hp_w, 7), border_radius=3)
                        fill_hp = int(hp_w * (a['hp'] / float(a['hp_max'])))
                        if fill_hp > 0:
                            cor_hp = (46, 204, 113) if a['tipo'] == 'verde' else (231, 76, 60)
                            pygame.draw.rect(tela, cor_hp, (hp_x, hp_y, fill_hp, 7), border_radius=3)
                        pygame.draw.rect(tela, (255, 255, 255), (hp_x, hp_y, hp_w, 7), width=1, border_radius=3)

                else:
                    sprite_key = f"enemy-{a['tipo']}"
                    sprite_img = SPRITES.get(sprite_key) or SPRITES.get('enemy-default')

                    if sprite_img:
                        tela.blit(sprite_img, (ax - a['largura']//2, ay))
                    else:
                        pygame.draw.rect(tela, (231, 76, 60), (ax - a['largura']//2, ay, a['largura'], a['altura']), border_radius=8)

                if esta_congelado:
                    s_ice = pygame.Surface((a['largura'] + 8, a['altura'] + 8), pygame.SRCALPHA)
                    s_ice.fill((52, 152, 219, 140))
                    tela.blit(s_ice, (ax - a['largura']//2 - 4, ay - 4))
                    pygame.draw.rect(tela, (200, 240, 255), (ax - a['largura']//2 - 4, ay - 4, a['largura'] + 8, a['altura'] + 8), width=2, border_radius=6)

        # RENDERIZAÇÃO DAS EXPLOSÕES USANDO O SPRITE explosion.gif
        for ex in explosoes[:]:
            decorrido_exp = agora - ex['criado']
            if decorrido_exp > 0.5:
                explosoes.remove(ex)
                continue

            progresso = decorrido_exp / 0.5
            tam_max = ex.get('tamanho', 110)
            tam_atual = int(tam_max * (0.5 + 0.5 * progresso))

            if SPRITES.get('explosion'):
                img_exp = pygame.transform.scale(SPRITES['explosion'], (tam_atual, tam_atual))
                tela.blit(img_exp, (int(ex['x']) - tam_atual // 2, int(ex['y']) - tam_atual // 2))
            else:
                pygame.draw.circle(tela, (241, 196, 15), (int(ex['x']), int(ex['y'])), tam_atual // 2)

        # --- HUD SUPERIOR ---
        pygame.draw.rect(tela, (20, 25, 38), (0, 0, LARGURA, 50))
        pygame.draw.line(tela, (45, 52, 70), (0, 50), (LARGURA, 50), 2)

        txt_score = fonte_hud.render(f"PTS: {pontuacao:04d}", True, (255, 255, 255))
        tela.blit(txt_score, (20, 15))

        # BARRA DE TEMPO DE VIDA
        bar_x, bar_y, bar_w, bar_h = 240, 16, 320, 18
        pygame.draw.rect(tela, (30, 35, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=9)
        
        pct_tempo = max(0.0, min(1.0, tempo_restante / TEMPO_MAXIMO_REF))
        fill_w = int(bar_w * pct_tempo)

        if pct_tempo > 0.5:
            cor_barra = (46, 204, 113)
        elif pct_tempo > 0.25:
            cor_barra = (241, 196, 15)
        else:
            cor_barra = (231, 76, 60)

        if fill_w > 0:
            pygame.draw.rect(tela, cor_barra, (bar_x, bar_y, fill_w, bar_h), border_radius=9)
        pygame.draw.rect(tela, (70, 80, 100), (bar_x, bar_y, bar_w, bar_h), width=2, border_radius=9)

        txt_tempo = fonte_hud.render(f"TEMPO: {tempo_restante:4.1f}s", True, (255, 255, 255))
        tela.blit(txt_tempo, (bar_x + bar_w//2 - txt_tempo.get_width()//2, bar_y - 1))

        status_str = f"ARDUINO ({arduino.port})" if arduino else "TECLADO"
        cor_st = (46, 204, 113) if arduino else (241, 196, 15)
        txt_status = fonte_hud.render(status_str, True, cor_st)
        tela.blit(txt_status, (LARGURA - txt_status.get_width() - 20, 15))

        # POPUPS FLUTUANTES
        for p in popups[:]:
            decorrido = agora - p['criado']
            if decorrido > 1.4:
                popups.remove(p)
                continue

            y_popup = p['y'] - int(decorrido * 35)
            x_popup = p['x']

            txt_pop = fonte_popup.render(p['texto'], True, p['cor'])
            tela.blit(txt_pop, (x_popup - txt_pop.get_width()//2, y_popup))

        # RODAPÉ DE INSTRUÇÕES
        txt_fase = f"FASE: {fase_jogo}"
        txt_dica = fonte_sub.render(f"{txt_fase} | Fundo Estelar Retro | Creeper não afeta Malware | Horda Máx 15", True, (140, 150, 170))
        tela.blit(txt_dica, (LARGURA // 2 - txt_dica.get_width() // 2, ALTURA - 20))

        pygame.display.flip()
        relogio.tick(60)

    return
