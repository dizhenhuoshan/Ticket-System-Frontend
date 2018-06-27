from flask import Flask
from flask import request, render_template, abort, redirect, url_for, session
from subprocess import Popen, PIPE, STDOUT

app = Flask(__name__)

# set it to a random string
app.secret_key = 'wym and ymt'

# set this to path/to/your/database/backend/program
database_exec_path = './train'


def app_init():
    app.proc = Popen([database_exec_path], stdin=PIPE, stdout=PIPE)


app_init()


def db_write(cmd):
    app.proc.stdin.write((cmd + '\n').encode())
    app.proc.stdin.flush()


def db_readline():
    return app.proc.stdout.readline().decode().strip('\n')


@app.route('/', methods=['GET'])
def home():
    # if 'home_success_info' in session and session['home_success_info'] != '':
    #     success_info = session['home_success_info']
    #     session.pop('home_success_info', None)
    # else:
    #     success_info = None
    # if 'home_err_info' in session and session['home_err_info'] != '':
    #     err_info = session['home_err_info']
    #     session.pop('home_err_info', None)
    # else:
    #     err_info = None
    if 'user_id' in session and 'user_name' in session and session['user_name'] != '':
        user_name = session['user_name']
    else:
        user_name = None
    if 'privilige' in session and 'privilige' in session and session['privilige'] != 1:
        is_admin = True
    else:
        is_admin = False
    return render_template('index.html', user_name=user_name, is_admin=is_admin)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        db_write(' '.join(['login', userid, password]))
        reply = db_readline()
        print(reply)
        if reply == '0' or reply == 'Wrong Command':
            return render_template('signin.html', err_info='Login failed for some reason.')
        else:
            session['home_success_info'] = 'Logged in successfully! Now you can play around.'
            session['user_id'] = userid
            db_write(' '.join(['query_profile', userid]))
            reply = db_readline()
            if reply == '0':
                session['home_err_info'] = 'Login failed! User does not exist.'
            else:
                session['user_name'] = reply.split(' ')[0]
            return redirect(url_for('home'))
    else:
        return render_template('index.html')


@app.route('/usermodify', methods=['POST', 'GET'])
def usermodify():
    return render_template('usermodify.html')


if __name__ == '__main__':
    app.debug=True
    app.run('0.0.0.0',5000)
