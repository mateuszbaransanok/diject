## Providers

Providers in `diject` define how classes and functions are created and managed.
They offer fine-grained control over the lifecycle of objects,
ensuring efficient and flexible dependency injection.

### **Container**

A `Container` is a special provider that groups related dependencies together, defining the
configuration for an entire project. Containers allow for structured dependency management and
automatic resolution.

```python
class MainContainer(di.Container):
    database = di.Singleton[Database](
        uri=os.getenv("DATABASE_URI")
    )

    service = di.Transient[Service](
        db=database
    )
```

```python
assert isinstance(MainContainer.database, SingletonProvider)
assert isinstance(MainContainer.service, TransientProvider)
```

However, `mypy` still assumes that `MainContainer.database` is a `Database` instance and
`MainContainer.service` is a `Service` instance. The same applies to the created container.

### Injecting Dependencies

You can provide a single provider from the container:

```python
with di.inject():
    assert isinstance(MainContainer.database, Database)
    assert isinstance(MainContainer.service, Service)
```

Or provide the whole container:

```python
@di.inject
def main() -> None:
    assert isinstance(MainContainer.database, Database)
    assert isinstance(MainContainer.service, Service)
```

Accessing attributes from a provided container re-invokes the provider each time. For `Transient`
providers, this means a new instance is created on every access.

```python
assert isinstance(di.inject(MainContainer.database), Database)
assert isinstance(di.inject(MainContainer.service), Service)
```

### Traversing Providers

To traverse defined providers in a container:

```python
for name, provider in SomeContainer.traverse():
    pass
```

To reference a provider object instead of its instance:

```python
di.Provide[SomeContainer.some_class].provider
```

### **Transient**

A `Transient` provider creates a new instance every time it is requested. This is useful for
short-lived dependencies that do not need to be reused.

```python
transient_provider = di.Transient[SomeClass](arg="some_value")
```

### **Singleton**

A `Singleton` provider ensures that only one instance of the dependency is created and reused
throughout the application’s lifecycle.

```python
singleton_provider = di.Singleton[SomeClass](arg="some_value")
```

To reset a singleton instance:

```python
di.Provide[singleton_provider].reset()
```

### **Resource**

A `Resource` provider is similar to a singleton but is eagerly instantiated and shared for the
entire application runtime. It must be explicitly started and shutdown.

```python
resource_provider = di.Resource[SomeClass](arg="some_value")
```

To start and shutdown the resource:

```python
di.Provide[resource_provider].start()
di.Provide[resource_provider].shutdown()
```

### **Scoped**

A `Scoped` provider maintains a single instance within a specific scope, such as a request or
session.

```python
scoped_provider = di.Scoped[SomeClass](arg="some_value")
```

Usage:

```python
@di.inject
def some_function(instance: SomeClass = scoped_provider):
    pass
```

Or with a context manager:

```python
with di.Provide[scoped_provider] as instance:
    pass
```

### **Thread**

A `Thread` provider creates a separate instance for each thread, ensuring thread-local storage.

```python
thread_provider = di.Thread[SomeClass](arg="some_value")
```

### **Object**

An `Object` provider holds a constant value that is injected when needed.

```python
constant_provider = di.Object("fixed_value")
```

### **Selector**

A `Selector` provider allows conditional dependency injection based on runtime values, such as
environment variables.

```python
repository = di.Selector[os.getenv("DATABASE")](
    in_memory=di.Transient[InMemoryRepository](),
    mysql=di.Transient[MySqlRepository]()
)
```

## Accessing Providers

You can access a provider directly:

```python
instance = di.Provide[singleton_provider]()
```

For async access:

```python
instance = await di.Provide[singleton_provider]
```

Or use scoped access:

```python
with di.Provide[singleton_provider] as instance:
    pass
```

For asynchronous providers:

```python
async with di.Provide[singleton_provider] as instance:
    pass
```

## Injecting Dependencies

```python
@di.inject
def function(instance: SomeClass = MainContainer.service):
    pass
```

```python
@di.inject
def function(instance: Annotated[SomeClass, MainContainer.service]):
    pass
```

## Provider Status

You can check the status of a provider to determine whether it has started, stopped, or encountered
an error:

```python
di.Provide[resource_provider].status
```

## Registering Providers

Providers can be registered to enable automatic dependency resolution:

```python
di.Provider[SomeClass].register()
```

This allows dependencies to be injected automatically:

```python
@di.inject
def function(instance: SomeClass):
    pass
```

```python
@di.inject
def function(instance: Annotated[SomeClass, "MainContainer.service"]):
    pass
```

```python
@di.inject
def function(instance: Annotated[SomeClass, "service"]):
    pass
```

By defining providers effectively, you can streamline dependency injection in your application.

## Using `di.Partial`

When creating multiple objects with common parameters, you can extract shared arguments into a
`di.Partial` object.

```python
from dataclasses import dataclass
import di


@dataclass
class Config:
    firstname: str
    lastname: str
    company: str
    company_address: str


# Define a partial configuration with shared attributes
config_partial = di.Partial[Config](
    company="Company",
    company_address="123 Main St",
)

# Create instances with specific values
user_x = di.Transient[config_partial](
    firstname="John",
    lastname="Doe",
)

user_y = di.Transient[config_partial](
    firstname="Jane",
    lastname="Smith",
)
```

## Testing

### Mocking Dependencies

You can mock dependencies in a test context:

```python
with di.Mock[MainContainer.database](return_value=Database(uri="db://test_mock")):
    print(di.Provide[MainContainer.service]().db.uri)
```

Within this context, `Database` is replaced with a mocked object.

### Patching Dependencies

```python
@di.patch(MainContainer.database, return_value=Database(uri="db://test_patch"))
def patched_test_function() -> None:
    print(di.Provide[MainContainer.service]().db.uri)
```

Within this function, `Database` is replaced with a mocked object.


