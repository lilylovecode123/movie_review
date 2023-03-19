from multiprocessing.connection import Client

# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from django.db import models

from movie_review import movie_review
from movie_review.movie_review_app.models import *


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

# Define a test case for the checkPassword function
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

# Define a test case for the searchByContainsWords function
class MovieSearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_by_contains_words(self):
        # Create a test Movie object
        test_movie = models.Movies.objects.create(
            movie_name='The Avengers',
            movie_intro='A team of superheroes fight to save the world.',
            release_time='2012-05-04',
            genre='Action, Adventure, Sci-Fi',
            producer='Marvel Studios',
            status='Released'
        )

        # Create a test User object to associate with the Movie's admin
        test_user = User.objects.create(
            username='test_user',
            email='test_user@example.com',
            password='password123',
            name='Test User',
            gender='Male',
            age=30,
            intro='I love movies!'
        )

        # Associate the test User with the Movie's admin
        test_admin = models.Admin.objects.create(
            user=test_user,
            login_time='2022-03-19 12:00:00'
        )
        test_movie.admin = test_admin
        test_movie.save()

        # Send a GET request to the view with the query parameter 'contain'
        request = self.factory.get('/search/', {'contain': 'Avengers'})
        response = movie_review.movie_review_app.views.MoviesView(request)

        # Check that the response contains the expected movie data
        expected_data = [{
            'id': test_movie.id,
            'movie_name': 'The Avengers',
            'movie_intro': 'A team of superheroes fight to save the world.',
            'release_time': '2012-05-04',
            'genre': 'Action, Adventure, Sci-Fi',
            'producer': 'Marvel Studios',
            'status': 'Released',
            'adminName': 'Test User',
            'adminGender': 'Male',
            'adminEmail': 'test_user@example.com',
            'adminAge': 30,
            'adminIntro': 'I love movies!',
            'adminLoginTime': '2022-03-19 12:00:00'
        }]
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected_data)