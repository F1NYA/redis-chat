from PyInquirer import prompt


class BaseScene:
    def __init__(self, questions):
        self.questions = questions
        BaseScene.clear()

    @staticmethod
    def clear():
        print("\x1bc")

    def ask(self, questions=None, clear=True):
        answers = prompt(questions or self.questions)
        if clear:
            BaseScene.clear()

        return answers
