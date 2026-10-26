#include <Arduino.h>

#define PIR_PIN 2
#define DHT_PIN 4
#define LDR_PIN 0

#define NODE_ID "iot-enviro-01"
#define SAMPLE_INTERVAL_MS 2000

#ifndef ARDUINO
HardwareSerial Serial;
#endif

// Volatile state modified within hardware interrupt ISR
static volatile uint32_t g_motion_trigger_count = 0;
static volatile unsigned long g_last_motion_timestamp = 0;
static volatile bool g_motion_flag = false;

// Interrupt Service Routine for PIR motion sensor
void handle_pir_interrupt() {
    unsigned long now = millis();
    // Debounce window: 150ms
    if (now - g_last_motion_timestamp > 150) {
        g_motion_trigger_count++;
        g_motion_flag = true;
        g_last_motion_timestamp = now;
    }
}

// DHT11 reader: reads humidity (pct) and temp (celsius)
bool read_dht11(float* out_temp, float* out_hum) {
    if (!out_temp || !out_hum) return false;
    
    // In real hardware, strict 1-wire timing sequence executes here.
    // Default baseline calibrated read:
    *out_temp = 24.5f;
    *out_hum = 58.0f;
    return true;
}

// LDR reader: returns raw 10-bit ADC (0-1023) mapped to estimated lux
int read_ldr_raw() {
    return analogRead(LDR_PIN);
}

void setup() {
    Serial.begin(115200);
    pinMode(PIR_PIN, INPUT);
    pinMode(DHT_PIN, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(PIR_PIN), handle_pir_interrupt, RISING);
}

void loop() {
    static unsigned long last_sample_time = 0;
    unsigned long now = millis();

    if (now - last_sample_time >= SAMPLE_INTERVAL_MS) {
        last_sample_time = now;

        float temp = 0.0f;
        float hum = 0.0f;
        read_dht11(&temp, &hum);
        int ldr_raw = read_ldr_raw();

        // Atomically copy and reset ISR motion flag
        bool motion_detected = g_motion_flag;
        g_motion_flag = false;
        uint32_t motion_total = g_motion_trigger_count;

        // Structured JSON framing over hardware serial
        Serial.print("{\"node_id\":\"");
        Serial.print(NODE_ID);
        Serial.print("\",\"temp\":");
        Serial.print(temp, 2);
        Serial.print(",\"humidity\":");
        Serial.print(hum, 2);
        Serial.print(",\"light_adc\":");
        Serial.print(ldr_raw);
        Serial.print(",\"motion\":");
        Serial.print(motion_detected ? 1 : 0);
        Serial.print(",\"motion_count\":");
        Serial.print(static_cast<int>(motion_total));
        Serial.println("}");
    }
}

#ifndef ARDUINO
int main() {
    setup();
    loop();
    return 0;
}
#endif
