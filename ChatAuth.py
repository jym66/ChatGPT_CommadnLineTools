import json
import tls_client
from clearance import clearance


class ChatAuth:
    def __init__(self, username, password, session: tls_client.Session):
        self.__session = session
        self.__GREEN = "\033[92m"
        self.__WARNING = "\033[93m"
        self.ENDCOLOR = "\033[0m"
        self.__config = "cookie.json"
        self.cf = clearance()
        self.__cf_clearance = self.__get_cf_cookie("init")
        self.__session.cookies.set("cf_clearance", self.__cf_clearance)
        self.__username = username
        self.__password = password
        # 从这个地方开始跳转
        self.__url = "https://chat.openai.com/api/auth/signin/auth0?prompt=login"
        self.__csrf_url = "https://chat.openai.com/api/auth/csrf"
        self.__auth_url = "https://chat.openai.com/api/auth/signin/auth0?prompt=login"
        self.__authBase = "https://auth0.openai.com"
        self.__accessToken_url = "https://chat.openai.com/api/auth/session"
        self.__identifier_url = None
        self.__csrf_token = None
        # self.__proxy = "http://127.0.0.1:8888"

    def __get_csrf_token(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/110.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "accept": "text/event-stream",
            "x-openai-assistant-app-id": "",
            "referer": "https://chat.openai.com/auth/login",
            "accept-language": "zh-CN,zh;q=0.9",
            "Connection": "close",
            "Origin": "https://chat.openai.com"
        }
        res = self.requests(url=self.__csrf_url, headers=headers, method="get", data=None)
        self.__csrf_token = res.json()['csrfToken']

    def __get_identifier_url(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/110.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "accept": "text/event-stream",
            "x-openai-assistant-app-id": "",
            "referer": "https://chat.openai.com/auth/login",
            "accept-language": "zh-CN,zh;q=0.9",
            "Connection": "close",
            "Origin": "https://chat.openai.com"
        }
        params = f"callbackUrl=%2Fchat&csrfToken={self.__csrf_token}&json=true"
        res = self.requests(url=self.__auth_url, headers=headers, data=params, method="post").json()
        self.__identifier_url = res['url']

    # 认证
    def __go_to_authorize(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/110.0.0.0 Safari/537.36",
            "accept": "text/event-stream",
            "x-openai-assistant-app-id": "",
            "referer": "https://chat.openai.com/auth/login",
            "accept-language": "zh-CN,zh;q=0.9",
            "Connection": "close",
            "Origin": "https://chat.openai.com"
        }
        # 登陆url
        location_url = \
            self.requests(self.__identifier_url, headers=headers, method="get", data=None).headers[
                'Location']
        username_state = str(location_url).split("state=")[-1]
        username_params = f"state={username_state}&username={self.__username}&js-available=true&webauthn-available" \
                          f"=true&is-brave=false&webauthn-platform-available=true&action=default "
        headers['Content-Type'] = "application/x-www-form-urlencoded"
        # 跳转password_url 302
        password_location = self.requests(
            self.__authBase + location_url, headers=headers, data=username_params, method="post").headers['Location']

        password_state = str(password_location).split("state=")[-1]
        password_params = f"state={password_state}&username={self.__username}&password={self.__password}&action=default"
        resume_location = self.requests(
            self.__authBase + password_location, headers=headers,
            data=password_params, method="post").headers[
            'Location']
        auth0_url = \
            self.requests(self.__authBase + resume_location, method="get", data=None,
                          headers=headers).headers[
                'Location']
        self.requests(auth0_url, headers=headers, method="get", data=None)
        access_token = \
            self.requests(self.__accessToken_url, headers=headers, method="get", data=None).json()[
                'accessToken']
        self.__session.headers.update({
            "authorization": f"Bearer {access_token}"
        })

    def __rw_config(self, mode):
        if mode == "r":
            with open(self.__config, "r+") as config:
                return config.read()
        if mode == "w":
            with open(self.__config, "w") as config:
                cookie_dict = self.__session.cookies.get_dict()
                del cookie_dict['cf_clearance']
                cookie_dict['access_token'] = self.__session.headers.get("authorization")
                config.write(json.dumps(cookie_dict))

    def __check_cookie(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/110.0.0.0 Safari/537.36",
            "accept": "text/event-stream",
            "x-openai-assistant-app-id": "",
            "referer": "https://chat.openai.com/auth/login",
            "accept-language": "zh-CN,zh;q=0.9",
            "Connection": "close",
            "Origin": "https://chat.openai.com"
        }
        status = self.requests("https://chat.openai.com/chat", headers=headers, method="post",
                               data=None)
        return status.status_code

    def __get_cf_cookie(self, name):
        cf_cookie = self.cf.get_cf_cookie()
        return cf_cookie

    def requests(self, url, headers, data, method):
        if method == "post":
            res = self.__session.post(url, data=data, headers=headers, timeout_seconds=180)
            if res.status_code == 403:
                print(f"{self.__GREEN} cf_clearance过期重新获取 {self.ENDCOLOR}")
                self.__session.cookies.set("cf_clearance", self.__get_cf_cookie("requests_post"))
                return self.__session.post(url, data=data, headers=headers, timeout_seconds=180)
            return res
        if method == "get":
            res = self.__session.get(url, headers=headers, timeout_seconds=180)
            if res.status_code == 403:
                print(f"{self.__GREEN} cf_clearance过期重新获取 {self.ENDCOLOR}")
                self.__session.cookies.set("cf_clearance", self.__get_cf_cookie("requests_get"))
                return self.__session.get(url, headers=headers, timeout_seconds=180)
            return res

    def __online_auth(self):
        print(f"{self.__GREEN} 认证过期 尝试重新认证 ！！{self.ENDCOLOR}")
        self.__session.cookies.clear()
        self.__session.cookies.set("cf_clearance", self.__cf_clearance)
        self.__session.headers.clear()
        self.__get_csrf_token()
        self.__get_identifier_url()
        self.__go_to_authorize()
        if self.__session.cookies.get("__Secure-next-auth.session-token"):
            print(f"{self.__GREEN} 认证成功！！ {self.ENDCOLOR}")
            self.__rw_config("w")
            return 1
        return -1

    def auth(self):
        config = self.__rw_config("r")
        if len(config):
            config_json = json.loads(config)
            print(f"{self.__GREEN} 尝试使用配置文件里的Cookie！！ {self.ENDCOLOR}")
            if "access_token" in config_json:
                self.__session.headers.update({
                    "authorization": config_json['access_token']
                })
                for key in config_json:
                    if key != "access_token" and key != "cf_clearance":
                        self.__session.cookies.set(key, config_json[key])
                # self.__session.cookies.set("cf_clearance", self.__cf_clearance)
                if self.__check_cookie() == 200:
                    print(f"{self.__GREEN} 成功使用配置文件里的Cookie！！ {self.ENDCOLOR}")
                    return 1
                else:
                    return self.__online_auth()
        else:
            return self.__online_auth()
