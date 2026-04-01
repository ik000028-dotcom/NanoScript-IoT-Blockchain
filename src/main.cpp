#include <Arduino.h>
#include <Arduino_MKRGPS.h>
#include <DHT.h>

#define DHTPIN A1
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

double lastLat = 0;
double lastLng = 0;
bool gpsFix = false;

void setup() {
  Serial.begin(9600);
  while (!Serial);

  GPS.begin();
  dht.begin();
}

void loop() {
  // Always read GPS in background
  if (GPS.available()) {
    lastLat = GPS.latitude();
    lastLng = GPS.longitude();
    gpsFix = true;
  }

  // Read DHT every 2 seconds
  static unsigned long lastRead = 0;
  if (millis() - lastRead >= 2000) {
    lastRead = millis();

    float t = dht.readTemperature();
    float h = dht.readHumidity();

    Serial.println("----------------------");

    Serial.print("Temperature: "); Serial.println(t);
    Serial.print("Humidity: "); Serial.println(h);

    if (gpsFix) {
      Serial.print("Latitude: "); Serial.println(lastLat, 6);
      Serial.print("Longitude: "); Serial.println(lastLng, 6);
    } else {
      Serial.println("Waiting for GPS fix...");
    }
  }
} 