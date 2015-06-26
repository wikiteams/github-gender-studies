from gender_getter import GeneralGetter
from copy import copy


names = list()


def stackWith(iterator, name):
    global names

    if name not in names:
        names.append(name)
    if (len(names) == 100):
        batch = copy(names)
        names = list()
        return GeneralGetter(int(iterator), batch)
    else:
        return None
