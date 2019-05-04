# fopd -> farm operation platform (fop) device

This code based originated as a fork of the [MVP II](https://github.com/webbhm/OpenAg-MVP-II).

Many thanks to the team that created the MVP II code and hardware designs with a shout out to the folks that answered the call in2016 and 2017 at the St Louis Tech Shop (since reborn as MADE St. Louis). They were fund times!

## Background 

fopd is a python based program that can be configured to operate grow systems such as the MVP II and the Openag Food Computers. 
In addition it can be configured to operate custom built grow systems.  The goal is to make the code agnostic as to the grow environment and systems that it operates and thus configurable as a controller for custom and 
modified grow devices (e.g. automatic dosers, light timers) and environments (e.g. Food Computer version II or a custom germinator that someone may build).  The goals of the project are:

- Target as many grow environments, devices, sensors and actuators as possible.
- Accommodate both the DIY builder and the needs of commercial and academic users. 
- Provide interoperability with the FutureAg St. Louis API and the Urban Space Farms fop API
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
