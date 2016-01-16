"""
This defines a very flexible serialization between Python objects and XML.
"""


# Python library imports


# local imports
from acorn_base import *


__all__ = ('AcornException',
           'Acorn')


class _AcornMetaClass(type):
    def __init__(cls, *ar):
        super(_AcornMetaClass, cls).__init__(*ar)
        # We want this to be a different object for every sub-class of Acorn.
        cls.__hooks__ = {
            'fromxml': [],
            'toxml':   [],
        }


class Acorn(object):
    """
    This defines a very flexible serialization between Python objects and XML.
    """

    xml_tag = None
    '''
    Tag to use for XML element created from the object.
    to 'person'.
    '''

    acorn_content = {}
    '''
    This dictionary defines what class attributes Acorn will load from/save
    to XML.

    acorn_content should be defined in the following way:

    .. code-block:: python

        class Example(Acorn):
            acorn_content = Acorn.parse_content({
                'attrib_name': {'type': str, ...},
                'other_attrib_name': ...,
                ...
            })
    '''

    __metaclass__ = _AcornMetaClass

    # - - - - - - - - - - -
    # Initialization code
    # - - - - - - - - - - -

    def __init__(self, **kwargs):
        """
        It is optional to call this when instantiating inheriting classes.
        If called, it will create all attributes with default values (and set
        them to the defaults) and create any attributes of 'children' type 
        and set them to empty lists.  It will create any attributes of 'child'
        type.

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
        'text':       AcornTextSource,
        'attr':       AcornAttrSource,
        'child.text': AcornSubTextSource,
        'child':      AcornChildSource,
        'children':   AcornChildrenSource
    }

    @classmethod
    def register_src(cls, src_name, src):
        """
        Registers the source **src** under the name **src_name**.

        **src_name**
            :class:`str`, name of source

        **src**
            Must inherit from :class:`~acorn_base.BaseAcornSource`.

        .. note::
            If there is already a source by **src_name**, it will be replaced \
            by **src**.

        .. note::
            This acts 'globally'. That is, the source will be registered to
            :class:`~acorn.Acorn` and all classes that inherit from it.
        """
        cls.__sources__[src_name] = src

    @classmethod
    def unregister_src(cls, src_name):
        """
        Unregisters the source associted with the name **src_name**.

        **src_name**
            :class:`str`, name of source

        .. note::
            This fails gracefully (without exceptions) in the event there is \
            no such source.

        .. note::
            This acts 'globally'. That is, the source will be unregistered from
            :class:`~acorn.Acorn` and all classes that inherit from it.
        """
        if src_name in cls.__sources__:
            del cls.__sources__[src_name]

    # - - - - - - - - - - - - - - -
    # Handle hooks
    # - - - - - - - - - - - - - - -

    @classmethod
    def add_hook(cls, event, hook):
        """
        Add **hook** to the event named **event**.

        **event**
            :class:`str`, name of event. Current options are 'fromxml' \
                and 'toxml'.

        **hook**
            A callable of the form:

            .. code-block:: python

                def hook(event, event_cls, obj):
                    ...

        - *event* - name of event

        - *event_cls* - the class of the object generating the event. If the \
            hook call resulted from doing:

            .. code-block:: python

                Acorn.fromxml(...)

            then *event_cls* would be :class:`~acorn.Acorn`.

        - *obj* - the object associated with the hook. For 'fromxml', this \
            is the Python object being created. For 'toxml', this is the \
            :class:`xml.etree.ElementTree.Element` being created.

        .. note::
            If this hook is already assigned to **event**, it will not be \
            added again.

        .. note::
            Unlike :func:`~acorn.Acorn.register_src`, this acts 'locally'.
            That is, it only acts on the class it is called with, not all
            classes inheriting from :class:`~acorn.Acorn`.
        """
        hlist = cls.__hooks__[event]

        # Make sure not to add twice.
        if hook not in hlist:
            hlist.append(hook)

    @classmethod
    def remove_hook(cls, event, hook):
        """
        Remove **hook** from the event named **event**.

        **event**
            :class:`str`, name of event. Current options are 'fromxml' \
                and 'toxml'.

        **hook**
            The hook callable.

        .. note::
            This fails gracefully (without exceptions) in the event there is \
            no such hook.

        .. note::
            Unlike :func:`~acorn.Acorn.register_src`, this acts 'locally'.
            That is, it only acts on the class it is called with, not all
            classes inheriting from :class:`~acorn.Acorn`.
        """
        if event in cls.__hooks__:
            try:
                cls.__hooks__[event].remove(hook)
            except ValueError:
                # The given hook wasn't in the given event, but just ignore.
                pass

    @classmethod
    def _apply_hooks(cls, event, obj):
        for h in cls.__hooks__[event]:
            h(event, cls, obj)

    @classmethod
    def parse_content(cls, content):
        """
        Processes the content dict into a more usable form for Acorn's
        internal code.  This should be used to define
        :attr:`~acorn.Acorn.acorn_content`.
        """
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

            src = src_cons(meta)

            parsed[name] = src

        return parsed

    # - - - - - - - - - - - - - - -
    # Code for loading from XML.
    # - - - - - - - - - - - - - - -

    @classmethod
    def fromxml(cls, xml_src):
        """
        Create and return a new object loaded from **xml_src**.

        **xml_src**
            Either :class:`xml.etree.ElementTree.Element` or a path of type
            :class:`str`. If the first, the object will be loaded from the
            element. If the second, the XML file at the path **xml_src** will
            be parsed and the object loaded from the root element.
        """
        if isinstance(xml_src, str):
            # It's a path, load from it.
            xml_src = etree.parse(xml_src).getroot()

        obj = cls()

        # load all the attributes and sub-objects
        for aname, meta in cls.acorn_content.items():
            meta.fromxml(aname, obj, xml_src)

        cls._apply_hooks('fromxml', obj)

        return obj

    # - - - - - - - - - - - - -
    # Code for saving to XML.
    # - - - - - - - - - - - - -

    def toxml(self, xml_dest=None, write_kwargs={'pretty_print': True}):
        """
        Convert the object to an XML element.

        **xml_dest**
            Either :class:`xml.etree.ElementTree.Element` or a path of type
            :class:`str`. If the first, the object, when converted to XML,
            will be placed as a sub-element of **xml_dest**. If the second,
            the XML will be written to the path.

        **write_kwargs**
            kwargs to pass to :func:`etree.ElementTree.write` if xml_dest
            is a path
        """
        if isinstance(xml_dest, str):
            # It's a path, write the tree out.
            el = self._toxml()
            tree = etree.ElementTree(el)
            tree.write(xml_dest, **write_kwargs)

            self._apply_hooks('toxml', el)

            return el
        else:
            # No path, just proceed as usual.
            el = self._toxml(xml_dest)
            self._apply_hooks('toxml', el)
            return el

    def _toxml(self, xml_dest=None):
        """
        Does the actual work.
        """
        # Create the element
        el = etree.Element(self.xml_tag)
        if xml_dest is not None:
            xml_dest.append(el)

        # Apply the attributes
        for aname, meta in self.acorn_content.items():
            meta.toxml(aname, self, el)

        return el


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
