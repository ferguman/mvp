# TBD - make the mvp hardware compatible with the carrot branch.  This will necessiate an
# mvp "driver" analogous to openag_micro
#
#Controls the turning on and turning off of lights
#Lights are wired into Relay #4 (Pin 29)

import RPi.GPIO as GPIO
from python.logData import logData
from time import sleep 
from datetime import datetime
import sys

from config.config import light_controller_program, log_light_state_to_local_couchdb, log_light_state_to_local_file


from logging import getLogger
logger = getLogger('mvp.' + __name__)

def log_lights(state: str):

   log_list = ['{:%Y-%m-%d %H:%M:%S}'.format(datetime.now()) , 'Light_Switch',
               'Success', 'light', None, {}.format(state), None, '']

   if log_light_state_to_local_couchdb:
      logDB(**log_list)

   if log_light_state_to_local_file:
      logFile(**log_list)

def setLightOff():

   "Check the time and determine if the lights need to be changed"
   lightPin = 29
   GPIO.setwarnings(False)
   GPIO.setmode(GPIO.BOARD)
   GPIO.setup(lightPin, GPIO.OUT)
   # For the relaly board, use the first line
   # For the Sparkfun PowerSwitch tail (https://www.sparkfun.com/products/10747)
   # Uncomment the second line, and comment out the first
   GPIO.output(lightPin, GPIO.LOW)
   #    GPIO.output(lightPin, GPIO.HIGH)
   logger.info('Turned light off')

   logData("Light_Switch", "Success", "light", None, "Off", None, '')


def setLightOn():

   "Check the time and determine if the lights need to be changed"
   lightPin = 29
   GPIO.setwarnings(False)
   GPIO.setmode(GPIO.BOARD)
   GPIO.setup(lightPin, GPIO.OUT)
   # For the relaly board, use the first line
   # For the Sparkfun PowerSwitch tail (https://www.sparkfun.com/products/10747)
   # Uncomment the second line, and comment out the first    
   GPIO.output(lightPin, GPIO.HIGH)
   #    GPIO.output(lightPin, GPIO.LOW)    
   logger.info('Turned light on')

   logData("Light_Switch", "Success", "light", None, "On", None, '')

