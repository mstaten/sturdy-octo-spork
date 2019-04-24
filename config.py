# a file for my config class to store configuration vbls
# from the-flask-mega-tutorial

import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://sturdy-octo-spork:cu3dKNFTXPF3wnH@localhost:3306/sturdy-octo-spork'

    SQLALCHEMY_ECHO = True
    POSTS_PER_PAGE = 6
    