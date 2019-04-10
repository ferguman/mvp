# fopd -> farm operation platform (fop) device

This is a fork of the [MVP II](https://github.com/webbhm/OpenAg-MVP-II).

It maintains the same functionality as the MVP and adds some additional features in order to make it compatible with other
grow environment devices.

Many thanks to the team that created the MVP II code and hardware designs.

## Background 

fopd is a python based program that can be configured to operate grow systems such as the MVP II and the Openag Food Computers. 
The goal is to make the code agnostic as to the grow environment that it operates and thus configurable as a controller for custom and 
modified grow devices (e.g. automatic dosers, light timers) and environments (e.g. Food Computer version II or a custom germinator that someone may build).  The goals of the project are:

- Target as many grow environments, devices, sensors and actuators as possible.
- Accommodate both the DIY builder and the needs of commercial and academic users. 
- Provide interoperability with the FutureAg API and the Urban Space Farms fop API
- Be free to adopt and extend, hence the MIT license 

## Architecture:

See the wiki page titled "Architecture".

## Hardware Build:

See the "Hardware Compatibility" page in the wiki.

### Versions

- Dill (next release)
- [Carrot](https://github.com/ferguman/fopd/wiki/Install-fopd-carrot)(current release)
- [Blossom](https://github.com/ferguman/fopd/wiki/Install-fopd-blossom)
 (drepecated)  


## Future Development (in no priority):
- Extend functionality of the web interface for controlling/monitoring/configuring
- Implement the ability for installation and setup to be done via a cloud service
- Allow headless configuration of new fopd installations
- Cloud backup of configuration file
- Implement firmware updates via Yocto/Mender
