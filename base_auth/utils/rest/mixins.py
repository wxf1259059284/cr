from base.utils.rest.mixins import BatchSetModelMixin

from base_auth.models import Owner
from base_auth.utils.owner import filter_operate_queryset


class BatchSetOwnerModelMixin(BatchSetModelMixin):

    batch_set_fields = {
        'public_mode': Owner.PublicMode.values()
    }

    def perform_batch_set(self, queryset, field, value):
        queryset = filter_operate_queryset(self.request.user, queryset)
        return super(BatchSetOwnerModelMixin, self).perform_batch_set(queryset, field, value)
