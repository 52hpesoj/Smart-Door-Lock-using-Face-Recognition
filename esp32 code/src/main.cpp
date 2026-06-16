#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ==========================================
// CONFIGURATION
// ==========================================
const char* ssid = "Android";         // <-- Change this
const char* password = "joseph1234";  // <-- Change this

// Pin Definitions
const int BUTTON_PIN = 14; // The Doorbell
const int GREEN_LED = 25;
const int RED_LED = 26;
const int BUZZER = 27;

// Initialize the LCD
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Create the web server on port 80
WebServer server(80);

// Memory variable to catch quick doorbell taps
bool doorbellRung = false; 

// ==========================================
// HARDWARE CONTROL FUNCTIONS
// ==========================================

void lockSystem() {
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, HIGH);
  digitalWrite(BUZZER, LOW);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SYSTEM SECURE");
  lcd.setCursor(0, 1);
  lcd.print("Awaiting Scan...");
  
  Serial.println("System Locked.");
}

void grantAccess(String personName) {
  digitalWrite(RED_LED, LOW);
  digitalWrite(GREEN_LED, HIGH);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ACCESS GRANTED");
  lcd.setCursor(0, 1);
  lcd.print(personName); // <-- Prints the dynamic name!
  
  // Audio Cue: Two short beeps
  digitalWrite(BUZZER, HIGH); delay(150);
  digitalWrite(BUZZER, LOW); delay(100);
  digitalWrite(BUZZER, HIGH); delay(150);
  digitalWrite(BUZZER, LOW);
  
  Serial.println("Access Granted to: " + personName);
  server.send(200, "text/plain", "Granted Sequence Complete");
}

void denyAccess() {
  digitalWrite(GREEN_LED, LOW);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("ACCESS DENIED");
  lcd.setCursor(0, 1);
  lcd.print("Unknown Entity");
  
  // Audio Cue: One long angry beep and flash red
  digitalWrite(RED_LED, HIGH);
  digitalWrite(BUZZER, HIGH);
  delay(1000); 
  digitalWrite(BUZZER, LOW);
  digitalWrite(RED_LED, LOW);
  
  // Return to locked state
  delay(1000);
  lockSystem();
  
  Serial.println("Access Denied Triggered.");
  server.send(200, "text/plain", "Denied Sequence Complete");
}

// ==========================================
// SETUP & LOOP
// ==========================================

void setup() {
  Serial.begin(115200);
  
  // Configure Pins
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("BOOTING UP...");
  
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("Door Controller IP Address: ");
  Serial.println(WiFi.localIP());
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("IP Address:");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP().toString());
  delay(4000); // Show IP on screen for 4 seconds
  
  // Define Web Routes
  server.on("/granted", []() {
    String recognizedName = "Welcome!"; // Default fallback
    if (server.hasArg("name")) {
      recognizedName = "Welcome " + server.arg("name"); // Grab the name from Python
    }
    grantAccess(recognizedName); 
  });
  server.on("/denied", denyAccess);
  server.on("/lock", []() {
    lockSystem();
    server.send(200, "text/plain", "Locked Sequence Complete");
  });
  
  // The Doorbell Route (Reads from memory)
  server.on("/button", HTTP_GET, []() {
    if (doorbellRung == true) {
      server.send(200, "text/plain", "pressed");
      doorbellRung = false; // Reset the memory immediately after Python reads it!
    } else {
      server.send(200, "text/plain", "idle");
    }
  });
  
  server.begin();
  lockSystem(); // Start in locked state
}

void loop() {
  server.handleClient(); // Listen for Wi-Fi commands
  
  // Catch the Doorbell Tap and save it to memory
  if (digitalRead(BUTTON_PIN) == LOW) {
    doorbellRung = true;
  }
}