UART_ON = true
MONITOR_MESSAGE = true

-- MQTTPASS
local myID = wifi.sta.getmac()
myID = myID:gsub(":", "")
local sta_config = wifi.sta.getconfig(true)

uart.setup(0, 115200, 8, uart.PARITY_NONE, uart.STOPBITS_1, 1)

local mqtt_client_cfg = {}
mqtt_client_cfg.clientid = myID
mqtt_client_cfg.keepalive = 120
mqtt_client_cfg.host = credentials[sta_config.ssid].MQTTHOST
mqtt_client_cfg.port = credentials[sta_config.ssid].MQTTPORT
mqtt_client_cfg.user = credentials[sta_config.ssid].MQTTUSER
mqtt_client_cfg.pass = credentials[sta_config.ssid].MQTTPASS
mqtt_client_cfg.topic_subscribe = 'homeassistant/sensor/' .. mqtt_client_cfg.clientid .. '/do'
mqtt_client_cfg.topic_state     = 'homeassistant/sensor/' .. mqtt_client_cfg.clientid .. '/state'
mqtt_client_cfg.topic_test      = 'homeassistant/sensor/' .. mqtt_client_cfg.clientid .. '/test'
mqtt_client_cfg.topic_command   = 'homeassistant/sensor/' .. mqtt_client_cfg.clientid .. '/command'
mqtt_client_cfg.topic_connect   = 'homeassistant/sensor/' .. mqtt_client_cfg.clientid .. '/connect'
mqtt_client_cfg.device              = true
mqtt_client_cfg.device_manufacturer = "CustomMQTT"
mqtt_client_cfg.device_model        = "Light Controller v1"
mqtt_client_cfg.device_name         = "Light Controller"


print(mqtt_client_cfg.topic_subscribe)
print(mqtt_client_cfg.topic_state)

-- mqtt.Client(clientid, keepalive[, username, password, cleansession, max_message_length])
c = mqtt.Client(mqtt_client_cfg.clientid, mqtt_client_cfg.keepalive, mqtt_client_cfg.user, mqtt_client_cfg.pass)
c:lwt(mqtt_client_cfg.topic_connect, "Offline", 0, 0)
is_connected = 0

-- callback on connect and disconnects
c:on("connect", function(conn)
    print("online")
    conn:subscribe(mqtt_client_cfg.topic_subscribe, 0, function(conn)
        print("subscribe success")
    end)
    is_connected = 1
end)

c:on("connfail", function(client, reason)
    print("connection failed", reason)
end)

c:on("offline", function(conn)
    is_connected = 0
    conn:close()
    publish("restarting")
end)

