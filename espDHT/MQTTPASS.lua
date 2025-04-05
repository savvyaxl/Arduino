
UART_ON = false
MONITOR_ON = false
MONITOR_DHT_ON = true

D1=1
D2=2
D1OnOff=0
D2OnOff=0
ON_=gpio.LOW
OFF_=gpio.HIGH

if MONITOR_DHT_ON then
    gpio.mode(D1, gpio.INPUT)
else
    gpio.mode(D1, gpio.OUTPUT)
    gpio.write(D1, gpio.LOW)
    gpio.mode(D2, gpio.OUTPUT)
    gpio.write(D2, gpio.LOW)
end



-- MQTTPASS
local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")

uart.setup(0, 115200, 8, uart.PARITY_NONE, uart.STOPBITS_1, 1)
--tls.cert.auth(false)
-- tls.cert.verify([[
--     -----BEGIN CERTIFICATE-----
--     MIIFvDCCA6SgAwIBAgIGICIHIAABMA0GCSqGSIb3DQEBCwUAMHUxCzAJBgNVBAYT
--     AkJSMQ8wDQYDVQQIDAZQYXJhbmExHTAbBgNVBAcMFFNhbyBKb3NlIGRvcyBQaW5o
--     YWlzMREwDwYDVQQKDAhTZWN1cml0eTETMBEGA1UECwwKV2ViIFNlcnZlcjEOMAwG
--     A1UEAwwFTXkgQ0EwHhcNMjIwNzIwMjIxNDE2WhcNMzIwNzE3MjIxNDE2WjB1MQsw
--     CQYDVQQGEwJCUjEPMA0GA1UECAwGUGFyYW5hMR0wGwYDVQQHDBRTYW8gSm9zZSBk
--     b3MgUGluaGFpczERMA8GA1UECgwIU2VjdXJpdHkxEzARBgNVBAsMCldlYiBTZXJ2
--     ZXIxDjAMBgNVBAMMBU15IENBMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKC
--     AgEAyuJosNZ4Qo2kUrtLq+r1tIcrZkVDU7olSSo716sfQBR7yK8S7Ay41LBwDKk9
--     Fb1qGaa6/fQl8rlXpWpvex3rLdat9/6yg9Is1TeRerokiMTXIZ09ZBJToLZuReIH
--     IJsKEqRfImJ71c1vwnWIZ5OWnMNm40KNHK2EkMrqIMlZkxZn83qyDfbhbITRsSmx
--     EOUumq0wZpTOLCQvDOduDmR8EuvfVevn+BYyfve5veSSc1g/UtKfYGQ3QeSALpm1
--     hVQxJW9ASjNHqfLBhVc6s9S1QsIaskslomMSYZsXyj0kIHVap+fa4VXFWVmLGfc6
--     kZ1/vzUAGnAGhPG6CzdcA7Ow6F4WhvY/bB/s5kFbo9NGwRFFcQPVOOuIWUlpP1td
--     HLbsjS/LP/ilhoo91+qkLOo3zY+u2eotsbLdFge99bjNu5QehuHEy8fu6iQhHUwV
--     FFI8EJj8aeM5DRKxRDf3DZsT3PY+OOaV/u7iMp938xZyLdIO4M0xTnEbF6yYnPX8
--     BLUXfrEdlsaAw13kAu681MGZpCUwinZgUID4yRoi5aF9juu6pO5oyEterNbXjjes
--     gZakNNI4rGlku3th/R9nvl/W/VYq+fJxUDHzt6nxO3CJv/Fvsm3jcxhk932lf2Cb
--     iMN4Y3TlVeSTl7fV46i/9F+K8wjJ0Na3xuQu6dU/dYD5isECAwEAAaNSMFAwHQYD
--     VR0OBBYEFGmquj2JMPB7ccsUnui5BFEXz4z6MA8GA1UdEwEB/wQFMAMBAf8wCwYD
--     VR0PBAQDAgEGMBEGCWCGSAGG+EIBAQQEAwIBBjANBgkqhkiG9w0BAQsFAAOCAgEA
--     pKdHNauUQuwcsrzUzsRwMykieMimB0OAMU7qf2snv3Gxc7Tj4K4n7TyD0oa7WQAz
--     jSx2urxd5RAOdz7g8sd2bygyLDsLrtUekWcVpnrBD4MIIvMEgL0KVtpKdyyFU+Ru
--     WiUdKjQ48Nw6I8LfS61WJ3q35SmK//iB5PZr9TRZwMtyV1d9HMAyFJZaU4TJyA1h
--     hdZCWTl2Qs/wX2JTUj2x8NsUbpDd/U1Fg0UD8ORblOrGBmTLD1T218l1rjinAaX7
--     206U92VAOdaPQq+AEYDfQYSmohebZVayEktg5JW8xVGXLQNYUpzrJPQbzlkaAjBc
--     R0sbeJmmGNG0Ii22ngmXthToA/gO7tSdhoA/SsNyxnK+OK/FrpjU6BJm2mHphQAk
--     Suh7d/cbHPJGlY6HCrfrnT4SnLrOur9Q9Vwxps/D9+1NsYQm+xhEHZE/foJt66K6
--     c5kDjKTGZKPJ4VW7bOM3SWfAfdBdB+YT0gKa8vXjgygdYWc2Bne0YKmS8dqFvh5N
--     pjaMEfJgZpRP4vSxLdTCb2X2Y2Xt0PP6kRT+XBxtHQTdqxclNXA4bOyiyfndb4UC
--     yqVCwkmVHzbFKAInSKcK6P8/K5kqBxNz7XojuJyaVKTnhSoFAy3A0R10f4oHkdsn
--     p3p1LzOM0/rQPUMhwImzD8VgcelkfTHeif4ue1wEE2A=
--     -----END CERTIFICATE-----
-- ]])
--tls.cert.verify(false)


