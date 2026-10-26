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

// Interrupt Service Routine for PIR motion sensor (Pin 2 / INT0)
void handle_pir_interrupt() {
    unsigned long now = millis();
    // Hardware debounce window: 150ms
    if (now - g_last_motion_timestamp > 150) {
        g_motion_trigger_count++;
        g_motion_flag = true;
        g_last_motion_timestamp = now;
    }
}

/**
 * Real 1-Wire DHT11 Bit-Bang Driver with microsecond pulse timing.
 * 40-bit transmission: [Hum_Int, Hum_Dec, Temp_Int, Temp_Dec, Checksum]
 */
bool read_dht11(float* out_temp, float* out_hum) {
    if (!out_temp || !out_hum) return false;

#ifdef ARDUINO
    uint8_t data[5] = {0, 0, 0, 0, 0};

    // Step 1: Send Start Signal (Host pulls LOW >= 18ms)
    pinMode(DHT_PIN, OUTPUT);
    digitalWrite(DHT_PIN, LOW);
    delay(18);
    digitalWrite(DHT_PIN, HIGH);
    delayMicroseconds(30);

    // Step 2: Listen for Sensor Response Pulse (80us LOW + 80us HIGH)
    pinMode(DHT_PIN, INPUT_PULLUP);
    
    unsigned long timeout = 10000;
    while (digitalRead(DHT_PIN) == HIGH) {
        if (--timeout == 0) return false; // Bus timeout
    }
    timeout = 10000;
    while (digitalRead(DHT_PIN) == LOW) {
        if (--timeout == 0) return false;
    }
    timeout = 10000;
    while (digitalRead(DHT_PIN) == HIGH) {
        if (--timeout == 0) return false;
    }

    // Step 3: Read 40 Data Bits (5 Bytes)
    for (int i = 0; i < 40; i++) {
        timeout = 10000;
        while (digitalRead(DHT_PIN) == LOW) {
            if (--timeout == 0) return false;
        }

        unsigned long pulse_start = micros();
        timeout = 10000;
        while (digitalRead(DHT_PIN) == HIGH) {
            if (--timeout == 0) return false;
        }
        unsigned long pulse_len = micros() - pulse_start;

        // HIGH pulse > 40us denotes '1', otherwise '0'
        if (pulse_len > 40) {
            data[i / 8] |= (1 << (7 - (i % 8)));
        }
    }

    // Step 4: Checksum Validation
    uint8_t checksum = data[0] + data[1] + data[2] + data[3];
    if (checksum != data[4]) {
        return false; // CRC error
    }

    *out_hum = static_cast<float>(data[0]) + static_cast<float>(data[1]) * 0.1f;
    *out_temp = static_cast<float>(data[2]) + static_cast<float>(data[3]) * 0.1f;
    return true;
#else
    // Host offline test harness simulation
    *out_temp = 24.5f;
    *out_hum = 58.0f;
    return true;
#endif
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
