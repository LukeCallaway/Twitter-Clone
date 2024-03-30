"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        test_user_id = 1000
        self.testuser.id = test_user_id
        
        test_message = Message(text = 'setUP test message', user_id = test_user_id)
        test_message_id = 1000
        self.test_message = test_message
        self.test_message.id = test_message_id

        db.session.add(test_message)
        db.session.commit()

    def tearDown(self):
        db.session.rollback()


    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            post_resp = c.post("/messages/new", data={"text": "test message"})

            # Make sure it redirects to the correct location
            self.assertEqual(post_resp.status_code, 302)
            self.assertEqual(post_resp.location, f'/users/{self.testuser.id}')

            # grab message and make sure the text is correct
            msg = Message.query.filter(Message.text == 'test message').one()
            self.assertEqual(msg.text, "test message")
    
    def test_add_message_get(self):
        """Can view page only when logged in?"""
        with self.client as c:
      
            # no user in session should redirect to home page
            no_user_get_resp = c.get('/messages/new')
            self.assertEqual(no_user_get_resp.location, "/")

            # add user
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # user in session should get corresponding page
            user_get_resp = c.get('/messages/new')
            self.assertEqual(user_get_resp.status_code, 200)

    def test_show_message(self):
        """Can view a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # get page and check it's showing the correct message in the response html
            resp = c.get(f'/messages/{self.test_message.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.test_message.text, html)   

    def test_delete_message(self):
        """Can delete message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            own_message_resp = c.post(f'/messages/{self.test_message.id}/delete')

            self.assertEqual(own_message_resp.status_code, 302)
            self.assertTrue(own_message_resp.location, f'/users/{self.testuser.id}')
            self.assertEqual(len(self.testuser.messages), 0)

    def test_toggle_like(self):
        """Can add and remove a like from a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            #create 'other_user' to test if we can like their message
            other_user = User.signup(username="otheruser",
                                    email="other@other.com",
                                    password="otheruser",
                                    image_url=None)
            other_user_id = 2000
            other_user.id = other_user_id
        
            test_likeable_message = Message(text = 'test message', user_id = other_user.id)
            test_likeable_message_id = 2000
            test_likeable_message = test_likeable_message
            test_likeable_message.id = test_likeable_message_id

            db.session.add(test_likeable_message)
            db.session.commit()

            # post to add like route
            like_resp = c.post(f'/users/add_like/{test_likeable_message.id}')
            
            self.assertEqual(like_resp.status_code, 302)
            self.assertEqual(like_resp.location, '/')
            self.assertEqual(len(self.testuser.likes), 1)

            # post to remove like route
            unlike_resp = c.post(f'/users/remove_like/{test_likeable_message.id}')

            self.assertEqual(unlike_resp.status_code, 302)
            self.assertEqual(unlike_resp.location, '/')
            self.assertEqual(len(self.testuser.likes), 0)      
