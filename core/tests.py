from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class AuthenticationAndViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='securepassword123')

    def test_login_page_status(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirects_unauthenticated(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_user_login_success(self):
        login_success = self.client.login(username='testuser', password='securepassword123')
        self.assertTrue(login_success)

# Create your tests here.
