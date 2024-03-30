import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        u1 = User.signup(
            email = 'test1@test.com',
            username = 'testuser1',
            password = 'password',
            image_url = None
        )
        u1id = 1000
        u1.id = u1id

        msg = Message(
            text = 'test message',
            user_id = u1id
        )
        msg_id = 10000
        msg.id = msg_id

        db.session.add(u1)
        db.session.add(msg)
        db.session.commit()

        u1 = db.session.get(User, u1id)
        msg = db.session.get(Message, msg_id)

        self.u1 = u1
        self.msg = msg

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Does message model work"""

        message = Message(
            text = 'test message',
            user_id = 1000
        )
        message_id = 1000
        message.id = message_id

        db.session.add(message)
        db.session.commit()

        query_msg = db.session.get(Message, message_id)
        
        self.assertTrue(message == query_msg)

    def test_message_user_relationship(self):
        """does message connect to the proper user"""
        wrong_id = 1001

        self.assertEqual(self.u1.id, self.msg.user_id)
        self.assertNotEqual(self.msg.user_id, wrong_id)

    def test_message_likes(self):
        """does liking message function properly"""

        self.u1.likes.append(self.msg)
        likes = Likes.query.filter(Likes.user_id == self.u1.id).all()
        
        self.assertEqual(len(self.u1.likes), 1)
        self.assertTrue(self.u1.likes[0] == self.msg)
