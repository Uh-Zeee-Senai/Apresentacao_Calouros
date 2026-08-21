const int PIN_X = A0;
const int PIN_Y = A1;
const int PIN_BTN_MENU = 2; // Clique do analógico (SW) - Força a volta para o Launcher
const int PIN_BTN_TIRE = 3; // Botão de ação na protoboard
const int PIN_BUZZER = 8;   // Buzzer para Efeitos Sonoros (Tiro, Morte, Vitória)
const int PIN_LED = 13;

unsigned long ultimoTempo = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN_MENU, INPUT_PULLUP);
  pinMode(PIN_BTN_TIRE, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
}

void loop() {
  // Transmissão Serial dos Controles a 60Hz (~16ms)
  if (millis() - ultimoTempo >= 16) {
    ultimoTempo = millis();
    Serial.print(analogRead(PIN_X)); Serial.print(",");
    Serial.print(analogRead(PIN_Y)); Serial.print(",");
    Serial.print(digitalRead(PIN_BTN_MENU)); Serial.print(",");
    Serial.println(digitalRead(PIN_BTN_TIRE));
  }

  // Efeitos sonoros acionados via comando Serial do Python
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == 'T') { 
      // Tiro acionado: Som curto no Buzzer (Pino 8)
      tone(PIN_BUZZER, 1000, 30);
    } 
    else if (cmd == 'M') { 
      // Inimigo Atingido: LED no pino 13 + Som de impacto no Buzzer (Pino 8)
      digitalWrite(PIN_LED, HIGH);
      tone(PIN_BUZZER, 350, 40);
      delay(40);
      digitalWrite(PIN_LED, LOW);
    } 
    else if (cmd == 'E') { 
      // Fanfarra Vitória
      int notas[] = {262, 330, 392, 523};
      for (int i = 0; i < 4; i++) {
        digitalWrite(PIN_LED, HIGH);
        tone(PIN_BUZZER, notas[i], 100); 
        delay(110);
        digitalWrite(PIN_LED, LOW);
      }
    }
  }
}
