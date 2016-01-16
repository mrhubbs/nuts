# nuts

Nuts is a collection of Python classes for very flexible serialization.  Currently, nuts is comprised of Acorn, which does XML serialization.

## acorn

Acorn is a flexible, concise, powerful mix-in class for serializing/deserializing to/from XML.

__Contents__

 * [simple example](#the_example)
 * [sources](#sources) - customizable, how Acorn processes the data from XML
 * [writing your own source](#writing_source)
 * [hooks](#hooks) - further customizability

<a name="the_example"></a>
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

Note that, by specifying the type of each attribute, Acorn can perform automatic type conversions.  It is able to load data from element attributes (such as with name, age, and habit) or element's children's text (such as with temperament).  The source of the data for the attribute is specified by the 'src' entry, which defaults to 'attr'.  See below for all the built-in sources.  Custom sources may also be used, which opens the door to a lot of flexibility (more on that later).

<a name="sources"></a>
### sources

This is an introduction by example.  More documentation is <a href='docs/build/index.html#module-acorn_base'>here</a>.

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

Get data from a child's text.

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

<a name="writing_source"></a>
### writing your own source

You can write your own sources.  Below is a simplified example that behaves like the 'attr' (__AcornAttrSource__) source.

```python
from nuts.acorn import Acorn
from nuts.acorn_base import BaseAcornSource

class AcornSimpleAttrSource(BaseAcornSource):
    def fromxml(self, name, obj, xml_el):
        # simple example, doesn't perform error checking
        type_conv = self.meta['type']
        val = type_conv(xml_el.attrib[name])
        setattr(obj, name, val)

    def toxml(self, name, obj, xml_el):
        # be sure to convert to string...
        xml_el.attrib[name] = str(getattr(obj, name))

Acorn.register_src('simple-attr', AcornSimpleAttrSource)

class Person(Acorn):
    xml_tag = 'person'
    acorn_content = Acorn.parse_content({
        'name': {'type': str, 'src': 'simple-attr'}
    })

# now AcornSimpleAttrSource will be used to parse Person's name attribute
```

The dictionary associated with 'name' is available within the fromxml and toxml methods as 'self.meta'. 

The arguments to fromxml and toxml:

 * __name__ - the attribute name
 * __obj__  - the instance of the Python object being loaded or saved
 * __xml_el__ - the etree Element instance the Python object is being loaded from or saved to
 
__BaseAcornSource__ has a method for creating default values.  You can override it, if you want to:

```python
class AcornSimpleAttrSource(BaseAcornSource):
    ...
    def create_default(self, name, obj):
        setattr(obj, name, 'default value')
    ...
```

You can also override the **\_\_init\_\_** method, like so:

```python
class AcornSimpleAttrSource(BaseAcornSource):
    def __init__(self, *args):
        super(AcornSimpleAttrSource, self).__init__(*args)
        
        # whatever code you want...
    ...
```

__NOTE:__ If your source is a bit more advanced, instead of using **BaseAcornSource**, consider extending one of the other **Acorn\*Source** classes in [acorn_base.py](acorn_base.py).

<a name="hooks"></a>
### hooks

Acorn supports hooks to allow customization.  Here is an example:

```xml
<person name='Roger'/>
```
```python

class Person(Acorn):
    xml_tag = 'person'
    acorn_content = Acorn.parse_content({
        'name': {'type': str}
    }

    @classmethod
    def extra_init_fluff(cls, event, event_cls, obj):
        obj.name = '[' + obj.name + ']'

Acorn.add_hook('fromxml', Person.extra_init_fluff)

person = Person.fromxml(...)
print('name = "%s"' % (person.name))

"name = [Roger]"
```

The Acorn.add_hook method takes two arguments, the hook event and a callback function.  Currently, the two hooks events are 'fromxml' and 'toxml'.  A hook callback should be of the form:

```python
def hook_callback(event_name,  # name of the event
                  event_cls,   # class generating the event
                  obj):        # relevant object
   ...
```

The 'obj' argument to the hook callback is the instantiated Python object for 'fromxml' and the etree Element for 'toxml'.

Hooks may be removed with:

```python
Acorn.remove_hook(event, hook)
```

**Note:** hooks are not inherited.  If you do:

```python
Acorn.add_hook('fromxml', lambda *ar: 0)
```

no hook is added to Person.