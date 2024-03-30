"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        u1 = User.signup(
            email = 'test1@test.com',
            username = 'testuser1',
            password = 'password',
            image_url = None
        )
        u1.id = 1000

        u2 = User.signup(
            email = 'test2@test.com',
            username = 'testuser2',
            password = 'password',
            image_url = None
        )
        u2.id = 2000
        db.session.add(u1,u2)
        db.session.commit()

        u1 = db.session.get(User,1000)
        u2 = db.session.get(User,2000)

        self.u1 = u1
        self.u2 = u2

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_model_repr(self):
        """Does repr method display correct info"""

        u = User(
            email = 'test@test.com',
            username = 'testuser',
            password = 'password'
        )
        db.session.add(u)
        db.session.commit()
        self.assertIn('test@test.com', u.__repr__())

    def test_is_following(self):
        """checks users followers and following lists"""

        self.u1.following.append(self.u2)

        self.assertTrue(len(self.u1.following) == 1)
        self.assertTrue(len(self.u1.followers) == 0)
        self.assertTrue(len(self.u2.following) == 0)
        self.assertTrue(len(self.u2.followers) == 1)

    def test_user_authenticate(self):
        """Does auth method only work for correct username and password"""

        self.assertFalse(self.u1.authenticate('testuser1', 'wrongpassword'))
        self.assertFalse(self.u1.authenticate('wrongusername', 'password'))
        self.assertTrue(self.u1.authenticate('testuser1', 'password'), self.u1)