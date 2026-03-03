from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from functools import wraps
import sqlite3
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'kondee_secret_key_2024'

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'kondee.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    #хэширование пароля
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    #инициализация бд и создание таблиц
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            fio       TEXT NOT NULL,
            phone     TEXT NOT NULL,
            login     TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            role      TEXT NOT NULL CHECK(role IN (
                'Администратор', 'Менеджер', 'Оператор', 'Специалист', 'Заказчик'
            ))
        );

        CREATE TABLE IF NOT EXISTS requests (
            request_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date          TEXT NOT NULL,
            climate_tech_type   TEXT NOT NULL,
            climate_tech_model  TEXT NOT NULL,
            problem_description TEXT NOT NULL,
            request_status      TEXT NOT NULL DEFAULT 'Новая заявка' CHECK(request_status IN (
                'Новая заявка', 'В процессе ремонта',
                'Ожидание комплектующих', 'Готова к выдаче', 'Завершена'
            )),
            completion_date TEXT,
            repair_parts    TEXT,
            master_id       INTEGER REFERENCES users(user_id),
            client_id       INTEGER NOT NULL REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            message    TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            master_id  INTEGER NOT NULL REFERENCES users(user_id),
            request_id INTEGER NOT NULL REFERENCES requests(request_id)
        );
    ''')

    user_count = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    if user_count == 0:
        _import_initial_data(cursor)

    conn.commit()
    conn.close()


def _import_initial_data(cursor):
    users = [
        ('Широков Василий Матвеевич',        '89210563128', 'login1',  'pass1',  'Менеджер'),
        ('Кудрявцева Ева Ивановна',           '89535078985', 'login2',  'pass2',  'Специалист'),
        ('Гончарова Ульяна Ярославовна',      '89210673849', 'login3',  'pass3',  'Специалист'),
        ('Гусева Виктория Данииловна',        '89990563748', 'login4',  'pass4',  'Оператор'),
        ('Баранов Артём Юрьевич',             '89994563847', 'login5',  'pass5',  'Оператор'),
        ('Овчинников Фёдор Никитич',          '89219567849', 'login6',  'pass6',  'Заказчик'),
        ('Петров Никита Артёмович',           '89219567841', 'login7',  'pass7',  'Заказчик'),
        ('Ковалева Софья Владимировна',       '89219567842', 'login8',  'pass8',  'Заказчик'),
        ('Кузнецов Сергей Матвеевич',         '89219567843', 'login9',  'pass9',  'Заказчик'),
        ('Беспалова Екатерина Даниэльевна',   '89219567844', 'login10', 'pass10', 'Специалист'),
        ('Администратор Системы',             '00000000000', 'admin',   'admin',  'Администратор'),
    ]
    for fio, phone, login, password, role in users:
        cursor.execute(
            'INSERT INTO users (fio, phone, login, password, role) VALUES (?,?,?,?,?)',
            (fio, phone, login, hash_password(password), role)
        )

    requests_data = [
        (1, '2023-06-06', 'Кондиционер',         'TCL TAC-12CHSA/TPG-W белый',
         'Не охлаждает воздух', 'В процессе ремонта', None, None, 2, 7),
        (2, '2023-05-05', 'Кондиционер',         'Electrolux EACS/I-09HAT/N3_21Y белый',
         'Выключается сам по себе', 'В процессе ремонта', None, None, 3, 8),
        (3, '2022-07-07', 'Увлажнитель воздуха', 'Xiaomi Smart Humidifier 2',
         'Пар имеет неприятный запах', 'Готова к выдаче', '2023-01-01', None, 3, 9),
        (4, '2023-08-02', 'Увлажнитель воздуха', 'Polaris PUH 2300 WIFI IQ Home',
         'Увлажнитель воздуха продолжает работать при предельном снижении уровня воды',
         'Новая заявка', None, None, None, 8),
        (5, '2023-08-02', 'Сушилка для рук',     'Ballu BAHD-1250',
         'Не работает', 'Новая заявка', None, None, None, 9),
    ]
    for r in requests_data:
        cursor.execute(
            '''INSERT INTO requests
               (request_id, start_date, climate_tech_type, climate_tech_model,
                problem_description, request_status, completion_date, repair_parts,
                master_id, client_id)
               VALUES (?,?,?,?,?,?,?,?,?,?)''', r
        )

    comments_data = [
        (1, 'Всё сделаем!',      2, 1),
        (2, 'Всё сделаем!',      3, 2),
        (3, 'Починим в момент.', 3, 3),
    ]
    for c in comments_data:
        cursor.execute(
            'INSERT INTO comments (comment_id, message, master_id, request_id) VALUES (?,?,?,?)', c
        )

def login_required(f):
#переадресация на странциу входа
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get('role') not in roles:
                flash('У вас недостаточно прав для выполнения этого действия.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Авторизация
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password  = request.form.get('password', '').strip()

        if not login_val or not password:
            flash('Введите логин и пароль.', 'error')
            return render_template('login.html')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE login = ? AND password = ?',
            (login_val, hash_password(password))
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['fio']     = user['fio']
            session['role']    = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль. Проверьте введённые данные и попробуйте снова.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Главная страница и список заявок
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    role = session['role']
    user_id = session['user_id']

    search = request.args.get('search', '').strip()
    filter_status = request.args.get('status', '').strip()

    query = '''
        SELECT r.*,
               u_client.fio AS client_fio,
               u_master.fio AS master_fio
        FROM requests r
        JOIN  users u_client ON r.client_id  = u_client.user_id
        LEFT JOIN users u_master ON r.master_id = u_master.user_id
        WHERE 1=1
    '''
    params = []

    if role == 'Заказчик':
        query += ' AND r.client_id = ?'
        params.append(user_id)
    elif role == 'Специалист':
        query += ' AND r.master_id = ?'
        params.append(user_id)

    if search:
        like = f'%{search}%'
        query += ''' AND (
            CAST(r.request_id AS TEXT) LIKE ? OR
            r.climate_tech_model       LIKE ? OR
            r.climate_tech_type        LIKE ? OR
            u_client.fio               LIKE ?
        )'''
        params.extend([like, like, like, like])

    if filter_status:
        query += ' AND r.request_status = ?'
        params.append(filter_status)

    query += ' ORDER BY r.start_date DESC'

    requests_list = conn.execute(query, params).fetchall()
    conn.close()

    statuses = [
        'Новая заявка', 'В процессе ремонта',
        'Ожидание комплектующих', 'Готова к выдаче', 'Завершена'
    ]
    return render_template(
        'dashboard.html',
        requests=requests_list,
        statuses=statuses,
        search=search,
        selected_status=filter_status
    )

# Заявки
@app.route('/requests/new', methods=['GET', 'POST'])
@login_required
@role_required('Оператор', 'Администратор', 'Заказчик')
def request_new():
    conn = get_db()

    if request.method == 'POST':
        climate_type = request.form.get('climate_tech_type', '').strip()
        model = request.form.get('climate_tech_model', '').strip()
        problem = request.form.get('problem_description', '').strip()
        client_id = request.form.get('client_id', '').strip()

        if session['role'] == 'Заказчик':
            client_id = str(session['user_id'])

        errors = []
        if not climate_type: errors.append('Укажите тип оборудования.')
        if not model: errors.append('Укажите модель устройства.')
        if not problem: errors.append('Опишите проблему.')
        if not client_id: errors.append('Выберите заказчика.')

        if errors:
            clients = conn.execute("SELECT * FROM users WHERE role = 'Заказчик'").fetchall()
            conn.close()
            for e in errors:
                flash(e, 'error')
            return render_template('request_form.html', clients=clients, form=request.form)

        conn.execute(
            '''INSERT INTO requests
               (start_date, climate_tech_type, climate_tech_model, problem_description, client_id)
               VALUES (?, ?, ?, ?, ?)''',
            (datetime.now().strftime('%Y-%m-%d'), climate_type, model, problem, client_id)
        )
        conn.commit()
        conn.close()
        flash('Заявка успешно создана.', 'success')
        return redirect(url_for('dashboard'))

    clients = conn.execute("SELECT * FROM users WHERE role = 'Заказчик'").fetchall()
    conn.close()
    return render_template('request_form.html', clients=clients, form={})


@app.route('/requests/<int:request_id>')
@login_required
def request_detail(request_id):
    conn = get_db()
    req = conn.execute(
        '''SELECT r.*,
                  u_client.fio   AS client_fio,
                  u_client.phone AS client_phone,
                  u_master.fio   AS master_fio
           FROM requests r
           JOIN  users u_client ON r.client_id  = u_client.user_id
           LEFT JOIN users u_master ON r.master_id = u_master.user_id
           WHERE r.request_id = ?''',
        (request_id,)
    ).fetchone()

    if not req:
        conn.close()
        flash('Заявка с указанным номером не найдена.', 'error')
        return redirect(url_for('dashboard'))

    comments = conn.execute(
        '''SELECT c.*, u.fio AS author_fio
           FROM comments c
           JOIN users u ON c.master_id = u.user_id
           WHERE c.request_id = ?
           ORDER BY c.created_at''',
        (request_id,)
    ).fetchall()

    conn.close()
    return render_template('request_detail.html', req=req, comments=comments)


@app.route('/requests/<int:request_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Оператор', 'Администратор', 'Менеджер')
def request_edit(request_id):
    conn = get_db()
    req = conn.execute('SELECT * FROM requests WHERE request_id = ?', (request_id,)).fetchone()

    if not req:
        conn.close()
        flash('Заявка с указанным номером не найдена.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        status = request.form.get('request_status', '').strip()
        problem = request.form.get('problem_description', '').strip()
        master_id = request.form.get('master_id') or None
        repair_parts = request.form.get('repair_parts', '').strip()

        completion_date = req['completion_date']
        if status == 'Завершена' and not completion_date:
            completion_date = datetime.now().strftime('%Y-%m-%d')

        conn.execute(
            '''UPDATE requests
               SET request_status      = ?,
                   problem_description = ?,
                   master_id           = ?,
                   repair_parts        = ?,
                   completion_date     = ?
               WHERE request_id = ?''',
            (status, problem, master_id, repair_parts, completion_date, request_id)
        )
        conn.commit()
        conn.close()
        flash('Заявка успешно обновлена.', 'success')
        return redirect(url_for('request_detail', request_id=request_id))

    specialists = conn.execute(
        "SELECT * FROM users WHERE role IN ('Специалист', 'Менеджер')"
    ).fetchall()
    statuses = [
        'Новая заявка', 'В процессе ремонта',
        'Ожидание комплектующих', 'Готова к выдаче', 'Завершена'
    ]
    conn.close()
    return render_template(
        'request_edit.html', req=req,
        specialists=specialists, statuses=statuses
    )


@app.route('/requests/<int:request_id>/delete', methods=['POST'])
@login_required
@role_required('Администратор')
def request_delete(request_id):
    conn = get_db()
    conn.execute('DELETE FROM comments WHERE request_id = ?', (request_id,))
    conn.execute('DELETE FROM requests WHERE request_id = ?', (request_id,))
    conn.commit()
    conn.close()
    flash('Заявка удалена.', 'success')
    return redirect(url_for('dashboard'))


# Комментарии
@app.route('/requests/<int:request_id>/comment', methods=['POST'])
@login_required
@role_required('Специалист', 'Менеджер', 'Администратор', 'Оператор')
def add_comment(request_id):
    message = request.form.get('message', '').strip()

    if not message:
        flash('Текст комментария не может быть пустым.', 'error')
        return redirect(url_for('request_detail', request_id=request_id))

    conn = get_db()
    conn.execute(
        'INSERT INTO comments (message, created_at, master_id, request_id) VALUES (?, ?, ?, ?)',
        (message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), session['user_id'], request_id)
    )
    conn.commit()
    conn.close()
    flash('Комментарий добавлен.', 'success')
    return redirect(url_for('request_detail', request_id=request_id))


# Статистика
@app.route('/statistics')
@login_required
@role_required('Администратор', 'Менеджер', 'Оператор')
def statistics():
    conn = get_db()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    where = 'WHERE 1=1'
    params = []
    if date_from:
        where += ' AND start_date >= ?'
        params.append(date_from)
    if date_to:
        where += ' AND start_date <= ?'
        params.append(date_to)

    total = conn.execute(
        f'SELECT COUNT(*) FROM requests {where}', params
    ).fetchone()[0]

    completed = conn.execute(
        f"SELECT COUNT(*) FROM requests {where} AND request_status = 'Завершена'", params
    ).fetchone()[0]

    avg_row = conn.execute(
        f'''SELECT AVG(julianday(completion_date) - julianday(start_date))
            FROM requests {where}
            AND completion_date IS NOT NULL
            AND request_status = 'Завершена' ''',
        params
    ).fetchone()[0]
    avg_time = round(avg_row, 1) if avg_row else None

    status_stats = conn.execute(
        f'''SELECT request_status, COUNT(*) AS cnt
            FROM requests {where}
            GROUP BY request_status''',
        params
    ).fetchall()

    type_stats = conn.execute(
        f'''SELECT climate_tech_type, COUNT(*) AS cnt
            FROM requests {where}
            GROUP BY climate_tech_type
            ORDER BY cnt DESC''',
        params
    ).fetchall()

    conn.close()
    return render_template(
        'statistics.html',
        total=total, completed=completed, avg_time=avg_time,
        status_stats=status_stats, type_stats=type_stats,
        date_from=date_from, date_to=date_to
    )


# Управление пользователями
@app.route('/users')
@login_required
@role_required('Администратор')
def users_list():
    conn  = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY role, fio').fetchall()
    conn.close()
    return render_template('users_list.html', users=users)


@app.route('/users/new', methods=['GET', 'POST'])
@login_required
@role_required('Администратор')
def user_new():
    if request.method == 'POST':
        fio = request.form.get('fio', '').strip()
        phone = request.form.get('phone', '').strip()
        login_v = request.form.get('login', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip()

        errors = []
        if not fio: errors.append('Введите ФИО.')
        if not phone: errors.append('Введите номер телефона.')
        if not login_v: errors.append('Введите логин.')
        if not password: errors.append('Введите пароль.')
        if not role: errors.append('Выберите роль.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('user_form.html', form=request.form)

        conn = get_db()
        existing = conn.execute(
            'SELECT user_id FROM users WHERE login = ?', (login_v,)
        ).fetchone()

        if existing:
            conn.close()
            flash('Пользователь с таким логином уже существует. Выберите другой логин.', 'error')
            return render_template('user_form.html', form=request.form)

        conn.execute(
            'INSERT INTO users (fio, phone, login, password, role) VALUES (?,?,?,?,?)',
            (fio, phone, login_v, hash_password(password), role)
        )
        conn.commit()
        conn.close()
        flash('Пользователь успешно создан.', 'success')
        return redirect(url_for('users_list'))

    return render_template('user_form.html', form={})


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('Администратор')
def user_delete(user_id):
    if user_id == session['user_id']:
        flash('Нельзя удалить собственную учётную запись.', 'error')
        return redirect(url_for('users_list'))

    conn = get_db()
    conn.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('Пользователь удалён.', 'success')
    return redirect(url_for('users_list'))

@app.route('/qr')
@login_required
def qr_page():
    return render_template('qr.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)