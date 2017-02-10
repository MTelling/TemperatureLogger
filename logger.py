import glob
import os
import sys
import time
import secret

import Adafruit_DHT
import MySQLdb

# Constants for reading DHT
HUMIDITY_SENSOR = Adafruit_DHT.DHT11
HUMIDITY_PIN = 5

# Constants for reading DS18B20
BASE_DIR = '/sys/bus/w1/devices/'
DEVICE_FOLDER = glob.glob(BASE_DIR + '28*')[0]
DEVICE_FILE = DEVICE_FOLDER + '/w1_slave'

# Other constants
MAX_FAILS = 10
SECONDS_TO_PAUSE_ON_FAIL = 0.5
READING_FREQUENCY_MILLIS = 30000
READING_FREQUENCY_SECONDS = READING_FREQUENCY_MILLIS / 1000


def readHumidity(attemptNumber):
    # This will try up to 15 times to read the temperature. 
    humidity, temperature = Adafruit_DHT.read_retry(HUMIDITY_SENSOR, HUMIDITY_PIN)

    if humidity and temperature:
        return int(humidity)
    elif (attemptNumber < MAX_FAILS):
        print "Failed reading humidity {0} times".format(attemptNumber)
        #No need to pause here - the library takes care of that. 
        read_temp(attemptNumber + 1)
    else:
        print "Failed reading humidity too many times".format(attemptNumber)
        return None

def setupTemperatureReader():
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

def readTemperature(attemptNumber):
    # Heavily inspired by: https://cdn-learn.adafruit.com/downloads/pdf/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing.pdf
    f = open(DEVICE_FILE, 'r')
    lines = f.readlines()
    f.close()

    # Find the temperature. 
    equalsPos = lines[1].find('t=')
    
    # This handles all cases where we fail getting the temperature. 
    if (lines[0].strip()[-3:] != 'YES' or equalsPos == -1) and attemptNumber < MAX_FAILS :
        print "Failed reading temperature {0} times".format(attemptNumber)
        print "Reading was: {0}".format(lines)
        time.sleep(SECONDS_TO_PAUSE_ON_FAIL)
        readTemperature(attemptNumber + 1)
    elif attemptNumber >= MAX_FAILS:
        print "Failed reading temperature too many times".format(attemptNumber)
        return None

    # Now we can return the temperature safely
    tempString = lines[1][equalsPos+2:]
    temp_c = float(tempString) / 1000.0
    return temp_c

def connectToDB():
    db = MySQLdb.connect(host="localhost",
                        user="mtelling",
                        passwd=secret.DB_PASSWORD,
                        db="monitordb")

    cur = db.cursor()

    return db, cur

def writeToDB(humidity, temperature, attemptNumber):
    db, cur = connectToDB()
    insert_statement = (
        "INSERT INTO Reading (temp, humidity, roomID) "
        "VALUES (%s, %s, %s)"
    )

    result = cur.execute(insert_statement, (temperature, humidity, 1))

    if result != 1:
        if attemptNumber < MAX_FAILS:
            print "Error nr. {0} on database: {1}".format(result, attemptNumber)
            time.sleep(SECONDS_TO_PAUSE_ON_FAIL)
            writeToDB(humidity, temperature, attemptNumber + 1)
        else:
            print "Too many errors from DB!"
            return None
    
    db.commit()
    db.close()

    return result
    

def main():

    setupTemperatureReader()

    while (True):  
        # First get the humidity 
        humidity = readHumidity(0)
        
        # Then get the temperature
        temperature = readTemperature(0)

        #Write to db
        dbResult = writeToDB(humidity, temperature, 0)

        # Now if one of them isn't found then exit. 
        if not humidity or not temperature or not dbResult:
            print "Exiting because of too many failures!"
            return
        
        print('{0}%, {1} degrees'.format(humidity, temperature))
        time.sleep(READING_FREQUENCY_SECONDS)
        

main()
