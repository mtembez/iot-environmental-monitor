#ifndef ARDUINO_MOCK_H
#define ARDUINO_MOCK_H

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

#define HIGH 0x1
#define LOW  0x0

#define INPUT 0x0
#define OUTPUT 0x1
#define INPUT_PULLUP 0x2

#define RISING 0x2
#define FALLING 0x3
#define CHANGE 0x4

typedef uint8_t byte;
typedef bool boolean;

inline unsigned long millis(void) { return 0; }
inline unsigned long micros(void) { return 0; }
inline void delay(unsigned long ms) { (void)ms; }
inline void delayMicroseconds(unsigned int us) { (void)us; }
inline void pinMode(uint8_t pin, uint8_t mode) { (void)pin; (void)mode; }
inline int digitalRead(uint8_t pin) { (void)pin; return 0; }
inline void digitalWrite(uint8_t pin, uint8_t val) { (void)pin; (void)val; }
inline int analogRead(uint8_t pin) { (void)pin; return 512; }
inline uint8_t digitalPinToInterrupt(uint8_t pin) { return pin; }
inline void attachInterrupt(uint8_t interruptNum, void (*userFunc)(void), int mode) {
    (void)interruptNum; (void)userFunc; (void)mode;
}

class HardwareSerial {
public:
    void begin(unsigned long baud) { (void)baud; }
    void print(const char* s) { printf("%s", s); }
    void print(int n) { printf("%d", n); }
    void print(float f, int prec = 2) { printf("%.*f", prec, f); }
    void println(const char* s) { printf("%s\n", s); }
    void println(int n) { printf("%d\n", n); }
    void println(void) { printf("\n"); }
};

extern HardwareSerial Serial;

#endif // ARDUINO_MOCK_H
