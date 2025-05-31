# src/shared/exceptions.py

class NotFoundException(Exception):
    def __init__(self, detail: str = "Resource not found"):
        self.detail = detail

class ConflictException(Exception):
    def __init__(self, detail: str = "Conflict occurred"):
        self.detail = detail

class ForbiddenException(Exception):
    def __init__(self, detail: str = "Not authorized to perform this action"):
        self.detail = detail

class BadRequestException(Exception):
    def __init__(self, detail: str = "Bad request"):
        self.detail = detail