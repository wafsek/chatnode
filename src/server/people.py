class Person:
    """A Person class"""

    def __init__(self, email, password):
        self.email = email
        self.password = password

    @property
    def fullname(self):
        return '{}'.format(self.email)
