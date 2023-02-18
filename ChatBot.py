from ChatAuth import ChatAuth
import tls_client
import uuid
import json


class ChatBot:
    def __init__(self):
        self.__session = tls_client.Session(client_identifier="chrome_109", )
        self.parent_message_id = str(uuid.uuid4())
        self.conversation = None
        self.parent_id = str(uuid.uuid4())
        self.base_url = "https://chat.openai.com/backend-api/conversation"
        self.email = None
        self.password = None
        self.get_email_password()
        # self.__proxy = "http://127.0.0.1:8888"
        self.auth = ChatAuth(self.email, self.password, self.__session)
        if self.auth.auth() != 1:
            exit(-4)

    def get_email_password(self):
        with open("config.json", "r") as conf:
            try:
                conf_json = json.loads(conf.read())
                self.email = conf_json['email']
                self.password = conf_json['password']
                if not self.email or not self.password:
                    print("请在config.json中填写email和password")
                    exit()
                return conf_json
            except Exception as e:
                print("配置文件格式不对")

    def ask(self, question):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Content-Type": "application/json",
            "accept": "text/event-stream",
            "x-openai-assistant-app-id": "",
            "referer": "https://chat.openai.com/chat",
            "accept-language": "zh-CN,zh;q=0.9",
            "Connection": "close",
            "Origin": "https://chat.openai.com"
        }

        data = {
            "action": "next",
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": {"content_type": "text", "parts": [question]},
                },
            ],
            # "conversation_id": self.conversation or str(uuid.uuid4()),
            "parent_message_id": self.parent_message_id,
            "model": "text-davinci-002-render-sha"
        }
        if self.conversation:
            data.update({
                "conversation_id": self.conversation,
            })
        res = self.auth.requests(self.base_url, data=json.dumps(data), headers=headers, method="post")
        try:
            res = res.text.splitlines()[-4]
            res = res[6:]
            if res.startswith("{"):
                response = json.loads(res)
                self.parent_message_id = response["message"]["id"]
                self.conversation = response["conversation_id"]
                message = response["message"]["content"]["parts"][0]
                print(message)
                return message
        except Exception as e:
            print(res.json("detail"))


if __name__ == "__main__":
    Bot = ChatBot()
    while 1:
        question = input("question: \n")
        Bot.ask(question)
