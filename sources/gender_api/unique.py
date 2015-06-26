class NamesCollection:
    #Define some static variables here
    names = dict()

    @classmethod
    def init(self):
        raise Exception('Don\'t create instances of NamesCollection')
        return self
