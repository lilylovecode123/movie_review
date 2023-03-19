from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from django.db import models

class LoginTestCase(TestCase):

    def setUp(self):
        # Create a user instance with valid username and password
        self.user = models.Users.objects.create(username='testuser', password='testpass')

    def test_login_with_valid_credentials(self):
        # Simulate a login request with valid username and password inputs
        url = reverse('login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'testpass'})

        # Check that the response status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # Check that the response contains a token and user ID
        self.assertIn('token', response.json())
        self.assertIn('id', response.json())

    def test_login_with_invalid_username(self):
        # Simulate a login request with invalid username input
        url = reverse('login')
        response = self.client.post(url, {'username': 'invaliduser', 'password': 'testpass'})

        # Check that the response status code is 400 Bad Request
        self.assertEqual(response.status_code, 400)

        # Check that the response contains an error message
        self.assertIn('User input a wrong username.', response.json()['error'])

    def test_login_with_invalid_password(self):
        # Simulate a login request with invalid password input
        url = reverse('login')
        response = self.client.post(url, {'username': 'testuser', 'password': 'invalidpass'})

        # Check that the response status code is 400 Bad Request
        self.assertEqual(response.status_code, 400)

        # Check that the response contains an error message
        self.assertIn('User inputs a wrong password.', response.json()['error'])

