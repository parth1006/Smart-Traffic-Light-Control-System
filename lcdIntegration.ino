#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <LiquidCrystal.h>
#include <ArduinoJson.h>  // You'll need to install this library

// WiFi credentials
const char* ssid = "iPhone";
const char* password = "Rakshitjan14@";

// Cat Facts API
const char* apiUrl = "https://catfact.ninja/fact";

// LCD pins
const int rs = D0, en = D1, d4 = D2, d5 = D3, d6 = D4, d7 = D5;
LiquidCrystal lcd(rs, en, d4, d5, d6, d7);

unsigned long previousMillis = 0;
const long interval = 60000;  // Fetch new fact every minute

// String to store the current cat fact
String catFact = "Waiting for cat fact...";

void setup() {
  // Initialize serial
  Serial.begin(115200);
  
  // Initialize LCD
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Cat Facts:");
  lcd.setCursor(0, 1);
  lcd.print("Connecting WiFi");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    lcd.setCursor(attempts % 16, 1);
    lcd.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected to WiFi!");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected!");
    lcd.setCursor(0, 1);
    lcd.print("Getting facts...");
    
    // Get first cat fact immediately
    getCatFact();
  } else {
    Serial.println("\nFailed to connect to WiFi.");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("WiFi Failed!");
    lcd.setCursor(0, 1);
    lcd.print("Check settings");
  }
  
  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();

  // Check if it's time to get a new cat fact
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    if (WiFi.status() == WL_CONNECTED) {
      getCatFact();
    } else {
      Serial.println("WiFi Disconnected! Attempting to reconnect...");
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("WiFi Lost");
      lcd.setCursor(0, 1);
      lcd.print("Reconnecting...");
      WiFi.reconnect();
    }
  }
  
  // Scroll the cat fact across the LCD
  displayScrollingText();
}

void getCatFact() {
  Serial.println("Fetching cat fact...");
  
  WiFiClientSecure client;
  client.setInsecure();  // Skip certificate validation
  
  HTTPClient https;
  
  if (https.begin(client, apiUrl)) {
    https.addHeader("User-Agent", "ESP8266CatFactClient/1.0");
    https.setTimeout(5000);
    
    int httpCode = https.GET();
    Serial.print("HTTP code: ");
    Serial.println(httpCode);
    
    if (httpCode == HTTP_CODE_OK) {
      String payload = https.getString();
      Serial.println("😺 Cat Fact:");
      Serial.println(payload);
      
      // Parse JSON to extract just the fact
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, payload);
      
      // Extract the fact and store it
      catFact = doc["fact"].as<String>();
      
      // Reset the LCD display
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Cat Fact:");
    } else {
      Serial.print("❌ HTTP Error: ");
      Serial.println(https.errorToString(httpCode));
      catFact = "Error getting fact";
    }
    
    https.end();
  } else {
    Serial.println("❌ Unable to connect to Cat Facts API");
    catFact = "Connection failed";
  }
}

void displayScrollingText() {
  // Clear second line
  lcd.setCursor(0, 1);
  lcd.print("                ");
  
  // If fact is longer than 16 characters, scroll it
  if (catFact.length() > 16) {
    // First display as much as fits
    lcd.setCursor(0, 1);
    lcd.print(catFact.substring(0, 16));
    delay(1000); // Let user start reading
    
    // Then scroll the text
    for (int i = 0; i <= catFact.length() - 16; i++) {
      lcd.setCursor(0, 1);
      lcd.print(catFact.substring(i, i + 16));
      delay(300); // Scroll speed
    }
    
    // Pause at the end before restarting
    delay(1000);
  } else {
    // If fact fits on display, just show it
    lcd.setCursor(0, 1);
    lcd.print(catFact);
    delay(1000);
  }
}