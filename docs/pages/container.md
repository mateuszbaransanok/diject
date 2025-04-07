## **Container**

A `Container` groups related dependencies together, defining the
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

### Start

To start application and prepare Singleton provider:

```python
SomeContainer.start()
```


### Shutdown

To shurdown application and clear providers state:

```python
SomeContainer.shutdown()
```
