#include "DHT.h"

#define DHTPINA 2     // Digital pin connected to the DHT sensor
//#define DHTPINB 3     // Digital pin connected to the DHT sensor
//#define DHTPINC 4     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11   // DHT 11

#define SENSOR0 A0   // first sensor
#define SENSOR1 A1   // first sensor

#ifdef DHTPINA
DHT dhtA(DHTPINA, DHTTYPE);
#endif
#ifdef DHTPINB
DHT dhtB(DHTPINB, DHTTYPE);
#endif
#ifdef DHTPINC
DHT dhtC(DHTPINC, DHTTYPE);
#endif

// take a reading every 5 seconds then average it over the minute
int averageCounter = 0;
int averageCounterMax = 20;
int delay_ = 5000;
int do_ = 0;

String str;

void config(String str_){
  Serial.println(str_);
  delay(20000);
  #ifdef SENSOR0
  Serial.println("CONFIGdevice_class:illuminance,name:Light_Outside,unit_of_measurement:°C,value_template:{{value_json.LightOutside|float*50/1024|int}}");
  #endif

  #ifdef SENSOR1
  delay(100);
  Serial.println("CONFIGdevice_class:None,name:Moisture_Outside,unit_of_measurement:Moisture,value_template:{{value_json.MoistureOutside}}");
  #endif

  #ifdef DHTPINA
  delay(100);
  Serial.println("CONFIGdevice_class:temperature,name:Temp_3,unit_of_measurement:°C,value_template:{{value_json.Temp3}}");
  delay(100);
  Serial.println("CONFIGdevice_class:humidity,name:Humidity_3,unit_of_measurement:°C,value_template:{{value_json.Humidity3}}");
  #endif
}

void setup() {
  Serial.begin(115200);
  #ifdef DHTPINA
  dhtA.begin();
  #endif
  #ifdef DHTPINB
  dhtB.begin();
  #endif
  #ifdef DHTPINC
  dhtC.begin();
  #endif

 
  config("Starting...");
  delay(1000);
}

int index = 0;
int index_max = 60;
void loop()
{
  #ifdef SENSOR0
  int readingA0 = 0;
  #endif
  #ifdef SENSOR1
  int readingA1 = 0;
  #endif

  #ifdef DHTPINA
  float hA = 0;
  float tA = 0;
  #endif
  #ifdef DHTPINB
  float hB = 0;
  float tB = 0;
  #endif
  #ifdef DHTPINC
  float hV = 0;
  float tC = 0;
  #endif


  for (int i = 0; i < averageCounterMax; i++) {

  #ifdef DHTPINA
    hA        += dhtA.readHumidity();
    tA        += dhtA.readTemperature();
  #endif
  #ifdef DHTPINB
    hB        += dhtB.readHumidity();
    tB        += dhtB.readTemperature();
  #endif
  #ifdef DHTPINC
    hC        += dhtC.readHumidity();
    tC        += dhtC.readTemperature();
  #endif

  #ifdef SENSOR0
    readingA0 += analogRead(SENSOR0);
  #endif
  #ifdef SENSOR1
    readingA1 += analogRead(SENSOR1);
  #endif

  delay(delay_);
  }


  #ifdef DHTPINA
  hA = hA/averageCounterMax;
  tA = tA/averageCounterMax;
  #endif
  #ifdef DHTPINB
  hB = hB/averageCounterMax;
  tB = tB/averageCounterMax;
  #endif
  #ifdef DHTPINC
  hC = hC/averageCounterMax;
  tC = tC/averageCounterMax;
  #endif

  #ifdef SENSOR0
  readingA0 = readingA0/averageCounterMax;
  #endif
  #ifdef SENSOR1
  readingA1 = readingA1/averageCounterMax;
  #endif


  str = String("{ ");
  #ifdef DHTPINA
  str += String(  "\"TempOutside\" : ") + String(tA);
  str += String(", \"HumidityOutside\" : ") + String(hA);
  #endif
  #ifdef DHTPINB
  str += String(  "\"TempOutside\" : ") + String(tB);
  str += String(", \"HumidityOutside\" : ") + String(hB);
  #endif
  #ifdef DHTPINC
  str += String(  "\"TempOutside\" : ") + String(tC);
  str += String(", \"HumidityOutside\" : ") + String(hC);
  #endif

  #ifdef SENSOR0
  str += String(", \"LightOutside\" : ") + String(readingA0);
  #endif
  #ifdef SENSOR1
  str += String(", \"MoistureOutside\" : ") + String(readingA1);
  #endif

  str += String(" }");
  Serial.println(str);

  if ( index > index_max){
    index = 0;
    config("Restarting...");
  }

}