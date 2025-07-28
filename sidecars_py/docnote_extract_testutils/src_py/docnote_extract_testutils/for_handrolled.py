"""This has any bits n bobs we need for handrolled test cases to work
correctly. This allows us to use the handrolled stuff both in situations
where we stub stuff out, and in situations where we need runtime objects
available.
"""

class ThirdpartyMetaclass(type):

    def __new__(metacls, *args, **kwargs):
        return super().__new__(metacls, *args)


class ThirdpartyBaseclass:

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
