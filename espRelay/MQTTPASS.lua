--MQTTPASS
UART_ON = false
--GPIO Switch
pin1=1
pin1OnOff=0
ON_=gpio.LOW
OFF_=gpio.HIGH
gpio.mode(pin1, gpio.OUTPUT)
gpio.write(pin1, OFF_)

pin2=2
gpio.mode(pin2, gpio.INPUT,gpio.PULLUP)

local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")

uart.setup(0, 115200, 8, uart.PARITY_NONE, uart.STOPBITS_1, 1)

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = MQTTHOST
mqtt_client_cfg.port                = MQTTPORT
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/do'
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_test          = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/test'

print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)

c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive)
c:lwt("/lwt", "offline", 0, 0)
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
                gpio.write(pin1, ON_)
                pin1OnOff=1
            end
            if t == "Off" then
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"Off\" }", 0, 0 )
                gpio.write(pin1, OFF_)
                pin1OnOff=0
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

