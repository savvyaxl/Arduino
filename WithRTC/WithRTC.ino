// modes
// mode 1 seed
// mode 2 grow
// mode 3 flower
// mode 4 test
int mode = 2;

// Water
int timesPerWeek = 2;
int duration = 30;

String indexNO = "3";
int realStartDay = 2;            // Sunday is really 1, 2 is Monday
int startDay = realStartDay + 5; // 1 is Sunday, WTF
int startHour = 6;
int startMinute = 4;

// CONNECTIONS:
// DS1302 CLK/SCLK
#define SCLK 5
// DS1302 DAT/IO
#define DAT 4
// DS1302 RST/CE
#define RST 2

// DS1302 VCC --> 3.3v - 5v
// DS1302 GND --> GND
// RST  --> 2
// DAT  --> 4
// SCLK  --> 5
// Relay1  --> 6
// Relay2  --> 7
// Relay3  --> 8
// Relay4  --> 9
// LightSwitch --> 10
// PumpSwitch1 --> 11
// PumpSwitch2 --> 12

const unsigned int MAX_MESSAGE_LENGTH = 255;

#include <ThreeWire.h>
#include <RtcDS1302.h>
#include <TimeLib.h>
#include <TimeAlarms.h>

int Relay1 = 6;
int Relay2 = 7;
int Relay3 = 8;
int Relay4 = 9;
int LightSwitch = 10; // instant on/off
int PumpSwitch1 = 11; // instant on/off
int PumpSwitch2 = 12; // instant on/off

int LightsONOFF = 0;
int PumpONOFF1 = 0;
int PumpONOFF2 = 0;

ThreeWire myWire(DAT, SCLK, RST); // DAT/IO, CLK/SCLK, RST/CE
RtcDS1302<ThreeWire> Rtc(myWire);

// Red Relay - OFF LOW
// Blue Relay - OFF HIGH
#define ON LOW
#define OFF HIGH

void setup()
{
  Serial.begin(115200);

  pinMode(Relay1, OUTPUT);
  pinMode(Relay2, OUTPUT);
  pinMode(Relay3, OUTPUT);
  pinMode(Relay4, OUTPUT);
  pinMode(LightSwitch, INPUT);
  pinMode(PumpSwitch1, INPUT);
  pinMode(PumpSwitch2, INPUT);

  digitalWrite(Relay1, OFF);
  digitalWrite(Relay2, OFF);
  digitalWrite(Relay3, OFF);
  digitalWrite(Relay4, OFF);

  Serial.println(__FILE__);
  Serial.println("Mode = " + String(mode));
  Serial.print("compiled: ");
  Serial.print(__DATE__);
  Serial.print(" ");
  Serial.println(__TIME__);

  Rtc.Begin();

  RtcDateTime compiled = RtcDateTime(__DATE__, __TIME__);
  RtcDateTime errorDate = RtcDateTime(2165, 165, 165, 0, 0, 0);

  if (!Rtc.IsDateTimeValid())
  {
    // Common Causes:
    //    1) first time you ran and the device wasn't running yet
    //    2) the battery on the device is low or even missing

    Serial.println("RTC lost confidence in the DateTime!");
    Rtc.SetDateTime(compiled);
  }

  if (Rtc.GetIsWriteProtected())
  {
    Serial.println("RTC was write protected, enabling writing now");
    Rtc.SetIsWriteProtected(false);
  }

  if (!Rtc.GetIsRunning())
  {
    Serial.println("RTC was not actively running, starting now");
    Rtc.SetIsRunning(true);
  }

  RtcDateTime _time = Rtc.GetDateTime();
  bool Time_Error = false;
  if (_time < compiled)
  {
    Serial.println("RTC is older than compile time!  (Updating DateTime)");
    if (_time > errorDate)
    {
      Serial.println("RTC is older than compile time! But it is 165/165/2165 37:165 (Update canceled)");
      Rtc.SetDateTime(compiled);
      Time_Error = true;
    }
    else
    {
      Serial.println("WTF");
      Rtc.SetDateTime(compiled); // should never execute
    }
  }
  else if (_time > compiled)
  {
    Serial.println("RTC is newer than compile time. (this is expected)");
  }
  else if (_time == compiled)
  {
    Serial.println("RTC is the same as compile time! (not expected but all is fine)");
  }

  if (Time_Error)
  {
    // setTime(compiled.Unix32Time());
    setTime(compiled.Hour(),compiled.Minute(),compiled.Second(),compiled.Day(),compiled.Month(),compiled.Year());
    Serial.println(DateMe(compiled.Unix32Time()));
    Serial.println(compiled.Hour());
    Serial.println(compiled.Minute());
    Serial.println(compiled.Second());
    Serial.println(compiled.Day());
    Serial.println(compiled.Month());
    Serial.println(compiled.Year());
    printJSON(getRTCDateTime(now()),"now","");
    // printJSON(now(),"now2","");
    printJSON(_time,"_time","");
    printJSON(compiled, "compiled", "");
// printDateTime(compiled,"label");

  }
  else
  {
    setTime(_time.Unix32Time());
    printJSON(_time, "RTC", "");
  }

  // Time update
  Alarm.alarmRepeat(dowFriday, 0, 2, 0, ReadRTC); // reset the time at midnight once a week on Sunday

  if (mode == 1)
  {
    // Lights 18 hours
    Alarm.alarmRepeat(6, 0, 0, LightsON);
    Alarm.alarmRepeat(23, 55, 00, LightsOFF);
  }

  if (mode == 2)
  {
    // Lights grow 16 hours
    Alarm.alarmRepeat(7, 0, 0, LightsON);
    Alarm.alarmRepeat(23, 0, 0, LightsOFF);
  }

  if (mode == 3)
  {
    // Lights bud 12 hours
    Alarm.alarmRepeat(9, 0, 0, LightsON);
    Alarm.alarmRepeat(21, 0, 0, LightsOFF);
  }

  if (mode == 4)
  {
    // Lights
    Alarm.alarmRepeat(11, 42, 0, LightsON);
    Alarm.alarmRepeat(11, 43, 0, LightsOFF);
  }

  if (mode == 5)
  {
    // Lights
    Serial.println("No Lights");
  }

  //  let's water
  for (int i = 1; i <= timesPerWeek; i++)
  {
    Serial.print(i);
    Serial.print(F(": "));
    Serial.print(lieDow(startDay));
    Serial.print(F(" "));
    Serial.print(startHour);
    Serial.print(F(":"));
    Serial.println(startMinute);

    Alarm.alarmRepeat(getRealDow(startDay), startHour, startMinute, 0, WaterOn);
    Alarm.alarmRepeat(getRealDow(startDay), startHour, startMinute, duration, WaterOff);
    calcTimes();
  }

  printJSON(getRTCDateTime(now()),"getTime","");
  printJSON(getRTCDateTime(Alarm.getNextTrigger()),"NextTrigger","");
}

