import unittest
from flask import current_app
from datetime import datetime
from app import create_app, db
from app.models import User, Role, Permission, AnonymousUser, Follow


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='schmidt')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='schmidt')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_check(self):
        u = User(password='schmidt')
        self.assertTrue(u.check_password('schmidt'))
        self.assertFalse(u.check_password('Danbove'))

    def test_password_salts_random(self):
        u = User(password='schmidt')
        v = User(password='schmidt')
        self.assertTrue(u.password_hash != v.password_hash)

    def test_roles_and_permissions(self):
        u = User(email='schmidt@slog.com', password='546231')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))

    def test_gravatar(self):
        u = User(email='yangwehhao@foxmail.com', password='546231')
        MD5 = 'acd59f95b952e6fd88ba7e24d5c5dd09'
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar256 = u.gravatar(size=256)
            gravatarpg = u.gravatar(rating='pg')
            gravatarretro = u.gravatar(default='retro')
        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatarssl = u.gravatar()

        self.assertTrue('http://www.gravatar.com/avatar/' + MD5 in gravatar)
        self.assertTrue('s=256' in gravatar256)
        self.assertTrue('r=pg' in gravatarpg)
        self.assertTrue('d=retro' in gravatarretro)
        self.assertTrue('https://secure.gravatar.com/avatar/' + MD5 in gravatarssl)

    def test_follows(self):
        u = User(email='yangwehhao@foxmail.com', password='yw546231')
        v = User(email='Schmidt@slog.com', password='546231')
        db.session.add(u)
        db.session.add(v)
        db.session.commit()
        self.assertFalse(u.is_following(v))
        self.assertFalse(u.is_followed_by(v))
        time_before = datetime.utcnow()
        u.follow(v)
        db.session.add(u)
        db.session.commit()
        time_after = datetime.utcnow()
        self.assertTrue(u.is_following(v))
        self.assertFalse(u.is_followed_by(v))
        self.assertTrue(v.is_followed_by(u))
        self.assertTrue(u.followed.count() == 1)
        self.assertTrue(v.followers.count() == 1)
        f = u.followed.all()[-1]
        self.assertTrue(f.followed == v)
        self.assertTrue(time_before <= f.starttime <= time_after)
        f = v.followers.all()[-1]
        self.assertTrue(f.follower == u)
        u.unfollow(v)
        db.session.add(u)
        db.session.commit()
        self.assertTrue(u.followed.count() == 0)
        self.assertTrue(v.followers.count() == 0)
        self.assertTrue(Follow.query.count() == 0)
        v.follow(u)
        db.session.add(u)
        db.session.add(v)
        db.session.commit()
        db.session.delete(v)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 0)
