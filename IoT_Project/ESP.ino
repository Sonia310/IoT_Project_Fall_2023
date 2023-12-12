#include "ESP8266WiFi.h"
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>

const char* ssid = "nelip0t";
const char* password = "Thisismypass123";

const char* mqtt_server = "192.168.125.78";

WiFiClient raspPi;
PubSubClient client(raspPi);

#define SS_PIN D8
#define RST_PIN D0

MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

byte nuidPICC[4];

static String lastPublishedCardID = "";

void setup() {
  Serial.begin(115200);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  SPI.begin();
  rfid.PCD_Init();
  Serial.println();
  Serial.print(F("Reader :"));
  rfid.PCD_DumpVersionToSerial();
  
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }

  printHex(key.keyByte, MFRC522::MF_KEY_SIZE);
}

void loop() {
  int lightValue = getPhotoSensorValue();

  if (!client.connected()) {
    reconnect();
  }

  if (!client.loop())
    client.connect("raspPi");

  Serial.println(lightValue);

  // Always publish light value to "GetSensorValue" topic
  client.publish("GetSensorValue", String(lightValue).c_str());

  if (!rfid.PICC_IsNewCardPresent())
    return;

  if (!rfid.PICC_ReadCardSerial())
    return;

  MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
  if (piccType != MFRC522::PICC_TYPE_MIFARE_MINI &&
      piccType != MFRC522::PICC_TYPE_MIFARE_1K &&
      piccType != MFRC522::PICC_TYPE_MIFARE_4K) {
    return;
  }

  String currentCardID = printDecCustom(rfid.uid.uidByte, rfid.uid.size);

  if (currentCardID != lastPublishedCardID) {
    // Card ID is different from the last published value
    for (byte i = 0; i < 4; i++) {
      nuidPICC[i] = rfid.uid.uidByte[i];
    }

    Serial.print(F("In dec:"));
    printDec(rfid.uid.uidByte, rfid.uid.size);
    Serial.println();

    // Publish RFID UID to "GetCard" topic
    client.publish("GetCard", currentCardID.c_str());

    // Update the last published card ID
    lastPublishedCardID = currentCardID;
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(2000);
}

void setup_wifi() {
  delay(10);

  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connection Successful");
  Serial.print("WiFi connected - ESP-8266 IP address: ");
  Serial.println(WiFi.localIP());
}

int getPhotoSensorValue() {
  // read the photo sensor value
  delay(1000);

  // read the input on analog pin 0:
  int sensorValue = analogRead(A0);

  // return out the value you read:
  return sensorValue;
}

void callback(String topic, byte* message, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
 
  String messagein;

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    messagein += (char)message[i];
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.println();
    Serial.print("Attempting MQTT connection...");
 
    if (client.connect("raspPi")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 3 seconds");
     
      // Wait 3 seconds before retrying
      delay(2000);
    }
  }
}

void printHex(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], HEX);
  }
}

void printDec(byte *buffer, byte bufferSize) {
  for (byte i = 0; i < bufferSize; i++) {
    Serial.print(buffer[i] < 0x10 ? " 0" : " ");
    Serial.print(buffer[i], DEC);
  }
}

String printDecCustom(byte *buffer, byte bufferSize) {
  String result = "";
  for (byte i = 0; i < bufferSize; i++) {
    result += (buffer[i] < 0x10 ? " 0" : " ");
    result += String(buffer[i], DEC);
  }
  return result;
}
