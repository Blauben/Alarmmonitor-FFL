"""Launches a kiosk-mode Chrome browser logged into the alarmruf112.eu monitor portal.

Reuses a previously stored monitor URL when possible to skip the login flow, and
exits once the browser window is closed by the user.
"""

import os
import dotenv
import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.select import Select

mainpage = "https://www.alarmruf112.eu/www/einloggen"
login_endpoint = "https://www.alarmruf112.eu/www/AlarmNG/auth_user.php"
dotenv.load_dotenv(".env")
username = os.getenv("ALARM_USERNAME")
password = os.getenv("ALARM_PASSWORD")
portal = "monitor"
selenium_profile_path = os.getenv("SELENIUM_PROFILE_PATH", ".selenium_profile")
selenium_binary_path = os.getenv("SELENIUM_BINARY_PATH")
selenium_driver_path = os.getenv("SELENIUM_DRIVER_PATH")


handlers = [
    logging.StreamHandler(sys.stdout),
    RotatingFileHandler("alarmmonitor.log", maxBytes=1024 * 1024, backupCount=2),
]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=handlers,
)


def selenium_driver():
    """Build and return a Chrome WebDriver configured for fullscreen kiosk display.

    Uses the persistent profile, binary, and driver paths from the environment
    when set, so login sessions and browser state survive across restarts.
    """
    options = ChromeOptions()
    if selenium_profile_path:
        profile_dir = os.path.abspath(selenium_profile_path)
        options.add_argument(f"--user-data-dir={profile_dir}")
        options.add_argument("--profile-directory=Default")

    if selenium_binary_path:
        options.binary_location = selenium_binary_path

    # Start directly in kiosk mode for a reliable fullscreen monitor display.
    options.add_argument("--kiosk")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.experimental_options["excludeSwitches"] = ["enable-automation"]

    if selenium_driver_path:
        driver = webdriver.Chrome(
            service=Service(
                executable_path=selenium_driver_path, log_output=sys.stdout
            ),
            options=options,
        )
    else:
        driver = webdriver.Chrome(options=options)
    return driver


def attempt_stored_login(driver):
    """Try to reuse a previously saved monitor URL instead of logging in again.

    Args:
        driver: The Selenium WebDriver to navigate.

    Returns:
        The monitor URL string if the stored session is still valid, otherwise
        None (meaning the caller should fall back to a fresh login).
    """
    if not os.path.exists("monitor_url.json"):
        logging.info("No stored monitor URL found. Continuing with login.")
        return None
    try:
        with open("monitor_url.json", "r") as f:
            data = json.load(f)
            monitor_url = data.get("monitor_url")
            driver.get(monitor_url)
            time.sleep(5)  # Wait for the page to load
            if driver.current_url == monitor_url:
                logging.info("Stored monitor URL is valid.")
                return monitor_url
            else:
                logging.info(
                    "Stored monitor URL is invalid or expired. Continuing with login."
                )
                return None
    except Exception as e:
        logging.error("Error reading stored monitor URL: %s", e)
        return None


def login(driver):
    """Fill in and submit the alarmruf112.eu login form to reach the monitor portal.

    Args:
        driver: The Selenium WebDriver to navigate and interact with.

    Returns:
        The URL the browser lands on after a successful login.
    """
    payload = {
        "data[Page][login]": username,
        "data[Page][password]": password,
        "data[Page][portal]": portal,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    driver.get(mainpage)
    login_form = driver.find_element("xpath", "//form[@action='/www/einloggen']")
    login_form.find_element("xpath", "//input[@name='data[Page][login]']").send_keys(
        username
    )
    login_form.find_element("xpath", "//input[@name='data[Page][password]']").send_keys(
        password
    )
    Select(
        login_form.find_element("xpath", "//select[@name='data[Page][portal]']")
    ).select_by_value(portal)
    login_form.submit()
    time.sleep(5)  # Wait for the page to load after login
    return driver.current_url


def signal_handler(signum, frame):
    """Placeholder OS signal handler; currently just logs that a signal arrived."""
    print("Signal received, executing handler...")


def main():
    """Log into the monitor portal (or reuse a stored session) and watch the
    browser until its DevTools connection drops, indicating the window was closed.
    """
    driver = selenium_driver()
    monitor_url = attempt_stored_login(driver)
    if not monitor_url:
        monitor_url = login(driver)
        with open("monitor_url.json", "w") as f:
            json.dump({"monitor_url": monitor_url, "timestamp": time.time()}, f)
            logging.info("Monitor URL stored in monitor_url.json.")

    logging.info("Monitor URL: %s", monitor_url)

    DISCONNECTED_MSG = (
        "Unable to evaluate script: disconnected: not connected to DevTools\n"
    )

    while True:
        log = driver.get_log("driver")
        if len(log) > 0 and log[-1]["message"] == DISCONNECTED_MSG:
            print("Browser window closed by user")
            exit(1)
        time.sleep(1)


if __name__ == "__main__":
    main()
