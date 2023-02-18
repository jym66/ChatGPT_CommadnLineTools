import undetected_chromedriver as uc
import re


class clearance:
    def __init__(self):
        self.__isFind = False
        self.__cf_clearance = None
        self.__driver = None
        self.baseUrl = "https://chat.openai.com/auth/login"

    def __find_cookie(self, msg):
        if "params" in msg:
            if "headers" in msg['params']:
                if 'set-cookie' in msg['params']["headers"]:
                    cf_clearance = re.findall("cf_clearance=(.*?);", msg['params']["headers"]['set-cookie'])
                    if cf_clearance:
                        self.__isFind = True
                        self.__cf_clearance = cf_clearance[0]
                        self.__driver.quit()

    def get_cf_cookie(self):
        self.__driver = uc.Chrome(
            enable_cdp_events=True,
            options=self.__get_ChromeOptions(),
            headless=True
        )
        self.__driver.add_cdp_listener(
            "Network.responseReceivedExtraInfo",
            lambda msg: self.__find_cookie(msg),
        )
        self.__driver.get(self.baseUrl)
        while not self.__isFind:
            pass
        return self.__cf_clearance

    def __get_ChromeOptions(self):
        options = uc.ChromeOptions()
        options.add_argument("--start_maximized")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return options
