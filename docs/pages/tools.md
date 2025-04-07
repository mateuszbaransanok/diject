# Tools

## Partial

When creating multiple objects with common parameters, you can extract shared arguments into a
`di.Partial` object.

```python
from dataclasses import dataclass
import di


@dataclass
class User:
    firstname: str
    lastname: str
    company: str
    company_address: str


# Define a partial configuration with shared attributes
user_partial = di.Partial[User](
    company="Company",
    company_address="123 Main St",
)

# Create instances with specific values
user_x = di.Transient[user_partial](
    firstname="John",
    lastname="Doe",
)

user_y = di.Transient[user_partial](
    firstname="Jane",
    lastname="Smith",
)
```

## Testing

### Mocking Dependencies

You can mock dependencies in a test context:

```python
with di.patch(MainContainer.database, return_value=Database(uri="db://test_patch")):
    print(di.provide(MainContainer.service).db.uri)
```

Within this context, `Database` is replaced with a mocked object.

### Patching Dependencies

```python
@di.patch(MainContainer.database, return_value=Database(uri="db://test_patch"))
def patched_test_function() -> None:
    print(di.provide(MainContainer.service).db.uri)
```

Within this function, `Database` is replaced with a mocked object.


