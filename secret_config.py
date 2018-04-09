#!/usr/bin/env python3.6.4
# secret configuration
SALT_KEY = b'p3hK_:>4C#a(v)(SH%(1}^egZ5Xa:1T1'
SECRET_KEY = 'dcevbrftfds123ws//?zdef23'
SQL_SERVER = 'mysql'
PYTHON_SQL_ENGINER = 'pymysql'
SQL_USER = 'root'
SQL_PASSWORD='ertyuiop'
SQL_HOST = '127.0.0.1'
SQL_DB = 'aryousleeping'

SQLALCHEMY_DATABASE_URI = "{server}+{engine}://{user}:{password}@{host}/{db}".format(
    server=SQL_SERVER, engine=PYTHON_SQL_ENGINER, user=SQL_USER, password=SQL_PASSWORD,host=SQL_HOST, db=SQL_DB)