if MONITOR_MESSAGE then
    c:on("message", function(conn, topic, data)
        if data ~= nil then
            -- print(data)
            local p = "TEST"
            data = trim2(data)
            local t = (data:sub(0, #p) == p) and data:sub(#p + 1) or nil
            if t ~= nil then
                c:publish(mqtt_client_cfg.topic_test, topic .. ":'" .. t .. "'", 0, 0)
                uart.write(0, t) -- this goes back to the arduino
            end
        end
    end)
end

-- on publish overflow receive event
c:on("overflow", function(client, topic, data)
    print(topic .. " partial overflowed message: " .. data)
end)


-- homeassistant/binary_sensor/lights_4/config
-- {
--   "name": "Lights 4 Sensor",
--   "unique_id": "lights_4_sensor",
--   "state_topic": "homeassistant/sensor/483fda75b4b7/state",
--   "payload_on": "On",
--   "payload_off": "Off",
--   "value_template": "{{ value_json.Lights_4 }}",
--   "device_class": "light",
--   "device": {
--     "identifiers": ["483fda75b4b7"],
--     "manufacturer": "CustomMQTT",
--     "model": "Light Controller v1",
--     "name": "Light 4 Controller"
--   }
-- }
-- homeassistant/switch/light_4_switch/config
-- {
--   "name": "Light 4 Switch",
--   "unique_id": "light_4_switch",
--   "state_topic": "homeassistant/sensor/483fda75b4b7/state",
--   "command_topic": "homeassistant/sensor/483fda75b4b7/command",
--   "payload_on": "SWITCHOn",
--   "payload_off": "SWITCHOff",
--   "state_on": "On",
--   "state_off": "Off",
--   "value_template": "{{ value_json.Lights_4 }}",
--   "qos": 0,
--   "retain": false,
--   "device": {"identifiers": ["483fda75b4b7"],"manufacturer": "CustomMQTT","model": "Light Controller v1","name": "Light 4 Controller"}
-- }
-- "CONFIGdevice_class:temperature,name:Temp_C,unit_of_measurement:°C,value_template:{{value_json.tC}}"  ,payload_on:SWITCHOn,payload_off:SWITCHOff,state_on:On,state_off:Off

local device_info = function(name)
    local s = ', "device": { "identifiers": [ "' .. mqtt_client_cfg.clientid .. '" ], "manufacturer": "espMQRepeater", "model": "esp8266", "name": "espMQRepeater ' .. mqtt_client_cfg.clientid .. '" }'
    return s
end
-- local safe_name = string.lower(string.gsub(name, "%s+", "_"))

local configDevice = function(name, device_class, unit_of_measurement, value_template)
    local str = '{ '
    str = str .. '"name": "' .. name .. '", '
    str = str .. '"unique_id": "' .. string.lower(string.gsub(name, "%s+", "_")) .. '_sensor", '
    str = str .. '"state_topic": "' .. mqtt_client_cfg.topic_state .. '", '
    if device_class ~= nil then
        str = str .. '"device_class": "' .. device_class .. '", '
    end
    if unit_of_measurement ~= nil then
        str = str .. '"unit_of_measurement": "' .. unit_of_measurement .. '", '
    end
    if value_template ~= nil then
        str = str .. '"value_template": "' .. value_template .. '", '
    end
    str = str .. device_info(name)
    str = str .. ' }'
    return str
end

-- helper to normalize names: lowercase + underscores
local function normalize_name(n)
    -- replace spaces with underscores
    local safe = string.gsub(n, "%s+", "_")
    -- convert to lowercase
    safe = string.lower(safe)
    return safe
end

local function template(t)
    local name = ''
    local stringBulder = "{ "
    -- "CONFIGdevice_class:temperature,name:Temp_C,unit_of_measurement:°C,value_template:{{value_json.tC}}"
    local outerTable = mysplit(t, ",")
    for i = 1, #outerTable do
        local b = outerTable[i]
        local innerTable = mysplit(b, ":")
        stringBulder = stringBulder .. quote_d(innerTable[1]) .. ":" .. quote_d(innerTable[2])
        stringBulder = stringBulder .. ","
        if innerTable[1] == "name" then
            name = innerTable[2]
        end
    end
    if mqtt_client_cfg.device ~= nil then
        local id =  quote_d(mqtt_client_cfg.clientid)
        local manufacturer = quote_d(mqtt_client_cfg.device_manufacturer)
        local model = quote_d(mqtt_client_cfg.device_model)
        local device_name = quote_d(mqtt_client_cfg.device_name)
        stringBulder = stringBulder .. '"device": {"identifiers": [' .. id .. '],"manufacturer": ' .. manufacturer .. ',"model": ' .. model .. ',"name": ' .. device_name .. '},'
    end
    stringBulder = stringBulder .. '"unique_id": ' .. quote_d(normalize_name(name)) .. ','
    stringBulder = stringBulder .. quote_d('state_topic') .. ":" .. quote_d(mqtt_client_cfg.topic_state)
    stringBulder = stringBulder .. " }"
    return name, stringBulder
end

-- publish the state, data comes from UART
local publish_state = function(data)
    local p = "CONFIG"
    data = trim2(data)
    if data:sub(0, #p) == p then
        local t = (data:sub(0, #p) == p) and data:sub(#p + 1) or data
        local name, stringBulder = template(t)
        c:publish('homeassistant/sensor/' .. mqtt_client_cfg.clientid .. '/' .. name .. '/config', stringBulder, 0, 1)
        do
            return
        end
    end
    p = "CONNECT"
    data = trim2(data)
    if data:sub(0, #p) == p then
        local t = (data:sub(0, #p) == p) and data:sub(#p + 1) or data
        c:publish(mqtt_client_cfg.topic_connect, t, 0, 1)
        do
            return
        end
    end
    -- print("Publishing " .. data .. " to " .. mqtt_client_cfg.topic_state)
    c:publish(mqtt_client_cfg.topic_state, data, 0, 1)
end

-- mqtt:connect(host[, port[, secure]][, function(client)[, function(client, reason)]])
local publish = function(data)
    if not is_connected then
        c:connect(mqtt_client_cfg.host, mqtt_client_cfg.port, false, function(conn)
            print("reconnected")
            publish_state(data)
            is_connected = 1
        end, function(conn, reason)
            print("failed reason: " .. reason)
        end)
    else
        publish_state(data)
    end
end

c:connect(mqtt_client_cfg.host, mqtt_client_cfg.port, false, function(conn)
    print("connected")
    is_connected = 1
    publish("CONNECTConnected to " .. sta_config.ssid)
    conn:subscribe(mqtt_client_cfg.topic_subscribe, 0, function(conn)
        publish("CONNECTSubscribed to " .. mqtt_client_cfg.topic_subscribe)
        print("subscribe success")
    end)
end, function(conn, reason)
    print("failed reason: " .. reason)
end)

if UART_ON then
    print("UART_ON")
    uart.on("data", "\r", function(data)
        --print("Publishing UART: " .. data)
        publish(data)
    end, 0)
end
