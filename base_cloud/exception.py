from __future__ import unicode_literals

from django.utils.translation import ugettext as _


class FriendlyException(Exception):
    message = _("Unknown error. Please try again later.")

    def __init__(self, message=None, *args, **kwargs):
        if message:
            self.message = message

        super(FriendlyException, self).__init__(self.message, *args, **kwargs)
