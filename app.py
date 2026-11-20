import psycopg2
from psycopg2 import IntegrityError
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'cinematrix_local_key_2026'

# Подставь сюда свой пароль от базы Supabase (и лучше смени старый в настройках Supabase)
DATABASE_URL = "postgresql://postgres.ymfqhmkayggfryhvwpev:e1Qi6p9M3Lo@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"


def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def log_visit(action: str, username: str | None = None, email: str | None = None):
    user = username or session.get('username') or 'гость'
    user_email = email or session.get('email') or '-'
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '')[:180]
    path = request.path

    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO visit_logs (username, email, action, path, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user, user_email, action, path, ip, ua),
                )
    finally:
        conn.close()


def init_db():
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS movies (
                    movie_id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    genre TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    age_rating TEXT NOT NULL,
                    description TEXT
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS halls (
                    hall_id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    hall_type TEXT NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id SERIAL PRIMARY KEY,
                    movie_id INTEGER NOT NULL REFERENCES movies(movie_id),
                    hall_id INTEGER NOT NULL REFERENCES halls(hall_id),
                    start_time TEXT NOT NULL,
                    base_price REAL NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id SERIAL PRIMARY KEY,
                    session_id INTEGER NOT NULL REFERENCES sessions(session_id),
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    row_number INTEGER NOT NULL,
                    seat_number INTEGER NOT NULL
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS visit_logs (
                    log_id SERIAL PRIMARY KEY,
                    username TEXT,
                    email TEXT,
                    action TEXT NOT NULL,
                    path TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cur.execute("SELECT COUNT(*) AS cnt FROM movies")
            if cur.fetchone()['cnt'] == 0:
                movies_data = [
                    ('Дюна: Часть вторая', 'Фантастика', 166, '16+', 'Пол Атрейдес объединяется с фрименами, чтобы отомстить заговорщикам.'),
                    ('Оппенгеймер', 'Драма', 180, '18+', 'История жизни физика Роберта Оппенгеймера и создания ядерной бомбы.'),
                    ('Интерстеллар', 'Фантастика', 169, '12+', 'Команда исследователей отправляется сквозь червоточину в космосе.'),
                    ('Джон Уик 4', 'Боевик', 169, '18+', 'Легендарный наемник продолжает войну против Правления Кланов.'),
                    ('Заклятие', 'Ужасы', 112, '16+', 'Паранормальные исследователи Эд и Лоррейн Уоррен помогают семье.'),
                    ('Аватар: Путь воды', 'Фантастика', 192, '12+', 'История семьи Джейка Салли и их борьба за выживание на Пандоре.'),
                    ('Титаник', 'Романтика', 194, '16+', 'Любовь бедного художника и аристократки на борту злополучного лайнера.'),
                    ('Мальчишник в Вегасе', 'Комедия', 100, '18+', 'Друзья просыпаются в Вегасе после мальчишника и ничего не помнят.'),
                    ('Начало', 'Триллер', 148, '12+', 'Кража секретов из подсознания через внедрение снов.'),
                    ('Побег из Шоушенка', 'Драма', 142, '16+', 'История банкира, обвинцаемого в убийстве, в суровой тюрьме.'),
                    ('Мстители: Финал', 'Боевик', 181, '16+', 'Оставшиеся в живых супергерои пытаются победить Таноса.'),
                    ('Оно', 'Ужасы', 135, '18+', 'Подростки из небольшого городка сталкиваются с древним злом.'),
                    ('Ла-Ла Ленд', 'Романтика', 128, '12+', 'История любви джазового пианиста и начинающей актрисы.'),
                    ('Форсаж 10', 'Боевик', 141, '16+', 'Доминик Торетто и его семья противостоят новому опасному врагу.'),
                    ('Один дома', 'Комедия', 103, '0+', 'Маленького мальчика случайно забывают дома на рождественские каникулы.'),
                    ('Гладиатор', 'Драма', 155, '18+', 'Римский полководец становится гладиатором ради мести императору.'),
                    ('Индиана Джонс и колесо судьбы', 'Приключения', 154, '16+', 'Археолог отправляется в новое эпическое путешествие.'),
                    ('Человек-паук: Паутина вселенных', 'Фантастика', 140, '6+', 'Многочисленные версии Паука-человека сражаются в мультивселенной.'),
                    ('Паразиты', 'Триллер', 132, '18+', 'Бедная семья хитростью устраивается на работу к богачам.'),
                    ('Зверополис', 'Комедия', 108, '6+', 'Кролик-полицейский и лис-мошенник расследуют загадочное дело.')
                ]
                cur.executemany(
                    "INSERT INTO movies (title, genre, duration_minutes, age_rating, description) VALUES (%s, %s, %s, %s, %s)",
                    movies_data
                )

                cur.executemany("INSERT INTO halls (name, hall_type) VALUES (%s, %s)", [
                    ('Зал №1 IMAX', 'IMAX 3D'),
                    ('Зал №2 Стандарт', '2D'),
                    ('Зал №3 VIP', 'Dolby Atmos')
                ])

                sessions_data = [
                    (1, 1, '2026-11-20 19:00', 2500),
                    (2, 2, '2026-11-20 21:30', 1800),
                    (3, 1, '2026-11-21 18:00', 2200),
                    (4, 3, '2026-11-21 21:00', 3000),
                    (5, 2, '2026-11-22 20:00', 1700),
                    (6, 1, '2026-11-22 15:00', 2600),
                    (7, 2, '2026-11-23 18:30', 1900),
                    (8, 2, '2026-11-23 21:00', 1600),
                    (9, 1, '2026-11-24 19:00', 2400),
                    (10, 2, '2026-11-24 17:00', 1800),
                    (11, 1, '2026-11-25 18:00', 2800),
                    (12, 2, '2026-11-25 22:00', 1700),
                    (13, 2, '2026-11-26 19:30', 1900),
                    (14, 3, '2026-11-26 21:30', 3100),
                    (15, 2, '2026-11-27 16:00', 1500)
                ]
                cur.executemany(
                    "INSERT INTO sessions (movie_id, hall_id, start_time, base_price) VALUES (%s, %s, %s, %s)",
                    sessions_data
                )

                cur.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    ('admin', 'admin@mail.ru', '1234')
                )
    conn.close()


@app.route('/')
def index():
    log_visit('открыл афишу')
    search_query = request.args.get('q', '').strip()
    conn = get_db()

    sql = '''
        SELECT s.session_id, m.title, m.genre, m.duration_minutes, m.age_rating, m.description,
               h.name as hall_name, h.hall_type, s.start_time, s.base_price
        FROM sessions s
        JOIN movies m ON s.movie_id = m.movie_id
        JOIN halls h ON s.hall_id = h.hall_id
        WHERE 1=1
    '''
    params = []
    if search_query:
        sql += " AND LOWER(m.title) LIKE %s"
        params.append(f"%{search_query.lower()}%")

    sql += " ORDER BY s.start_time ASC"

    with conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            raw_sessions = cur.fetchall()

            sessions = []
            for s in raw_sessions:
                cur.execute(
                    "SELECT row_number, seat_number FROM tickets WHERE session_id = %s",
                    (s['session_id'],)
                )
                booked = cur.fetchall()
                booked_set = {f"{b['row_number']}-{b['seat_number']}" for b in booked}
                s_dict = dict(s)
                s_dict['booked'] = booked_set
                sessions.append(s_dict)

            my_tickets = []
            if 'user_id' in session:
                cur.execute('''
                    SELECT t.ticket_id, m.title, h.name as hall_name, s.start_time, t.row_number, t.seat_number, s.base_price
                    FROM tickets t
                    JOIN sessions s ON t.session_id = s.session_id
                    JOIN movies m ON s.movie_id = m.movie_id
                    JOIN halls h ON s.hall_id = h.hall_id
                    WHERE t.user_id = %s
                    ORDER BY t.ticket_id DESC
                ''', (session['user_id'],))
                my_tickets = cur.fetchall()

    conn.close()
    return render_template('index.html', sessions=sessions, my_tickets=my_tickets, search_query=search_query)


@app.route('/movies')
def movies_page():
    log_visit('открыл каталог фильмов')
    selected_genre = request.args.get('genre', 'Все')
    search_query = request.args.get('q', '').strip()

    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT genre FROM movies")
            genres_rows = cur.fetchall()
            genres = ['Все'] + [row['genre'] for row in genres_rows]

            sql = "SELECT * FROM movies WHERE 1=1"
            params = []

            if selected_genre and selected_genre != 'Все':
                sql += " AND genre = %s"
                params.append(selected_genre)

            if search_query:
                sql += " AND LOWER(title) LIKE %s"
                params.append(f"%{search_query.lower()}%")

            sql += " ORDER BY title ASC"
            cur.execute(sql, params)
            movies = cur.fetchall()

    conn.close()
    return render_template('movies.html', movies=movies, genres=genres, selected_genre=selected_genre, search_query=search_query)


@app.route('/buy', methods=['POST'])
def buy_ticket():
    if 'user_id' not in session:
        log_visit('попытка купить билет без входа')
        flash('Для покупки билета необходимо войти в аккаунт.')
        return redirect(url_for('login'))

    session_id = request.form['session_id']
    row_num = request.form['row_number']
    seat_num = request.form['seat_number']
    user_id = session['user_id']

    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM tickets WHERE session_id = %s AND row_number = %s AND seat_number = %s",
                (session_id, row_num, seat_num)
            )
            exists = cur.fetchone()

            if exists:
                flash('Это место уже занято!')
            else:
                cur.execute(
                    "INSERT INTO tickets (session_id, user_id, row_number, seat_number) VALUES (%s, %s, %s, %s)",
                    (session_id, user_id, row_num, seat_num)
                )
                log_visit(f'купил билет: ряд {row_num}, место {seat_num} (сеанс {session_id})')
                flash(f'Билет успешно оформлен: Ряд {row_num}, Место {seat_num}.')

    conn.close()
    return redirect(url_for('index'))


@app.route('/cancel/<int:ticket_id>', methods=['POST'])
def cancel_ticket(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tickets WHERE ticket_id = %s AND user_id = %s", (ticket_id, session['user_id']))
    conn.close()

    log_visit(f'отменил бронь билета #{ticket_id}')
    flash('Бронь отменена, место снова свободно.')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                        (username, email, password)
                    )
            log_visit('регистрация нового аккаунта', username=username, email=email)
            flash('Аккаунт создан! Теперь выполните вход.')
            return redirect(url_for('login'))
        except IntegrityError:
            flash('Этот Email уже зарегистрирован.')
        finally:
            conn.close()

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
                user = cur.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['email'] = user['email']
            log_visit('вошёл в аккаунт', username=user['username'], email=user['email'])
            return redirect(url_for('index'))
        else:
            log_visit('неудачная попытка входа', email=email)
            flash('Неверный email или пароль.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    log_visit('вышел из аккаунта')
    session.clear()
    return redirect(url_for('index'))


@app.route('/database')
def db_view():
    log_visit('открыл просмотр базы')
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            cur.execute("SELECT * FROM movies")
            movies = cur.fetchall()

            cur.execute("SELECT * FROM halls")
            halls = cur.fetchall()

            cur.execute("SELECT * FROM sessions")
            sessions = cur.fetchall()

            cur.execute('''
                SELECT t.ticket_id, u.username, m.title, s.start_time, t.row_number, t.seat_number
                FROM tickets t
                JOIN users u ON t.user_id = u.user_id
                JOIN sessions s ON t.session_id = s.session_id
                JOIN movies m ON s.movie_id = m.movie_id
            ''')
            tickets = cur.fetchall()

            cur.execute("SELECT * FROM visit_logs ORDER BY visited_at DESC LIMIT 100")
            logs = cur.fetchall()

    conn.close()
    return render_template(
        'db_view.html',
        users=users,
        movies=movies,
        halls=halls,
        sessions=sessions,
        tickets=tickets,
        logs=logs
    )


if __name__ == '__main__':
    init_db()
    app.run(debug=True)