# Interfaces

Interfaces are used to **extend the functionality of providers** and enable execute operations on
them. They define specific behaviors that providers can implement, allowing for better control and
lifecycle management.

The following interfaces define different behaviors for dependency providers:

- **`StartProvider`** – Ensures providers can be started when needed.
- **`ResetProvider`** – Enables resetting a provider’s internal state.
- **`ContextProvider`** – Manages resource cleanup at the end of a scope.
- **`StatusProvider`** – Allows checking the current status of a provider.

Each interface has **synchronous (`sync`) and asynchronous (`async`) counterparts**, providing
flexibility in different execution models.

---

## Start Interface

The `StartProvider` ensures that providers can be **started at the appropriate time**, making sure
that all required dependencies are properly initialized before use. This is especially useful for
managing providers that require **explicit setup**, such as **database connections, background
tasks, or network clients**.

### How It Works

- The **start process is recursive**—it traverses all involved providers and checks if they require
  initialization.
- If a provider needs to be started, it is initialized **along with all its dependencies** before
  being provided.

### Usage

#### Starting a Provider

```python
resource = di.Resource[int]("1")

# Start a provider synchronously
di.Provide[resource].start()

# Start a provider asynchronously
await di.Provide[resource].astart()
```

#### When to Use

- Use `start()` or `astart()` when a provider **requires explicit initialization** before being
  used.
- Works well for **resource-heavy** providers such as **database clients, connection pools, and
  worker threads**.
- Ensures that **all dependencies** required by the provider are **recursively resolved and started
  **.

By enforcing **structured initialization**, the `StartProvider` helps maintain **predictable,
well-managed dependency lifecycles**, improving application stability and resource efficiency.

---

## Reset Interface

The `ResetProvider` enables resetting the **state** of a provider, allowing it to be
**reinitialized** when necessary. This is useful in scenarios where providers maintain internal
state that needs to be cleared and refreshed, such as
**database connections, caches, or configuration-loaded services**.

### How It Works

- **`reset()`** / **`areset()`** – Clears the internal state of a provider without affecting its
  dependencies.
- **`shutdown()`** / **`ashutdown()`** – Recursively resets the provider and all its dependent
  providers, ensuring a complete teardown.

### Usage

```python
singleton = di.Singleton[int]("1")

# Reset a provider synchronously
di.Provide[singleton].reset()

# Reset a provider asynchronously
await di.Provide[singleton].areset()

# Reset all dependent providers recursively (synchronous)
di.Provide[some_provider].shutdown()

# Reset all dependent providers recursively (asynchronous)
await di.Provide[some_provider].ashutdown()
```

- Use **`reset()`** when you need to clear the provider’s state but don’t need to stop its
  dependencies.
- Use **`shutdown()`** when you need to fully reset a provider and all its dependencies.

#### When to Use

This mechanism ensures that providers remain **flexible, reusable, and maintainable**, especially in
long-running applications where state consistency is critical.

---

## Scope Interface

The `ContextProvider` ensures that resources are **properly managed and released** at the end of their
lifecycle. This is essential for managing **temporary objects, database transactions, file handles,
and other resources** that should not persist beyond their intended scope.

### How It Works

All data associated with a **scope** is stored in a dedicated `Scope` instance. This ensures that
scoped resources are **properly tracked** and **automatically cleaned up** when the scope exits.

### Usage

#### Manually Entering and Exiting a Scope

A provider can be **used within a scope**, ensuring that it is correctly managed during its
lifecycle:

```python
scoped = di.Scoped[int]("1")

# Enter scope synchronously
with di.Provide[scoped] as instance:
    # The scoped instance is available within this block
    pass

# Enter scope asynchronously
async with di.Provide[scoped] as instance:
    # The scoped instance is available within this block
    pass
```

When the **context (`with` or `async with`) exits**, the `ContextProvider` ensures that any cleanup
logic is executed, releasing resources as needed.

#### Using Scope in Injected Functions

A scope is also automatically **created inside injected functions**, ensuring that scoped resources
are available during the function execution:

```python
@di.inject
def function(instance: int = scoped) -> None:
    # The scoped instance is available while the function executes
    pass
```

### When to Use

- Use **scoped providers** when a resource should only exist **for a specific duration** (e.g., per
  request in a web framework, per transaction in a database).
- Scoping **automatically manages resource cleanup**, preventing leaks and unintended persistence of
  temporary objects.
- Works seamlessly with **dependency injection**, ensuring that dependencies are only active within
  their intended lifecycle.

By leveraging the `ContextProvider`, dependency injection becomes **more efficient, predictable, and
memory-safe**, making it ideal for managing **short-lived resources** in complex applications.

---

## Status Interface

The `StatusProvider` allows checking the **current status** of a provider. Providers that maintain
an internal state should implement this interface to indicate whether they are **active, stopped, or
have encountered an error**. This is particularly useful for **tracking provider lifecycle states**
in complex dependency injection setups.

### Usage

```python
# Check the status of a provider
di.Provide[some_provider].status()
```

### Possible Statuses

- **`STARTED`** – The provider is **active and running**.
- **`STOPPED`** – The provider has been **stopped** and is no longer active.
- **`ERROR`** – The provider **encountered an error** and may require intervention.

### When to Use

- Monitor the **availability and health** of providers.
- Ensure a provider is **running before usage** to prevent unexpected failures.
- Debug provider issues by checking if they are in an **error state**.

By implementing `StatusProvider`, applications gain **better observability and control** over
provider states, improving **reliability and maintainability** in dependency injection systems.

---

## Summary

Interfaces in dependency injection systems are designed to **extend the functionality** of providers
and offer **better control and management** over their lifecycle. By implementing these interfaces,
providers can perform specific behaviors such as initialization, state resetting, resource cleanup,
and status monitoring, leading to **greater flexibility and efficiency** in dependency management.

The **StartProvider** ensures that providers can be **initialized** at the appropriate time,
allowing their dependencies to be properly set up before use. This is especially helpful for
resource-intensive providers that require explicit startup, like database connections or background
tasks.

The **ResetProvider** allows providers to **reset their internal state**, enabling them to be
reinitialized when necessary. This is useful in cases where a provider manages mutable state that
may need to be cleared and refreshed, such as caches or connection pools.

The **ContextProvider** provides mechanisms for managing resources **within a defined scope**,
ensuring proper cleanup when the scope ends. This is essential for managing temporary resources that
should not persist beyond their intended lifespan, such as transaction contexts or request-specific
data.

Finally, the **StatusProvider** allows you to **monitor the status** of a provider, checking if it
is **active, stopped, or in an error state**. This ensures better visibility and control over the
provider's lifecycle, helping to maintain the health of the application and troubleshoot issues more
effectively.

Together, these interfaces form a powerful toolkit for managing dependency lifecycles, ensuring that
resources are properly initialized, cleaned up, and monitored, thus improving the **stability,
maintainability, and performance** of your application.
