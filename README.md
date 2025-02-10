# diject

A powerful dependency injection framework that automatically injects objects,
promoting loose coupling, improving testability,
and centralizing configuration for easier maintenance.

## What is dependency injection?

Dependency Injection (DI) is a design pattern that decouples the creation of
an object's dependencies from the object itself. Instead of hard-coding dependencies,
they are provided ("injected") from the outside.

## Why Use Dependency Injection in Python?

Even though Python is a dynamically-typed language with flexible object construction, DI brings
significant benefits:

* **Better Structure**: By explicitly declaring dependencies, the code becomes self-documenting and
  easier to understand.
* **Simplified Testing**: Dependencies can be replaced with mocks effortlessly, reducing the
  overhead of setting up tests.
* **Enhanced Maintainability**: Changes to the implementation of a dependency do not ripple through
  the codebase as long as the interface remains consistent.

## How to use diject?

**diject** simplifies the process of configuring and setting object dependencies.
The framework allows you to:

* Define your classes with explicit dependencies in the constructor.
* Configure a container where you specify how each dependency should be provided (as singletons,
  factories, etc.).
* Use decorators (e.g., @di.inject) to automatically inject dependencies into functions or class
  methods.

By centralizing the configuration in a container, diject enables consistent dependency management
across your application.

## Examples

### Basic Example

A typical Python application without dependency injection might instantiate dependencies directly:

```python
import os


class Database:
    def __init__(self) -> None:
        self.uri = os.getenv("DATABASE_URI")  # <-- dependency


class Service:
    def __init__(self) -> None:
        self.db = Database()  # <-- dependency


def main() -> None:
    service = Service()  # <-- dependency
    # some logic here...
    ...


if __name__ == "__main__":
    main()
```

### Dependency Injection Pattern

In a DI pattern, dependencies are passed into objects rather than being created inside them:

```python
import os


class Database:
    def __init__(self, uri: str) -> None:  # <-- dependency is injected
        self.uri = uri


class Service:
    def __init__(self, db: Database) -> None:  # <-- dependency is injected
        self.db = db


DATABASE = Database(  # <-- create global database instance
    uri=os.getenv("DATABASE_URI"),
)


def create_service() -> Service:  # <-- creates new instance for each call
    return Service(
        db=DATABASE,
    )


def main(service: Service) -> None:  # <-- dependency is injected
    # some logic here...
    ...


if __name__ == "__main__":
    main(
        service=create_service(),  # <-- injecting dependency
    )
```

### Using diject

With diject, you can simplify dependency management further by declaring a container for your
configurations:

```python
import os
import diject as di


class Database:
    def __init__(self, uri: str) -> None:  # <-- dependency is injected
        self.uri = uri


class Service:
    def __init__(self, db: Database) -> None:  # <-- dependency is injected
        self.db = db


class MainContainer(di.Container):  # <-- container for configuration
    database = di.Singleton[Database](  # <-- creates one instance for entire application
        uri=os.getenv("DATABASE_URI"),
    )

    service = di.Factory[Service](  # <-- creates new instance for each call
        db=database,  # <-- injecting always the same database instance
    )


@di.inject
def main(service: Service = MainContainer.service) -> None:  # <-- injecting dependency by default
    # some logic here...
    ...


if __name__ == "__main__":
    main()  # <-- service is injected automatically
```

# Key Concepts and Features

* **Sync & Async Support**: Seamlessly manage both synchronous and asynchronous dependencies.
* **Pure Python Implementation**: No need for external dependencies or language modifications.
* **Performance**: Low overhead with efficient dependency resolution.
* **Clear Debugging**: Built-in logging and debugging aids help trace dependency injection flow.
* **Type Safety**: Full MyPy and type annotation support ensures robust static analysis.
* **Easy Testing**: Simplified testing with native support for mocks and patches.
* **Integration**: Easily integrate with other frameworks and libraries.
* **Inheritance and Protocols**: Use Python's protocols to enforce contracts and ensure consistency
  across implementations.

# Installation

```shell
pip install diject
```

# Providers

diject gives you fine-grained control over the lifecycle of your objects.
Consider the following example functions:

```python
def some_function(arg: str) -> str:
    # some logic here...
    return "some_output"


def some_iterator(arg: str) -> Iterator[str]:
    # some preparation logic here...
    yield "some_output"
    # some clean up logic here...
```

## Creators

Creators are responsible for creating new instances whenever a dependency is requested.

### Factory

A **Factory** creates a new instance on every request.

```python
some_factory = di.Factory[some_function](arg="some_value")
```

## Services

Services manage dependencies that require a setup phase (before use) and a cleanup phase (after
use). They are especially useful for dependencies defined as generators, but they also work
with functions and classes.

### Singleton

A **Singleton** is lazily instantiated and then shared throughout the application's lifetime.