local mqtt_client_cfg = {}
mqtt_client_cfg.clientid            = myID        
mqtt_client_cfg.keepalive           = 120             
mqtt_client_cfg.host                = MQTTHOST
mqtt_client_cfg.port                = MQTTPORT
mqtt_client_cfg.user                = MQTTUSER
mqtt_client_cfg.pass                = MQTTPASS
mqtt_client_cfg.topic_subscribe     = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/do'
mqtt_client_cfg.topic_state         = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/state'
mqtt_client_cfg.topic_test          = 'homeassistant/sensor/'..mqtt_client_cfg.clientid..'/test'

print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)


-- local handler = io.popen("ping -c 3 -i 0.5 192.168.0.101")
-- local response = handler:read("*a")
-- print(response)


-- mqtt.Client(clientid, keepalive[, username, password, cleansession, max_message_length])
c=mqtt.Client(mqtt_client_cfg.clientid,mqtt_client_cfg.keepalive,mqtt_client_cfg.user,mqtt_client_cfg.pass)
c:lwt("/lwt", "offline", 0, 0)
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
                D1OnOff=1
            end
            if t == "Off" then
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"Off\" }", 0, 0 )
                gpio.write(D1, OFF_)
                D1OnOff=0
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
                if D2OnOff == 0 then
                    c:publish(mqtt_client_cfg.topic_state, "{ \"Alarm\":\"On\" }", 0, 0 )
                    gpio.write(D1, gpio.HIGH)
                    D2OnOff = 1
                    tmr.create():alarm(1500, tmr.ALARM_SINGLE, function()
                        gpio.write(D1, gpio.LOW)
                    end)
                else
                    c:publish(mqtt_client_cfg.topic_state, "{ \"Alarm\":\"Off\" }", 0, 0 )
                    gpio.write(D1, gpio.HIGH)
                    D2OnOff = 0
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
    else
	    c:publish(mqtt_client_cfg.topic_state, data, 0, 0 )
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

if UART_ON then
    print("UART_ON")
    uart.on("data", "\r",
    function(data)
        publish (data)
    end, 0)
end

if MONITOR_ON then
    function monitor()
        if gpio.read(pin2) == ON_ then
            if D1OnOff == 0 then
                gpio.write(D1, ON_)
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"On\" }", 0, 0 )
                --print("on - on")
                D1OnOff = 1
            else
                gpio.write(D1, OFF_)
                c:publish(mqtt_client_cfg.topic_state, "{ \"Lights_4\":\"Off\" }", 0, 0 )
                --print("off - off")
                D1OnOff = 0
        end
        end
    end
    local tObj2 = tmr.create()
    tObj2:alarm(500,tmr.ALARM_AUTO,function() monitor(pin2) end)
end

-- new
function configure()
    -- "CONFIGdevice_class:temperature,name:Temp_C,unit_of_measurement:°C,value_template:{{value_json.tC}}"
    publish ("CONFIGdevice_class:temperature,name:Temp_Rack,unit_of_measurement:°C,value_template:{{value_json.tRack}}")
    tmr.create():alarm(500, tmr.ALARM_SINGLE, function() 
        publish ("CONFIGdevice_class:humidity,name:Humidity_Rack,unit_of_measurement:°C,value_template:{{value_json.hRack}}")
    end)
end

function read_dht()
    status, temp, humi, temp_dec, humi_dec = dht.read11(D1)
    if status == dht.OK then
        -- Float firmware just rounds down
        publish ("{\"tRack\" : "..temp..", \"hRack\" : "..humi.."}")

    elseif status == dht.ERROR_CHECKSUM then
        print( "DHT Checksum error." )
    elseif status == dht.ERROR_TIMEOUT then
        print( "DHT timed out." )
    end
end

if MONITOR_DHT_ON then
    --configure()
    local tObj1 = tmr.create()
    tObj1:alarm(2000, tmr.ALARM_AUTO,function() 
        if is_connected then
            tObj1:unregister()
            configure()
        end
    end)
    local tObj2 = tmr.create()
    tObj2:alarm(30000,tmr.ALARM_AUTO,function() read_dht() end)
end