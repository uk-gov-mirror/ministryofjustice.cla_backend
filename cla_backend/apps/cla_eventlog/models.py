from django.db import models
from django.conf import settings

from model_utils.models import TimeStampedModel

from timer.models import Timer

from .constants import LOG_LEVELS, LOG_TYPES


class Log(TimeStampedModel):
    case = models.ForeignKey('legalaid.Case')
    timer = models.ForeignKey(Timer, null=True, blank=True)
    code = models.CharField(max_length=20)
    type = models.CharField(choices=LOG_TYPES.CHOICES, max_length=20)
    level = models.PositiveSmallIntegerField(choices=LOG_LEVELS.CHOICES)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    notes = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return u'%s - %s:%s' % (self.case, self.type, self.code)

    class Meta:
        ordering = ['-created']
