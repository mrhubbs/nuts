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
    content_tag = 'example_acorn'

    content_defs = {
        'name':        AcornAttrMeta(type=str),
        'description': AcornTextMeta(type=str)
    }

    content_tag should be a string.  It is XML tag which corresponds to
    the object type.

    content_defs should be defined with the following form:

    content_defs = {
        'attrib_name': {'type': TYPE, 'default': DEFAULT_VALUE},
    }

    The key of each entry in the content def dict is a string name,
    corresponding to the name of the XML attribute.

    The value of each entry is a dictionary containing meta-data about
    the attribute.

    type:
    Specifies what type to convert the string XML attribute to.
    It must be a callable accepting one argument, such as int or:
        lambda x: int(x, 16)

    save_conv:
    Specifies what function to use to convert the attribute into
    a string for saving into XML.  For example, if 'type' is set as above,
    'save_conv' should be set to:
        lambda x: hex(x)

    default:
    Contains a default value to use in case the XML element does
    not have the attribute.  The default value is not converted using
    the type parameter and so, for example, if type is 'float' then 'default'
    should be 0.0 and not '0.0'.

    options:
    Contains permissible values for the attribute.  An exception will
    be raised on creating an element from XML if the XML attribute has an
    illegal value (legality is checked after converting with 'type').

    subels:
    A special type that defines a list of child objects that should be loaded
    from the XML element.  Every attribute with the 'subels' type should have
    'cls' in the meta-deta specifying the class of the children.  That class
    must also inherit from StorableContent.

    subel:
    Similar to 'subels' but, instead of defining a list of child objects,
    defines just a single child object.  A 'subel' may have an 'optional',
    specifying whether it is required or not.   If not set it is assumed to
    be False.  NOTE: optional is only valid for subel type.

    cls:
    See 'subels'.

    For more, see the example at the bottom of this file.
    """

    content_tag = 'acorn'

    content_defs = {}

    # - - - - - - - - - - -
    # Initialization code
    # - - - - - - - - - - -

    def __init__(self, **kwargs):
        """
        It is optional to call Acorn.__init__.  If you do, it will
        create all attributes with default values (and set them to the
        defaults) and create any attributes of 'subels' type and set them to
        empty lists.  It will create any attributes of 'subel' type.

        It will also set any attributes to any values specified in kwargs.
        These values override the defaults.  For any attributes with
        'options' specified, no checking is done to ensure the values in
        kwargs are permissible.
        """

        # Create all defaults.
        for aname, meta in self.content_defs.items():
            meta.create_default(aname, self)

        # Apply any attribute values specified in kwargs.
        for aname, value in kwargs.items():
            if aname in self.content_defs:
                setattr(self, aname, value)

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
        for aname, meta in cls.content_defs.items():
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
        el = etree.Element(self.content_tag)
        if xml_dest is not None:
            xml_dest.append(el)

        # Apply the attributes
        for aname, meta in self.content_defs.items():
            meta.toxml(aname, self, el)

        return el

    # - - - - - - - - - - -
    # Common helper methods
    # - - - - - - - - - - -


# Example
if __name__ == '__main__':
    class NestedObject(Acorn):
        content_tag = 'nested_object'
        content_defs = {
            'name': AcornAttrMeta(type=str),
        }

    class Child(Acorn):
        content_tag = 'child'
        content_defs = {
            'name': AcornAttrMeta(type=str),
        }

    class Item(Acorn):
        content_tag = 'item'
        content_defs = {
            'name':          AcornAttrMeta(type=str),
            'description':   AcornSubTextMeta(type=str),
            'nested_object': AcornChildMeta(type=str, cls=NestedObject),
            'children':      AcornChildrenMeta(type=str, cls=Child),
        }

        def __init__(self, **kw):
            super(Item, self).__init__(**kw)

        def __str__(self):
            return self.name + ' (' + self.description + ')'

    xml_text = """
<root>
    <item name='the little example'>
        <description>I am just an example, nothing special.</description>
        <nested_object name='a full-fledged sub-object'/>
        <child name='roger'/>
        <child name='fred'/>
        <child name='babies'/>
    </item>
</root>
    """
    root = etree.fromstring(xml_text)
    ea = Item.fromxml(list(root)[0])

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
    root = etree.Element('root')
    ea.toxml(root)
    print('This resulted in:')
    print(etree.tostring(root, pretty_print=True))

