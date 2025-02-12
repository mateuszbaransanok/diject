# Get Started

Welcome to **diject**, a lightweight yet powerful dependency injection framework designed to
simplify and enhance dependency management in your Python applications. With diject, you can
create more maintainable, modular, and testable code by automatically managing the lifecycle and
relationships of objects in your system.

Whether you’re building a small script or a large-scale web application, diject can help
streamline your codebase, eliminate repetitive boilerplate, and facilitate smoother integration with
various frameworks.

### Key Features

* Automatic Dependency Injection – Inject dependencies effortlessly without manual wiring.
* Lifecycle Management – Control object creation strategies (Singleton, Transient, etc.).
* Minimal Boilerplate – Simplifies complex dependency graphs, reducing redundant code.
* Framework Agnostic – Works seamlessly with Flask, FastAPI, Django, or standalone applications.
* Centralized Configuration – Manage all dependencies in a structured way.

## Installation

Install **diject** via [PyPI](https://pypi.org/project/diject/):

```shell
pip install diject
```  

## Hexagonal architecture

Before integrating **diject** into your application, it's important to structure your project in a
way that promotes modularity and maintainability. One of the best approaches for this is using the
**hexagonal architecture** pattern, which helps separate business logic from infrastructure
concerns.

Hexagonal architecture, also known as **ports and adapters**, is a design pattern that structures
applications in a way that decouples core business logic from external dependencies such as
databases, APIs, and frameworks. This separation allows for greater flexibility, testability, and
maintainability.

A typical **diject**-powered project using Hexagonal Architecture might be structured as follows:

```
my_project/
│── src/
│   ├── core/           # Core business logic (entities, services)
│   ├── adapters/       # Implementations for core abstractions (repositories, LLM providers)
│   ├── gateways/       # Low-level connections (database, API clients)
│   ├── apps/           # Service layer (CLI application, REST API)
│   ├── containers/     # Dependency injection containers (project configuration)
│
│── data/               # Additional data files (configs, static assets)
│── tests/              # Unit and integration tests
```

With this architecture, **diject** allows you to register and inject dependencies at the
infrastructure level while keeping your business logic independent from specific implementations.

## Creating a `containers` Folder

To keep dependency management organized, create a `containers` folder inside your project. This
folder will store all **dependency injection containers**, which define how objects are instantiated
and provided throughout your application.

### Example: Defining a Dependency Container

Create a new file inside `containers/`, for example, `containers/main_container.py`:

```python
class MainContainer(di.Container):
    database = di.Singleton[Database](
        uri=os.getenv("DATABASE_URI")
    )

    service = di.Transient[Service](
        db=database
    )
```

### Explanation

- `Singleton[Database]`: Ensures a single database instance is shared throughout the application.
- `Transient[Service]`: Creates a new `Service` instance whenever it's requested, while
  always using the same `Database` instance.

Now, dependencies can be injected automatically into your application logic, reducing boilerplate
and improving maintainability.

---

Would you like me to add more sections, such as **Using Dependency Injection in Your Code**, 
**Testing with diject**, or **Advanced Configuration**?