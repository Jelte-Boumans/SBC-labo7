#include <Wire.h>

#define POT A0

#define LED_R 5
#define LED_G 6

char seed[16] =  { "rzebczwwhpnflsyr" } ;
char crypt[16] = { "                " } ;
int adcval = 1023;

void setup() {
  Serial.begin(9600);
  
  Wire.begin(0x08); // Address = 8
  Wire.onRequest(request);
  Wire.onReceive(receive);

  pinMode(POT, INPUT);
  pinMode(A4, INPUT); // SDA
  pinMode(A5, INPUT); // SCL
  pinMode(LED_R, OUTPUT);
  pinMode(LED_G, OUTPUT);

  digitalWrite(LED_R, LOW);
  digitalWrite(LED_G, LOW);
}

void loop() {
  delay(1);
}

void request() {
  adcval = analogRead(POT);
  adcflipencrypt(adcval);
  Wire.write(crypt);
}

void receive() {
  while (Wire.available()) {
    char transactState = Wire.read();  // c = confirm and r = reject
    Serial.println(transactState);

    if(transactState == 'c') {
      digitalWrite(LED_R, LOW);
      digitalWrite(LED_G, HIGH);
    }
    else if (transactState == 'r') {
      digitalWrite(LED_R, HIGH);
      digitalWrite(LED_G, LOW);
    }
  }
}

void adcflipencrypt (int adc) {
 int adcbit = adc ; 
 for ( byte p=0; p<16; p++ ) {
   byte abit = adcbit & 1;
   adcbit = adcbit >> 1;
   byte sb = ( seed[p] >> 3) & 1;
   if (sb) {
      if (abit) { crypt[p] = seed[p] & 0b11110111;} else { crypt[p] = seed[p] | 0b00001000; }
   } else {
      if (abit) { crypt[p] = seed[p] | 0b00001000;} else { crypt[p] = seed[p] & 0b11110111; } 
   }
 }  
}

/*
int adcflipdecrypt ( char hexseed[16], char hexcrypt[16] ) {
   int adcv = 0;
   for ( byte p=0; p<16; p++ ) {
     byte cbit = ( crypt[p] & 0b00001000 ) >> 3;
     byte sbit = ( seed[p]  & 0b00001000 ) >> 3;

     if ( sbit ) {
         if (!cbit) adcv |= 1 << p;          
     } else {
        if (cbit) adcv |= 1 << p;
     }
   } 
   return adcv;
}*/
