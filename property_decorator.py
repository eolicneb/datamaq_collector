class classaware_property:
    def __init__(self, fget=None):
        self.fget = fget
        self.fset = None
        self.fdel = None

    def __get__(self, obj, objtype=None):
        if obj is None:
            print(f"Accediendo desde la clase: {objtype.__name__}")
        else:
            print(f"Accediendo desde la instancia de: {obj.__class__.__name__}")

        if self.fget is None:
            raise AttributeError("Unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("Can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("Can't delete attribute")
        self.fdel(obj)

    def setter(self, fset):
        self.fset = fset
        return self

    def deleter(self, fdel):
        self.fdel = fdel
        return self


class MyClass:
    @classaware_property
    def my_prop(self):
        return 42

    @my_prop.setter
    def my_prop(self, value):
        print(f"Setter llamado con valor: {value}")


if __name__ == "__main__":
    obj = MyClass()
    print(obj.my_prop)  # Accede desde instancia
    print(MyClass.my_prop)  # Accede desde clase

    obj.my_prop = 100  # Llama al setter
