from django.db import models
import yaml
import os
import json
from django.conf import settings
from urllib.parse import urlparse

# Create your models here.

class Server(models.Model):
    name = models.CharField(max_length=100, unique=True)
    base_url = models.CharField(max_length=500, help_text="Base URL of the server (e.g., http://127.0.0.1:8000)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate the base_url format
        try:
            result = urlparse(self.base_url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format. Must include scheme (http/https) and host.")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

    def __str__(self):
        return f"{self.name} ({self.base_url})"

    class Meta:
        ordering = ['-updated_at']

class Profile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    cookies = models.JSONField(default=dict, help_text="User's cookies in JSON format")
    common_parameters = models.JSONField(default=dict, help_text="Common parameters like user_id, book_id, etc.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Create the profiles directory if it doesn't exist
        os.makedirs(settings.PROFILES_DIR, exist_ok=True)
        
        # Create YAML content
        yaml_content = {
            'name': self.name,
            'description': self.description,
            'cookies': self.cookies,
            'common_parameters': self.common_parameters
        }
        
        # Save the YAML file
        yaml_path = os.path.join(settings.PROFILES_DIR, f"{self.name}.yaml")
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-updated_at']

class APIEndpoint(models.Model):
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ]
    
    name = models.CharField(max_length=200)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    endpoint = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    required_parameters = models.JSONField(default=list, help_text="List of required parameters")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.method} {self.name}"

    class Meta:
        ordering = ['-updated_at']

class TestRun(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    target_profile = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_test_runs')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='completed')  # completed, failed, in_progress

    def __str__(self):
        return f"Test Run {self.id} - {self.profile.name} on {self.server.name}"

class TestResult(models.Model):
    TEST_TYPE_CHOICES = [
        ('normal', 'Normal Test'),
        ('target_params', 'Target Profile Parameters Test'),
    ]
    
    test_run = models.ForeignKey(TestRun, on_delete=models.CASCADE, related_name='results')
    endpoint = models.ForeignKey(APIEndpoint, on_delete=models.CASCADE)
    request_url = models.URLField()
    request_method = models.CharField(max_length=10)
    request_parameters = models.JSONField(default=dict)
    response_status = models.IntegerField()
    response_headers = models.JSONField(default=dict)
    response_data = models.JSONField(null=True)
    error_message = models.TextField(null=True, blank=True)
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.request_method} {self.endpoint.name} - Status: {self.response_status}"

    class Meta:
        ordering = ['-created_at']
