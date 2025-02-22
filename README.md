# ANT+ 2 MQTT

This Add-on forwards ANT+ fitness tracker data to MQTT for integration into Home Assistant. It is a work in progress and may be unstable.

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/millskyle/hass_ant-2mqtt)



# Standalone use

Perhaps you wish to plug your ANT+ dongle into a computer other than the one running HomeAssistant. In that case, you will want to use a standalone docker image on another computer (e.g. RPi), rather than the Add-on.  In this case:

1) Modify `standalone_options.yaml` to configure the options.
2) Run `docker compose up -d` to build and run the image/container.
3) If you have the MQTT settings correctly configured in `standalone_options.yaml`, the messages should get forwarded and the devices should show up in HomeAssistant just like if you used the Add-on.



