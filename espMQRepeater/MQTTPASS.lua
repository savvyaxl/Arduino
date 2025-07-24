UART_ON = true
MONITOR_MESSAGE = true

if UART_ON then
    print("uart on")
end

-- MQTTPASS
local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")
local sta_config=wifi.sta.getconfig(true)

uart.setup(0, 115200, 8, uart.PARITY_NONE, uart.STOPBITS_1, 1)

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = credentials[sta_config.ssid].MQTTHOST
mqtt_client_cfg.port                = credentials[sta_config.ssid].MQTTPORT
mqtt_client_cfg.user                = credentials[sta_config.ssid].MQTTUSER
mqtt_client_cfg.pass                = credentials[sta_config.ssid].MQTTPASS
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/do'
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_test          = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/test'
mqtt_client_cfg.topic_connect       = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/connect'

print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)

-- mqtt.Client(clientid, keepalive[, username, password, cleansession, max_message_length])
c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive,mqtt_client_cfg.user,mqtt_client_cfg.pass)
c:lwt(mqtt_client_cfg.topic_connect, "Offline", 0, 0)
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

if MONITOR_MESSAGE then
    c:on("message", function(conn,topic,data)
        if data~=nil then
            print(data)
            local p = "TEST"
            data = trim2(data)
            local t = (data:sub(0, #p) == p) and data:sub(#p+1) or nil
            if t~=nil then
                c:publish(mqtt_client_cfg.topic_test, topic .. ":'" .. t .. "'", 0, 0 )
                uart.write( 0, t ) -- this goes back to the arduino
            end
        end
    end)
end

-- on publish overflow receive event
c:on("overflow", function(client, topic, data)
    print(topic .. " partial overflowed message: " .. data )
end)

-- publish the state, data comes from UART
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
        c:publish('homeassistant/sensor/' .. mqtt_client_cfg.clientid..'/' .. name .. '/config', stringBulder, 0, 0 )
        do return end
    end
    p = "CONNECT"
    data = trim2(data)
    if data:sub(0, #p) == p then
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or data
        c:publish(mqtt_client_cfg.topic_connect, t, 0, 0 )
        do return end
    end
    c:publish(mqtt_client_cfg.topic_state, data, 0, 0 )
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
        publish_state (data) 
    end
end

c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
    function(conn)
        print("connected")
        is_connected = 1
        publish ("CONNECTGood")
        conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe success") end)      
        end,
    function(conn, reason)
        print("failed reason: " .. reason)
end)

if UART_ON then
    print("UART_ON")
    uart.on("data", "\r",
    function(data)
        publish (data)
    end, 0)
end
