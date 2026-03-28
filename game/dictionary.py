import os

_WORD_SET = None
_DICT_PATH = os.path.join(os.path.dirname(__file__), 'twl06.txt')


def _load_words():
    global _WORD_SET
    if _WORD_SET is not None:
        return
    _WORD_SET = set()
    with open(_DICT_PATH) as f:
        for line in f:
            word = line.strip()
            if word:
                _WORD_SET.add(word.upper())


def is_valid_word(word):
    _load_words()
    return word.upper() in _WORD_SET
