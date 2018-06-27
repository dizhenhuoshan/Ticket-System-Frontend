from flask import Flask
from flask import request, render_template, abort, redirect, url_for, session
from pipeline import PipeLine
from mail import SendEmail
from pic import PictureMaker
from deleter import TrashCan

app = Flask(__name__)

# set it to a random string
app.secret_key = 'any random string that are long enough'

# set this to path/to/your/database/backend/program
database_exec_path = './train_modified'
rand_exec_path = './gen_rand'
graph_exec_path = './static/'

app.pipe = PipeLine(database_exec_path)
app.rand = PipeLine(rand_exec_path)
app.email = SendEmail()
app.pic_make = PictureMaker(graph_exec_path)
app.trash_can = TrashCan()

# add_train 1 C1001(长春-延吉西) C 4 2 硬卧 软卧
# 长春 xx:xx 05:47 xx:xx ￥0.0 ￥0.0
# 吉林 06:27 06:29 00:02 ￥478.97 ￥980.89
# 敦化 07:23 07:25 00:02 ￥911.62 ￥2748.9
# 延吉西 08:04 08:04 xx:xx ￥1454.54 ￥2489.5


class StationInfo(object):
    def __init__(self, seat_num):
        self.name = None
        self.arrive = None
        self.leave = None
        self.wait = None
        self.price = []
        self.seatnum = seat_num

    def read_stdin(self):
        tmp = app.pipe.readline().split(' ')
        self.name = tmp[0]
        self.arrive = tmp[1]
        self.leave = tmp[2]
        self.wait = tmp[3]
        for i in range(self.seatnum):
            self.price.append(tmp[4 + i])


class TrainInfo(object):
    def __init__(self):
        self.sale = False
        self.id = None
        self.name = None
        self.catalog = None
        self.stationNum = None
        self.seatNum = None
        self.seat = []
        self.station = []

    def read_stdin(self):
        tmp = app.pipe.readline().split(' ')
        self.id = tmp[0]
        self.name = tmp[1]
        self.catalog = tmp[2]
        self.stationNum = int(tmp[3])
        self.seatNum = int(tmp[4])
        for i in range(self.seatNum):
            self.seat.append(tmp[5 + i])
        for i in range(self.stationNum):
            self.station.append(StationInfo(self.seatNum))
            self.station[i].read_stdin()


class TicketInfo(object):
    def __init__(self):
        self.id = None
        self.departure = None
        self.leaveTime = None
        self.leaveDate = None
        self.destination = None
        self.arriveTime = None
        self.arriveDate = None
        self.seats = []

    def read_query_ticket(self):
        tmp = app.pipe.readline().split(' ')
        print(tmp)
        seatnum = int((len(tmp) - 7) / 3.0)
        self.id = tmp[0]
        self.departure = tmp[1]
        self.leaveDate = tmp[2]
        self.leaveTime = tmp[3]
        self.destination = tmp[4]
        self.arriveDate = tmp[5]
        self.arriveTime = tmp[6]
        for i in range(seatnum):
            newseats = {'seatname': tmp[6 + 3 * i + 1],
                        'seatleft': int(tmp[6 + 3 * i + 2]),
                        'price': float(tmp[6 + 3 * i + 3])}
            self.seats.append(newseats)


