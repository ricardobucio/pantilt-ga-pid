// BORRADOR (no probado aún): recibe "P<deg>,T<deg>\n" por serial y mueve 2 servos. Requiere librería ESP32Servo.
#include <ESP32Servo.h>
Servo pan, tilt; unsigned long lastMsg = 0; String buf;
void setup() { Serial.begin(115200); pan.attach(18, 500, 2400); tilt.attach(19, 500, 2400); pan.write(90); tilt.write(90); }
void loop() {
  while (Serial.available()) { char c = Serial.read();
    if (c == '\n') { int p = buf.indexOf('P'), t = buf.indexOf('T');
      if (p >= 0 && t > p) { pan.write(constrain(buf.substring(p + 1).toFloat(), 0, 180)); tilt.write(constrain(buf.substring(t + 1).toFloat(), 0, 180)); lastMsg = millis(); }
      buf = ""; } else buf += c; }
  if (millis() - lastMsg > 300) { pan.write(90); tilt.write(90); }  // watchdog: vuelve al centro
}
