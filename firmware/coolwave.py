import time
from machine import Pin, I2C, Timer
from dht12 import DHT12
from dht20 import DHT20

# Offsets used to calibrate temprature sensors
dht12TemperatureOffset = 0.0
dht12HumidityOffset = 0.0
dht20TemperatureOffset = 0.0
dht20HumidityOffset = 0.0

# Differance in temprature requires to switch the fan
temperatureGap = 2.0

# Temprature where we want to start working
heatwaveTemperature = 35.0

i2c = I2C(0, scl=Pin(9), sda=Pin(8))
dht12 = DHT12(i2c, 0x5c)
dht20 = DHT20(0x38, i2c)
led = Pin(18, Pin.OUT)
relay = Pin(10, Pin.OUT)

# Read from the DHT12 sensor module (outside)
# Returned as a temperature, humidity tuplet
def readDHT12():
    dht12.measure()
    temperature = dht12.temperature() + dht12TemperatureOffset
    humidity = dht12.humidity() + dht12HumidityOffset
    return temperature, humidity
    
# Read from the DHT20 sensor module (inside)
# Returned as a temperature, humidity tuplet
def readDHT20():
    measurements = dht20.measurements
    temperature = measurements["t"] + dht20TemperatureOffset
    humidity = measurements["rh"] + dht20HumidityOffset
    return temperature, humidity

# Turn on or off the fan
# "active" is True for on, and False for off
def setFan(active):
    relay.value(active)

pastTemperatures = [0 for i in range(24)]
inHeatwave = False

# Main loop that is executed once a minute
def minuteLoop(minuteTimer):
    outsideTemperature, outsideHumidity = readDHT12()
    insideTemperature, insideHumidity = readDHT20()
    if inHeatwave and ( insideTemperature > (outsideTemperature + temperatureGap) ):
        setFan( True )
    elif insideTemperature < outsideTemperature:
        setFan( False )

# A loop that is executed once an hour
def hourLoop(hourTimer):
    global pastTemperatures
    global inHeatwave
    outsideTemperature, outsideHumidity = readDHT12()
    pastTemperatures = pastTemperatures[1:]
    pastTemperatures.append(outsideTemperature)
    inHeatwave = ( max(pastTemperatures) > heatwaveTemperature )

# Start a timer that calls the main loop once a minute
minuteTimer = Timer(-1)
minuteTimer.init(period=60000, mode=Timer.PERIODIC, callback=minuteLoop)

# Start a timer that calls the hour loop once an hour
hourTimer = Timer(-1)
hourTimer.init(period=3600000, mode=Timer.PERIODIC, callback=minuteLoop)

