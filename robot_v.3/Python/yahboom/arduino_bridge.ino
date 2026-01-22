/**
 * Arduino bridge for main board:
 * - PING -> PONG for sanity check
 * - LED <0|1> to toggle front light (relay/LED pin)
 * - SVP <id> to run servo presets
 * - Publishes telemetry every 50 ms:
 *     IMU X:<yaw> Y:<pitch> Z:<roll>   (from MPU-6050 complementary filter)
 *     IR1 <adc>
 *     IR2 <adc>
 *
 * Hardware:
 * - Servo + sensors only (motors handled by Yahboom motor driver)
 * - MPU-6050 IMU over I2C
 * - 2x analog IR sensors on A2/A3 (edit if needed)
 *
 * Edit the pin map to match your wiring before flashing.
 */

#include <Arduino.h>
#include <Wire.h>
#include <MPU6050_tockn.h>
#include <Servo.h>

// ---------------- Pin mapping ----------------
// IR analog pins
const uint8_t IR1_PIN = A2;
const uint8_t IR2_PIN = A3;
const uint8_t IR_BACK_PIN = A4;  // optional back IR

// Light/LED pin (set to your relay/LED control pin; on Mega choose any free digital)
const uint8_t LED_PIN = 22;

// Servo pins (adjust to your hardware)
const uint8_t SERVO_G1 = 24;  // Lift Arm
const uint8_t SERVO_K1 = 25;  // Rotate Gripper
const uint8_t SERVO_K2 = 26;  // Open/Close Gripper
const uint8_t SERVO_S1 = 27;  // Main Barrier
const uint8_t SERVO_S2 = 28;  // Dead Barrier
const uint8_t SERVO_C1 = 29;  // Camera

// Telemetry period (ms)
const uint16_t TELEMETRY_MS = 50;  // 20 Hz

// IMU (MPU-6050)
MPU6050 mpu(Wire);
bool imuReady = false;

// Servos
Servo G1, K1, K2, S1, S2, C1;
float lastServoPosG1 = 13.0;
float lastServoPosK1 = 180.0;
float lastServoPosK2 = 49.0;
float lastServoPosS1 = 120.0;
float lastServoPosS2 = 0.0;
float lastServoPosC1 = 0.0;

// Command buffer
const size_t BUF_SIZE = 96;
char rxBuf[BUF_SIZE];
size_t rxLen = 0;

// ---------------- Command parsing ----------------
void handleLine(char *line) {
  char *cmd = strtok(line, " \r\n");
  if (!cmd) return;

  if (strcmp(cmd, "PING") == 0) {
    Serial.println("PONG");
    return;
  }

  if (strcmp(cmd, "LED") == 0) {
    char *t1 = strtok(NULL, " ");
    if (t1) {
      int on = atoi(t1);
      digitalWrite(LED_PIN, on ? HIGH : LOW);
      Serial.println("OK LED");
    } else {
      Serial.println("ERR LED ARGS");
    }
    return;
  }

  if (strcmp(cmd, "SVP") == 0) {  // Servo preset
    char *t1 = strtok(NULL, " ");
    if (t1) {
      int preset = atoi(t1);
      switch (preset) {
        case 1: lower_arm(); break;
        case 2: raise_arm_left(); break;
        case 3: raise_arm_right(); break;
        case 4: open_gate1(); break;
        case 5: close_gate1(); break;
        case 6: open_gate2(); break;
        case 7: close_gate2(); break;
        default: Serial.println("ERR SVP ID"); return;
      }
      Serial.println("OK SVP");
    } else {
      Serial.println("ERR SVP ARGS");
    }
    return;
  }

  if (strcmp(cmd, "STOP") == 0) {
    Serial.println("OK STOP");
    return;
  }

  Serial.println("ERR UNKNOWN");
}

