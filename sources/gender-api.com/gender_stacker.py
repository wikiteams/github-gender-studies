from gender_getter import GeneralGetter


class GetterJobs():

    names = set()

    def __init__(self, decorated):
        self._decorated = decorated

    def Instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def stackWith(self, iterator, name):
        self.names.append(name)
        if (len(self.names) == 100):
            self.batch = self.names.copy()
            self.names = set()
            return GeneralGetter(int(iterator), self.batch)
        else:
            return None

    def __call__(self):
        raise TypeError('Singletons must be accessed through `Instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)