# 注意：Flask里用户名统一使用user_id表示, form里统一使用user_id表示
@app.route('/', methods=['GET'])
def home():
    #session.clear()
    #if 'validate_code' in session:
    #    path = './static/' + session['validate_code'] + '.png'
    #    app.trash_can.unlink(path)

    session['validate_code'] = app.pic_make.gene_text(6, 3)
    app.pic_make.gene_code(session['validate_code'])
    if 'home_success_info' in session:
        success_info = session['home_success_info']
        session.pop('home_success_info', None)
    else:
        success_info = None
    if 'home_err_info' in session:
        err_info = session['home_err_info']
        session.pop('home_err_info', None)
    else:
        err_info = None
    if 'user_id' in session and 'name' in session:
        name = session['name']
    else:
        name = None
    if 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False
    return render_template('index.html', name=name, is_admin=is_admin, success_info=success_info, err_info=err_info,
                           validate_src=(session['validate_code'] + '.png'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        cmd = ' '.join(['login', user_id, password])
        app.pipe.write(cmd)
        print(cmd)
        reply = app.pipe.readline()
        print(reply)
        print()
        if reply == '0' or reply == 'Wrong Command':
            session['home_err_info'] = '对不起，用户名不存在，请检查后再试。'
            return redirect(url_for('home'))
        else:
            # 生成email_code
            app.rand.write('10 10000007 1')
            session['email_code'] = app.rand.readline()
            session['home_success_info'] = '登录成功，您现在可以像孙恩泽一样无忧无虑地玩耍了。'
            session['user_id'] = user_id
            app.pipe.write(' '.join(['query_profile', user_id]))
            user_info = app.pipe.readline()
            if user_info == '0':
                print('后端出错了！！！')
            else:
                session['name'] = user_info.split(' ')[1]
                session['privilege'] = user_info.split(' ')[5]
                if int(session['privilege']) > 1:
                    print('是管理员')
                else:
                    print('不是管理员')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    # remove user_id and is_admin if they are there
    # session.pop('name', None)
    # session.pop('user_id', None)
    # session.pop('privilege', None)
    session.clear()
    return redirect(url_for('home'))


@app.route('/user_query_profile', methods=['GET'])
def user_query_profile():
    if 'user_id' not in session or 'name' not in session:
        session['home_err_info'] = '对不起，您还没有登陆。如果您还没有账号，请在右上角注册。'
        return redirect(url_for('home'))
    user_id = session['user_id']
    cmd = ' '.join(['query_profile', user_id])
    app.pipe.write(cmd)
    reply = app.pipe.readline()
    print(reply)

    if reply == '0':
        print('后端出bug了！！！')

    reply = reply.split(' ')
    user_info = {'user_id': reply[0],
                 'name': reply[1],
                 'password': reply[2],
                 'email': reply[3],
                 'phone': reply[4],
                 'is_admin': (int(reply[5]) > 1)}

    if 'profile_success_msg' in session:
        profile_success_msg = session['profile_success_msg']
        session.pop('profile_success_msg', None)
    else:
        profile_success_msg = None
    return render_template('user_query_profile.html', user_info=user_info)


@app.route('/user_modify_profile', methods=['GET', 'POST'])
def user_modify_profile():
    if request.method == 'GET':
        if 'user_id' not in session or 'name' not in session:
            session['home_err_info'] = '对不起，您还没有登陆。如果您还没有账号，请在右上角注册。'
            return redirect(url_for('home'))
        user_id = session['user_id']
        cmd = ' '.join(['query_profile', user_id])
        app.pipe.write(cmd)
        reply = app.pipe.readline()
        print(reply)

        if reply == '0':
            print('后端出bug了！！！')

        reply = reply.split(' ')
        user_info = {'user_id': reply[0],
                     'name': reply[1],
                     'password': reply[2],
                     'email': reply[3],
                     'phone': reply[4],
                     'is_admin': (int(reply[5]) > 1)}

        if 'profile_err_msg' in session:
            profile_err_msg = session['profile_err_msg']
            session.pop('profile_err_msg', None)
        else:
            profile_err_msg = None
        return render_template('user_modify_profile.html', user_info=user_info,
                               profile_err_msg=profile_err_msg,
                               profile_success_msg=None)
    # modified info is post up
    else:
        # robust check
        if request.form['password'] != request.form['repassword']:
            session['profile_err_msg'] = '两次密码输入不一致，请检查后再试。'
            return redirect(url_for('user_modify_profile'))

        # get info
        modified_user_info = {'user_id': session['user_id'],
                              'name': request.form['name'],
                              'email': request.form['email'],
                              'phone': request.form['phone'],
                              'password': request.form['password']}
        print(modified_user_info)
        session['modified_user_info'] = modified_user_info
        # send email
        user_id = session['user_id']
        cmd = ' '.join(['query_profile', user_id])
        app.pipe.write(cmd)
        reply = app.pipe.readline()
        email = reply.split(' ')[3]
        app.rand.write('10 10000007 1')
        session['email_code'] = app.rand.readline()
        app.email.send(email,
                       'ACM 12306 火车订票系统 个人信息重置',
                       '亲爱的' + modified_user_info['name'] + '：\n' + '您的个人信息邮箱验证码为' + session['email_code'] + '。\n' +
                       '请输入验证码完成修改，祝您旅行愉快！')
        return redirect(url_for('user_confirm_profile'))


@app.route('/user_confirm_profile', methods=['GET', 'POST'])
def user_confirm_profile():
    if request.method == 'GET':
        return render_template('user_confirm_profile.html', user_info=session['modified_user_info'])
    else:
        user_email_code = request.form['email_code']
        if user_email_code != session['email_code']:
            session['profile_err_msg'] = '邮箱验证码输入错误，请确认后再试。'
            return redirect(url_for('user_modify_profile'))
        else:
            session['home_success_info'] = '用户' + session['modified_user_info']['name'] + '个人信息重置成功。'
            cmd = ' '.join(['modify_profile',
                            session['modified_user_info']['user_id'],
                            session['modified_user_info']['name'],
                            session['modified_user_info']['password'],
                            session['modified_user_info']['email'],
                            session['modified_user_info']['phone']])
            print(cmd)
            app.pipe.write(cmd)
            reply = app.pipe.readline()
            if reply == '0':
                print('后端出bug啦！！！')
            session['name'] = session['modified_user_info']['name']
            session['home_success_info'] = '您已成功修改个人信息'
            return redirect(url_for('home'))


@app.route('/register_send_email', methods=['POST', 'GET'])
def register_send_email():
    if request.form['password'] != request.form['repassword']:
        session['home_err_info'] = '注册时两次输入密码不匹配。'
        return redirect(url_for('home'))
    if request.form['validation_code'] != session['validate_code']:
        session['home_err_info'] = '验证码输入不匹配。'
        return redirect(url_for('home'))
    user_info = {'user_id': request.form['user_id'],
                 'name': request.form['name'],
                 'email': request.form['email'],
                 'phone': request.form['phone'],
                 'password': request.form['password']}

    session['user_to_confirm'] = user_info
    app.rand.write('10 10000007 1')
    session['email_code'] = app.rand.readline().split()[0]
    print(session['email_code'])
    app.email.send(user_info['email'],
                   'ACM 12306 火车订票系统 个人信息注册',
                   '亲爱的' + user_info['name'] + '：\n' + '您的个人信息邮箱验证码为' + session['email_code'] + '。\n' +
                   '请输入验证码完成修改，祝您旅行愉快！')
    return render_template('index.html', user_info=user_info, confirm_email=True)


@app.route('/register_confirm_email', methods=['POST'])
def register_confirm_email():
    user_email_code = request.form['email_code']

    if user_email_code != session['email_code']:
        session['home_err_info'] = '邮箱验证码输入不匹配，请重新注册。'
        return redirect(url_for('home'))
    else:
        user_info = session['user_to_confirm']
        cmd = ' '.join(['register', user_info['user_id'], user_info['name'], user_info['password'], user_info['email'],
                        user_info['phone']])
        print(cmd)  # check point
        app.pipe.write(cmd)
        reply = app.pipe.readline()

        # if user_id has been registered
        if reply == '0':
            session['home_err_info'] = '该用户名已经被注册，请更换后再试一次。'
            return redirect(url_for('home'))

        # if registration succeeds
        session['home_success_info'] = '注册成功，请您像孙恩泽一样无忧无虑地玩耍。'
        return redirect(url_for('home'))


@app.route('/query_tickets', methods=['POST', 'GET'])
def query_tickets():
    if 'user_id' in session and 'name' in session and session['name'] != '':
        name = session['name']
    else:
        name = None
    if 'privilege' in session and 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False
    if request.method == 'POST':
        # read in command
        cmd = ""
        res = request.form['departure']
        if (len(res.split()) == 0):
            res = 'hahaha594438233666'
        cmd += res + ' '
        res = request.form['destination']
        if (len(res.split()) == 0):
            res = 'hahaha594438233666'
        cmd += res + ' '
        res = request.form['date']
        if (res == ''):
            res = '2018-06-15'
        cmd += res + ' '

        cnt = int(0)
        if 'C' in request.form:
            cmd += 'C'
            cnt = cnt + 1
        if 'D' in request.form:
            cmd += 'D'
            cnt = cnt + 1
        if 'G' in request.form:
            cmd += 'G'
            cnt = cnt + 1
        if 'K' in request.form:
            cmd += 'K'
            cnt = cnt + 1
        if 'O' in request.form:
            cmd += 'O'
            cnt = cnt + 1
        if 'T' in request.form:
            cmd += 'T'
            cnt = cnt + 1
        if (cnt == 0):
            cmd += 'CDGKOT'

        if 'transfer' in request.form:
            cmd = 'query_transfer ' + cmd
        else:
            cmd = 'query_ticket ' + cmd

        print(cmd)
        # get data from backEnd
        # record seatlens because of jinja's weakness
        tickets = []
        seatlens = []

        app.pipe.write(cmd)

        ticketnum = app.pipe.readline().split()[0]
        if ticketnum == '-1' or ticketnum == '0':
            return render_template('user_query_ticket.html', name=name, is_admin=is_admin, query_err_msg='您查找的列车不存在。')
        ticketnum = int(ticketnum)
        for i in range(ticketnum):
            tickets.append(TicketInfo())
            tickets[i].read_query_ticket()
            seatlens.append(len(tickets[i].seats))
        print(tickets[0].seats[0]['seatname'])

        for i in range(len(tickets)):
            print(tickets[i].id)
            print(tickets[i].arriveDate)
            for j in range(seatlens[i]):
                print(tickets[i].seats[j]['seatname'])
                print(tickets[i].seats[j]['seatleft'])
                print(tickets[i].seats[j]['price'])
        return render_template('display_user_ticket.html', name=name, is_admin=is_admin, tickets=tickets,
                               ticketlen=len(tickets), seatlens=seatlens)
    return render_template('user_query_ticket.html', name=name, is_admin=is_admin)


@app.route(
    '/display_confirm/<train_id>/<departure>/<destination>/<leaveDate>/<leaveTime>/<arriveDate>/<arriveTime>/<seatname>/<seatleft>/<price>',
    methods=['GET', 'POST'])
def display_confirm(train_id, departure, destination, leaveDate, leaveTime, arriveDate, arriveTime, seatname, seatleft,
                    price):
    if 'user_id' in session and 'name' in session and session['name'] != '':
        username = session['name']
    else:
        session['home_err_info'] = '对不起，您还没有登陆。如果您还没有账号，请在右上角注册。'
        return redirect(url_for('home'))
    if 'privilege' in session and 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False
    return render_template('confirm_tickets.html', name=username, is_admin=is_admin, train_id=train_id,
                           departure=departure, destination=destination, leaveDate=leaveDate, leaveTime=leaveTime,
                           arriveDate=arriveDate, arriveTime=arriveTime, seatname=seatname, seatleft=seatleft,
                           price=price)


@app.route('/confirm_tickets', methods=['POST'])
def confirm_tickets():
    if 'user_id' in session and 'name' in session and session['name'] != '':
        name = session['name']
    else:
        name = None
    if 'privilege' in session and 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False
    cmd = 'buy_ticket' + ' ' + session['user_id'] + ' ' + request.form['number'] + ' ' + request.form[
        'train_id'] + ' ' + request.form['departure'] + ' ' + request.form['destination'] + ' ' + request.form[
              'leaveDate'] + ' ' + request.form['seatname']
    print(cmd)
    app.pipe.write(cmd)
    result = int(app.pipe.readline()[0])
    print(result)
    if result == 1:
        # success_info = '您的 ' + request.form['departure'] + ' 到 ' + request.form['destination'] + '的 ' + request.form['train_id'] + ' 次列车的 ' + request.form.['seatname'] + ' 已购票成功'
        session['home_success_info'] = '购票成功, 要不要考虑给女朋友也买一张?'
    else:
        session['home_err_info'] = '购票失败'
    return redirect(url_for('home'))


@app.route(
    '/display_delete/<train_id>/<departure>/<destination>/<leaveDate>/<leaveTime>/<arriveDate>/<arriveTime>/<seatname>/<seatleft>/<price>',
    methods=['GET', 'POST'])
def display_delete(train_id, departure, destination, leaveDate, leaveTime, arriveDate, arriveTime, seatname, seatleft,
                   price):
    if 'user_id' in session and 'name' in session and session['name'] != '':
        username = session['name']
    else:
        session['home_err_info'] = '对不起，您还没有登陆。如果您还没有账号，请在右上角注册。'
        return redirect(url_for('home'))
    if 'privilege' in session and 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False
    return render_template('confirm_delete.html', name=username, is_admin=is_admin, train_id=train_id,
                           departure=departure, destination=destination, leaveDate=leaveDate, leaveTime=leaveTime,
                           arriveDate=arriveDate, arriveTime=arriveTime, seatname=seatname, seatleft=seatleft,
                           price=price)


@app.route('/confirm_delete', methods=['POST'])
def confirm_delete():
    if 'user_id' in session and 'name' in session and session['name'] != '':
        name = session['name']
    else:
        name = None
    if 'privilege' in session and 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False
    cmd = 'refund_ticket' + ' ' + session['user_id'] + ' ' + request.form['number'] + ' ' + request.form[
        'train_id'] + ' ' + request.form['departure'] + ' ' + request.form['destination'] + ' ' + request.form[
              'leaveDate'] + ' ' + request.form['seatname']
    print(cmd)
    app.pipe.write(cmd)
    result = int(app.pipe.readline()[0])
    print(result)
    if result == 1:
        # success_info = '您的 ' + request.form['departure'] + ' 到 ' + request.form['destination'] + '的 ' + request.form['train_id'] + ' 次列车的 ' + request.form.['seatname'] + ' 已退票成功'
        session['home_success_info'] = '你为何要退掉女朋友的票?'
    else:
        session['home_err_info'] = '退票失败'
    return redirect(url_for('home'))


@app.route('/query_order', methods=['POST', 'GET'])
def query_order():
    if 'user_id' not in session or 'name' not in session or 'user_id' == '':
        session['home_err_info'] = '对不起，您还没有登陆。如果您还没有账号，请在右上角注册。'
        return redirect(url_for('home'))
    name = ""
    if 'user_id' in session and 'name' in session and session['name'] != '':
        name = session['name']
    if 'home_err_info' in session:
        err_info = session['home_err_info']
        session.pop('home_err_info', None)
    else:
        err_info = None
    if 'privilege' in session and 'privilege' in session and session['privilege'] != 1:
        is_admin = True
    else:
        is_admin = False

    if request.method == 'POST':
        # read in command
        cmd = ""
        cmd += session['user_id'] + ' '
        res = request.form['date']
        if (res == ''):
            res = '2018-06-15'
        cmd += res + ' '
        cnt = int(0)
        if 'C' in request.form:
            cmd += 'C'
            cnt = cnt + 1
        if 'D' in request.form:
            cmd += 'D'
            cnt = cnt + 1
        if 'G' in request.form:
            cmd += 'G'
            cnt = cnt + 1
        if 'K' in request.form:
            cmd += 'K'
            cnt = cnt + 1
        if 'O' in request.form:
            cmd += 'O'
            cnt = cnt + 1
        if 'T' in request.form:
            cmd += 'T'
            cnt = cnt + 1
        if (cnt == 0):
            cmd += 'CDGKOT'
        cmd = 'query_order ' + cmd

        print(cmd)
        # get data from backEnd
        # record seatlens because of jinja's weakness
        orders = []
        seatlens = []

        app.pipe.write(cmd)
        ticketnum = int(app.pipe.readline().split()[0])
        if ticketnum == -1 or ticketnum == 0:
            session['home_err_info'] = '您查找的车票不存在。'
            return redirect(url_for('home'))
        for i in range(ticketnum):
            orders.append(TicketInfo())
            orders[i].read_query_ticket()
            seatlens.append(len(orders[i].seats))
        print(orders[0].seats[0]['seatname'])

        for i in range(len(orders)):
            print(orders[i].id)
            print(orders[i].arriveDate)
            for j in range(seatlens[i]):
                print(orders[i].seats[j]['seatname'])
                print(orders[i].seats[j]['seatleft'])
                print(orders[i].seats[j]['price'])
        return render_template('display_user_order.html', name=name, is_admin=is_admin, orders=orders,
                               ticketlen=len(orders), seatlens=seatlens)
    return render_template('user_query_order.html', name=name, is_admin=is_admin)


@app.route('/user_buy_ticket/<train_idx>/<seat_idx>', methods=['POST'])
def user_buy_ticket(train_idx, seat_idx):
    print(train_idx)
    print(seat_idx)
    return redirect(url_for('query_order'))


@app.route('/admin', methods=['GET'])
def admin_manage_master():
    if 'action' in session:
        # pre-define variables
        go_to_add = None
        add_success_msg = None
        add_err_msg = None
        go_to_privilege = None
        user_info = None
        privilege_success_msg = None
        privilege_err_msg = None
        go_to_query = None
        train_info = None
        query_success_msg = None
        query_err_msg = None
        modify_train_mode = None

        act = session['action']
        session.pop('action', None)

        if act == 'add_train':
            go_to_add = session['go_to_add']
            session.pop('go_to_add', None)
            if 'add_success_msg' in session:
                add_success_msg = session['add_success_msg']
                session.pop('add_success_msg', None)
            if 'add_err_msg' in session:
                add_err_msg = session['add_err_msg']
                session.pop('add_err_msg', None)

        elif act == 'admin_query_user':
            go_to_privilege = session['go_to_privilege']
            session.pop('go_to_privilege', None)
            if 'user_info' in session:  # leave user_info un-popped.
                user_info = session['user_info']
            if 'privilege_err_msg' in session:
                privilege_err_msg = session['privilege_err_msg']
                session.pop('privilege_err_msg', None)

        elif act == 'en_admin_user':
            go_to_privilege = session['go_to_privilege']
            session.pop('go_to_privilege', None)
            if 'privilege_err_msg' in session:
                privilege_err_msg = session['privilege_err_msg']
                session.pop('privilege_err_msg', None)
            if 'privilege_success_msg' in session:
                privilege_success_msg = session['privilege_success_msg']
                session.pop('privilege_err_msg', None)

        # 因为傻逼类不能json传，所以他妈只能这么尴尬
        elif act == 'query_train':
            go_to_query = session['go_to_query']
            session.pop('go_to_query', None)
            train_id = session['train_id']

            cmd = ' '.join(['admin_query_train', train_id])
            print(cmd)
            app.pipe.write(cmd)

            exist = app.pipe.readline()
            print(exist)
            if exist == '0':
                query_err_msg = '您查询的列车' + train_id + '不存在，请检查后重试。'
            else:
                train_info = TrainInfo()
                sale = app.pipe.readline()
                if sale == '1':
                    train_info.sale = True
                else:
                    train_info.sale = False
                train_info.read_stdin()

        elif act == 'delete_train':
            go_to_query = session['go_to_query']
            session.pop('go_to_query', None)
            if 'query_success_msg' in session:
                query_success_msg = session['query_success_msg']
                session.pop('query_success_msg', None)
            if 'query_err_msg' in session:
                query_err_msg = session['query_err_msg']
                session.pop('query_err_msg', None)

        elif act == 'sale_train':
            go_to_query = session['go_to_query']
            session.pop('go_to_query', None)
            if 'query_success_msg' in session:
                query_success_msg = session['query_success_msg']
                session.pop('query_success_msg', None)
            if 'query_err_msg' in session:
                query_err_msg = session['query_err_msg']
                session.pop('query_err_msg', None)

        elif act == 'admin_back_continue_query_train':
            go_to_query = session['go_to_query']
            session.pop('go_to_query', None)

        elif act == 'admin_back_continue_query_user':
            go_to_privilege = session['go_to_privilege']
            session.pop('go_to_privilege', None)

        elif act == 'modify_train_post':
            go_to_query = session['go_to_query']
            session.pop('go_to_query', None)
            query_success_msg = session['query_success_msg']
            session.pop('query_success_msg', None)

        return render_template('admin_manage.html',
                               name=session['name'],
                               go_to_add=go_to_add,
                               add_success_msg=add_success_msg,
                               add_err_msg=add_err_msg,
                               go_to_privilege=go_to_privilege,
                               user_info=user_info,
                               privilege_success_msg=privilege_success_msg,
                               privilege_err_msg=privilege_err_msg,
                               go_to_query=go_to_query,
                               train_info=train_info,
                               modify_train_mode=modify_train_mode,
                               query_success_msg=query_success_msg,
                               query_err_msg=query_err_msg)
    else:
        return render_template('admin_manage.html',
                               name=session['name'],
                               go_to_add=True,
                               add_success_msg=None,
                               add_err_msg=None,
                               go_to_privilege=None,
                               user_info=None,
                               privilege_success_msg=None,
                               privilege_err_msg=None,
                               go_to_query=None,
                               train_info=None,
                               modify_train_mode=None,
                               query_success_msg=None,
                               query_err_msg=None)


@app.route('/add_train', methods=['POST'])
def add_train():
    # get all information
    train_id = request.form['id']
    name = request.form['name']
    catalog = request.form['catalog']
    seat_num = 0
    station_num = 0
    while request.form.get(str('seat' + str(seat_num + 1))):
        seat_num = seat_num + 1
    while request.form.get(str('station_name' + str(station_num + 1))):
        station_num = station_num + 1

    general_cmd = ['add_train', train_id, name, catalog, str(station_num), str(seat_num)]
    for i in range(seat_num):
        general_cmd.append(request.form.get(str('seat' + str(i + 1))))

    print(general_cmd)
    print(' '.join(general_cmd))

    app.pipe.write(' '.join(general_cmd))

    for i in range(station_num):
        station_name = request.form.get(str('station_name' + str(i + 1)))
        arrive_time = request.form.get(str('arrive_time' + str(i + 1)))
        leave_time = request.form.get(str('leave_time' + str(i + 1)))
        wait_time = request.form.get(str('wait_time' + str(i + 1)))
        if i == 0:
            arrive_time = 'xx:xx'
            wait_time = 'xx:xx'
        elif i == station_num - 1:
            wait_time = 'xx:xx'
        station_cmd = [station_name, arrive_time, leave_time, wait_time]
        for j in range(seat_num):
            price = str('￥' + request.form.get(str('price' + str(j + 1) + str(i + 1))))
            station_cmd.append(price)
        print(station_cmd)
        print(' '.join(station_cmd))
        app.pipe.write(' '.join(station_cmd))

    reply = app.pipe.readline()
    if reply == '0':
        session['add_err_msg'] = '该列车ID' + train_id + '已经存在。请检查输入是否正确，或前往修改该列车的信息。'
    else:
        session['add_success_msg'] = '添加列车' + train_id + '成功。'

    session['action'] = 'add_train'
    session['go_to_add'] = True
    return redirect(url_for('admin_manage_master'))


@app.route('/admin_query_train', methods=['POST'])
def admin_query_train():
    train_id = request.form['admin_query_train_id']
    session['train_id'] = train_id
    session['action'] = 'query_train'
    session['go_to_query'] = True
    return redirect(url_for('admin_manage_master'))


@app.route('/sale_train', methods=['GET'])
def sale_train():
    session['action'] = 'sale_train'
    session['go_to_query'] = True
    train_id = session['train_id']
    session.pop('train_id', None)

    cmd = ' '.join(['sale_train', train_id])
    print(cmd)
    app.pipe.write(cmd)
    reply = app.pipe.readline()
    if reply == '1':
        session['query_success_msg'] = '列车' + train_id + '已经成功发售'
    else:
        print('后端出错啦！！！')
    return redirect(url_for('admin_manage_master'))


@app.route('/del_train', methods=['GET'])
def del_train():
    session['action'] = 'sale_train'
    session['go_to_query'] = True
    train_id = session['train_id']
    session.pop('train_id', None)

    cmd = ' '.join(['delete_train', train_id])
    print(cmd)
    app.pipe.write(cmd)
    reply = app.pipe.readline()
    if reply == '1':
        session['query_success_msg'] = '列车' + train_id + '已经成功删除'
    else:
        print('后端出错啦！！！')
    return redirect(url_for('admin_manage_master'))


@app.route('/admin_back_continue_query_train', methods=['GET'])
def admin_back_continue_query_train():
    session['action'] = 'admin_back_continue_query_train'
    session.pop('train_id', None)
    session['go_to_query'] = True
    return redirect(url_for('admin_manage_master'))


@app.route('/admin_query_user', methods=['POST'])
def admin_query_user():
    session['action'] = 'admin_query_user'
    session['go_to_privilege'] = True

    user_id = request.form['admin_query_user_id']
    cmd = ' '.join(['query_profile', user_id])
    app.pipe.write(cmd)
    reply = app.pipe.readline()
    if reply == '0':
        session['privilege_err_msg'] = '您查找的用户' + user_id + '不存在，请检查后再试。'
    else:
        reply = reply.split(' ')
        session['user_info'] = {'user_id': reply[0],
                                'name': reply[1],
                                'password': reply[2],
                                'email': reply[3],
                                'phone': reply[4],
                                'is_admin': (int(reply[5]) > 1)
                                }
    return redirect(url_for('admin_manage_master'))


@app.route('/en_admin_user', methods=['GET'])
def en_admin_user():
    session['action'] = 'en_admin_user'
    session['go_to_privilege'] = True

    admin = session['user_id']
    searched_user = session['user_info']
    session.pop('user_info', None)
    cmd = ' '.join(['modify_privilege', admin, searched_user['user_id'], str(2)])
    app.pipe.write(cmd)
    reply = app.pipe.readline()
    if reply == '0':
        print('后端出错啦！！！')
    session['privilege_success_msg'] = '您已成功将' + searched_user['name'] + '升级为管理员。'
    return redirect(url_for('admin_manage_master'))


@app.route('/admin_back_continue_query_user')
def admin_back_continue_query_user():
    session['action'] = 'admin_back_continue_query_user'
    session.pop('user_info', None)
    session['go_to_privilege'] = True
    return redirect(url_for('admin_manage_master'))


@app.route('/modify_train', methods=['GET', 'POST'])
def modify_train():
    if request.method == 'GET':
        train_id = session['train_id']
        cmd = ' '.join(['admin_query_train', train_id])
        app.pipe.write(cmd)

        exist = app.pipe.readline()
        train_info = TrainInfo()
        sale = app.pipe.readline()
        if sale == '1':
            train_info.sale = True
        else:
            train_info.sale = False
        train_info.read_stdin()
        return render_template('admin_modify_train.html', train_info=train_info)
    else:
        train_id = request.form['id']
        session.pop('train_id', None)
        name = request.form['name']
        catalog = request.form['catalog']
        seat_num = 0
        station_num = 0
        while request.form.get(str('seat' + str(seat_num + 1))):
            seat_num = seat_num + 1
        while request.form.get(str('station_name' + str(station_num + 1))):
            station_num = station_num + 1

        general_cmd = ['modify_train', train_id, name, catalog, str(station_num), str(seat_num)]
        for i in range(seat_num):
            general_cmd.append(request.form.get(str('seat' + str(i + 1))))

        print(general_cmd)
        print(' '.join(general_cmd))

        app.pipe.write(' '.join(general_cmd))

        for i in range(station_num):
            station_name = request.form.get(str('station_name' + str(i + 1)))
            arrive_time = request.form.get(str('arrive_time' + str(i + 1)))
            leave_time = request.form.get(str('leave_time' + str(i + 1)))
            wait_time = request.form.get(str('wait_time' + str(i + 1)))
            if i == 0:
                arrive_time = 'xx:xx'
                wait_time = 'xx:xx'
            elif i == station_num - 1:
                wait_time = 'xx:xx'
            station_cmd = [station_name, arrive_time, leave_time, wait_time]
            for j in range(seat_num):
                price = str('￥' + request.form.get(str('price' + str(j + 1) + str(i + 1))))
                station_cmd.append(price)
            print(station_cmd)
            print(' '.join(station_cmd))
            app.pipe.write(' '.join(station_cmd))

        reply = app.pipe.readline()
        if reply == '0':
            print('后端出bug啦！！！')
        else:
            session['add_success_msg'] = '修改列车' + train_id + '成功。'

        session['action'] = 'modify_train_post'
        session['go_to_query'] = True
        session['query_success_msg'] = '您已成功修改列车' + train_id + '。'
        return redirect(url_for('admin_manage_master'))


@app.route('/clean', methods=['POST'])
def clean():
    if 'user_id' not in session or 'name' not in session:
        session['home_err_info'] = '对不起，您还没有登陆。如果您还没有账号，请在右上角注册。'
        return redirect(url_for('home'))
    if request.form['password'] != request.form['repassword']:
        session['home_err_info'] = '危险操作：重置数据库密码验证失败，密码输入不匹配。'
        return redirect(url_for('home'))

    cmd = ' '.join(['query_profile', session['user_id']])
    app.pipe.write(cmd)
    reply = app.pipe.readline()
    reply = reply.split(' ')
    if request.form['password'] != reply[2]:
        session['home_err_info'] = '危险操作：重置数据库密码验证失败，密码输入错误。'
        return redirect(url_for('home'))
    cmd = 'clean'
    app.pipe.write(cmd)
    app.pipe.readline()
    session['home_success_info'] = '已成功重置系统'
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
