from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**param):
    return get_user_model().objects.create_user(**param)


class PublicUserApiTests(TestCase):
    '''
    Test the users API (public)
    '''

    def setup(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        '''
        Test creating user with valid payload is successful
        '''
        payload = {
            'email': 'test@thoth-science.com',
            'password': 'testpass',
            'name': 'Xecus'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        '''
        Test creating user that already exists fails
        '''
        payload = {
            'email': 'test@thoth-science.com',
            'password': 'testpass',
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        '''
        Test that the password must be more than 5 characters
        '''
        payload = {
            'email': 'test2@thoth-science.com',
            'password': 'pw',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
            )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        '''
        Test that a token is created for the user
        '''
        payload = {
            'email': 'test3@thoth-science.com',
            'password': 'testpass',
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        '''
        Test that token is not created if invalid credentials are given
        '''
        create_user(
            email='test4@thoth-science.com',
            password='testpass',
        )
        payload = {
            'email': 'test4@thoth-science.com',
            'password': 'worng',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        '''
        Test thay token is not created if user doesn't exist
        '''
        payload = {
            'email': 'test5@thoth-science.com',
            'password': 'testpass',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        '''
        Test that email and password are required
        '''
        res = self.client.post(
            TOKEN_URL,
            {
                'email': 'test',
                'password': '',
            }
        )
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        '''
        Test that authentication is required for users
        '''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatUserApiTest(TestCase):
    '''
    Test API requirs that require authentication
    '''

    def setUp(self):
        self.user = create_user(
            email='test@email.com',
            password='testpassword',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_sucess(self):
        '''
        Test retrieving profile for logged in used
        '''
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        '''
        Test the POST is not allowed on the me url
        '''
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''
        Test Updating the user profile for authenticated user
        '''
        payload = {'name': 'new name', 'password': 'newpassword2'}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
