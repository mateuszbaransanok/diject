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

    service = di.Transient[Service](  # <-- creates new instance for each call
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

### Transient

A **Transient** creates a new instance on every request.

```python
some_transient = di.Transient[some_function](arg="some_value")
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
di.shutdown(some_singleton)
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
def func(some_instance: str = scoped_provider):
    # Use some_instance within this function
    pass
```

Or by using a context manager:

```python
with di.inject():
    some_instance = di.provide(scoped_provider)
    # Use some_instance within this block
```

### Transient

A **Transient** dependency is similar to a scoped dependency but creates a new instance every time
it is requested—behaving like a transient.

```python
transient_provider = di.Transient[some_iterator](arg="some_value")
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
    in_memory=di.Transient[InMemoryRepository](),
    mysql=di.Transient[MySqlRepository](),
)
```

You can also use a grouped approach if multiple selectors share the same selection variable:

```python
with di.Selector[os.getenv("DATABASE")] as Selector:
    user_repository = Selector[UserRepository]()
    book_repository = Selector[BookRepository]()

with Selector == "in_memory" as Option:
    Option[user_repository] = di.Transient[InMemoryUserRepository]()
    Option[book_repository] = di.Transient[InMemoryBookRepository]()

with Selector == "mysql" as Option:
    Option[user_repository] = di.Transient[MySqlUserRepository]()
    Option[book_repository] = di.Transient[MySqlBookRepository]()
```

## Container

Containers group related dependencies together. They are defined by subclassing di.Container:

```python
class MainContainer(di.Container):
    service = di.Transient[Service]()
```


### Traversal

The Travers functionality allows you to iterate over all providers. Its parameters include:

* **types**: Filter by specific provider types.
* **recursive**: Traverse providers recursively.
* **only_public**: Include only public providers.
* **only_selected**: Include only providers that have been selected.

```python
for name, provider in MainContainer.travers():
    pass
```

### Status

You can retrieve the status of a Resource to determine whether it has started, stopped,
or if an error occurred during startup:

```python
di.status(some_resource)
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
