# Get started

**Diject** is a framework that provides a consistent structure and set of conventions for configuring
dependencies. It supports lifecycle management for classes and functions, allowing you to create
objects on demand. In addition, diject offers a variety of instantiation strategies to suit your
application's needs:

* **New Instance Per Call**: A fresh object is created every time it’s requested.
* **Shared Singleton**: A single, shared instance is maintained across the application, with support for
  both lazy and eager initialization.
* **Thread-Specific Instance**: An instance unique to each thread is provided.
* **Request-Scoped Instance**: An object that exists only within the lifecycle of a specific request.

Furthermore, diject lets you choose which class to instantiate based on conditions (for example, an
environment variable), so you can inject the appropriate implementation into your high-level
abstractions. Containers help you organize your entire configuration into a logical, coherent
structure.

---

## Concept

When using an object-creating provider (e.g. `di.Factory`), you first supply the function or class
that should be provided. For example:

```python
di.Factory[SomeClass]
```

This returns an instance of a `FactoryProvider` with the signature of `SomeClass`, which aids static
type checking (using tools like mypy) by catching errors early and enhancing configuration with IDE
auto-completion.

Next, you create a provider instance:

```python
some_class = di.Factory[SomeClass](arg="some_arg")
```

This returns a `FactoryProvider` that *pretends* to be an instance of `SomeClass`. Thanks to this
design, you can inject this provider into other providers, for example:

```python
another_class = di.Factory[AnotherClass](some_class=some_class)
```

Static type checking will work seamlessly with this approach.

To obtain an instance along with all its dependencies, call:

```python
another_class_instance = di.Provide[another_class]()
```

Similarly, you can expose dependency-related helper functions with:

```python
another_class_dependency = di.Provide[another_class]
```

which provides methods to interact with the provider's internals.

### Containers

Containers define the configuration for an entire project by grouping related dependencies. They are
created by subclassing `di.Container`:

```python
class SomeContainer(di.Container):
    some_class = di.Factory[SomeClass](arg="some_arg")
    another_class = di.Factory[AnotherClass](some_class=some_class)
```

You can provide a single provider:

```python
another_class_instance = di.Provide[SomeContainer.another_class]()
```

or the whole container:

```python
some_container = di.Provide[SomeContainer]()
```

When you access attributes from a provided container (e.g., `some_container.another_class`), the
provider is re-invoked each time. For a `FactoryProvider`, this means a new instance of
`AnotherClass` is created on every access.

When defining objects in a container or as function arguments, note that:

```python
class MainContainer(di.Container):
    val = 1
    assert isinstance(val, int)


assert isinstance(MainContainer.val, ObjectProvider)
```

– inside the container body, `some_number` remains an `int`, but outside the body, objects defined
in the container are automatically converted into `ObjectProvider`s. Collections like lists, tuples,
sets, and dicts are also converted (recursively scanning for nested providers). To avoid this,
explicitly wrap your object with `di.Object`, for example:

```python
di.Object([1, 2, 3])
```

You can traverse defined providers using:

```python
for name, provider in di.Provide[SomeContainer].traverse():
    # Process each provider
    pass
```

You can also filter the traversal by specific provider types, include only public providers (those
whose names do not start with `_`), or restrict to providers selected by a `SelectorProvider`.

Finally, if you need to reference the provider object itself (rather than the provided instance),
use:

```python
di.Provide[some_class].provider
```

Keep in mind that for static typing, `some_class` is treated as an instance of `SomeClass`, not as a
provider.

---

## Providers

diject gives you fine-grained control over the lifecycle of your objects. Consider the following
example functions:

```python
def some_function(arg: str) -> str:
    # Some logic here...
    return "some_output"


def some_iterator(arg: str) -> Iterator[str]:
    # Preparation logic here...
    yield "some_output"
    # Cleanup logic here...
```

### Creators

Creators are responsible for creating new instances whenever a dependency is requested.

#### Factory

A **Factory** creates a new instance on every request:

```python
some_factory = di.Factory[some_function](arg="some_value")
```

---

### Services

Services manage dependencies that require an explicit setup phase (before use) and a cleanup phase (
after use). They work well with generators, as well as functions and classes.

