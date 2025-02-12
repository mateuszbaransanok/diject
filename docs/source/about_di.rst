diject
======


# What is dependency injection?

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

.. codeblock::
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

### Dependency Injection Pattern

In a DI pattern, dependencies are passed into objects rather than being created inside them:

.. codeblock::
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

### Using diject

With diject, you can simplify dependency management further by declaring a container for your
configurations:

.. codeblock::
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


.. toctree::
   :maxdepth: 4

   diject
