

Co poprawia diject

diject wprowadza framework nadający strukturę i spójną konwencję w zarzadzaniu i konfigurowaniu zależności.
Pozwala na zarządzaniu cyklem życia dla zwykłych klas i funkcji. Pozwala tworzyć obiekty na każde żadanie, 
jednorazowo dla całej aplikacji w sposób eager albo leniwy, oddzielnie na każdy wątek lub per request scope.
Umożliwia wybranie, które klasy powinny się tworzyc w zależności od wartości np. ze zmiennej środowiskowej, dzięki czemu można wstrzykiwać odpowiednią implementację do wysokopoziomowych abstrakcji.
Kontenery pomagają w uporzadkowaniu całej konfiguracji i nadaniu jej logicznego i spójnego wyglądu.


jak wygląda koncept

kiedy korzystamy z obiektu tworzącego provider np. di.Factory podajemy najpierw funkcję lub klasę która ma być dostarczana.
Tą klasę podajemy w `[]` -> `di.Factory[SomeClass]` . To zwraca instancję tworzącą FactoryProvider, ale posiada sygnaturę klasy SomeClass.
Ma to na celu pomoc w statycznej typizacji mypy, wczesnym wykrywaniu błędów i prosrzemu konfigurowaniu przez podpowiadanie i autouzupełnianie dzięki IDE.
Następnie utwórz provider `some_class = di.Factory[SomeClass](arg="some_arg")` to zwraca  FactoryProvider, ale it pretends that is instance SomeClass.
Dzięki temu można używać ten provider do wstrzykiwania do innych providerów `another_class = di.Factory[AnotherClass](some_class=some_class)` i statyczna typizacja będzie się zgadzać.

Aby dostarczyć taki provider wraz ze wszystkimi zależnościami, należy `another_class_instance = di.Provide[another_class]()`. 
Dependency `another_class_dependency = di.Provide[another_class]` udostępnia funkcje operujące na donder methods providerów `another_class`.

jest di.Container gdzie definiuje się konfigurację całego projektu. 
W ramach potrzeb można utworzyć wiele kontenerów grupując komponenty aplikacji.

```python
class SomeContainer(di.Container):
    some_class = di.Factory[SomeClass](arg="some_arg")
    another_class = di.Factory[AnotherClass](some_class=some_class)
```

dostarczać można albo pojedynczy provider `another_class_instance = di.Provide[SomeContainer.another_class]()`,
albo cały kontener `some_container = di.Provide[SomeContainer]()`.
Tak dostarczony kontener dostarcza providery w czasie getattr `another_class_instance = some_container.another_class` 
i za każdym razem ponawia dostarczanie co dla FactoryProvider za każdem razem tworzy nową instancję klasy AnotherClass.

Definiując obiekty w kontenerze, lub jako argumenty

```python
class SomeContainer(di.Container):
    some_number = 1
    some_class = di.Factory[SomeClass](arg="some_arg")
```

w ciele `SomeContainer` `some_number` pozostaje `int`, ale poza tym ciałem `SomeContainer` następuje konwersja obiektów zdefiniowanych w kontenerze do `ObjectProvider`.
Listy, tuple, set oraz dict są zamieniane na di.Factory, oraz są rekurencyjnie przeszukiwane pod kątem zagnieżdzonych providerów.
Aby uniknąć takiego przeszukiwania utwórz obiekt eplicite przez `di.Object([1, 2, 3])`

Możesz również przeszukiwać zdefiniowane providery
`di.Provide[SomeContainer].travers()`
możesz Filter by specific provider types.
Traverse providers recursively.
Include only public providers started without `_` in container.
Include only providers that have been selected by SelectorProvider.

```python
for name, provider in di.Provide[SomeContainer].travers():
    pass
```

Masz również dostęp do providera `di.Provide[some_class].provider`, jest to ten sam obiekt co `some_class`, ale pamiętaj, że dla statycznej typizacji `some_class` to instancja SomeClass a nie provider.
Dlatego powinno się korzystać z `di.Provide[some_class].provider`.

Istnieje więcej providerów 


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

### Status

You can retrieve the status of a Resource to determine whether it has started, stopped,
or if an error occurred during startup:

```python
di.Provide[some_resource].status
```

Start  - opisz
Reset  - opisz
Shutdown  - opisz


### Provide

Providers can be provided in five ways:
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

oprócz explicite dostarczania można skorzystać z wstrzykiwania do funkcji

```python
@di.inject
def function(some_value: Any = some_provider):
    pass
```

implicite gdy zarejstrujemy provider

`di.Provider[some_class].register()`

```python
@di.inject
def function(some_class: SomeClass):
    pass
```

register działa na mro klasy i przeszukuje całą hierarchię tak by wstrzyknąć pasujący obiekt.
Gdy nie ma lub gdy jest więcej niż jeden zarejestrowany provider do danej klasy, nie zostaje on wstrzyknięty
przez co trzeba podać go manualnie przy wywołaniu funkcji, albo użyć alias i zaznaczyć go przez annotatację `typing.Annotated[SomeClass, "alias"]`