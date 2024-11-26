class LayerNotQueryable(Exception):
    """Raised when the layer is not queryable"""
    pass


class OperationNotSupported(Exception):
    """Raised when the service does not support the operation"""
    pass


class NoContent(Exception):
    """Raised when remote metadata is empty"""
    pass
