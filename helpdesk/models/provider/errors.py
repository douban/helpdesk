class ProviderError(Exception):
    def __init__(self, error, tb="", description="provider error"):
        self.description = description
        self.error = error
        self.tb = tb

    def __str__(self):
        return "[{message}] {description}".format(**self.to_dict())

    __repr__ = __str__

    def to_dict(self):
        return {"description": self.description, "message": str(self.error)}


class ResolvePackageError(ProviderError):
    pass


class InitProviderError(ProviderError):
    pass
