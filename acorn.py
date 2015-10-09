"""
This defines some very flexible functionality to create Python classes from XML
and create XML from Python classes.
"""


# Python library imports


# local imports
from acorn_base import *


__all__ = ('AcornException',
           'Acorn')


class Acorn(object):
    """
    xml_tag = 'example_acorn'

    acorn_content = {
        'name':        AcornAttrMeta(type=str),
        'description': AcornTextMeta(type=str)
    }

    xml_tag should be a string.  It is XML tag which corresponds to
    the object type.

    acorn_content should be defined with the following form:

    acorn_content = {
        'attrib_name': {'type': TYPE, 'default': DEFAULT_VALUE},
    }

    The key of each entry in the content def dict is a string name,
    corresponding to the name of the XML attribute.

    The value of each entry is a dictionary containing meta-data about
    the attribute.

    type:
    For simple data, this is generally a string-to-whatever conversion
    function.  In this cas, it must be a callable, accepting one argument,
    such as int or:
        lambda x: int(x, 16)

    str:
    Specifies what function to use to convert the attribute into
    a string for saving into XML.  For example, if 'type' is set as above,
    'str' should be set to:
        lambda x: hex(x)

    src:
    Specifies where in the XML to get/put the data, as well as what parser
    to use.  This defaults to 'attr' if not specified.

    default:
    Contains a default value to use in case the XML element does
    not have the attribute.  The default value is not converted using
    the type parameter and so, for example, if type is 'float' then 'default'
    should be 0.0 and not '0.0'.

    options:
    Contains permissible values for the attribute.  An exception will
    be raised on creating an element from XML if the XML attribute has an
    illegal value (legality is checked after converting with 'type').

    children:
    A special type that defines a list of child objects that should be loaded
    from the XML element.

    child:
    Similar to 'children' but, instead of defining a list of child objects,
    defines just a single child object.  A 'child' may have an 'optional',
    specifying whether it is required or not.   If not set it is assumed to
    be False.  NOTE: optional is only valid for child type.

    For more, see the example at the bottom of this file.
    """

    xml_tag = 'acorn'

    acorn_content = {}

    # - - - - - - - - - - -
    # Initialization code
    # - - - - - - - - - - -

    def __init__(self, **kwargs):
        """
        It is optional to call Acorn.__init__.  If you do, it will
        create all attributes with default values (and set them to the
        defaults) and create any attributes of 'children' type and set them to
        empty lists.  It will create any attributes of 'child' type.

        It will also set any attributes to any values specified in kwargs.
        These values override the defaults.  For any attributes with
        'options' specified, no checking is done to ensure the values in
        kwargs are permissible.
        """

        # Create all defaults.
        for aname, meta in self.acorn_content.items():
            meta.create_default(aname, self)

        # Apply any attribute values specified in kwargs.
        for aname, value in kwargs.items():
            if aname in self.acorn_content:
                setattr(self, aname, value)

    # - - - - - - - - - - - - - - -
    # Handle sources
    # - - - - - - - - - - - - - - -

    __sources__ = {
        'text':       AcornTextMeta,
        'attr':       AcornAttrMeta,
        'child.text': AcornSubTextMeta,
        'child':      AcornChildMeta,
        'children':   AcornChildrenMeta
    }

    @classmethod
    def register_src(cls, src_name, src):
        cls.__sources__[src_name] = src

    @classmethod
    def unregister_src(cls, src_name):
        if src_name in cls.__sources__:
            del cls.__sources__[src_name]

    @classmethod
    def parse_content(cls, content):
        parsed = {}

        for name, meta in content.items():
            src_name = meta.get('src', 'attr')
            # Create source to handle meta.
            try:
                src_cons = cls.__sources__[src_name]
            except KeyError:
                raise AcornException((
                    "No source named \"{}\" is registered "
                    "with {}").format(src_name, cls)
                )

            src = src_cons(**meta)

            parsed[name] = src

        return parsed

    # - - - - - - - - - - - - - - -
    # Code for loading from XML.
    # - - - - - - - - - - - - - - -

    @classmethod
    def fromxml(cls, xml_el):
        """
        Create and return a new object loaded from the XML element or path.
        """
        if isinstance(xml_el, str):
            # It's a path, load from it.
            xml_el = etree.parse(xml_el).getroot()

        obj = cls()

        # load all the attributes and sub-objects
        for aname, meta in cls.acorn_content.items():
            meta.fromxml(aname, obj, xml_el)

        return obj

    # - - - - - - - - - - - - -
    # Code for saving to XML.
    # - - - - - - - - - - - - -

    def toxml(self, xml_dest=None, write_kwargs={'pretty_print': True}):
        """
        Convenience wrapper, which handles the case where the passed-in element
        is actually a string path.
        """
        if isinstance(xml_dest, str):
            # It's a path, write the tree out.
            el = self._toxml()
            tree = etree.ElementTree(el)
            tree.write(xml_dest, **write_kwargs)
            return el
        else:
            # No path, just proceed as usual.
            return self._toxml(xml_dest)

    def _toxml(self, xml_dest=None):
        """
        Convert the object to an XML element and place it under the given
        XML element.
        """
        # Create the element
        el = etree.Element(self.xml_tag)
        if xml_dest is not None:
            xml_dest.append(el)

        # Apply the attributes
        for aname, meta in self.acorn_content.items():
            meta.toxml(aname, self, el)

        return el

    # - - - - - - - - - - -
    # Common helper methods
    # - - - - - - - - - - -


# Example
if __name__ == '__main__':
    class NestedObject(Acorn):
        xml_tag = 'nested_object'
        acorn_content = Acorn.parse_content({
            'name': {'type': str, 'src': 'attr'},
        })

    class Child(Acorn):
        xml_tag = 'child'
        acorn_content = Acorn.parse_content({
            'name': {'type': str, 'src': 'attr'}
        })

    class Item(Acorn):
        xml_tag = 'item'
        acorn_content = Acorn.parse_content({
            'name': {
                'type': str,
                'src': 'attr'
            },
            'description': {
                'type': str,
                'src': 'child.text'
            },
            'nested_object': {
                'type': NestedObject,
                'src': 'child'
            },
            'children': {
                'type': Child,
                'src': 'children'
            },
        })

        def __init__(self, **kw):
            super(Item, self).__init__(**kw)

        def __str__(self):
            return self.name + ' (' + self.description + ')'

    xml_text = """
<item name='the little example'>
    <description>I am just an example, nothing special.</description>
    <nested_object name='a full-fledged sub-object'/>
    <child name='roger'/>
    <child name='fred'/>
    <child name='babies'/>
</item>
    """
    root = etree.fromstring(xml_text)
    ea = Item.fromxml(root)

    print('# from XML #')
    print(xml_text)
    print('This resulted in:')
    print(str(ea))

    print('\n# to XML #\n')
    ea = Item(name='test', description='yes, just a test',
              nested_object=NestedObject(name='nester'),
              children=[
                  Child(name='1'),
                  Child(name='2')])
    print(str(ea))
    root = ea.toxml()
    print('\nThis resulted in:')
    print(etree.tostring(root, pretty_print=True))

