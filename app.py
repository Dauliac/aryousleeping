#!/usr/bin/env python3.6.4
import binascii
from flask import Flask, url_for, render_template, request, redirect, session, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask_sqlalchemy import SQLAlchemy
import hashlib
import telegram as tlg
from datetime import date, time, datetime
import requests
import json

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)
app.config.from_pyfile('secret_config.py', silent=True)
db = SQLAlchemy(app)

# variable ===========================================================================
SALT_KEY = app.config['SALT_KEY']
ALERT_DELTA = app.config['ALERT_DELTA']
TELEGRAM_TOKEN = app.config['TELEGRAM_TOKEN']


# functions ===========================================================================
def hash_string(password):
    password = password.encode('UTF-8')
    password = hashlib.pbkdf2_hmac('sha256', password, SALT_KEY, 100000)
    password = binascii.hexlify(password).decode('UTF-8')
    return password


# DB ===========================================================================
#class
class User(db.Model):
    """ Create user table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    chat_id = db.Column(db.Integer, unique=True)
    chat_token = db.Column(db.String(256), nullable=False)
    server = db.relationship('Server', backref='user', cascade="all, save-update, merge, delete")

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.chat_token = hash_string(username + password + datetime.now().replace(microsecond=0))
        self.chat_id = None


class Server(db.Model):
    """ Create server table"""
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(80), nullable=False)
    alias = db.Column(db.String(80), nullable=False)
    last_status =  db.Column(db.String(80), nullable=True)
    last_alert = db.Column(db.DateTime())
    user_id = db.Column(db.Integer, 
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False,
                        )
    log = db.relationship('Log', backref='server', cascade="all, save-update, merge, delete")


    def __init__(self, hostname, alias, user_id, last_status=None, last_alert=None):
        self.hostname = hostname
        self.alias = alias
        self.user_id = user_id
        self.last_status = last_status
        self.last_alert = last_alert



class Log(db.Model):
    """ Create log table"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime())
    server_id = db.Column(db.Integer, 
                        db.ForeignKey('server.id', ondelete='CASCADE'),
                        nullable=False)

    def __init__(self, code, date,  server_id):
        self.code = code
        self.date = date
        self.server_id = server_id

# Init
db.create_all()

# Async ===========================================================================
# functions
def ping_all(server_id):
    for server in servers_global:
        if server.id == server_id:
            print
            srv = db.session.query(Server).filter(Server.id == server_id).first()
            try:
                url = 'http://' + server.hostname
                rsp = requests.get(url, timeout=100)
                response = {'code': rsp.status_code,
                            'date': datetime.now().replace(microsecond=0)}
            except:
                response = {'code': 500,
                            'date': datetime.now().replace(microsecond=0)}
                now = datetime.now().replace(microsecond=0)
                time_limit = 60*60*1  # hour minute secondes
                if not srv.last_alert:
                    delta = time_limit
                else:
                    print(srv.hostname)
                    delta = now - srv.last_alert
                    delta = delta.total_seconds()
                if delta >= time_limit:
                    message = "Alert ! server {alias} on http://{hostname} is down ! ".format(
                            alias=srv.alias, 
                            hostname=srv.hostname)
                    srv.last_alert = now
                    tlg.send_message(srv.user.chat_id, TELEGRAM_TOKEN,message)
            new_log = Log(code=response['code'], date=response['date'], server_id = server.id )
            db.session.add(new_log)
            srv.last_status = response['code']
            db.session.commit()



# Init
scheduler = BackgroundScheduler()
scheduler.start()
servers_global = Server.query.all()
for server in servers_global:
    if server.user:
        scheduler.add_job(
        func=ping_all,
        args=[server.id ],
        trigger=IntervalTrigger(minutes=1),
        id='logs_server_' + str(server.id),
        name='Log severs'  + str(server.id),
        max_instances=2,
        replace_existing=True)



# routes ===========================================================================
# base
@app.route('/', methods=['GET', 'POST'])
def login():
    """Login Form"""
    if request.method == 'GET':
        test_user = User.query.first()
        if not test_user:
            return redirect(url_for('register'))
        if not session.get('auth_user'):
            return render_template('login.html')
        else:
            return redirect(url_for('admin'))
    else:
        name = request.form['username']
        passw = hash_string(request.form['password'])
        try:
            data = User.query.filter_by(username = name, password = passw).first()
            if data is not None:
                user = {'id': data.id,
                        'username': data.username,
                        'chat_token': data.chat_token}
                session['auth_user'] = user
                return redirect(url_for('admin'))
            else:
                return render_template('login.html', notify="bad identifier")
        except:
            return render_template('login.html', notify="WTF error")


