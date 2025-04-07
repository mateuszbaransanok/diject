import diject as di


class Database:
    def __init__(self, uri: str) -> None:
        self.uri = uri


class Service:
    def __init__(self, db: Database) -> None:
        self.db = db


class MainContainer(di.Container):
    database = di.Singleton[Database](
        uri="db://production",
    )

    service = di.Transient[Service](
        db=database,
    )


@di.inject
def production_function(service: Service = MainContainer.service) -> str:
    return service.db.uri


@di.patch(MainContainer.database, return_value=Database(uri="db://test_patch"))
def patched_dec_test_function() -> str:
    return production_function()


def patched_ctx_test_function() -> str:
    with di.patch(MainContainer.database, return_value=Database(uri="db://test_patch")):
        return production_function()


print("  production   >", production_function())
print("  patch dec    >", patched_dec_test_function())
print("  production   >", production_function())
print("  patch ctx    >", patched_ctx_test_function())
print("  production   >", production_function())
