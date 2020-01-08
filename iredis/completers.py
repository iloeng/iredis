import logging

from prompt_toolkit.completion import WordCompleter, FuzzyWordCompleter

from .config import config
from .redis_grammar import CONST
from .commands_csv_loader import group2commands, commands_summary, all_commands


logger = logging.getLogger(__name__)


class LatestUsedFirstWordCompleter(FuzzyWordCompleter):
    """
    Not thread safe.
    """

    def __init__(self, max_words, words, *args, **kwargs):
        self.words = words
        self.max_words = max_words
        super().__init__(words, *args, **kwargs)

    def touch(self, word):
        """
        Make sure word is in the first place of the completer
        list.
        """
        if word in self.words:
            self.words.remove(word)
        else:  # not in words
            if len(self.words) == self.max_words:  # full
                self.words.pop()
        self.words.insert(0, word)

    def touch_words(self, words):
        for word in words:
            self.touch(word)


def get_completer_mapping():
    completer_mapping = {}
    # patch command completer with hint
    command_hint = {key: info["summary"] for key, info in commands_summary.items()}
    for command_group, commands in group2commands.items():
        words = commands + [command.lower() for command in commands]
        if config.newbie_mode:
            hint = {command: command_hint.get(command.upper()) for command in words}
        else:
            hint = None
        completer_mapping[command_group] = WordCompleter(
            words, sentence=True, meta_dict=hint
        )

    completer_mapping.update(
        {
            key: WordCompleter(tokens.split(" "), ignore_case=True)
            for key, tokens in CONST.items()
        }
    )
    key_completer = LatestUsedFirstWordCompleter(config.completer_max, [])
    member_completer = LatestUsedFirstWordCompleter(config.completer_max, [])
    field_completer = LatestUsedFirstWordCompleter(config.completer_max, [])

    completer_mapping.update(
        {
            # all key related completers share the same completer
            "keys": key_completer,
            "key": key_completer,
            "destination": key_completer,
            "newkey": key_completer,
            # member
            "member": member_completer,
            "members": member_completer,
            # hash fields
            "field": field_completer,
            "fields": field_completer,
        }
    )
    completer_mapping["command"] = WordCompleter(
        all_commands, ignore_case=True, sentence=True
    )
    return completer_mapping


completer_mapping = get_completer_mapping()
