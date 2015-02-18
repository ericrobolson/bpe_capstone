# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('registration', '0002_auto_20150214_1946'),
    ]

    operations = [
        migrations.AddField(
            model_name='person',
            name='user',
            field=models.OneToOneField(default=0, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