void loop()
{
  readSerial();
  readSwitch();
  Alarm.delay(1000); // tick
}

void readSerial()
{
  while (Serial.available() > 0)
  {
    // Create a place to hold the incoming message
    static char message[MAX_MESSAGE_LENGTH];
    static unsigned int message_pos = 0;

    // Read the next available byte in the serial receive buffer
    char inByte = Serial.read();

    // Message coming in (check not terminating character) and guard for over message size
    if (inByte != ';' && (message_pos < MAX_MESSAGE_LENGTH - 1))
    {
      // Add the incoming byte to our message
      message[message_pos] = inByte;
      // Serial.println(inByte);
      message_pos++;
      // Serial.println(message_pos);
    }
    // Full message received...
    else
    {
      // Add null character to string
      message[message_pos] = '\0';
      // Serial.println(String(message));

      // Reset for the next message
      message_pos = 0;
      // Lights_3_On
      if (String(message) == "Lights_" + indexNO + "_On")
      {
        LightsON();
      }
      if (String(message) == "Lights_" + indexNO + "_Off")
      {
        LightsOFF();
      }
      if (String(message) == "Water_" + indexNO + "_On")
      {
        WaterOn();
      }
      if (String(message) == "Water_" + indexNO + "_Off")
      {
        // Water_3_Off;
        WaterOff();
      }
      if (String(message) == "Water_Return_" + indexNO + "_On")
      {
        WaterReturnOn();
      }
      if (String(message) == "Water_Return_" + indexNO + "_Off")
      {
        // Water_Return_3_Off;
        WaterReturnOff();
      }
      if (String(message).startsWith("Time_Set" + indexNO + "-"))
      {
        // Time_Set3-2024,06,10,21,52,00;
        String temp = String(message);
        temp.remove(0, 10);
        char buf[20];
        temp.toCharArray(buf, 20);
        setMyRTC(buf);
      }
      if (String(message).startsWith("Time_Get" + indexNO + "-"))
      {
        // Time_Get3-;
        printJSON(Rtc.GetDateTime(), "getMyRTC", "");
      }
      if (String(message).startsWith("Alarm_NextTrigger" + indexNO + "-"))
      {
        // Alarm_NextTrigger3-;
        printJSON("NextTrigger", DateMe(Alarm.getNextTrigger()));
      }
      if (String(message).startsWith("Alarm_Read" + indexNO + "-"))
      {
        // Alarm_Read3-;
        printJSON("AlarmRead", DateMe(Alarm.read(0)));
      }
    }
  }
}
void readSwitch()
{
  if (digitalRead(LightSwitch) == HIGH)
  {
    if (LightsONOFF == 0)
    {
      // turn on
      LightsON();
      LightsONOFF = 1;
    }
    else
    {
      LightsOFF();
      LightsONOFF = 0;
    }
  }
  if (digitalRead(PumpSwitch1) == HIGH)
  {
    if (PumpONOFF1 == 0)
    {
      // turn on
      WaterOn();
      PumpONOFF1 = 1;
    }
    else
    {
      WaterOff();
      PumpONOFF1 = 0;
    }
  }
  if (digitalRead(PumpSwitch2) == HIGH)
  {
    if (PumpONOFF2 == 0)
    {
      // turn on
      WaterReturnOn();
      PumpONOFF2 = 1;
    }
    else
    {
      WaterReturnOff();
      PumpONOFF2 = 0;
    }
  }
}

