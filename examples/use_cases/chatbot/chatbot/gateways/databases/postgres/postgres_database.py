class PostgresDatabase:
    def __init__(self, url: str) -> None:
        self._url = url
        print("__init__", "PostgresDatabase")
