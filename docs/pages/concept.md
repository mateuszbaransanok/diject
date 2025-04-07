# Concept

Let's assume we have a class implementing a database and a service:

```python
class Database:
    def __init__(self, uri: str) -> None:
        self.uri = uri


class Service:
    def __init__(self, db: Database) -> None:
        self.db = db
```

To create instances of these classes, simply call their constructors:

```python
database = Database(
    uri="db://production",
)

service = Service(
    db=database,
)
```

The above code creates a global variable holding the database instance.

## Introducing Diject

Diject allows you to define a lifecycle for the database instance:

```python
database_provider = di.Singleton[Database](
    uri="db://production",
)

service_provider = di.Transient[Service](
    db=database_provider,
)
```

When using an object-creating provider (e.g., `di.Singleton`), you first specify the function or
class to be provided:

```python
di.Singleton[Database]
```

This returns an instance of a `SingletonPretender` with the signature of `Database`. This approach
enhances static type checking (using tools like mypy) by catching errors early and improving IDE
auto-completion.

Next, create a provider instance:

```python
di.Singleton[Database](uri="db://production")
```

This returns a `SingletonProvider` that behaves like an instance of `Database`.

Arguments for pretenders can include both normal Python objects (e.g., `uri` of type `str`) and
providers (e.g., `database_provider` of type `SingletonProvider`). Since `database_provider`
pretends to be a `Database` instance, type checking remains valid.

Thanks to this design, you can inject this provider into other providers:

```python
di.Transient[Service](db=database)
```

Besides `Singleton`, Diject also supports other lifecycle scopes such as `Transient`, `Scoped`,
`Thread`, and `Resource`.

## Provider-Based Project Configuration

Configure your project based on providers but treat them as standard Python objects. You can access
attributes and call providers:

```python
service_provider = di.Transient[Service](db=database_provider.get_session())
```

## Automatic Conversion to Providers

Be cautious when using Python objects within a block. Upon exiting the block, they are automatically
converted into `ObjectProvider` for consistency. Similarly, lists, sets, tuples, and dictionaries
are converted into `TransientProvider`, ensuring that any providers inside them are also recognized
and supplied.

Once the block ends, further operations on these objects are not possible as they have been
transformed into Providers.

## Managing Providers

To provide dependency, use `di.provide`:

```python
database_dependency = di.provide[database_provider]
```

`database_dependency` is an instance of `Dependency`, enabling various operations on the given
provider.

