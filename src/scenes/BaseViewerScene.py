from abc import abstractmethod
from math import ceil

from .BaseScene import BaseScene


BACK = "⬅️ prev page"
NEXT = "➡️ next page"
EXIT = "◀️ return"

ITEMS_PER_PAGE = 25


class BaseViewerScene(BaseScene):
    def __init__(self, items_per_page=ITEMS_PER_PAGE):
        super().__init__(
            [
                {
                    "type": "list",
                    "name": "action",
                    "message": "Navigation",
                    "choices": [NEXT, BACK, EXIT],
                }
            ]
        )
        self.items_per_page = items_per_page
        self.cursor = 0

    def load(self):
        items = self.fetch(self.cursor, self.cursor + ITEMS_PER_PAGE)
        if not len(items):
            return []
        else:
            return items

    @abstractmethod
    def fetch(self, start, end):
        pass

    @abstractmethod
    def items_count(self):
        pass

    def __change_page(self, items_per_page):
        self.cursor += items_per_page
        if self.cursor > self.items_count() or self.cursor < 0:
            self.cursor = 0

    def next_page(self):
        self.__change_page(+ITEMS_PER_PAGE)

    def prev_page(self):
        self.__change_page(-ITEMS_PER_PAGE)

    def enter(self):
        while True:
            page = ceil(self.cursor // ITEMS_PER_PAGE)
            total = self.items_count()

            print("Page: %i" % page)
            print("Total: %i" % total)
            print("\n".join(self.load()))

            action = self.ask()["action"]
            if action == NEXT:
                self.next_page()
            elif action == BACK:
                self.prev_page()
            else:
                return
