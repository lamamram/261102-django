# ------------- programmation fonctionnelle ------------

def square(x: int) -> int:
    return x ** 2

def my_map(f, data: list):
    return [ f(elem) for elem in data ]

data = list(range(10))
# print(my_map(square, data))
# print(list(map(square, data)))

print(list(map(lambda x: x**2, data)))


