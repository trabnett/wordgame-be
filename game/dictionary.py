import os

_WORD_SET = None
_DICT_PATH = '/usr/share/dict/american-english'


def _load_words():
    global _WORD_SET
    if _WORD_SET is not None:
        return
    _WORD_SET = set()
    if not os.path.exists(_DICT_PATH):
        return
    with open(_DICT_PATH) as f:
        for line in f:
            word = line.strip()
            if not word or "'" in word:
                continue
            # Skip proper nouns (capitalized in the dictionary)
            if word[0].isupper():
                continue
            if len(word) >= 2:
                _WORD_SET.add(word.upper())


def is_valid_word(word):
    _load_words()
    if not _WORD_SET:
        # No dictionary available — accept all words (local dev fallback)
        return True
    return word.upper() in _WORD_SET
