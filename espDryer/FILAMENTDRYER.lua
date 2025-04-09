-- FILAMENTDRYER
-- ada,dht,file,gpio,mqtt,net,node,tmr,uart,wifi
UART_ON = false
DALLAS_TEMP_ON = false
--GPIO Switch - Relay
pin1=1
pin1OnOff=0
ON_=gpio.LOW
OFF_=gpio.HIGH
gpio.mode(pin1, gpio.OUTPUT)
gpio.write(pin1, OFF_)

-- either button or DHT
-- Button
BUTTON_ON = false
if BUTTON_ON then
    pin2=2
    gpio.mode(pin2, gpio.INPUT,gpio.PULLUP)
end
-- DHT
max_temp = 60
DHT_ON = true
if DHT_ON then
    pinDHT=2
    gpio.mode(pinDHT, gpio.INPUT)
end

if UART_ON then
    uart.setup(0, 115200, 8, uart.PARITY_NONE, uart.STOPBITS_1, 1)
end

local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = credentials['829D_Fibra'].MQTTHOST
mqtt_client_cfg.port                = credentials['829D_Fibra'].MQTTPORT
mqtt_client_cfg.user                = credentials['829D_Fibra'].MQTTUSER
mqtt_client_cfg.pass                = credentials['829D_Fibra'].MQTTPASS
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/do'
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_test          = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/test'

print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)

c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive)
c:lwt("/lwt", "offline"..myID, 0, 0)
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
        local p = "TEMP"
        data = trim2(data)
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or nil
        if t~=nil and type(t) == "number" then
            max_temp = t
        end
        p = "PID"
        data = trim2(data)
        local t = (data:sub(0, #p) == p) and data:sub(#p+1) or nil
        if t~=nil and type(t) == "number" then
            max_temp = t
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

-- ################################################################

if UART_ON then
    print("UART_ON")
    uart.on("data", "\r",
    function(data)
        publish (data)
    end, 0)
end

-- ################################################################

if BUTTON_ON then
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

-- ################################################################

function configureTemp()
    publish ("CONFIGdevice_class:temperature,name:temp_Dryer,unit_of_measurement:°C,value_template:{{value_json.tDryer | round(1)}}")
end

function publish_Temp( _temp )
    publish ("{ \"tDryer\" : ".._temp.." }")
end

if DALLAS_TEMP_ON then
    t = require('ds18b20')
    t.setup(1) -- pin number
    local tObj1 = tmr.create()
    tObj1:alarm(600000,tmr.ALARM_AUTO,function()
        configureTemp()
    end)
    local tObj2 = tmr.create()
    tObj2:alarm(10000,tmr.ALARM_AUTO,function()
        local temp = t.readTemp()
        publish_Temp( temp )
    end)
end

-- ################################################################

function configure()
    publish ("CONFIGdevice_class:temperature,name:Temp_Dryer,unit_of_measurement:°C,value_template:{{value_json.tDryer | round(1)}}")
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:humidity,name:Humidity_Dryer,unit_of_measurement:%,value_template:{{value_json.hDryer | round(1)}}")
    end)
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:temperature,name:Pin_Dryer,unit_of_measurement:°C,value_template:{{value_json.Pin | round(1)}}")
    end)

end


function read_dht()
    status, temp, humi, temp_dec, humi_dec = dht.read11(pinDHT)
    if status == dht.OK then
        -- Float firmware just rounds down
        if temp < max_temp then
            gpio.write(pin1, ON_)
            pin1OnOff = 1
        else
            gpio.write(pin1, OFF_)
            pin1OnOff = 0
        end
        publish ("{\"tDryer\" : "..temp..", \"hDryer\" : "..humi.. ", \"Pin\" : "..pin1OnOff.."}")
    elseif status == dht.ERROR_CHECKSUM then
        print( "DHT Checksum error." )
    elseif status == dht.ERROR_TIMEOUT then
        print( "DHT timed out." )
    end
end

if DHT_ON then
    --configure()
    local tObj1 = tmr.create()
    tObj1:alarm(2000, tmr.ALARM_AUTO,function() 
        if is_connected then
            tObj1:unregister()
            configure()
        end
    end)
    local tObj2 = tmr.create()
    tObj2:alarm(10000,tmr.ALARM_AUTO,function() read_dht() end)
end