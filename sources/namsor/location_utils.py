import pycountry


def get_code(location):
    if (location is not None) and (len(location) > 3):
        location = location.lower()
        for idx, country_object in enumerate(pycountry.countries):
            country_name = country_object.name.lower()
            if country_name in location:
                country_code = country_object.alpha2.lower()
                assert len(country_code) == 2
                return country_code
    else:
        return None
