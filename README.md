
## Home Assistant Custom Component: Hemglass

[![GitHub Release][releases-shield]][releases]
![Project Stage][project-stage-shield]
[![issues-shield]](issues)
[![License][license-shield]](LICENSE.md)
[![hacs_badge][hacs-shield]][hacs]

[![Buy me a coffee][buymeacoffee-shield]][buymeacoffee]

A sensor for getting information about the next time Hemglass comes to visit. You give it coordinates and it will pick the closest stop, if you want a specific stop, use the coordinates for that stop.


|Parameter| What to put |
|--|--|
| Name | This is the name you want for the sensor in Home Assistant |
| latitude | Latitude coordinate close to the stop you want |
| longitude | Longitude coordinate close to the stop you want |


```
- platform: hemglass
  name: "Glassbilen"
  latitude: 59.331
  longitude: 18.1278
```

[releases-shield]: https://img.shields.io/github/release/popeen/Home-Assistant-Addon-Hemglass.svg
[releases]: https://github.com/popeen/Home-Assistant-Addon-Hemglass/releases
[project-stage-shield]: https://img.shields.io/badge/project%20stage-ready%20for%20use-green.svg
[issues-shield]: https://img.shields.io/github/issues-raw/popeen/Home-Assistant-Addon-Hemglass.svg
[license-shield]: https://img.shields.io/github/license/popeen/Home-Assistant-Addon-Hemglass.svg
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg
[hacs]: https://github.com/custom-components/hacs
[buymeacoffee-shield]: https://www.buymeacoffee.com/assets/img/guidelines/download-assets-sm-2.svg
[buymeacoffee]: https://www.buymeacoffee.com/popeen