// functions to be called when an alarm triggers:
void LightsON()
{
  printJSON("Lights_" + indexNO, "On");
  digitalWrite(Relay1, ON);
  digitalWrite(Relay2, ON);
  LightsONOFF = 1;
}
void LightsOFF()
{
  printJSON("Lights_" + indexNO, "Off");
  digitalWrite(Relay1, OFF);
  digitalWrite(Relay2, OFF);
  LightsONOFF = 0;
}
void WaterOn()
{
  printJSON("Water_" + indexNO, "On");
  digitalWrite(Relay3, ON);
  PumpONOFF1 = 1;
}
void WaterOff()
{
  printJSON("Water_" + indexNO, "Off");
  digitalWrite(Relay3, OFF);
  PumpONOFF1 = 0;
}

void WaterReturnOn()
{
  printJSON("Water_Return_" + indexNO, "On");
  digitalWrite(Relay4, ON);
  PumpONOFF2 = 1;
}
void WaterReturnOff()
{
  printJSON("Water_Return_" + indexNO, "Off");
  digitalWrite(Relay4, OFF);
  PumpONOFF2 = 0;
}

void ReadRTC()
{
  RtcDateTime _time = Rtc.GetDateTime();
  if (!_time.IsValid())
  {
    // Common Causes:
    //    1) the battery on the device is low or even missing and the power line was disconnected
    Serial.println("RTC lost confidence in the DateTime!");
  }
  else
  {
    setTime(_time.Unix32Time());
  }
  //  printDateTime(_time, "Time after Update: ");
  printJSON(_time, "TimeUpdate", "");
}

#define countof(a) (sizeof(a) / sizeof(a[0]))

void printDateTime(const RtcDateTime &dt, String lable)
{
  char datestring[20];
  String dow = getDOW(dt);
  snprintf_P(datestring,
             countof(datestring),
             PSTR("%02u/%02u/%04u %02u:%02u:%02u"),
             dt.Month(),
             dt.Day(),
             dt.Year(),
             dt.Hour(),
             dt.Minute(),
             dt.Second());
  Serial.print(lable);
  Serial.print(dow + " ");
  Serial.println(datestring);
}

String str;
void printJSON(const RtcDateTime &dt, String lable, String state)
{
  char datestring[20];
  String dow = getDOW(dt);
  snprintf_P(datestring,
             countof(datestring),
             PSTR("%02u/%02u/%04u %02u:%02u:%02u"),
             dt.Month(),
             dt.Day(),
             dt.Year(),
             dt.Hour(),
             dt.Minute(),
             dt.Second());

  str = String("{ ");
  str = str + String("\"") + String(lable) + String("_TIME") + String("\" : \"") + String(dow) + String(" ") + String(datestring) + String("\"");
  if (state != "")
  {
    str = str + String(",\"") + String(lable) + String("\" : \"") + String(state) + String("\"");
  }
  str = str + String(" }");
  Serial.println(str);
}

void printJSON(time_t time, String lable, String state)
{
  // char datestring[20];
  // String dow = getDOW(dt);
  // snprintf_P(datestring,
  //         countof(datestring),
  //         PSTR("%02u/%02u/%04u %02u:%02u:%02u"),
  //         dt.Month(),
  //         dt.Day(),
  //         dt.Year(),
  //         dt.Hour(),
  //         dt.Minute(),
  //         dt.Second() );

  str = String("{ ");
  str = str + String("\"") + String(lable) + String("_TIME") + String("\" : \"") + String(time) + String("\"");
  if (state != "")
  {
    str = str + String(",\"") + String(lable) + String("\" : \"") + String(state) + String("\"");
  }
  str = str + String(" }");
  Serial.println(str);
}

