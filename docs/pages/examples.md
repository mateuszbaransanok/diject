Hello World



## configuration dataclasses, pydantic, custom


## Transient

Stosuj do tworzenia klas, ktore przechowują jakiś stan, powinny one być lekkie i szybkie w tworzeniu 

## Partial

Jeżeli masz dużo razy transient z tymi samymi argumentami, 
wydziel je do Partiala aby uniknąć duplikacji kodu.

## Singleton

...

## Resource

## Scoped

Połączenie Scoped z Resource


```python
def create_session(session_maker):
    with session_maker as session:
        yield session
        
        
def create_session_maker(
    url: str,
):
    ses = session_maker(engine=Engine(url))
    
    # create schema
    
    yield ses
    
    # close connections etc


db_session = di.Scoped[create_session](
  session_maker=di.Resource[create_session_maker](
      url=di.Singleton[os.getenv]("DATABASE_URL"),
  ),
)

```
