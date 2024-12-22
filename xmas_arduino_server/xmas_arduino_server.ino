#include <Servo.h>


Servo servo1, servo2, servo3, servo4;
int servoPins[] = {3, 5, 6, 9}; // Pins for servos
int outputPins[] = {10, 11, 12, 13}; // Pins for digital outputs

void setup() {
  Serial.begin(9600);

  // Attach servos to their pins
  servo1.attach(servoPins[0]);
  servo2.attach(servoPins[1]);
  servo3.attach(servoPins[2]);
  servo4.attach(servoPins[3]);

  // Initialize digital output pins
  for (int i = 0; i < 4; i++) {
    pinMode(outputPins[i], OUTPUT);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    executeCommand(command);
  }
}

void executeCommand(String command) {
  // Find the delimiter between servo and digital commands
  int delimiterIndex = command.indexOf(';');
  
  String servoCommand = command.substring(1, delimiterIndex);
  String digitalCommand = command.substring(delimiterIndex + 2);

  // Parse and execute servo commands
  int sPos[4];
  for (int i = 0; i < 4; i++) {
    int commaIndex = servoCommand.indexOf(',');
    sPos[i] = servoCommand.substring(0, commaIndex).toInt();
    servoCommand = servoCommand.substring(commaIndex + 1);
  }

  servo1.write(sPos[0]);
  servo2.write(sPos[1]);
  servo3.write(sPos[2]);
  servo4.write(sPos[3]);

  // Parse and execute digital output commands
  for (int i = 0; i < 4; i++) {
    int dState = digitalCommand.substring(0, 1).toInt();
    digitalWrite(outputPins[i], dState);
    digitalCommand = digitalCommand.substring(2);
  }
}