# server
@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    """Show server"""
    if not session.get('auth_user'):
        return redirect(url_for('login'))
    if request.method == 'GET':
        srv = Server.query.filter_by(user_id = session['auth_user']['id'])
        return render_template('index.html',servers = srv)

@app.route('/admin/server/add/', methods=['POST'])
def add_server():
    if not session.get('auth_user'):
        return redirect(url_for('login'))
    hostname=request.form['hostname'].replace('http://','').replace('https://','')
    new_server = Server(hostname = hostname, alias=request.form['alias'], user_id = session['auth_user']['id'])
    db.session.add(new_server)
    db.session.commit()
    global servers_global
    servers_global = Server.query.all()
    for srv in servers_global:
        if srv.hostname == new_server.hostname and srv.alias == new_server.alias and srv.user_id == new_server.user_id:
            scheduler.add_job(
                func=ping_all,
                args=[srv.id],
                trigger=IntervalTrigger(minutes=1),
                id='logs_server_' + str(srv.id),
                name='Log server: ' + str(srv.id),
                max_instances=2,
                replace_existing=True)
    return redirect(url_for('admin'))


@app.route('/admin/server/<int:srv_id>/', methods=['GET', 'POST'])
def get_server(srv_id):
    """Show realtime logs"""
    if not session.get('auth_user'):
        return redirect(url_for('login'))
    srv = Server.query.filter_by(id = srv_id).first()
    old_logs = srv.log

    return render_template('log.html', server = srv, old_logs = old_logs)

@app.route('/_get_logs/')
def get_logs():
    try:
        srv_id = request.args.get('id')
        log = Log.query.filter_by(server_id = srv_id).order_by(Log.date.desc()).first()
        if(log):
            log = {'STATUS': log.code, 'DATE': str(log.date)}
            js_resp = json.dumps(log, ensure_ascii=False)
            return jsonify(js_resp)
        else:
            return jsonify(None)
    except:
            return jsonify(Error)


@app.route('/admin/server/<int:srv_id>/remove/', methods=['GET'])
def remove_server(srv_id):
    """Remove server"""
    if not session.get('auth_user'):
        return redirect(url_for('login'))
    srv = Server.query.filter_by(id = srv_id).first()
    db.session.delete(srv)
    db.session.commit()
    global servers_global
    servers_global = Server.query.all()
    scheduler.remove_job('logs_server_' + str(srv_id))
    return redirect(url_for('admin'))


# session
@app.route('/register/', methods=['GET', 'POST'])
def register():
    """Register user"""        
    test_user = User.query.first()
    if test_user:
        return redirect(url_for('login'))
    if requestgenerate_token().method == 'POST':
        print("new_user")
        new_user = User(username=request.form['username'], password=hash_string(request.form['password']))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    else:
        return render_template('register.html')


@app.route('/user/', methods=['GET', 'POST'])
def get_user():
    """Show user"""
    notify = ''
    auth_user = session.get('auth_user')
    if request.method == 'POST':
        password = request.form['password']
        passw_confirm = request.form['password-confirm']
        if password != passw_confirm:
            notify = "Not the same passwords"
        else:
            user_to_update = User.query.filter_by(id = auth_user['id']).first()
            user_to_update.password = hash_string(password)
            db.session.commit()
            notify = "password updated !"
    return render_template('user.html', user = auth_user, notify = notify)

@app.route("/logout/")
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/user/telegram/', methods=['GET'])
def set_user_telegram():
    """Show user"""
    user = session.get('auth_user')
    result = tlg.get_chat_id(TELEGRAM_TOKEN, user['chat_token'])
    user_to_update = User.query.filter_by(id = user['id']).first()
    user_to_update.chat_id = result
    db.session.commit()
    tlg.send_message(user_to_update.chat_id, TELEGRAM_TOKEN, "Token activated")
    return redirect(url_for('get_user'))


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

# run ===========================================================================
if __name__ == '__main__':
    app.secret_key = app.config['SECRET_KEY']
    db.create_all()
    app.run(debug=False, host='0.0.0.0')
