
def simple_correct_spelling(word):
    word = word.replace(u'\u0985\u09BE', u'\u0986')
    return word


def get_possible_roots(word):
    roots = []

    # Try removing off a bunch of suffixes (order is important!)
    suffixes = [
        u'\u0995\u09c7', # "ke"
        u'\u09A6\u09C7\u09B0', # "der"
        u'\u09C7\u09B0\u09BE', # "era"
        u'\u09B0', # "r"
    ]
    for suffix in suffixes:
        if word.endswith(suffix):
            word = word[:-len(suffix)]
            roots.append(word)

    return roots