```python
some_singleton = di.Singleton[some_iterator](arg="some_value")
```

To clear the singleton's state, call:

```python
di.Provide[some_singleton].reset()
```

### Resource

A **Resource** is eagerly instantiated and shared for the application's lifetime.

```python
some_resource = di.Resource[some_iterator](arg="some_value")
```

Start the resource before use:

```python
di.Provide[some_resource].start()
```

Shutdown the resource to perform cleanup with all dependencies:

```python
di.Provide[some_resource].shutdown()
```

### Scoped

A **Scoped** provider behaves like a singleton within a specific scope. Within that scope, the
same instance is reused.

```python
scoped_provider = di.Scoped[some_iterator](arg="some_value")
```

You can inject a scoped dependency using the `@di.inject` decorator:

```python
@di.inject
def func(some_instance: Any = scoped_provider):
    # Use some_instance within this function
    pass
```

Or by using a context manager:

```python
with di.Provide[scoped_provider] as some_instance:
    # Use some_instance within this block
    pass
```

### Transient

A **Transient** dependency is similar to a scoped dependency but creates a new instance every time
it is requested—behaving like a factory.

```python
transient_provider = di.Transient[some_iterator](arg="some_value")
```

### Thread

A **Thread** dependency is similar to a singleton, but it creates and maintains separate instances
for each thread.

```python
thread_provider = di.Thread[some_iterator](arg="some_value")
```

## Object

An Object holds a constant value that is injected on request.
Instances defined in containers or as function arguments are automatically wrapped
by an ObjectProvider.

## Selector

Selectors allow you to include conditional logic (like an if statement) to configure
your application for different variants.

For example, to choose a repository implementation based on an environment variable:

```python
repository = di.Selector[os.getenv("DATABASE")](
    in_memory=di.Factory[InMemoryRepository](),
    mysql=di.Factory[MySqlRepository](),
)
```

You can also use a grouped approach if multiple selectors share the same selection variable:

```python
with di.Selector[os.getenv("DATABASE")] as Selector:
    user_repository = Selector[UserRepository]()
    book_repository = Selector[BookRepository]()

with Selector == "in_memory" as Option:
    Option[user_repository] = di.Factory[InMemoryUserRepository]()
    Option[book_repository] = di.Factory[InMemoryBookRepository]()

with Selector == "mysql" as Option:
    Option[user_repository] = di.Factory[MySqlUserRepository]()
    Option[book_repository] = di.Factory[MySqlBookRepository]()
```

## Container

Containers group related dependencies together. They are defined by subclassing di.Container:

```python
class MainContainer(di.Container):
    service = di.Factory[Service]()
```

You can inject an entire container so that its attributes are automatically
provided within the same scope:

```python
with di.Provide[MainContainer] as container:
    service = container.service  # <-- container provide service object
    # Use some_instance within this block
    pass
```

## Attribute & Callable

Providers mimic the objects they create.
This means you can access attributes or call them directly,
and the actual object is instantiated lazily on request.

```python
factory = di.Factory[SomeClass]()

# Access an attribute (or call a method) on the provided instance:
some_value = di.Provide[factory.get_value()]()
```

# Providable

### Provide

Providers can be provided in five ways:
* as decorator
```python
@di.inject
def function(some_value: Any = some_provider):
    pass
```
* Sync without scope
```python
some_value = di.Provide[some_provider]()
```
* Async without scope
```python
some_value = await di.Provide[some_provider]
```
* Sync with scope
```python
with di.Provide[some_provider] as some_value:
    pass
```
* Async with scope
```python
async with di.Provide[some_provider] as some_value:
    pass
```

### Traversal

The Travers functionality allows you to iterate over all providers. Its parameters include:

* **types**: Filter by specific provider types.
* **recursive**: Traverse providers recursively.
* **only_public**: Include only public providers.
* **only_selected**: Include only providers that have been selected.

```python
for name, provider in di.Provide[some_resource].travers():
    pass
```

### Status

You can retrieve the status of a Resource to determine whether it has started, stopped,
or if an error occurred during startup:

```python
di.Provide[some_resource].status()
```

### Get provider

Retrieve the underlying provider instance.
This is primarily used to map a "pretender" type to its actual provider type:

```python
di.Provide[pretender].provider
```

# License

Distributed under the terms of the [MIT license](LICENSE),
**diject** is free and open source framework.

# Contribution

Contributions are always welcome! To ensure everything runs smoothly,
please run tests using `tox` before submitting your changes.
Your efforts help maintain the project's quality and drive continuous improvement.

# Issues

If you encounter any problems, please leave [issue](../../issues/new), along with a detailed
description.

---

*Happy coding with diject! Enjoy cleaner, more maintainable Python applications through effective
dependency injection.*
