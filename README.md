# Alarmmonitor-FFL
By leveraging Selenium, this project connects to the Alarmruf112 alarm-monitoring portal and displays the monitor in a web browser.

## Requirements
The credentials for the alarm system are expected to be stored in the .env file in the following format:
```
ALARM_USERNAME=your_username
ALARM_PASSWORD=your_password
```

You may also specify selenium options in the .env file:
```
SELENIUM_PROFILE_PATH=path_to_your_selenium_profile
SELENIUM_BINARY_PATH=path_to_your_selenium_binary
SELENIUM_DRIVER_PATH=path_to_your_selenium_driver (default: .selenium_profile)
```

## Intended Use
This project does not keep the browser alive if it has been closed. It is intended to be run as a service to be restarted on failure. The service should be configured to run the script `alarmmonitor.py` with the appropriate environment variables set.
