from django.core.management.commands.loaddata import Command as LoadDataCommand

from apps.runtime.models import RuntimeAppModel


class Command(LoadDataCommand):
    def handle(self, *args, **options):
        if options["app_label"] == "runtime":
            # 清空表，否则初始化无法更新已有数据
            RuntimeAppModel.objects.all().delete()
        super(Command, self).handle(*args, **options)
