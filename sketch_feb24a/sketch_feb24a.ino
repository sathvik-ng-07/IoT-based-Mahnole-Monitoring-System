/******************************************************
   Simple Monitoring Code for Arduino Mega 2560
   Components: 
   - DHT Sensor (DHT11 or DHT22)
   - MQ Gas Sensor (Analog)
   - HC-SR04 Ultrasonic Sensor
*******************************************************/

#include <DHT.h>  // Adafruit DHT library

// 1) Pin Definitions
#define DHTPIN 2           // DHT data pin
#define DHTTYPE DHT11      // or DHT22 if you're using that model
#define MQ_PIN A0          // MQ sensor analog pin
#define TRIG_PIN 9         // Ultrasonic trigger
#define ECHO_PIN 10        // Ultrasonic echo

// 2) Create DHT object
DHT dht(DHTPIN, DHTTYPE);

// 3) Setup function
void setup() {
  Serial.begin(9600);
  
  // Pin modes
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(MQ_PIN, INPUT);

  // Initialize DHT
  dht.begin();
  
  // Print an initial message
  Serial.println("Starting Manhole Monitoring...");
  Serial.println("-----------------------------");
}

// 4) Function to read distance from Ultrasonic Sensor
float readDistance() {
  // Ensure trigger is LOW for a moment
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  // Send a 10µs pulse to TRIG
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Read the time of the echo pulse
  long duration = pulseIn(ECHO_PIN, HIGH);

  // Convert the time into distance (in cm)
  float distance = duration * 0.0343 / 2; 
  return distance;
}

// 5) Function to read gas level from MQ sensor
int readGasLevel() {
  return analogRead(MQ_PIN);
}

// 6) Main loop
void loop() {
  // Read temperature & humidity
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Read distance from ultrasonic
  float distance = readDistance();

  // Read gas sensor
  int gasValue = readGasLevel();

  // Check if DHT sensor reading is valid
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Error reading DHT sensor!");
  } else {
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.print(" °C,  Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  }

  // Print ultrasonic reading
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");

  // Print gas sensor reading
  Serial.print("Gas Sensor Value: ");
  Serial.println(gasValue);

  // Separator
  Serial.println("-----------------------------");

  // Delay between readings
  delay(2000);  // 2 seconds
}
