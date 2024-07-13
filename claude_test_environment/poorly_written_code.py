
    def do_stuff(x, y, z):
        a = x + y
        b = x - y
        c = z * (a + b)
        d = z / (a - b)
        e = a ** 2 + b ** 2 + c ** 2 + d ** 2
        f = math.sqrt(e)
        print(f"The result is: {f}")
        return f
    # Usage
    result = do_stuff(10, 5, 3)
    print(f"Final result: {result}")
        