#### Singleton

A **Singleton** is lazily instantiated and then shared throughout the application's lifetime:

```python
some_singleton = di.Singleton[some_iterator](arg="some_value")
```

To clear the singleton’s state, call:

```python
di.Provide[some_singleton].reset()
```

#### Resource

A **Resource** is eagerly instantiated and shared for the application's lifetime:

```python
some_resource = di.Resource[some_iterator](arg="some_value")
```

Before using the resource, start it:

```python
di.Provide[some_resource].start()
```

When shutting down your application, clean up the resource (along with its dependencies) using:

```python
di.Provide[some_resource].shutdown()
```

#### Scoped

A **Scoped** provider behaves like a singleton within a specific scope. The same instance is reused
within that scope:

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

Or use a context manager:

```python
with di.Provide[scoped_provider] as some_instance:
    # Use some_instance within this block
    pass
```

#### Transient

A **Transient** dependency creates a new instance every time it is requested—behaving similarly to a
factory:

```python
transient_provider = di.Transient[some_iterator](arg="some_value")
```

#### Thread

A **Thread** dependency creates and maintains a separate instance for each thread, much like a
singleton but per thread:

```python
thread_provider = di.Thread[some_iterator](arg="some_value")
```

---

### Object

An **Object** holds a constant value that is injected on demand. Instances defined in containers or
as function arguments are automatically wrapped by an `ObjectProvider`.

---

### Selector

Selectors allow you to include conditional logic—similar to an if statement—to configure your
application for different variants. For example, you can choose a repository implementation based on
an environment variable:

```python
repository = di.Selector[os.getenv("DATABASE")](
    in_memory=di.Factory[InMemoryRepository](),
    mysql=di.Factory[MySqlRepository](),
)
```

Alternatively, you can group multiple selectors sharing the same selection variable:

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

---

## Container

Containers group related dependencies together. Define a container by subclassing `di.Container`:

```python
class MainContainer(di.Container):
    service = di.Factory[Service]()
```

You can inject an entire container so that its attributes are automatically provided within the same
scope:

```python
with di.Provide[MainContainer] as container:
    service = container.service  # The service instance is provided by the container
    # Use the service within this block
    pass
```

---

## Attributes & Callables

Providers mimic the objects they create. This means you can access attributes or call them directly,
with the actual object being instantiated lazily when needed:

```python
factory = di.Factory[SomeClass]()

# Access an attribute (or call a method) on the provided instance:
some_value = di.Provide[factory.get_value()]()
```

---

### Status

Each resource exposes a status that indicates whether it has started, stopped, or encountered an
error during startup. For example:

```python
di.Provide[some_resource].status
```

The key status operations are:

- **Start**: Initializes the resource. **Call this before using the resource.**
- **Reset**: Clears the current state of a singleton, forcing reinitialization upon the next
  request.
- **Shutdown**: Cleans up the resource and its dependencies.

---

### Provide

There are several ways to resolve (or "provide") dependencies:

- **Synchronous (without scope):**
  ```python
  some_value = di.Provide[some_provider]()
  ```
- **Asynchronous (without scope):**
  ```python
  some_value = await di.Provide[some_provider]
  ```
- **Synchronous (with scope):**
  ```python
  with di.Provide[some_provider] as some_value:
      pass
  ```
- **Asynchronous (with scope):**
  ```python
  async with di.Provide[some_provider] as some_value:
      pass
  ```

In addition to explicit provisioning, you can inject dependencies directly into functions:

```python
@di.inject
def function(some_value: Any = some_provider):
    pass
```

Implicit injection is also supported when you register a provider:

```python
di.Provider[some_class].register()
```

Then:

```python
@di.inject
def function(some_class: SomeClass):
    pass
```

The `register` method traverses the class hierarchy (MRO) to find a matching provider. If no
provider is found—or if more than one provider is registered for the same class—the dependency will
not be injected automatically. In such cases, you must either provide it manually when calling the
function or use an alias via the annotation `typing.Annotated[SomeClass, "alias"]`.

---

This improved documentation should help you get started with diject and understand its various
components and usage patterns. Happy coding!