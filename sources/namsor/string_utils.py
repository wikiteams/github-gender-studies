# I find it quite uncommon to seperate name from surname with something else than a space
# In some cultures first name comes after surname, but very often for the sake of westerners,
# this is reversed-back (source: https://en.wikipedia.org/wiki/Surname#Order_of_names)


from logger.scream import log


def split(s, na="NoneType"):
    name_splits = s.split()
    name = name_splits[0]
    surname = name_splits[1] if len(name_splits) > 1 else (" " if na == "space" else None)
    log("\tName is: " + str(name.encode('unicode_escape')) + " and surname is: " + str(surname.encode('unicode_escape')))
    return name, surname
