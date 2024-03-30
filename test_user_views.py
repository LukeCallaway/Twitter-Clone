import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes
from sqlalchemy.exc import IntegrityError


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        # add testuser and test_message
        testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        test_user_id = 1000
        testuser.id = test_user_id
        
        test_message = Message(text = 'test message 1', user_id = test_user_id)
        test_message_id = 1000
        test_message.id = test_message_id

        # add a 2nd test user and test message
        # need 2nd user for multipe routes
        other_user = User.signup(username="otheruser",
                                    email="other@other.com",
                                    password="otheruser",
                                    image_url=None)
        other_user_id = 2000
        other_user.id = other_user_id
        
        other_user_test_message = Message(text = 'test message 2', user_id = other_user.id)
        other_user_test_message_id = 2000
        other_user_test_message = other_user_test_message
        other_user_test_message.id = other_user_test_message_id

        # add all and commit to db
        db.session.add(testuser)
        db.session.add(test_message)
        db.session.add(other_user)
        db.session.add(other_user_test_message)

        db.session.commit()

        self.testuser = testuser
        self.test_message = test_message
        self.other_user = other_user
        self.other_user_test_message = other_user_test_message

    def tearDown(self):
        db.session.rollback()

    def test_signup(self):
        """Can sign up?"""

        with self.client as c:

            post_resp = c.post("/signup", data={"username": "sign up test user", 
                                                "password": "sign up test user",
                                                "email": "validsignuptestuser@test.com",
                                                "image_url": None})

            self.assertEqual(post_resp.status_code, 302)
            self.assertEqual(post_resp.location, '/')

    def test_login(self):
        """Can login?"""
        with self.client as c:

            post_resp = c.post('/login', data = {"username": "testuser", "password":"testuser"})

            self.assertEqual(post_resp.status_code, 302)
            self.assertEqual(post_resp.location, '/')

    def test_logout(self):
        """Can logout?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            get_resp = c.get('/logout')

            self.assertEqual(get_resp.status_code, 302)
            self.assertEqual(get_resp.location, '/login')

    def test_list_users(self):
        """Makes sure search page displays users"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # make sure testuser shows up in the search response html
            get_resp = c.get('/users')
            html = get_resp.get_data(as_text=True)

            self.assertEqual(get_resp.status_code, 200)
            self.assertIn('testuser', html)
            self.assertIn('/users/1000', html)

            # make sure no users show when a search term has no matching users
            search_resp = c.get('/users?q=tim')
            search_html = search_resp.get_data(as_text=True)

            self.assertIn('Sorry, no users found', search_html)
            self.assertEqual(search_resp.status_code, 200)
    
    def test_users_show(self):
        """Make sure user page displays info."""

        with self.client as c:

            get_resp = c.get('/users/1000')
            html = get_resp.get_data(as_text=True)

            # make sure user page shows user details
            self.assertEqual(get_resp.status_code, 200)
            self.assertIn(self.testuser.username, html)
            self.assertIn(self.test_message.text, html)

    def test_show_following(self):
        """Make sure following page shows all follows"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            # add new follow
            new_follow = Follows(user_being_followed_id = self.other_user.id, 
                                user_following_id = self.testuser.id)

            db.session.add(new_follow)
            db.session.commit()

            get_resp = c.get('/users/1000/following')
            html = get_resp.get_data(as_text=True)

            # check if followed user info displays
            self.assertEqual(get_resp.status_code, 200)
            self.assertIn('testuser', html)
            self.assertIn('No Bio', html)
            self.assertIn('Unfollow', html)

    def test_users_followers(self):
        """Make sure followers page shows all followers"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
        
            # add new follower
            new_follow = Follows(user_being_followed_id = self.testuser.id, 
                                user_following_id = self.other_user.id)

            db.session.add(new_follow)
            db.session.commit()

            get_resp = c.get('/users/1000/followers')
            html = get_resp.get_data(as_text=True)

            # check if follower info displays
            self.assertEqual(get_resp.status_code, 200)
            self.assertIn('otheruser', html)
            self.assertIn('No Bio', html)
            self.assertIn('Follow', html)

    def test_users_likes(self):
        """Make sure liked messages display"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # add new like
            new_like = Likes(user_id = self.testuser.id, message_id = self.other_user_test_message.id)

            db.session.add(new_like)
            db.session.commit()

            get_resp = c.get('/users/1000/likes')
            html = get_resp.get_data(as_text=True)

            # check if liked message info displays
            self.assertEqual(get_resp.status_code, 200)
            self.assertIn(self.other_user_test_message.text, html)

    def test_add_follow(self):
        """Can add and remove a follow?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # post to follow a user
            post_follow_resp = c.post('/users/follow/2000')

            self.assertEqual(len(self.testuser.following), 1)
            self.assertEqual(post_follow_resp.status_code, 302)
            self.assertEqual(post_follow_resp.location, '/users/1000/following')

            # post to unfollow a user
            post_unfollow_resp = c.post('/users/stop-following/2000')

            self.assertEqual(len(self.testuser.following), 0)
            self.assertEqual(post_follow_resp.status_code, 302)
            self.assertEqual(post_follow_resp.location, '/users/1000/following')

    def test_profile(self):
        """Can update profile info?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # updated testuser info
            # added follow redirects to test if the users page was updated
            post_resp = c.post("/users/profile", data={"username": "new improved test user name", 
                                                        "password": "testuser",
                                                        "email": "test@test.com",
                                                        "image_url": None,
                                                        "bio": "Bio has been updated"},
                                                        follow_redirects=True)
            html = post_resp.get_data(as_text=True)

            # test if updated name is on users page
            # get status code 200 rather than 302 using follow redirects               
            self.assertEqual(post_resp.status_code, 200)
            self.assertIn('new improved test user name', html)

    def test_delete_user(self):
        """Can delete profile?"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            post_resp = c.post('/users/delete')

            self.assertEqual(post_resp.status_code, 302)
            self.assertEqual(post_resp.location, '/signup')
