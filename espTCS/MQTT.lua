--MQTT
require("TCS34725")

TCS_ON = true

local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = 'tcs_'..myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = credentials['829D_Fibra'].MQTTHOST
mqtt_client_cfg.port                = credentials['829D_Fibra'].MQTTPORT
mqtt_client_cfg.user                = credentials['829D_Fibra'].MQTTUSER
mqtt_client_cfg.pass                = credentials['829D_Fibra'].MQTTPASS
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/restart'
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_config_uptime = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/Uptime/config'
mqtt_client_cfg.topic_config_red    = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/Red/config'
mqtt_client_cfg.topic_config_green  = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/Green/config'
mqtt_client_cfg.topic_config_blue   = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/Blue/config'
mqtt_client_cfg.topic_config_clear  = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/Clear/config'

print(mqtt_client_cfg.topic_subscribe)
--print(mqtt_client_cfg.topic_state)
--print(mqtt_client_cfg.topic_config_red)

c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive,mqtt_client_cfg.user,mqtt_client_cfg.pass)
c:lwt("/lwt/"..myID, "offline", 0, 0)
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
    print(topic..":")
    if data~=nil then
        print(data)
        if data=="restart" then
            resetmY()
        end
        if data=="uptime" then
            local uptime = tmr.time()
            print('Uptime: '..uptime)
            publish_state_uptime(c,uptime)
        end
    end
end)

resetmY = function ()
  -- restarting
    local uptime = tmr.time()
    print('Restarting, uptime: '..uptime)
    node.restart()
end

-- on publish overflow receive event
c:on("overflow", function(client, topic, data)
    print(topic .. " partial overflowed message: " .. data )
end)

c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
    function(conn)
        print("connected")
        conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe success") end)
        publish_config_red (conn)
        publish_config_green (conn)
        publish_config_blue (conn)
        publish_config_clear (conn)
        publish_config_uptime (conn)
        
        tmr.create():alarm(5000, tmr.ALARM_AUTO, 
            function() publish(conn) end)        
        end,
    function(conn, reason)
        print("failed reason: " .. reason)
end)

publish_config_uptime = function (c_)
    c_:publish(mqtt_client_cfg.topic_config_uptime, "{\"name\": \"Uptime\", \"state_topic\": \""..mqtt_client_cfg.topic_state.."\", \"unit_of_measurement\": \"time\", \"value_template\": \"{{ value_json.uptime"..myID.."}}\" }", 0, 0 )
end
publish_config_red = function (c_)
    c_:publish(mqtt_client_cfg.topic_config_red, "{\"device_class\": \"illuminance\", \"name\": \"Red\", \"state_topic\": \""..mqtt_client_cfg.topic_state.."\", \"unit_of_measurement\": \"lx\", \"value_template\": \"{{ value_json.red"..myID.."}}\" }", 0, 0 )
end
publish_config_green = function (c_)
    c_:publish(mqtt_client_cfg.topic_config_green, "{\"device_class\": \"illuminance\", \"name\": \"Green\", \"state_topic\": \""..mqtt_client_cfg.topic_state.."\", \"unit_of_measurement\": \"lx\", \"value_template\": \"{{ value_json.green"..myID.."}}\" }", 0, 0 )
end
publish_config_blue = function (c_)
    c_:publish(mqtt_client_cfg.topic_config_blue, "{\"device_class\": \"illuminance\", \"name\": \"Blue\", \"state_topic\": \""..mqtt_client_cfg.topic_state.."\", \"unit_of_measurement\": \"lx\", \"value_template\": \"{{ value_json.blue"..myID.."}}\" }", 0, 0 )
end
publish_config_clear = function (c_)
    c_:publish(mqtt_client_cfg.topic_config_clear, "{\"device_class\": \"illuminance\", \"name\": \"Clear\", \"state_topic\": \""..mqtt_client_cfg.topic_state.."\", \"unit_of_measurement\": \"lx1\", \"value_template\": \"{{ value_json.clear"..myID.."}}\" }", 0, 0 )
end

publish_state = function (c_,clear,red,green,blue)
    c_:publish(mqtt_client_cfg.topic_state, "{ \"red"..myID.."\": "..red..", \"green"..myID.."\": "..green..", \"blue"..myID.."\": "..blue..", \"clear"..myID.."\": "..clear.." }", 0, 0 )
end

publish_state_uptime = function (c_,uptime)
    c_:publish(mqtt_client_cfg.topic_state, "{ \"uptime"..myID.."\": "..uptime.." }", 0, 0 )
end


get_color = function (clear,red,green,blue)
    red = 256 * red / clear
    green  = 256 * green / clear
    blue = 256 * blue / clear
    return  clear,red,green,blue
end

function publish(c_)
    print(is_connected) 
    if is_connected == 10 then
        local clear,red,green,blue=TCS34725.getRawData()
        c_:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
            function(conn) 
                print("reconnected") 
                publish_state (c_,clear,red,green,blue) 
                is_connected = 1
            end,
            function(conn, reason)
                print("failed reason: " .. reason) 
            end
        ) 
    else
        local clear,red,green,blue=TCS34725.getRawData()
        publish_state (c_,clear,red,green,blue) 
    end
end

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

-- ################################################################

function configure()
    -- c_:publish(mqtt_client_cfg.topic_config_uptime, "{\"name\": \"Uptime\", \"state_topic\": \""..mqtt_client_cfg.topic_state.."\", \"unit_of_measurement\": \"time\", \"value_template\": \"{{ value_json.uptime"..myID.."}}\" }", 0, 0 )
    publish ("CONFIGdevice_class:temperature,name:Temp_Dryer,unit_of_measurement:°C,value_template:{{value_json.tDryer | round(1)}}")
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:humidity,name:Humidity_Dryer,unit_of_measurement:%,value_template:{{value_json.hDryer | round(1)}}")
    end)
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:temperature,name:Pin_Dryer,unit_of_measurement:°C,value_template:{{value_json.Pin | round(1)}}")
    end)
end

function read_tcs()
    local clear,red,green,blue=TCS34725.getRawData()
    -- publish ("{ \"red"..myID.."\": "..red..", \"green"..myID.."\": "..green..", \"blue"..myID.."\": "..blue..", \"clear"..myID.."\": "..clear.." }")
    publish ("{ \"red"..myID.."\": "..red..", \"green"..myID.."\": "..green..", \"blue"..myID.."\": "..blue..", \"clear"..myID.."\": "..clear.." }")
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
    tObj2:alarm(10000,tmr.ALARM_AUTO,function() read_tcs() end)
end