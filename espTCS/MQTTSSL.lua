--MQTT
require("TCS34725")

USE_SSL=false
if USE_SSL then
    dofile("tls.cert")
    tls.cert.auth(true)
    tls.cert.verify(true)
end

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

if USE_SSL then
    mqtt_client_cfg.port = credentials[def_sta_config.ssid].MQTTPORTSSL
end
        

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
    -- publish("restarting")
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
    if is_connected == 10 then
        c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,USE_SSL,
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

c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,USE_SSL,
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

function configure()
    publish ("CONFIGdevice_class:illuminance,name:Red,unit_of_measurement:lx,value_template:{{value_json.red1 | int }}")
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:illuminance,name:Green,unit_of_measurement:lx,value_template:{{ value_json.green1 | int }}")
    end)
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:illuminance,name:Blue,unit_of_measurement:lx,value_template:{{ value_json.blue1 | int }}")
    end)
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:illuminance,name:Clear,unit_of_measurement:lx,value_template:{{ value_json.clear1 | float*1/3 | int }}")
        -- | float*1/3 
    end)
end

function read_tcs()
    local clear,red,green,blue=TCS34725.getRawData()
    publish ("{ \"red1\": "..red..", \"green1\": "..green..", \"blue1\": "..blue..", \"clear1\": "..clear.." }")
end

if TCS_ON then
    --configure()
    local tObj1 = tmr.create()
    tObj1:alarm(2000, tmr.ALARM_AUTO,function() 
        if is_connected then
            tObj1:unregister()
            configure()
        end
    end)
    local tObj2 = tmr.create()
    tObj2:alarm(5000,tmr.ALARM_AUTO,function() read_tcs() end)
end