-- main.lua --
dofile("functions.lua");

----------------------------------
-- WiFi Connection Verification --
----------------------------------

-- create a timer object
local tObj = tmr.create()
-- register an alarm
tObj:alarm(2000, tmr.ALARM_AUTO, function ()
  if wifi.sta.getip() then
    tObj:unregister()
    print("Config done, IP is " .. wifi.sta.getip())
    require("MQTTPASS")
  end
end)
 
