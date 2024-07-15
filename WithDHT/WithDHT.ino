#include "DHT.h"

#define DHTTYPE DHT11   // DHT 11

#define DHTPINA 2     // Digital pin connected to the DHT sensor
//#define DHTPINB 3     // Digital pin connected to the DHT sensor
//#define DHTPINC 4     // Digital pin connected to the DHT sensor

#define SENSOR0 A0   // first sensor
#define SENSOR1 A1   // first sensor

#ifdef DHTPINA
DHT dhtA(DHTPINA, DHTTYPE);
String tA_name = "Temp 3";
String tA_json = "Temp3";
String hA_name = "Humidity 3";
String hA_json = "Humidity3";
#endif
#ifdef DHTPINB
DHT dhtB(DHTPINB, DHTTYPE);
String tB_name = "Temp 4";
String tB_json = "Temp4";
String hB_name = "Humidity 4";
String hB_json = "Humidity4";
#endif
#ifdef DHTPINC
DHT dhtC(DHTPINC, DHTTYPE);
String tC_name = "Temp 5";
String tC_json = "Temp5";
String hC_name = "Humidity 5";
String hC_json = "Humidity5";
#endif
#ifdef SENSOR0
String sA_name = "Light_Outside";
String sA_json = "LightOutside|float*50/1024|int";
#endif
#ifdef SENSOR1
String sB_name = "Moisture_Outside";
String sB_json = "Moisture_Outside";
#endif



// take a reading every 5 seconds then average it over the minute
int averageCounter = 0;
int averageCounterMax = 20;
int delay_ = 5000;
int do_ = 0;


void config(String str_){
  Serial.println(str_);
  delay(20000);
  #ifdef SENSOR0
  Serial.println("CONFIGdevice_class:illuminance,name:"+sA_name+",unit_of_measurement:°C,value_template:{{value_json."+sA_json+"}}");
  #endif

  #ifdef SENSOR1
  delay(100);
  Serial.println("CONFIGdevice_class:None,name:"+sB_name+",unit_of_measurement:Moisture,value_template:{{value_json."+sB_json+"}}");
  #endif

  #ifdef DHTPINA
  delay(100);
  Serial.println("CONFIGdevice_class:temperature,name:"+tA_name+",unit_of_measurement:°C,value_template:{{value_json."+tA_json+"}}");
  delay(100);
  Serial.println("CONFIGdevice_class:humidity,name:"+hA_name+",unit_of_measurement:°C,value_template:{{value_json."+hA_json+"}}");
  #endif
  #ifdef DHTPINB
  delay(100);
  Serial.println("CONFIGdevice_class:temperature,name:"+tB_name+",unit_of_measurement:°C,value_template:{{value_json."+tB_json+"}}");
  delay(100);
  Serial.println("CONFIGdevice_class:humidity,name:"+hB_name+",unit_of_measurement:°C,value_template:{{value_json."+hB_json+"}}");
  #endif
  #ifdef DHTPINC
  delay(100);
  Serial.println("CONFIGdevice_class:temperature,name:"+tC_name+",unit_of_measurement:°C,value_template:{{value_json."+tC_json+"}}");
  delay(100);
  Serial.println("CONFIGdevice_class:humidity,name:"+hC_name+",unit_of_measurement:°C,value_template:{{value_json."+hC_json+"}}");
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
  float hC = 0;
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


  String str = String("{ ");
  #ifdef DHTPINA
  str += String(  "\"TempOutside\" : ") + String(tA);
  str += String(", \"HumidityOutside\" : ") + String(hA);
  #endif
  #ifdef DHTPINB
  str += String(", \"TempOutside\" : ") + String(tB);
  str += String(", \"HumidityOutside\" : ") + String(hB);
  #endif
  #ifdef DHTPINC
  str += String(", \"TempOutside\" : ") + String(tC);
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