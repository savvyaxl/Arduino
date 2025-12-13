-- File espDallaTemp/MQTTPASS.lua

DALLAS_TEMP_ON = true

-- MQTTPASS
local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")
local def_sta_config=wifi.sta.getconfig(true)

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = credentials[def_sta_config.ssid].MQTTHOST
mqtt_client_cfg.port                = credentials[def_sta_config.ssid].MQTTPORT
mqtt_client_cfg.user                = credentials[def_sta_config.ssid].MQTTUSER
mqtt_client_cfg.pass                = credentials[def_sta_config.ssid].MQTTPASS
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/do'
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_test          = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/test'

print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)

-- mqtt.Client(clientid, keepalive[, username, password, cleansession, max_message_length])
c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive,mqtt_client_cfg.user,mqtt_client_cfg.pass)
c:lwt("/lwt", "offline "..mqtt_client_cfg.clientid, 0, 0)
is_connected = 0
--callback on connect and disconnects
c:on("connect", function(conn) 
    print("online")
    conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe success") end)
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

-- on publish overflow receive event
c:on("overflow", function(client, topic, data)
    print(topic .. " partial overflowed message: " .. data )
end)

local publish_state = function (data)
    local p = "CONFIG"
    data = trim2(data)
    if data:sub(0, #p) == p then
        local name = ''
        local value_template = ''
        local stringBulder = "{ "
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or data
        -- "CONFIGdevice_class:temperature,name:Temp_C,unit_of_measurement:°C,value_template:{{value_json.tC}}"
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
        c:publish('homeassistant/sensor/' .. mqtt_client_cfg.clientid..'/' .. name .. '/config', stringBulder, 0, 1 )
    else
	    c:publish(mqtt_client_cfg.topic_state, data, 0, 1 )
    end
end

-- mqtt:connect(host[, port[, secure]][, function(client)[, function(client, reason)]])
local publish = function (data)
    if not is_connected then
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
        -- print("connected")
        publish_state (data) 
    end
end

c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
    function(conn)
        print("connected")
        is_connected = 1
        conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe success") end)      
        end,
    function(conn, reason)
        print("failed reason: " .. reason)
end)

-- ################################################################

function configure()
    publish ("CONFIGdevice_class:temperature,name:Temp_Boil4,unit_of_measurement:°C,value_template:{{value_json.tBoil4 | round(1)}}")
    print("Published Homeassistant Config")
end



function publish_Temp( _temp )
    if _temp ~= nil then
        publish ("{ \"tBoil4\" : ".._temp.." }")
    else
        print("Failed to read temperature.")
    end
end


if DALLAS_TEMP_ON then
    local ds18b20 = require('ds18b20')
    ds18b20.setup(1) -- pin number
    local tObj1 = tmr.create()
    tObj1:alarm(2000, tmr.ALARM_AUTO,function() 
        if is_connected then
            tObj1:unregister()
            configure()
        end
    end)
    local tObj2 = tmr.create()
    tObj2:alarm(10000,tmr.ALARM_AUTO,function()
        local temp = ds18b20.readTemp()
        print("time")
        publish_Temp( temp )
    end)
end
