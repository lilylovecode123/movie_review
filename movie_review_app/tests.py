from multiprocessing.connection import Client

# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from django.db import models

from movie_review.movie_review_app.models import User


# Define a test case for the login function
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

class CheckPasswordViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_correct_password(self):
        # Set up a user with a known password
        username = 'testuser'
        password = 'testpassword'
        user = User.objects.create_user(username=username, password=password)

        # Log in as the user
        self.client.login(username=username, password=password)

        # Call the checkPassword view with the correct original password
        response = self.client.get('/check_password/', {'originPwd': password, 'token': user.id})

        # Check that the response is a success response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})

    def test_incorrect_password(self):
        # Set up a user with a known password
        username = 'testuser'
        password = 'testpassword'
        user = User.objects.create_user(username=username, password=password)

        # Log in as the user
        self.client.login(username=username, password=password)

        # Call the checkPassword view with an incorrect original password
        response = self.client.get('/check_password/', {'originPwd': 'wrongpassword', 'token': user.id})

        # Check that the response is a warning response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'warning', 'message': 'User inputs wrong original password.'})