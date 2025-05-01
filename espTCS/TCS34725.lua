--TCS34725 Color Sensor Example using Lua on Esp8266 by Craig Scott cjscottcjscott@gmail.com
-- Based on work by zeroday & sancho among many other open source authors
-- filename = tcs34725.lua
--dofile("credentials.lua")

-- Set module name as parameter of require
local modname = 'TCS34725'
local M = {}
_G[modname] = M
--------------------------------------------------------------------------------
-- Local used modules
--------------------------------------------------------------------------------
-- Table module
local table = table
-- String module
local string = string
-- One wire module
local ow = ow
-- Timer module
local tmr = tmr
-- Limited to local environment
setmetatable( M, { __index = _G })
setfenv(1,M)

id=0  -- need this to identify (software) IC2 bus?
sda=2-- connect to pin GPIO0
scl=1 -- connect to pin GPIO2
addr=0x29 -- the I2C address of our device

CDATAL=0x14   -- Clear channel data
CDATAH=0x15
RDATAL=0x16   -- Red channel data
RDATAH=0x17
GDATAL=0x18   -- Green channel data
GDATAH=0x19
BDATAL=0x1A   -- Blue channel data
BDATAH=0x1B   

ENABLE=0x00
ENABLE_AEN=0x02 --RGBC Enable - Writing 1 actives the ADC, 0 disables it
ENABLE_PON=0x01 -- Power on - Writing 1 activates the internal oscillator, 0 disables it

INTEGRATIONTIME_2MS=0xFF   --<  2.4ms - 1 cycle    - Max Count: 1024 
INTEGRATIONTIME_24MS=0xF6   --<  24ms  - 10 cycles  - Max Count: 10240
INTEGRATIONTIME_50MS=0xEB   --<  50ms  - 20 cycles  - Max Count: 20480
INTEGRATIONTIME_101MS=0xD5   --<  101ms - 42 cycles  - Max Count: 43008
INTEGRATIONTIME_154MS=0xC0   --<  154ms - 64 cycles  - Max Count: 65535
INTEGRATIONTIME_700MS=0x00   --<  700ms - 256 cycles - Max Count: 65535

GAIN_1X=0x00   --<  No gain 
GAIN_4X=0x01   --<  2x gain 
GAIN_16X=0x02   --<  16x gain
GAIN_60X=0x03   --<  60x gain
ATIME=0x01     --< Set the Integration Time
CONTROL=0x0F   --< Set the gain level
REGISTER_ID=0x12   -- register for Device ID 0x44 for TCS34725
COMMAND_BIT=0x80   --   Used for reads and writes

INTEGRATIONTIME=INTEGRATIONTIME_50MS
GAIN_=GAIN_1X

function initialise(addr)
  i2c.setup(id,sda,scl,i2c.SLOW)
  result=read_reg(addr,REGISTER_ID)
  if (string.byte(result)==0x44) then
    print("Found TCS34725 using sda pin: "..sda.." and scl pin: "..scl)
  else
    print(string.byte(result).." TCS34725 Not Found using sda pin: "..sda.." and scl pin: "..scl)
  end
end

-- user defined function: read from reg_addr content of dev_addr

function read_reg(dev_addr, reg_addr)
  reg_addr=bit.bor(COMMAND_BIT,reg_addr)
  i2c.start(id)
  i2c.address(id, dev_addr ,i2c.TRANSMITTER)
  i2c.write(id,reg_addr)
  i2c.stop(id)
  i2c.start(id)
  i2c.address(id, dev_addr,i2c.RECEIVER)
  c=i2c.read(id,1)
  i2c.stop(id)
  return c
end

function write_reg(dev_addr, reg_addr, reg_val)
  reg_addr=bit.bor(COMMAND_BIT,reg_addr)
  i2c.start(id)
  i2c.address(id, dev_addr, i2c.TRANSMITTER)
  i2c.write(id, reg_addr)
  i2c.write(id, reg_val)
  i2c.stop(id)
end

function getRawData ()
  clear_l = string.byte(read_reg(addr,CDATAL))
  clear_h = string.byte(read_reg(addr,CDATAH))
  red_l = string.byte(read_reg(addr,RDATAL))
  red_h = string.byte(read_reg(addr,RDATAH))
  green_l = string.byte(read_reg(addr,GDATAL))
  green_h = string.byte(read_reg(addr,GDATAH))
  blue_l = string.byte(read_reg(addr,BDATAL))
  blue_h = string.byte(read_reg(addr,BDATAH))
  clear =bit.bor(bit.lshift(clear_h,8),clear_l)
  red=bit.bor(bit.lshift(red_h,8),red_l)
  green=bit.bor(bit.lshift(green_h,8),green_l)
  blue=bit.bor(bit.lshift(blue_h,8),blue_l)
  -- Set a delay for the worst case integration time
  tmr.delay(700)
  return clear,red,green,blue
end

function enable()
  write_reg(addr,ENABLE,ENABLE_PON)
  tmr.delay(30)
  write_reg(addr, ENABLE, bit.bor(ENABLE_PON,ENABLE_AEN)) 
end

   
function disable()
  reg=0
  reg=read_reg(addr,ENABLE)
  tmr.delay(3)
  write_reg(ENABLE, bit.band(reg, bit.bnot(bit.bor(ENABLE_PON,ENABLE_AEN)))) 
end


initialise(addr)
write_reg(addr,ATIME, INTEGRATIONTIME)
print("Integration Time Set",INTEGRATIONTIME)
write_reg(addr,CONTROL, GAIN)
print("Gain Set",GAIN)
enable()

return M