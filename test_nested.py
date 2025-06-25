class Outer:

    def outer_method(self):
        return "outer"

    class Inner:

        def inner_method(self):
            return "replaced inner method"

        def another_inner(self):
            return "another inner"