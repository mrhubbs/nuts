# nuts

Nuts is a collection of Python classes for loading and saving data.  The specific goal is to easily create Python objects from file data (XML, JSON, etc.) and vice-versa.  Thus nuts is essentially a serialization/deserialization tool; it allows a great deal of flexibility.  Currently, nuts is comprised of Acorn.

## acorn

Acorn is a flexible, concise, powerful mix-in class for serializing/deserializing to/from XML.

### simple example

Let's say you have some data in an XML file that looks like this:

```xml
<person name='King Henry II' age='30'
    habit='regaining control of ancestral lands'>
    <temperament>quite a lot of it</temperament>
</person>
```

To load that into Python, you may do:

```python
from lxml import etree
person_el = etree.parse('people.xml').getroot()


class Person(object):
    def __init__(self, name, age, habit, temperament):
        self.name = name
        self.age = int(age)
        self.habit = habit
        self.temperament

person = Person(
    person_el.attrib['name'],
    person_el.attrib['age'],
    person_el.attrib['habit'],
    person_el.find('temperament').text)
```

This can get tiresome rather quickly.  It's also not very efficient, as you must write the name of every attribute at least four times.

To use Acorn, simply do this:

```python
from nuts.acorn import Acorn


class Person(Acorn):
    # this specifies what tag a Person will have
    # when represented as an XML element
    xml_tag = 'person'
    acorn_content = Acorn.parse_content({
        'name':        {'type': str},
        'age':         {'type': int},
        'habit':       {'type': str},
        'temperament': {'type': str, 'src': 'child.text'},
    })

person = Person.fromxml('people.xml')
```

and voila!

```python
print('name = %s, age = %d' % (person.name, person.age))

"name = King Henry II, age = 30"

print(person)

<Person object at 0x7fab5270d910, name="King Henry II", age=30,
    habit="regaining control of ancestral lands",
    temperament="quite a lot of it">
```

Note that, by specifying the type of each attribute, Acorn can perform automatic type conversions.  It is able to load data from element attributes (such as with name, age, and habit) or element's children's text (such as with temperament).  The source of the data for the attribute is specified by the 'src' entry.  See below for all the built-in sources.  Custom sources may also be used, which opens the door to a lot of flexibility (more on that later).

### sources

Built-in values for the 'src' entry are:

#### attr

Get data from element attribute.

```xml
<examp data="..."/>
```

#### text

Get data from element text.

```xml
<examp>
    ...
</examp>
```

#### child.text

Get data from child's text.

```xml
<examp>
    <data>...</data>
</examp>
```

The tag of the child is assumed to be the name of the attribute.  This can be overridden like so:

```python
class Person(Acorn):
    ...
    acorn_content = Acorn.parse_content({
        'misnamed_data': {'type': str, 'src': 'child.text', 'tag': 'data'},
    })
    ...
```

#### child

Load an entire object from a child.  For example:

```xml
<person>
    <weapon type='sword'/>
</person>
```
```python
class Weapon(Acorn):
    xml_tag = 'weapon'
    acorn_content = Acorn.parse_content({
        'type': {'type': str}
    })

class Person(Acorn):
    xml_tag = 'person'
    acorn_content = Acorn.parse_content({
        . . .
        'weapon':      {'type': Weapon, 'src': 'child'}
    })

person = Person.fromxml(...)
print(person.weapon)

<Weapon object at 0x7fab5270d910>
```

#### children

Load a series of objects from the children.

```xml
<person>
    <weapon type='sword'/>
    <weapon type='bow'/>
    <weapon type='dirk'/>
</person>
```
```python
class Weapon(Acorn):
    ...

class Person(Acorn):
    xml_tag = 'person'
    acorn_content = Acorn.parse_content({
        . . .
        'weapons':      {'type': Weapon, 'src': 'children'}
    })

person = Person.fromxml(...)
print(person.weapons)

[<Weapon object at 0x7fab52......>,
 <Weapon object at 0x7fab52......>,
 <Weapon object at 0x7fab52......>]
```

TODO: write about recursion trick for children/child

### writing your own source

TODO: write about this...
