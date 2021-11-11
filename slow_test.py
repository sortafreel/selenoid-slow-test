import types
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.remote_connection import ChromeRemoteConnection
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def prepare_driver(
    description=None,
    vnc=False,
    selenium_url="http://localhost:4444/wd/hub",
    screen_resolution=(1920, 1080),
):
    capabilities = {
        "browserName": "chrome",
        "version": "69.0",
        "enableVNC": vnc,
        "enableVideo": False,
        "screenResolution": "{}x{}x24".format(
            screen_resolution[0], screen_resolution[1]
        ),
        "env": ["LANG=ru_RU.UTF-8", "LANGUAGE=ru:en", "LC_ALL=ru_RU.UTF-8"],
        "chromeOptions": {
            "args": [
                "--disable-infobars",
                # '--disable-features=EnableEphemeralFlashPermission',
            ],
            # 'prefs': {
            #     'profile.default_content_setting_values.plugins': 1,
            #     'profile.content_settings.plugin_whitelist.adobe-flash-player': 1,
            #     'profile.content_settings.exceptions.plugins.*,'
            #     '*.per_resource.adobe-flash-player': 1,
            #     'profile.default_content_settings.state.flash': 1,
            #     'profile.content_settings.exceptions.plugins.*,*.setting': 1,
            # },
        },
    }
    # Set the session name
    if description:
        capabilities["name"] = "{} {}".format(
            datetime.utcnow().strftime("%d.%m.%y %H:%M:%S"), description
        )
    # Connect to the remote Selenium instance
    driver = webdriver.Remote(
        command_executor=selenium_url, desired_capabilities=capabilities
    )
    # Inject network conditions into remove Chrome driver
    driver.command_executor = ChromeRemoteConnection(driver.command_executor._url)
    driver.set_network_conditions = types.MethodType(
        webdriver.Chrome.set_network_conditions, driver
    )
    driver.get_network_conditions = types.MethodType(
        webdriver.Chrome.get_network_conditions, driver
    )

    # Set full screen
    driver.set_window_size(screen_resolution[0], screen_resolution[1])
    return driver


def watch_slow_stream(description, stream_url, selenium_url, vnc=False):
    """
    Limit the connection speed when processing video content through tests
    """
    driver = prepare_driver(
        description=description,
        vnc=vnc,
        # task_proxy=task_proxy,
        selenium_url=selenium_url,
        screen_resolution=(1024, 768),
    )
    # Limit the speed (better also to set Selenoid idle-limit to 3 minutes)
    driver.set_network_conditions(
        offline=False,
        latency=5,  # additional latency (ms)
        download_throughput=5000 * 1024,  # maximal throughput
        upload_throughput=5000 * 1024,  # maximal throughput
    )
    driver.get(stream_url)
    # Do some actions every 5 seconds to stay alive
    while True:
        ActionChains(driver).send_keys(Keys.ALT).perform()
        sleep(5)


if __name__ == "__main__":
    watch_slow_stream(
        description="Stream test",
        stream_url="https://www.twitch.tv/aoiharu",
        selenium_url="http://51.15.143.106:4444/wd/hub",
        vnc=True,
    )
