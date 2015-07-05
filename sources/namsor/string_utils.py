# I find it quite uncommon to seperate name from surname with something else than a space
# In some cultures first name comes after surname, but very often for the sake of westerners,
# this is reversed-back (source: https://en.wikipedia.org/wiki/Surname#Order_of_names)


from logger.scream import log


def split(s, na="NoneType"):
    name_splits = s.split()
    name = name_splits[0]

    if na == "encoded_space":
        empty_surname = "%20"
    elif na == "space":
        empty_surname = " "
    else:
        empty_surname = "None"

    surname = name_splits[1] if len(name_splits) > 1 else empty_surname
    log("\tName is: " + str(name.encode('unicode_escape')) + " and surname is: " + str(surname.encode('unicode_escape')))
    return name, surname


def StripNonAlpha(s, leave_html):  # API accepts non-latin characters, but numbers are usually unwanted, remove them
    if leave_html and (s == "%20"):
        return s
    return "".join(c for c in s if c.isalpha())  # this means that transcripted-arabic won't be recognized
