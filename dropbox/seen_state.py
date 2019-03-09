# -*- coding: utf-8 -*-
# Auto-generated by Stone, do not modify.
# @generated
# flake8: noqa
# pylint: skip-file
try:
    from . import stone_validators as bv
    from . import stone_base as bb
except (ImportError, SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import stone_validators as bv
    import stone_base as bb

class PlatformType(bb.Union):
    """
    Possible platforms on which a user may view content.

    This class acts as a tagged union. Only one of the ``is_*`` methods will
    return true. To get the associated value of a tag (if one exists), use the
    corresponding ``get_*`` method.

    :ivar seen_state.PlatformType.web: The content was viewed on the web.
    :ivar seen_state.PlatformType.mobile: The content was viewed on a mobile
        client.
    :ivar seen_state.PlatformType.desktop: The content was viewed on a desktop
        client.
    :ivar seen_state.PlatformType.unknown: The content was viewed on an unknown
        platform.
    """

    _catch_all = 'other'
    # Attribute is overwritten below the class definition
    web = None
    # Attribute is overwritten below the class definition
    mobile = None
    # Attribute is overwritten below the class definition
    desktop = None
    # Attribute is overwritten below the class definition
    unknown = None
    # Attribute is overwritten below the class definition
    other = None

    def is_web(self):
        """
        Check if the union tag is ``web``.

        :rtype: bool
        """
        return self._tag == 'web'

    def is_mobile(self):
        """
        Check if the union tag is ``mobile``.

        :rtype: bool
        """
        return self._tag == 'mobile'

    def is_desktop(self):
        """
        Check if the union tag is ``desktop``.

        :rtype: bool
        """
        return self._tag == 'desktop'

    def is_unknown(self):
        """
        Check if the union tag is ``unknown``.

        :rtype: bool
        """
        return self._tag == 'unknown'

    def is_other(self):
        """
        Check if the union tag is ``other``.

        :rtype: bool
        """
        return self._tag == 'other'

    def _process_custom_annotations(self, annotation_type, processor):
        super(PlatformType, self)._process_custom_annotations(annotation_type, processor)

    def __repr__(self):
        return 'PlatformType(%r, %r)' % (self._tag, self._value)

PlatformType_validator = bv.Union(PlatformType)

PlatformType._web_validator = bv.Void()
PlatformType._mobile_validator = bv.Void()
PlatformType._desktop_validator = bv.Void()
PlatformType._unknown_validator = bv.Void()
PlatformType._other_validator = bv.Void()
PlatformType._tagmap = {
    'web': PlatformType._web_validator,
    'mobile': PlatformType._mobile_validator,
    'desktop': PlatformType._desktop_validator,
    'unknown': PlatformType._unknown_validator,
    'other': PlatformType._other_validator,
}

PlatformType.web = PlatformType('web')
PlatformType.mobile = PlatformType('mobile')
PlatformType.desktop = PlatformType('desktop')
PlatformType.unknown = PlatformType('unknown')
PlatformType.other = PlatformType('other')

ROUTES = {
}
