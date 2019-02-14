'''
Implements a Singleton pattern class to be inherited by other classes.
To make child classes singletons, do this:

from patterns.singleton import Singleton

class MyClass(BaseClass):
    __metaclass__ = Singleton

Ref:
http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

'''

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]