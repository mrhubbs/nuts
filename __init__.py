

__version__ = '0.1'

__all__ = ('NutsException', )


class NutException(Exception):
    pass


# Try to import some version of etree.
try:
    from lxml import etree
    # running with lxml.etree
except ImportError:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
        # running with cElementTree on Python 2.5+
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
            # "running with ElementTree on Python 2.5+
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
                # running with cElementTree"
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                    # running with ElementTree
                except ImportError:
                    raise Exception(
                        "Failed to import ElementTree from any known place")
