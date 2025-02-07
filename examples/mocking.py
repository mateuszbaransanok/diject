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

    service = di.Factory[Service](
        db=database,
    )


@di.patch(MainContainer.database, return_value=Database(uri="db://test_patch"))
def patched_test_function() -> str:
    return di.Provide[MainContainer.service]().db.uri


print("START".center(50, "="))
print("  before       >", di.Provide[MainContainer.service]().db.uri)
print("  patch        >", patched_test_function())
print("  after patch  >", di.Provide[MainContainer.service]().db.uri)

with di.Mock[MainContainer.database](return_value=Database(uri="db://test_mock")):
    print("  mock         >", di.Provide[MainContainer.service]().db.uri)

print("  after mock   >", di.Provide[MainContainer.service]().db.uri)
print("END".center(50, "="))
