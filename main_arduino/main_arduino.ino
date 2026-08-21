const int PIN_X = A0;
const int PIN_Y = A1;
const int PIN_BTN_MENU = 2; // Clique do analógico (SW) - Força a volta para o Launcher
const int PIN_BTN_TIRE = 3; // Botão de ação na protoboard
const int PIN_BUZZER = 8;
const int PIN_LED = 13;

unsigned long ultimoTempo = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_BTN_MENU, INPUT_PULLUP);
  pinMode(PIN_BTN_TIRE, INPUT_PULLUP);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
}

void loop() {
  // Envia dados do hardware a 60Hz (~16ms)
  if (millis() - ultimoTempo >= 16) {
    ultimoTempo = millis();
    Serial.print(analogRead(PIN_X)); Serial.print(",");
    Serial.print(analogRead(PIN_Y)); Serial.print(",");
    Serial.print(digitalRead(PIN_BTN_MENU)); Serial.print(",");
    Serial.println(digitalRead(PIN_BTN_TIRE));
  }

  // Escuta os comandos que o Launcher ou os jogos enviam de volta
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == 'T') { // Tiro (Space Invaders / Doom)
      digitalWrite(PIN_LED, HIGH);
      tone(PIN_BUZZER, 1100, 40);
      delay(40);
      digitalWrite(PIN_LED, LOW);
    } 
    else if (cmd == 'M') { // Morte do Inimigo (Space Invaders)
      for(int f = 300; f > 100; f -= 30) { tone(PIN_BUZZER, f, 12); delay(12); }
      noTone(PIN_BUZZER);
    } 
    else if (cmd == 'E') { // Fanfarra Vitória (Easter Egg Labirinto)
      int notas[] = {262, 330, 392, 523};
      for (int i = 0; i < 4; i++) {
        digitalWrite(PIN_LED, HIGH);
        tone(PIN_BUZZER, notas[i], 120); delay(140);
        digitalWrite(PIN_LED, LOW);
      }
    }
  }
}
