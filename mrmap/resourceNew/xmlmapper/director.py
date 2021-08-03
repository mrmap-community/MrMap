from resourceNew.xmlmapper.builder import WmsServiceBuilder


class WmsServiceDirector:
    """
    The Director is only responsible for executing the building steps in a
    particular sequence. It is helpful when producing products according to a
    specific order or configuration. Strictly speaking, the Director class is
    optional, since the client can control builders directly.
    """

    def __init__(self) -> None:
        self._builder = None

    @property
    def builder(self) -> WmsServiceBuilder:
        return self._builder

    @builder.setter
    def builder(self, builder: WmsServiceBuilder) -> None:
        """
        The Director works with any builder instance that the client code passes
        to it. This way, the client code may alter the final type of the newly
        assembled product.
        """
        self._builder = builder

    """
    The Director can construct several product variations using the same
    building steps.
    """

    def build_db_service(self) -> None:
        self.builder.produce_service()
        self.builder.produce_service_metadata()
        self.builder.produce_layer_tree()
        self.builder.produce_layer_metadata()
