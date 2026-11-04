# ------------- programmation fonctionnelle ------------

def square(x: int) -> int:
    return x ** 2

def my_map(f, data: list):
    return [ f(elem) for elem in data ]

data = list(range(10))
# print(my_map(square, data))
# print(list(map(square, data)))

print(list(map(lambda x: x**2, data)))

# ------------------- utilisation de * et ** à l'appel d'une fonction ---------

def func(a, b, c):
    return a, b, c

params = [1, 2, 3]
func(params[0], params[1], params[2])
func(*params)

params = {"a": 1, "c": 2, "b": 3}
func(**params)

def func(**kwargs):
    return list(kwargs.items())

print(func(**params))

