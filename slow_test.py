#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Тест замедления скорости соединения в Selenium/Selenoid
from selenium.webdriver.chrome.remote_connection import ChromeRemoteConnection
from datetime import datetime
from selenium import webdriver
from time import sleep
import types
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


# Функция подготовки драйвера
def prepare_driver(
    description=None,
    vnc=False,
    selenium_url='http://localhost:4444/wd/hub',
    screen_resolution=(1920, 1080),
):

    # Настраиваю свойства драйвера
    capabilities = {
        'browserName': 'chrome',
        'version': '69.0',
        'enableVNC': vnc,
        'enableVideo': False,
        'screenResolution': '{}x{}x24'.format(
            screen_resolution[0], screen_resolution[1]
        ),
        'env': ['LANG=ru_RU.UTF-8', 'LANGUAGE=ru:en', 'LC_ALL=ru_RU.UTF-8'],
        'chromeOptions': {
            'args': [
                '--disable-infobars',
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

    # Настраиваю имя теста
    if description:
        capabilities['name'] = '{} {}'.format(
            datetime.utcnow().strftime('%d.%m.%y %H:%M:%S'), description
        )

    # Подключаюсь к удалённому Selenium
    driver = webdriver.Remote(
        command_executor=selenium_url, desired_capabilities=capabilities
    )

    # Повязываю network conditions из Chromedriver в Remote
    driver.command_executor = ChromeRemoteConnection(driver.command_executor._url)
    driver.set_network_conditions = types.MethodType(
        webdriver.Chrome.set_network_conditions, driver
    )
    driver.get_network_conditions = types.MethodType(
        webdriver.Chrome.get_network_conditions, driver
    )

    # Разворачиваю браузер на всё окно
    driver.set_window_size(screen_resolution[0], screen_resolution[1])

    # Возвращаю драйвер
    return driver


# Функция теста лимитирования соединения на примере Twitch-стримов
def watch_slow_stream(description, stream_url, selenium_url, vnc=False):

    # Подготавливаю драйвер
    driver = prepare_driver(
        description=description,
        vnc=vnc,
        # task_proxy=task_proxy,
        selenium_url=selenium_url,
        screen_resolution=(1024, 768),
    )

    # Лимитирую скорость соединения
    # Желательно поставить лимит idle-отключения в Selenoid на 3 минуты+
    driver.set_network_conditions(
        offline=False,
        latency=5,  # additional latency (ms)
        download_throughput=5000 * 1024,  # maximal throughput
        upload_throughput=5000 * 1024,  # maximal throughput
    )

    # Открываю страницу
    driver.get(stream_url)

    # Запускаю 5-секундный цикл, чтобы Selenoid оставался активным
    while True:

        # Выполняю минимальное действие, чтобы сессия считалась активной
        ActionChains(driver).send_keys(Keys.ALT).perform()

        # Пауза на 5 секунд
        sleep(5)


# Основные замечания:
# - Для использования set_network_conditions приходится использовать костыли
# - network_conditions лимитируют только загрузку статичного контента (js, изображения,
# css и т.п.),но не лимитирует загрузку видео (в данном примере Twitch)
# в то время как desktop DevTools лимитируют (через network throttling)
if __name__ == "__main__":

    # При правильном лимитировании, Twitch должен автоматически снизить качество видео
    # Сейчас же он запускает видео в 1080p(60fps), даже когда статика грузится 3 минуты+
    # Конечная скорость напрямую зависит от сервера, проверял на Scaleway
    # Для эксперимента замелял всю машину через wondershaper - видео сразу же ужимается

    # Необходимо указать адрес работающего Selenoid
    # И адрес любого стрима, который поддерживает форматы от 160p до 1080p
    watch_slow_stream(
        description='Тест стрима',
        stream_url='https://www.twitch.tv/aoiharu',
        selenium_url='http://51.15.143.106:4444/wd/hub',
        vnc=True,
    )