// ---------------- Setup / loop ----------------
void setup() {
  Serial.begin(115200);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  G1.attach(SERVO_G1);
  K1.attach(SERVO_K1);
  K2.attach(SERVO_K2);
  S1.attach(SERVO_S1);
  S2.attach(SERVO_S2);
  C1.attach(SERVO_C1);

  G1.write(lastServoPosG1);
  K1.write(lastServoPosK1);
  K2.write(lastServoPosK2);
  S1.write(lastServoPosS1);
  S2.write(lastServoPosS2);
  C1.write(lastServoPosC1);

  Wire.begin();
  if (mpu.begin()) {
    mpu.calcGyroOffsets(true);  // optional self-calibration; could be set manual
    imuReady = true;
  } else {
    Serial.println("WARN NO_MPU6050");
  }

  Serial.println("READY");
}

// Servo preset motions (adapted from servo_main)
void lower_arm() {
  float EndPosG1 = 153;
  float EndPosK1 = 91;
  float EndPosK2 = 80;

  float MoveK1_Start = 60;
  float MoveK1_End = 130;
  float MoveK2_Start = 60;
  float MoveK2_End = 120;

  for (int servoPos = (int)lastServoPosG1; servoPos <= EndPosG1; servoPos++) {
    G1.write(servoPos);
    if ((servoPos >= MoveK1_Start) && (servoPos <= MoveK1_End)) {
      K1.write(lastServoPosK1 - ((lastServoPosK1 - EndPosK1) * ((servoPos - MoveK1_Start) / (MoveK1_End - MoveK1_Start))));
    }
    if ((servoPos >= MoveK2_Start) && (servoPos <= MoveK2_End)) {
      K2.write(lastServoPosK2 + ((EndPosK2 - lastServoPosK2) * ((servoPos - MoveK2_Start) / (MoveK2_End - MoveK2_Start))));
    }
    delay(5);
  }
  lastServoPosG1 = EndPosG1;
  lastServoPosK1 = EndPosK1;
  lastServoPosK2 = EndPosK2;
}

void raise_arm_left() {
  float StopPosG1_1 = 40;
  float StopPosG1_2 = 70;
  float StopPosK1 = 0;
  float StopPosK2 = 60;

  float MoveK1_Start_1 = 140;
  float MoveK1_End_1 = 100;

  float EndPosG1 = 15;
  float EndPosK1 = 180;
  float EndPosK2 = 49;

  float MoveK1_Start_2 = 50;
  float MoveK1_End_2 = 40;

  K2.write(EndPosK2);
  delay(500);

  for (int servoPos = (int)lastServoPosG1; servoPos >= StopPosG1_1; servoPos--) {
    G1.write(servoPos);
    if ((servoPos <= MoveK1_Start_1) && (servoPos >= MoveK1_End_1)) {
      K1.write(lastServoPosK1 + ((lastServoPosK1 - StopPosK1) * ((servoPos - MoveK1_Start_1) / (MoveK1_Start_1 - MoveK1_End_1))));
    }
    delay(5);
  }
  lastServoPosK1 = StopPosK1;

  delay(500);
  K2.write(StopPosK2);
  delay(500);
  K2.write(EndPosK2);

  G1.write(StopPosG1_2);
  delay(300);
  lastServoPosG1 = StopPosG1_2;

  for (int servoPos = (int)lastServoPosG1; servoPos >= EndPosG1; servoPos--) {
    G1.write(servoPos);
    if ((servoPos <= MoveK1_Start_2) && (servoPos >= MoveK1_End_2)) {
      K1.write(lastServoPosK1 + ((lastServoPosK1 - EndPosK1) * ((servoPos - MoveK1_Start_2) / (MoveK1_Start_2 - MoveK1_End_2))));
    }
    delay(2);
  }

  lastServoPosG1 = EndPosG1;
  lastServoPosK1 = EndPosK1;
  lastServoPosK2 = EndPosK2;
}

