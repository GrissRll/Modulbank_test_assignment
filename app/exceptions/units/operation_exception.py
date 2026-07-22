class OperationExistingError(Exception):
    pass


class OperationNotFoundError(Exception):
    pass


class OperationStatusError(Exception):
    def __init__(self, status: str, reason: str):
        self.status = status
        self.reason = reason
        super().__init__(f"Status:{self.status}. Wrong status for this action.")


class OperationSubmitConflict(Exception):
    pass
