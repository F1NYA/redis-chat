from PyInquirer import ValidationError, Validator
from src.definitions import Role, MessageEvent
from src import User, Message
from random import random

from .UserActionsScene import UserActionsScene
from .BaseScene import BaseScene


WORKER = "🤖 Be a worker"
USER = "🤓 Be a user"
EXIT = "❌ exit"


class LoginValidator(Validator):
    def validate(self, document):
        if not len(str(document.text).strip()):
            pos = len(document.text)
            raise ValidationError(message="Login cannot be empty", cursor_position=pos)


class GreetingScene(BaseScene):
    def __init__(self, session, redis):
        super().__init__(
            [
                {
                    "type": "list",
                    "name": "role",
                    "message": "What do you want to do?",
                    "choices": [WORKER, USER, EXIT],
                },
                {
                    "type": "input",
                    "name": "login",
                    "message": "Your login",
                    "when": lambda answers: answers["role"] == USER,
                    "validate": LoginValidator,
                },
            ]
        )
        self.redis = redis
        self.chat = session["chat"]
        self.thread = None
        self.session = session

    def enter_as_worker(self):
        self.session["role"] = Role.WORKER
        self.thread = self.chat.listen_events(
            {"%s:*" % MessageEvent.CREATED: self.handle_message_created_as_worker}
        )
        while True:
            message = self.chat.get_next_unprocessed_message("auto_worker")
            if not message:
                break
            self.process_message_as_worker(message)

    def handle_message_created_as_worker(self, message):
        message_instance = Message.load(message["data"], self.redis)
        self.process_message_as_worker(message_instance)

    def process_message_as_worker(self, message):
        print("⚠️ receive msg %s, working..." % message.id)
        if random() > 0.7:
            print("❌ block msg %s" % message.id)
            self.chat.ban_message("auto_worker", message)
        else:
            print("✅ confirm msg %s" % message.id)
            self.chat.confirm_message("auto_worker", message)

    def enter_as_user(self, answers):
        self.session["role"] = Role.USER

        login = str(answers["login"]).strip()

        me = User.load(self.redis, login)
        if not me:
            me = User(login, "admin" if login.endswith("admin") else "user", self.redis)
            me.save()

        if login.endswith("admin"):
            self.thread = self.chat.listen_events(
                {
                    "%s:%s"
                    % (MessageEvent.CREATED, login): self.handle_message_created,
                    "%s:%s"
                    % (MessageEvent.PENDING, login): self.handle_pending_message,
                    "%s:%s"
                    % (MessageEvent.CONFIRMED, login): self.handle_message_confirm,
                    "%s:%s" % (MessageEvent.BANNED, login): self.handle_message_ban,
                    "%s:*" % MessageEvent.CREATED: self.handle_else_message_created,
                    "%s:*" % MessageEvent.PENDING: self.handle_else_pending_message,
                    "%s:*" % MessageEvent.CONFIRMED: self.handle_else_message_confirm,
                    "%s:*" % MessageEvent.BANNED: self.handle_else_message_ban,
                }
            )
        else:
            self.thread = self.chat.listen_events(
                {
                    "%s:%s"
                    % (MessageEvent.CREATED, login): self.handle_message_created,
                    "%s:%s"
                    % (MessageEvent.PENDING, login): self.handle_pending_message,
                    "%s:%s"
                    % (MessageEvent.CONFIRMED, login): self.handle_message_confirm,
                    "%s:%s" % (MessageEvent.BANNED, login): self.handle_message_ban,
                }
            )
        self.session["me"] = me
        UserActionsScene(self.session, self.redis).enter()

    @staticmethod
    def __print_format_else_msg(format_str, msg):
        sender = msg["channel"].split(":")[1]
        print(format_str % (sender, msg["data"]))

    @staticmethod
    def handle_else_message_created(msg):
        GreetingScene.__print_format_else_msg("💬 %s create a message %s", msg)

    @staticmethod
    def handle_else_pending_message(msg):
        GreetingScene.__print_format_else_msg("💬 %s has an incoming message %s", msg)

    @staticmethod
    def handle_else_message_confirm(msg):
        GreetingScene.__print_format_else_msg("💬 %s message %s was approved", msg)

    @staticmethod
    def handle_else_message_ban(msg):
        GreetingScene.__print_format_else_msg("💬 %s message %s was banned", msg)

    @staticmethod
    def __print_format_msg(format_str, msg):
        print(format_str % msg["data"])

    @staticmethod
    def handle_message_created(msg):
        GreetingScene.__print_format_msg("⭐️ Your message %s created", msg)

    @staticmethod
    def handle_pending_message(msg):
        GreetingScene.__print_format_msg("⭐️ You have a new pending message: %s", msg)

    @staticmethod
    def handle_message_confirm(msg):
        GreetingScene.__print_format_msg("✅ Your message %s was confirmed", msg)

    @staticmethod
    def handle_message_ban(msg):
        GreetingScene.__print_format_msg("⛔️ Your message %s was banned", msg)

    def enter(self):
        while True:
            if self.thread:
                self.thread.stop()
                self.thread = None

            answers = self.ask()
            if "role" not in answers:
                continue

            role = answers["role"]
            if role == WORKER:
                self.enter_as_worker()
                break
            if role == USER:
                self.enter_as_user(answers)
            if role == EXIT:
                return

    def __del__(self):
        if self.thread:
            self.thread.stop()
