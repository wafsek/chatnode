class Message:
    """A Message class"""

    def __init__(self, from_email, to_email, message):
        self.from_email = from_email
        self.to_email = to_email
        self.message = message

    @property
    def info(self):
        return '{}{}'.format((self.from_email, self.to_email, self.message))
