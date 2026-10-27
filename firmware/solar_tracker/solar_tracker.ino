/*
  Dual-axis solar tracker - Arduino Uno + 2x SG90 + 4x LDR
  ------------------------------------------------------------
  WIRING
    Each LDR:   5V --- LDR ---+--- analog pin
                              |
                             10k
                              |
                             GND        (more light = bigger number)

    LDR TOP    (the one farthest from the panel)  -> A0
    LDR BOTTOM (the one closest to the panel)     -> A1
    LDR EAST   (on the lid's "E" side)            -> A2
    LDR WEST   (on the lid's "W" side)            -> A3

    Panel +  --- 10k ---+--- 10k --- GND      panel - to GND
                        |
                        A4   (measures panel voltage, max 10 V)

    Pan servo  (east-west, in base)   signal -> D9
    Tilt servo (up-down, on the yoke) signal -> D10
    Servo red -> 5V, brown -> GND.  Better: power servos from a separate
    5V supply (4xAA or USB power bank), with GND connected to Arduino GND.

  CALIBRATION (do once, with a phone flashlight)
    1. Upload, open Serial Monitor at 9600.
    2. Shine the light from the east: pan must turn toward it.
       If it turns away -> change PAN_DIR to -1.
    3. Shine the light from above/in front: tilt must move toward it.
       If it moves away -> change TILT_DIR to -1.
*/
#include <Servo.h>

// ---------- pins ----------
const int LDR_TOP = A0, LDR_BOT = A1, LDR_EAST = A2, LDR_WEST = A3;
const int PANEL_V = A4;
const int PAN_PIN = 9, TILT_PIN = 10;

// ---------- settings ----------
int PAN_DIR  = 1;     // flip to -1 if pan moves the wrong way
int TILT_DIR = 1;     // flip to -1 if tilt moves the wrong way
const int TOLERANCE  = 25;    // ignore differences smaller than this (stops shaking)
const int DARK_LEVEL = 60;    // average below this = night
const int PAN_MIN = 0,  PAN_MAX = 180;    // 90 = facing south
const int TILT_MIN = 0, TILT_MAX = 140;   // 90 = panel flat. The sensor-head end can only go DOWN ~50 deg
                                          // past flat. If it hits the base near 140, use 40 and 180 instead.
const int STEP_DELAY = 30;    // ms between steps (bigger = slower, smoother)
const unsigned long LOG_EVERY = 5000;   // print data every 5 s

Servo pan, tilt;
int panPos = 90, tiltPos = 90;
unsigned long lastLog = 0;

int readAvg(int pin) {           // average 8 readings to reduce noise
  long s = 0;
  for (int i = 0; i < 8; i++) s += analogRead(pin);
  return s / 8;
}

void setup() {
  Serial.begin(9600);
  pan.attach(PAN_PIN);
  tilt.attach(TILT_PIN);
  pan.write(panPos);
  tilt.write(tiltPos);
  delay(1000);
  Serial.println(F("time_s,top,bottom,east,west,pan,tilt,panel_V"));
}

void loop() {
  int top = readAvg(LDR_TOP), bot = readAvg(LDR_BOT);
  int east = readAvg(LDR_EAST), west = readAvg(LDR_WEST);
  int avg = (top + bot + east + west) / 4;

  if (avg < DARK_LEVEL) {
    // night: park facing east, ready for sunrise
    panPos = PAN_DIR > 0 ? PAN_MIN + 10 : PAN_MAX - 10;
    tiltPos = 90;
  } else {
    int dEW = east - west;
    int dTB = top - bot;
    if (abs(dEW) > TOLERANCE) panPos  += (dEW > 0 ? -1 : 1) * PAN_DIR;
    if (abs(dTB) > TOLERANCE) tiltPos += (dTB > 0 ? -1 : 1) * TILT_DIR;
    panPos  = constrain(panPos,  PAN_MIN,  PAN_MAX);
    tiltPos = constrain(tiltPos, TILT_MIN, TILT_MAX);
  }
  pan.write(panPos);
  tilt.write(tiltPos);

  if (millis() - lastLog >= LOG_EVERY) {   // CSV log for your experiment
    lastLog = millis();
    float v = analogRead(PANEL_V) * 5.0 / 1023.0 * 2.0;   // x2 because of the divider
    Serial.print(millis() / 1000); Serial.print(',');
    Serial.print(top);  Serial.print(','); Serial.print(bot);  Serial.print(',');
    Serial.print(east); Serial.print(','); Serial.print(west); Serial.print(',');
    Serial.print(panPos); Serial.print(','); Serial.print(tiltPos); Serial.print(',');
    Serial.println(v, 2);
  }
  delay(STEP_DELAY);
}
