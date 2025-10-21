from functools import wraps


def deco(func):
    @wraps(func)
    def _inner(self, *args, **kwargs):
        print(f"inner... {self.__class__.__name__}")
        result = func(self, *args, **kwargs)
        return f"result: {result}"
    return _inner


class prop_deco:
    def __init__(self, fget=None):
        self.fget = fget

    def __get__(self, obj, objtype=None):
        return self.fget(obj)


class Test:
    def __init__(self, value):
        print(f"__init__ - {__class__}")
        self.value = value

    @deco
    def method_A(self, *args, **kwargs):
        print(f"method {self.__class__.__name__}")
        print(args, kwargs)
        return f"{args} | {kwargs}"

    @prop_deco
    def da_prop(self):
        print(f"Da value {self.value}")
        return self.value


if __name__ == "__main__":
    print(Test(9).method_A(1, 2, a=4))
    print(Test(8).da_prop)
