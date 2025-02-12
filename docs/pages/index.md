# Diject documentation

**Diject** is an open-source Python framework that provides a consistent structure and set of
conventions for configuring your application in the **dependency injection** pattern.
It supports lifecycle management of classes and functions, allowing control over the creation of new
objects and their deletion.

### What is dependency injection?

Dependency injection is a design pattern that decouples the creation of
an object's dependencies from the object itself. Instead of hard-coding dependencies,
they are provided from the outside.
This approach aligns with the dependency inversion principle, which states that high-level modules
should not depend on low-level modules. Both should rely on abstractions rather than concrete
implementations.

### Why use dependency injection in Python?

Even though Python is a dynamically-typed language with flexible object construction,
dependency injection brings significant benefits:

* **Better structure**: By explicitly declaring dependencies, the code becomes self-documenting and
  easier to understand.
* **Simplified testing**: Dependencies can be replaced with mocks effortlessly, reducing the
  overhead of setting up tests.
* **Enhanced maintainability**: Changes to the implementation of a dependency do not ripple through
  the codebase as long as the interface remains consistent.

### What is diject for?

**Diject** simplifies the process of configuring and setting object dependencies.
The framework allows you to:

* Define your classes with explicit dependencies in the constructor.
* Configure a container where you specify lifecycle each dependency that be provided.
* Use decorators to automatically inject dependencies into functions or class
  methods.

By centralizing the configuration in a container, diject enables consistent dependency management
across your application.

## Basic example

A typical Python application without dependency injection directly instantiates its dependencies:

```python
import os


class Database:
    def __init__(self) -> None:
        self.uri = os.getenv("DATABASE_URI")  # <-- dependency


class Service:
    def __init__(self) -> None:
        self.db = Database()  # <-- dependency
        
    def get_users(self) -> list[str]:
        return ["John", "Adam"] 


def main() -> None:
    service = Service()  # <-- dependency
    users = service.get_users()
    # some logic here...
    ...


if __name__ == "__main__":
    main()
```

This implementation is short and quick to set up, making it easy to get started. However, as the
application grows, **maintaining it becomes difficult** because dependencies are tightly coupled.
The `Service` class directly depends on the `Database` class, meaning any change to `Database`
requires modifying `Service`. This not only makes it hard to replace or extend functionality but
also **mixes configuration with business logic**, reducing flexibility. As a result, introducing new
features or refactoring existing ones becomes cumbersome, requiring changes across multiple parts
of the code.

### Dependency injection pattern

In a dependency Injection pattern, dependencies are passed into objects rather than being created
inside them:

```python
import os


class Database:
    def __init__(self, uri: str) -> None:  # <-- dependency is injected
        self.uri = uri


class Service:
    def __init__(self, db: Database) -> None:  # <-- dependency is injected
        self.db = db
        
    def get_users(self) -> list[str]:
        return ["John", "Adam"] 


def main(service: Service) -> None:  # <-- dependency is injected
    users = service.get_users()
    # some logic here...
    ...


if __name__ == "__main__":
    database = Database(  # <-- create global database instance
        uri=os.getenv("DATABASE_URI"),
    )

    service = Service(
        db=database,
    )

    main(
        service=service,  # <-- injecting dependency
    )
```

By passing dependencies as arguments, the relationships between classes are weakened, **making the
system more flexible**. This approach allows dependencies, such as the database, to be easily
swapped out with another implementation or a mock for testing. The separation of concerns improves
testability, maintainability, and modularity.
However, **managing dependencies manually without a library can become tedious as your application
grows**. This approach also lacks proper lifecycle management, meaning there is no automatic way to
control the creation, reuse, or disposal of objects. Developers must manually handle tasks like
reusing instances where necessary or closing database connections, which increases the risk of
resource leaks and inefficient memory usage, **ultimately making the application harder to scale**.

### Using **diject**

With **diject**, dependency management becomes even more streamlined by using a container for
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
        
    def get_users(self) -> list[str]:
        return ["John", "Adam"] 


class MainContainer(di.Container):  # <-- container for configuration
    database = di.Singleton[Database](  # <-- creates one instance for the entire application
        uri=os.getenv("DATABASE_URI"),
    )

    service = di.Transient[Service](  # <-- creates a new instance for each call
        db=database,  # <-- injecting the same database instance into each service
    )


@di.inject
def main() -> None:
    users = MainContainer.service.get_users()  # <-- injecting dependency
    # some logic here...
    ...


if __name__ == "__main__":
    main()
```

This example demonstrates how **diject** simplifies dependency management in Python applications by
centralizing configuration. Instead of manually instantiating and passing dependencies, a
`MainContainer` defines all dependencies in one place.

- **Providers:** The container ensures that the `Database` class is a singleton, meaning
  the same instance is shared across the application, while `Service` is transient, meaning a new
  instance is created for each call.
- **Automatic Injection:** The `@di.inject` decorator allows dependencies to be injected
  automatically into functions, eliminating the need for explicit wiring.

**Diject** significantly improves maintainability and consistency,
especially in larger applications. It removes the burden of manually managing dependencies, reduces
boilerplate code, and ensures that configurations are centralized. This leads to a cleaner, more
scalable, and testable architecture.
