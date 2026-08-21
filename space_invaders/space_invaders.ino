// Definição dos Pinos (Baseado na montagem física do Master Kit)
const int PIN_X = A0;         // Eixo X do Joystick para movimentação
const int PIN_Y = A1;         // Eixo Y do Joystick (reservado para menus futuros)
const int PIN_BTN_MENU = 2;   // Clique do Analógico (SW)
const int PIN_BTN_TIRE = 3;   // Botão de Tiro fixo na protoboard
const int PIN_BUZZER = 8;     // Buzzer para efeitos sonoros
const int PIN_LED = 13;        // LED indicador de disparos

// Variáveis de debounce e temporização
unsigned long ultimoTempoEnvio = 0;
const int intervaloEnvio = 16; // Mantém o envio fixo em ~60Hz

void setup() {
  // Inicializa a comunicação Serial em alta velocidade (115200 bps)
  Serial.begin(115200);
  
  // Configura os pinos dos botões com resistores internos de Pull-Up
  pinMode(PIN_BTN_MENU, INPUT_PULLUP);
  pinMode(PIN_BTN_TIRE, INPUT_PULLUP);
  
  // Configura os pinos de saída para atuadores
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
}

void loop() {
  // 1. Controle de frequência de envio para evitar sobrecarga no buffer serial
  unsigned long tempoAtual = millis();
  if (tempoAtual - ultimoTempoEnvio >= intervaloEnvio) {
    ultimoTempoEnvio = tempoAtual;

    // Leitura dos sensores analógicos e botões digitais
    int xVal = analogRead(PIN_X);
    int yVal = analogRead(PIN_Y);
    int btnMenu = digitalRead(PIN_BTN_MENU);
    int btnTire = digitalRead(PIN_BTN_TIRE);

    // Envio formatado por vírgulas para o Python: X,Y,BotaoMenu,BotaoTiro
    Serial.print(xVal);
    Serial.print(",");
    Serial.print(yVal);
    Serial.print(",");
    Serial.print(btnMenu);
    Serial.print(",");
    Serial.println(btnTire);
  }

  // 2. Escuta comandos recebidos de volta do notebook (Gatilhos de Feedback)
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    if (comando == 'T') {
      // Efeito sonoro e visual de TIRO (Som agudo curto)
      digitalWrite(PIN_LED, HIGH);
      tone(PIN_BUZZER, 1200, 30);
      delay(30);
      digitalWrite(PIN_LED, LOW);
    } 
    else if (comando == 'M') {
      // Efeito sonoro de EXPLOSÃO do alien (Som grave decrescente)
      for(int freq = 250; freq > 80; freq -= 30) {
        tone(PIN_BUZZER, freq, 10);
        delay(10);
      }
      noTone(PIN_BUZZER);
    }
  }
}
