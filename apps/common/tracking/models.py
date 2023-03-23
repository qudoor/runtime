from django.db import models


class ApiRecord(models.Model):
    api = models.CharField(max_length=1024, help_text='API URL')
    headers = models.JSONField(null=True, blank=True)
    body = models.JSONField(null=True, blank=True)
    method = models.CharField(max_length=10, db_index=True)
    client_ip_address = models.CharField(max_length=50)
    response = models.TextField()
    status_code = models.PositiveSmallIntegerField(help_text='Response status code', db_index=True)
    execution_time = models.CharField(max_length=32)
    action = models.CharField(max_length=64, null=True, blank=True)
    user_id = models.CharField(max_length=50, null=True, blank=True)
    added_on = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.api

    class Meta:
        verbose_name = 'API Log'
        verbose_name_plural = 'API Logs'