void printJSON(String lable, String state)
{
  str = String("{ ");
  str = str + String("\"") + String(lable) + String("\" : \"") + String(state) + String("\"");
  str = str + String(" }");
  Serial.println(str);
}

String getDOW(const RtcDateTime &dt)
{
  int dow = dt.DayOfWeek();
  return getDow(dow + 1);
}

String getDow(int dow)
{
  switch (dow)
  {
  case 2:
    return "Mon";
    break;
  case 3:
    return "Tue";
    break;
  case 4:
    return "Wed";
    break;
  case 5:
    return "Thu";
    break;
  case 6:
    return "Fri";
    break;
  case 7:
    return "Sat";
    break;
  case 1:
    return "Sun";
    break;
  }
}

String lieDow(int dow)
{
  switch (dow)
  {
  case 7:
    return "Mon";
    break;
  case 1:
    return "Tue";
    break;
  case 2:
    return "Wed";
    break;
  case 3:
    return "Thu";
    break;
  case 4:
    return "Fri";
    break;
  case 5:
    return "Sat";
    break;
  case 6:
    return "Sun";
    break;
  }
}

void calcTimes()
{

  //  int timesPerWeek = 5;
  //  int startHour    = 6;
  //  int startMinute  = 4;
  //  int duration     = 50;
  int hoursInWeek = 168;
  int days_ = (hoursInWeek / timesPerWeek) / 24;
  // Serial.println(days_);
  startDay = startDay + days_;
  // Serial.println(startDay);
  int hours_ = (hoursInWeek / timesPerWeek) - (days_ * 24);
  // Serial.println(hours_);
  startHour = startHour + hours_;

  if (hoursInWeek > (hoursInWeek / timesPerWeek) * timesPerWeek)
  {
    float hours__ = float(hoursInWeek) / float(timesPerWeek);
    int minutes_ = (hours__ - int(hoursInWeek / timesPerWeek)) * 60;
    // Serial.println(minutes_);
    startMinute = startMinute + minutes_ + 1; // somewhere in the float to int conversion I lose 1, it is 36 and not 35 for 5 times a week
    if (startMinute >= 60)
    {
      startMinute = startMinute - 60;
      startHour = startHour + 1;
    }
  }
  if (startHour >= 24)
  {
    startDay = startDay + 1;
    startHour = startHour - 24;
  }
  if (startDay > 7)
  {
    startDay = startDay - 7;
  }
}

String pad10(int i)
{
  if (i < 10)
  {
    return "0" + String(i);
  }
}

timeDayOfWeek_t getRealDow(int dow)
{
  switch (dow)
  {
  case 2:
    return dowMonday;
    break;
  case 3:
    return dowTuesday;
    break;
  case 4:
    return dowWednesday;
    break;
  case 5:
    return dowThursday;
    break;
  case 6:
    return dowFriday;
    break;
  case 7:
    return dowSaturday;
    break;
  case 1:
    return dowSunday;
    break;
  }
}

void setMyRTC(char temp_string[])
{
  char *ptr = strtok(temp_string, ",");
  byte i = 0;
  int myarray[6];
  while (ptr)
  {
    myarray[i] = atoi(ptr);
    ptr = strtok(NULL, ",");
    i++;
  }
  // Time_Set3-2023,09,04,21,00,00;
  RtcDateTime myTime = RtcDateTime(myarray[0], myarray[1], myarray[2], myarray[3], myarray[4], myarray[5]);
  Rtc.SetDateTime(myTime);
  setTime(myTime.Unix32Time());
  printJSON(myTime, "setMyRTC", "");
}

String DateMe(time_t t_unix_date1)
{
  String t = "";
  t = year(t_unix_date1);
  t = t + "/";
  t = t + month(t_unix_date1);
  t = t + "/";
  t = t + day(t_unix_date1);
  t = t + " ";
  t = t + hour(t_unix_date1);
  t = t + ":";
  t = t + minute(t_unix_date1);
  t = t + ":";
  t = t + second(t_unix_date1);

  return t;
}

RtcDateTime getRTCDateTime(uint32_t t_unix_date1)
{
  return RtcDateTime(year(t_unix_date1), month(t_unix_date1), day(t_unix_date1), hour(t_unix_date1), minute(t_unix_date1), second(t_unix_date1));
}
