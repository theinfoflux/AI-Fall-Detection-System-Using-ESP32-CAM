#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "AndroidAP3DEC";
const char* password = "11122233";

WebServer server(80);

#define RELAY_PIN 2

void handleLightOn() {
  digitalWrite(RELAY_PIN, HIGH);
  server.send(200, "text/plain", "LIGHT ON");
}

void handleLightOff() {
  digitalWrite(RELAY_PIN, LOW);
  server.send(200, "text/plain", "LIGHT OFF");
}

void setup() {

  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);

  digitalWrite(RELAY_PIN, LOW);

  WiFi.begin(ssid, password);

  Serial.print("Connecting");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi Connected");

  Serial.print("XIAO IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/lighton", handleLightOn);
  server.on("/lightoff", handleLightOff);

  server.begin();

  Serial.println("Server Started");
}

void loop() {
  server.handleClient();
}
