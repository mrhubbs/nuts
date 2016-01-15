
from __init__ import etree, NutException


class AcornException(NutException):
    pass


class BaseAcornSource(object):
    """
    The base class for every source.
    """

    def __init__(self, meta):
        self.meta = meta

    def create_default(self, name, obj):
        if self.meta.get('default') is not None:
            setattr(obj, name, self.meta['default'])

    def fromxml(self, name, obj, xml_el):
        raise AcornException("Must implement in inheriting class")

    def toxml(self, name, obj, xml_el):
        raise AcornException("Must implement in inheriting class")


class AcornTextSource(BaseAcornSource):
    """
    Source to get data from element's text.
    """

    type = 'text'

    @staticmethod
    def _get_text(name, xml_el):
        return xml_el.text

    def fromxml(self, name, obj, xml_el):
        """
        Loads an object's attribute from the XML element's attribute or child's texts.

        This applies options and default.
        """

        meta = self.meta

        try:
            # Attempt to get the attribute and convert
            # it to the correct type.
            val = self._process_val_fxml(
                self._get_text(name, xml_el),
                meta)
        except KeyError:
            try:
                # Couldn't get the attribute, try and use a default.
                val = meta['default']
            except KeyError:
                # No default supplied, we have to raise
                # an exception.
                raise AcornException((
                    "No {} \"{}\" in XML "
                    "element and no default given").format(
                        self.type,
                        name))

        setattr(obj, name, val)

    def toxml(self, name, obj, xml_el):
        xml_el.text = self._process_val_txml(getattr(obj, name))

    def _process_val_fxml(self, raw_val, obj):
        """
        Helper method to process a raw value from XML attribute/text.

        This is where options are applied.
        """
        meta = self.meta
        val = meta['type'](raw_val)

        # Enforce that val be one of the permissible options, if options
        # are specified.
        if meta.get('options') is not None:
            if val not in meta['options']:
                raise AcornException((
                    "Value \"{}\" is illegal for attribute of "
                    "class \"{}\". Permissible options are: "
                    "{}").format(val, obj, meta['options']))

        return val

    def _process_val_txml(self, val):
        conv = self.meta.get('str', str)
        return conv(val)


class AcornAttrSource(AcornTextSource):
    """
    Source to get data from element's attribute.
    """

    type = 'attrib'

    @staticmethod
    def _get_text(name, xml_el):
        return xml_el.attrib[name]

    def toxml(self, name, obj, xml_el):
        xml_el.attrib[name] = self._process_val_txml(getattr(obj, name))


class AcornSubTextSource(AcornTextSource):
    """
    Source to get data from element's child's text.
    """

    type = 'child'

    def _get_text(self, name, xml_el):
        tag = self.meta.get('tag', name)

        child = xml_el.find(tag)
        if child is None:
            raise KeyError

        return child.text

    def toxml(self, name, obj, xml_el):
        child = etree.SubElement(xml_el, self.meta.get('tag', name))
        child.text = self._process_val_txml(getattr(obj, name))


class AcornChildSource(BaseAcornSource):
    """
    Source to load object from element's child.
    """

    def create_default(self, name, obj):
        if self.meta.get('default') is not None:
            setattr(obj, name, self.meta['type']())

    def fromxml(self, name, obj, xml_el):
        child_cls = self.meta['type']
        child_tag = child_cls.xml_tag

        child_el = xml_el.find(child_tag)

        if child_el is not None:
            setattr(obj, name, child_cls.fromxml(child_el))

        elif not self.meta.get('optional'):
            # We don't have the child and it's not optional, complain.
            raise AcornException((
                "Object of tag \"{}\" should specify child of tag "
                "\"{}\"".format(self.xml_tag, child_cls.xml_tag)))

    def toxml(self, name, obj, xml_el):
        try:
            child = getattr(obj, name)
        except AttributeError:
            # This is not optional, complain.
            if not self.meta.get('optional'):
                raise AcornException((
                    "Object \"{}\" of type \"{}\" "
                    "has no attribute "
                    "\"{}\"".format(obj, type(obj), name)))
        else:
            child.toxml(xml_el)


class AcornChildrenSource(BaseAcornSource):
    """
    Load a series of objects from the direct children (children's children
    are ignored).

    .. code-block:: XML
        <person>
            <weapon type='sword'/>
            <weapon type='bow'/>
            <weapon type='dirk'/>
        </person>

    .. code-block:: python

        class Weapon(Acorn):
            ...

        class Person(Acorn):
            xml_tag = 'person'
            acorn_content = Acorn.parse_content({
                . . .
                'weapons': {'type': Weapon, 'src': 'children'}
            })

        person = Person.fromxml(...)
        print(person.weapons)

        [<Weapon object at 0x7fab52......>,
         <Weapon object at 0x7fab52......>,
         <Weapon object at 0x7fab52......>]

    TODO: write about recursion trick for children/child
    """

    def create_default(self, name, obj):
        setattr(obj, name, [])

    def fromxml(self, name, obj, xml_el):
        child_cls = self.meta['type']
        child_tag = child_cls.xml_tag

        children_objs = []
        setattr(obj, name, children_objs)

        for child in xml_el.iterfind(child_tag):
            children_objs.append(child_cls.fromxml(child))

    def toxml(self, name, obj, xml_el):
        for child in getattr(obj, name):
            child.toxml(xml_el)
