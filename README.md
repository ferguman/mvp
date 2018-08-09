# fopd -> farm operations platform (fop) device

This is a fork of the [MVP II](https://github.com/webbhm/OpenAg-MVP-II).

It maintains the same functionality as the MVP and adds some additional features in order to make it compatible with other
grow environments such as the Food Computer V1.

Many thanks to the team that created the MVP II code and hardware designs.

## Background 

Python code that can be configured to peform the same functions as the MVP II.  The goals of the project are:

- Target other grow enviroments and MVP modifications (e.g. add PH probe to an MVP system).   
- Provide "easy button" functionality such as headless installation
- Provide interoperability with a cloud based MVP learning environment that allows students and teachers to manage their MVPs from a cloud application.
- Provide interoperability with commercial cloud based grow management platforms.


## Architecture:

Upon boot the main program (mvp.py) reads the local configuration file (config/config.py) and spawns threads for
each resource located in the configuration file.

## Hardware Build:

Refer to [MVP II](https://github.com/webbhm/OpenAg-MVP-II) for the details on the hardware build of an MVP. The goal of this project is break 
dependencies between the brain code and the hardware that it will be used on.  Of course at the end of the day everything needs to be compatible but we hope to provide configuration flexiblity so that this code can be used with any grow environment that contains compatible sensors and
actuators.

### Versions

- Blossom is the current release build.  
- Carrot will be the next release.

[blossom build](https://github.com/ferguman/openag-mvp/wiki/Install-mvp-blossom)

## Changes implemented in blossom : 

  - Configuration information is stored in a configuration file named config.py.
  - cron is not needed to operate the system.
  - MQTT has been added.  This allows sensor readings to be sent to a cloud MQTT broker.
  - Data logging has been changed to use the Python logging facility

## Changes planned for carrot:

  - Image upload to the cloud.
  - Compatibility with the Food Computer Version 1
  - Make setup simpler and run within a Pthon venv

## Future Development (in no priority):
- Next release name: carrot
- GUI interface for controlling/monitoring/configuring
- Receive commands via MQTT
- Allow headless configuration of new mvp installations
- Cloud backup of configuration file