void raise_arm_right() {
  float StopPosG1_1 = 40;
  float StopPosG1_2 = 55;
  float StopPosK1 = 180;
  float StopPosK2 = 70;

  float MoveK1_Start_1 = 140;
  float MoveK1_End_1 = 100;

  float EndPosG1 = 15;
  float EndPosK1 = 180;
  float EndPosK2 = 49;

  K2.write(EndPosK2);
  delay(500);

  for (int servoPos = (int)lastServoPosG1; servoPos >= StopPosG1_1; servoPos--) {
    G1.write(servoPos);
    if ((servoPos <= MoveK1_Start_1) && (servoPos >= MoveK1_End_1)) {
      K1.write(lastServoPosK1 + ((lastServoPosK1 - StopPosK1) * ((servoPos - MoveK1_Start_1) / (MoveK1_Start_1 - MoveK1_End_1))));
    }
    delay(5);
  }
  lastServoPosK1 = StopPosK1;

  delay(500);
  K2.write(StopPosK2);
  delay(500);
  K2.write(EndPosK2);

  G1.write(StopPosG1_2);
  delay(300);
  lastServoPosG1 = StopPosG1_2;

  for (int servoPos = (int)lastServoPosG1; servoPos >= EndPosG1; servoPos--) {
    G1.write(servoPos);
    if (servoPos >= MoveK1_End_1) {
      K1.write(lastServoPosK1 + ((lastServoPosK1 - EndPosK1) * ((servoPos - MoveK1_End_1) / (MoveK1_Start_1 - MoveK1_End_1))));
    }
    delay(2);
  }

  lastServoPosG1 = EndPosG1;
  lastServoPosK1 = EndPosK1;
  lastServoPosK2 = EndPosK2;
}

void open_gate1() {
  float EndPosS1 = 0;
  for (int servoPos = (int)lastServoPosS1; servoPos >= EndPosS1; servoPos--) {
    S1.write(servoPos);
    delay(2);
  }
  lastServoPosS1 = EndPosS1;
}

void close_gate1() {
  float EndPosS1 = 120;
  for (int servoPos = (int)lastServoPosS1; servoPos <= EndPosS1; servoPos++) {
    S1.write(servoPos);
    delay(2);
  }
  lastServoPosS1 = EndPosS1;
}

void open_gate2() {
  float EndPosS2 = 120;
  for (int servoPos = (int)lastServoPosS2; servoPos <= EndPosS2; servoPos++) {
    S2.write(servoPos);
    delay(2);
  }
  lastServoPosS2 = EndPosS2;
}

void close_gate2() {
  float EndPosS2 = 0;
  for (int servoPos = (int)lastServoPosS2; servoPos >= EndPosS2; servoPos--) {
    S2.write(servoPos);
    delay(2);
  }
  lastServoPosS2 = EndPosS2;
}
void loop() {
  // Handle incoming serial
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      rxBuf[rxLen] = '\0';
      handleLine(rxBuf);
      rxLen = 0;
    } else if (rxLen < BUF_SIZE - 1) {
      rxBuf[rxLen++] = c;
    }
  }

  static uint32_t lastTel = 0;
  uint32_t now = millis();
  if (now - lastTel >= TELEMETRY_MS) {
    lastTel = now;

    if (imuReady) {
      mpu.update();
      Serial.print("IMU X:");
      Serial.print(mpu.getAngleZ());  // yaw
      Serial.print(" Y:");
      Serial.print(mpu.getAngleY());  // pitch
      Serial.print(" Z:");
      Serial.println(mpu.getAngleX());  // roll
    } else {
      Serial.println("IMU X:No Y:No Z:No");
    }

    int ir1 = analogRead(IR1_PIN);
    int ir2 = analogRead(IR2_PIN);
    int irb = analogRead(IR_BACK_PIN);
    Serial.print("IR1 ");
    Serial.println(ir1);
    Serial.print("IR2 ");
    Serial.println(ir2);
    Serial.print("IRB ");
    Serial.println(irb);
  }
}
