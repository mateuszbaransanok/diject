# Providers

Providers in `diject` define how classes and functions are created and managed.
They offer fine-grained control over the lifecycle of objects,
ensuring efficient and flexible dependency injection.

## **Transient**

A `Transient` provider creates a new instance every time it is requested. This is useful for
short-lived dependencies that do not need to be reused.

```python
transient_provider = di.Transient[SomeClass](arg="some_value")
```

## **Singleton**

A `Singleton` provider ensures that only one instance of the dependency is created and reused
throughout the application’s lifecycle.

```python
singleton_provider = di.Singleton[SomeClass](arg="some_value")
```

To reset a singleton instance:

```python
di.Provide[singleton_provider].reset()
```

## **Scoped**

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

## **Selector**

A `Selector` provider allows conditional dependency injection based on runtime values, such as
environment variables.

```python
repository = di.Selector[os.getenv("DATABASE")](
    in_memory=di.Transient[InMemoryRepository](),
    mysql=di.Transient[MySqlRepository]()
)
```

## **Object**

An `Object` provider holds a constant value that is injected when needed.

```python
constant_provider = di.Object("fixed_value")
```

## **Dict**

An `Dict` provider holds a dictionary that is injected when needed.

```python
dict_provider = di.Dict({"key": "value"})
```

## **List**

An `List` provider holds a list that is injected when needed.

```python
list_provider = di.List(["value1", "value2"])
```

## **Tuple**

An `Tuple` provider holds a tuple that is injected when needed.

```python
tuple_provider = di.Tuple(("value1", "value2"))
```
