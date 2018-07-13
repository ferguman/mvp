# fopd -> farm operations platform (fop) device

This is a fork of the [MVP II](https://github.com/webbhm/OpenAg-MVP-II).

## Background 

Python code that can be configured to peform the same functions as the MVP II.  The goals of the project are:

- Target other grow enviroments and MVP modifications (e.g. add PH probe to an MVP system).   
- Provide "easy button" functionality such as headless installation
- Provide interoperability with a cloud based MVP learning environment that allows students and teachers to manage their MVPs from a cloud application.

## Changes made to this fork: 

  - Configuration information is stored in a configuration file named config.py.
  - cron is not needed to operate the system.
  - MQTT has been added.  This allows sensor readings to be sent to a cloud MQTT broker.
  - Data logging has been changed to use the Python logging facility

## Architecture:

The main program (mvp.py) starts threads that handle the following tasks:
  - MQTT client
  - Image capture
  - Log Sensors
  - Light Controller
  - Fan Controller
  - Refresh charts and picture for the UI (render.sh)

Local data storage is in a csv formatted (without header) flat file (/home/pi/MVP/data/data.txt) - this will likely be deprected in the future.
CouchDB is the main data storage system, and will provide easy replication to the cloud in the future.

## Hardware Build:

Refer to [MVP II](https://github.com/webbhm/OpenAg-MVP-II) for the details on the hardware build of an MVP. The goal of this project is break 
dependencies between the brain code and the hardware that it will be used on.  Of course at the end of the day everything needs to be compatible but we hope to provide configuration flexiblity so that this code can be used with any grow environment that contains compatible sensors and
actuators.

### Software Build

[blossom build](https://github.com/ferguman/openag-mvp/wiki/Install-mvp-blossom)

## Future Development (in no priority):
- Next release name: carrot
- GUI interface for controlling/monitoring/configuring
- Receive commands via MQTT
- Send pictures to cloud (such as an Amazon S3 bucket)
- Allow headless configuration of new mvp installations
- Cloud backup of configuration file
