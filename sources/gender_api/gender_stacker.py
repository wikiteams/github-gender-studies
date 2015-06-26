from gender_getter import GeneralGetter
from copy import copy


names = set()


def stackWith(iterator, name):
    global names

    names.add(name)
    if (len(names) == 100):
        batch = copy(names)
        names = set()
        return GeneralGetter(int(iterator), batch)
    else:
        return None
