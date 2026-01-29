
--MQTTPASS
UART_ON = false
MONITOR_ON = false
--GPIO Switch
-- D1 - OUTPUT
D1=1
pin1OnOff=0
AlarmOnOff=0
ON_=gpio.LOW
OFF_=gpio.HIGH
gpio.mode(D1, gpio.OUTPUT)
gpio.write(D1, gpio.LOW)

-- D2 - OUTPUT
D2=2
--gpio.mode(D2, gpio.INPUT,gpio.PULLUP)
gpio.mode(D2, gpio.OUTPUT)
gpio.write(D2, gpio.LOW)

local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")
local def_sta_config=wifi.sta.getconfig(true)


uart.setup(0, 115200, 8, uart.PARITY_NONE, uart.STOPBITS_1, 1)

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
mqtt_client_cfg.topic_connect       = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/connect'

print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)

c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive,mqtt_client_cfg.user,mqtt_client_cfg.pass)
c:lwt(mqtt_client_cfg.topic_connect, "Offline", 0, 0)
is_connected = "?"

--callback on connect and disconnects
c:on("connect", function(conn) 
    print("online")
    conn:subscribe(mqtt_client_cfg.topic_subscribe,0,
            function(conn) print("subscribe success") end)
    is_connected = "true"
end)
c:on("connfail", function(client, reason) 
    print ("connection failed", reason) 
end)
c:on("offline", function(conn) 
    is_connected = "false"
    conn:close()
    publish("restarting")
end)

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
        p = "SWITCH"
        data = trim2(data)
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or nil
        if t~=nil then
            if t == "On" then
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"On\" }", 0, 0 )
                gpio.write(D1, ON_)
                pin1OnOff=1
            end
            if t == "Off" then
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"Off\" }", 0, 0 )
                gpio.write(D1, OFF_)
                pin1OnOff=0
            end
        end
        p = "BUTTON"
        data = trim2(data)
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or nil
        if t~=nil then
            if t == "Garage" then
                c:publish(mqtt_client_cfg.topic_state, "{ \"Garage\":\"On\" }", 0, 0 )
                gpio.write(D2, gpio.HIGH)
                tmr.create():alarm(1500, tmr.ALARM_SINGLE, function()
                    c:publish(mqtt_client_cfg.topic_state, "{ \"Garage\":\"Off\" }", 0, 0 )
                    gpio.write(D2, gpio.LOW)
                end)
            end
            if t == "Alarm" then
                if AlarmOnOff == 0 then
                    c:publish(mqtt_client_cfg.topic_state, "{ \"Alarm\":\"On\" }", 0, 0 )
                    gpio.write(D1, gpio.HIGH)
                    AlarmOnOff = 1
                    tmr.create():alarm(1500, tmr.ALARM_SINGLE, function()
                        gpio.write(D1, gpio.LOW)
                    end)
                else
                    c:publish(mqtt_client_cfg.topic_state, "{ \"Alarm\":\"Off\" }", 0, 0 )
                    gpio.write(D1, gpio.HIGH)
                    AlarmOnOff = 0
                    tmr.create():alarm(1500, tmr.ALARM_SINGLE, function()
                        gpio.write(D1, gpio.LOW)
                    end)
                end
            end
        end
    end
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
    if is_connected == "false" then
        c:connect(mqtt_client_cfg.host,mqtt_client_cfg.port,false,
            function(conn) 
                print("reconnected") 
                publish_state (data) 
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

if MONITOR_ON then
    function monitor(pin)
        if gpio.read(pin2) == ON_ then
            if pin1OnOff == 0 then
                gpio.write(pin1, ON_)
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"On\" }", 0, 0 )
                --print("on - on")
                pin1OnOff = 1
            else
                gpio.write(pin1, OFF_)
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"Off\" }", 0, 0 )
                --print("off - off")
                pin1OnOff = 0
            end
        end
    end
    local tObj2 = tmr.create()
    tObj2:alarm(500,tmr.ALARM_AUTO,function() monitor(pin2) end)
end
