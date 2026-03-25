import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status


@pytest.mark.integration
class ProfileAPITest(APITestCase):
    def test_get_profile_unauthenticated(self):
        """Test profile endpoint without authentication"""
        url = reverse('profile')
        response = self.client.get(url)
        # Should return 401 or appropriate auth error
        self.assertIn(response.status_code, [401, 403])


@pytest.mark.integration
class ChatAPITest(APITestCase):
    def test_chat_endpoint_exists(self):
        """Test that chat endpoint is accessible"""
        url = reverse('chat')
        # This will test if the URL exists, even if auth fails
        response = self.client.post(url, {'message': 'test'})
        # Should not be 404
        self.assertNotEqual(response.status_code, 404)


@pytest.mark.unit
class URLTest(TestCase):
    def test_main_urls_resolve(self):
        """Test that main URLs resolve correctly"""
        # Test dashboard URL
        response = self.client.get('/dashboard/')
        self.assertNotEqual(response.status_code, 404)

        # Test login URL
        response = self.client.get('/loginui/')
        self.assertNotEqual(response.status_code, 404)