--MQTT
-- require("TCS34725")

TCS_ON = true

local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")
local def_sta_config=wifi.sta.getconfig(true)

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = 'tcs_'..myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = credentials[def_sta_config.ssid].MQTTHOST
mqtt_client_cfg.port                = credentials[def_sta_config.ssid].MQTTPORT
mqtt_client_cfg.user                = credentials[def_sta_config.ssid].MQTTUSER
mqtt_client_cfg.pass                = credentials[def_sta_config.ssid].MQTTPASS
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/do'

c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive,mqtt_client_cfg.user,mqtt_client_cfg.pass)
c:lwt("/lwt", "offline "..mqtt_client_cfg.clientid, 0, 0)
is_connected = 0
--callback on connect and disconnects
c:on("connect", function(conn) 
    print("online")
    conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe success connect callback") end)
    is_connected = 1
end)
c:on("connfail", function(client, reason) 
    print ("connection failed", reason) 
end)
c:on("offline", function(conn) 
    is_connected = 0
    conn:close()
    publish("restarting")
end)

c:on("message", function(conn,topic,data)
end)

-- on publish overflow receive event
c:on("overflow", function(client, topic, data)
    print(topic .. " partial overflowed message: " .. data )
end)

-- ################################################################

local publish_state = function (data)
    local p = "CONFIG"
    data = trim2(data)
    print(data) 
    if data:sub(0, #p) == p then
        local name = ''
        local value_template = ''
        local stringBulder = "{ "
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or data
        local outerTable = mysplit (t, ",")
        for i = 1, #outerTable do
            local b = outerTable[i]
            local innerTable = mysplit (b, ":")
            stringBulder = stringBulder .. quote_d ( innerTable[1] ) .. ":" .. quote_d ( innerTable[2] )
            stringBulder = stringBulder .. ","
            if innerTable[1]=="name" then name = innerTable[2] end
            if innerTable[1]=="value_template" then value_template = innerTable[2] end
        end
        stringBulder = stringBulder .. quote_d ( 'state_topic' ) .. ":" .. quote_d ( mqtt_client_cfg.topic_state )
        stringBulder = stringBulder .. " }"
        c:publish('homeassistant/sensor/' .. mqtt_client_cfg.clientid..'/' .. name .. '/config', stringBulder, 0, 0 )
    else
	    c:publish(mqtt_client_cfg.topic_state, data, 0, 0 )
    end
end

local publish = function (data)
    if is_connected == 0 then
        c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
            function(conn) 
                print("reconnected") 
                publish_state (data) 
                is_connected = 1
            end,
            function(conn, reason)
                print("failed reason: " .. reason) 
            end
        ) 
    else
        publish_state (data) 
    end
end

c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
    function(conn)
        print("connected")
        is_connected = 1
        conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe successful to "..mqtt_client_cfg.topic_subscribe) end)      
        end,
    function(conn, reason)
        print("failed reason: " .. reason)
end)

-- ################################################################
-- id=0  -- need this to identify (software) IC2 bus?
-- sda=2-- connect to pin GPIO0
-- scl=1 -- connect to pin GPIO2
-- addr=0x29 -- the I2C address of our device
-- REGISTER_ID=0x12   -- register for Device ID 0x44 for TCS34725
-- COMMAND_BIT=0x80   --   Used for reads and writes

-- function read_reg(dev_addr, reg_addr)
--   reg_addr=bit.bor(COMMAND_BIT,reg_addr)
--   i2c.start(id)
--   i2c.address(id, dev_addr ,i2c.TRANSMITTER)
--   i2c.write(id,reg_addr)
--   i2c.stop(id)
--   i2c.start(id)
--   i2c.address(id, dev_addr,i2c.RECEIVER)
--   c=i2c.read(id,1)
--   i2c.stop(id)
--   return c
-- end

-- function initialise(addr)
--   i2c.setup(id,sda,scl,i2c.SLOW)
--   result=read_reg(addr,REGISTER_ID)
--   if (string.byte(result)==0x44) then
--     print("Found TCS34725 using sda pin: "..sda.." and scl pin: "..scl)
--   else
--     print(string.byte(result).." TCS34725 Not Found using sda pin: "..sda.." and scl pin: "..scl)
--   end
-- end

function configure()
    publish ("CONFIGdevice_class:illuminance,name:Red,unit_of_measurement:lx,value_template:{{value_json.red1 | int }}")
    -- publish ("CONFIGdevice_class:illuminance,name:Green,unit_of_measurement:lx,value_template:{{ value_json.green1 | int }}")
    -- publish ("CONFIGdevice_class:illuminance,name:Blue,unit_of_measurement:lx,value_template:{{ value_json.blue1 | int }}")
    -- publish ("CONFIGdevice_class:illuminance,name:Clear,unit_of_measurement:lx,value_template:{{ value_json.clear1 | float*1/3 | int }}")
end

function read_tcs()
    -- local clear,red,green,blue=TCS34725.getRawData()
    local clear,red,green,blue=tcs34725.raw()
    publish ("{ \"red1\": "..red..", \"green1\": "..green..", \"blue1\": "..blue..", \"clear1\": "..clear.." }")
    print(clear)
end

if TCS_ON then
    --configure()
    local tObj1 = tmr.create()
    tObj1:alarm(2000, tmr.ALARM_AUTO,function() 
        if is_connected then
            tObj1:unregister()
            configure()
            -- initialise(addr)
            tcs34725.setup()
            tcs34725.enable(function()
                print("TCS34275 Enabled")
                tcs34725.setGain(0x00)
                tcs34725.setIntegrationTime(0xEB)
                clear,red,green,blue=tcs34725.raw()
                print(clear)
                print(red)
                print(green)
                print(blue)
                publish ("{ \"red1\": "..red..", \"green1\": "..green..", \"blue1\": "..blue..", \"clear1\": "..clear.." }")
            end)
        end
    end)
    local tObj2 = tmr.create()
    tObj2:alarm(5000,tmr.ALARM_AUTO,function() read_tcs() end)
end

