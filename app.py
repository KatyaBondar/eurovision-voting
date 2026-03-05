import streamlit as st
import sqlite3
import pandas as pd
import hashlib

# Налаштування сторінки
st.set_page_config(page_title="Голосування Євробачення", layout="wide")

# Функція для хешування пароля
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Функція для підключення до БД
def get_db_connection():
    conn = sqlite3.connect('voting.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ініціалізація БД
def init_db():
    conn = get_db_connection()

    # Таблиця експертів
    conn.execute('''
        CREATE TABLE IF NOT EXISTS experts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблиця пісень (без поля image_url)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL
        )
    ''')

    # Таблиця голосів
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expert_id INTEGER UNIQUE NOT NULL,
            first_choice INTEGER,
            second_choice INTEGER,
            third_choice INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (expert_id) REFERENCES experts(id),
            FOREIGN KEY (first_choice) REFERENCES songs(id),
            FOREIGN KEY (second_choice) REFERENCES songs(id),
            FOREIGN KEY (third_choice) REFERENCES songs(id)
        )
    ''')

    # Додаємо пісні (тільки європейські виконавці)
    cursor = conn.execute("SELECT COUNT(*) FROM songs")
    if cursor.fetchone()[0] == 0:
        songs = [
            ("Waterloo", "ABBA (Швеція)"),
            ("Ne partez pas sans moi", "Céline Dion (Швейцарія)"),
            ("Hold Me Now", "Johnny Logan (Ірландія)"),
            ("Euphoria", "Loreen (Швеція)"),
            ("Fairytale", "Alexander Rybak (Норвегія)"),
            ("Wild Dances", "Ruslana (Україна)"),
            ("My Number One", "Helena Paparizou (Греція)"),
            ("Hard Rock Hallelujah", "Lordi (Фінляндія)"),
            ("Molitva", "Marija Šerifović (Сербія)"),
            ("Satellite", "Lena (Німеччина)"),
            ("Running Scared", "Ell & Nikki (Азербайджан)"),
            ("Only Teardrops", "Emmelie de Forest (Данія)"),
            ("Rise Like a Phoenix", "Conchita Wurst (Австрія)"),
            ("Heroes", "Måns Zelmerlöw (Швеція)"),
            ("1944", "Jamala (Україна)"),
            ("Amar pelos dois", "Salvador Sobral (Португалія)"),
            ("Toy", "Netta (Ізраїль)"),
            ("Arcade", "Duncan Laurence (Нідерланди)"),
            ("Zitti e buoni", "Måneskin (Італія)"),
            ("Fuego", "Eleni Foureira (Кіпр)")
        ]
        for title, artist in songs:
            conn.execute("INSERT INTO songs (title, artist) VALUES (?, ?)",
                         (title, artist))
        conn.commit()
    conn.close()

init_db()

# Функція автентифікації
def authenticate(username, password):
    conn = get_db_connection()
    expert = conn.execute("SELECT * FROM experts WHERE username = ?", (username,)).fetchone()
    conn.close()
    if expert and expert['password_hash'] == hash_password(password):
        return dict(expert)
    return None

# Функція реєстрації нового експерта
def register_user(username, password, full_name):
    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM experts WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return False, "Користувач з таким логіном вже існує"
    try:
        conn.execute("INSERT INTO experts (username, password_hash, full_name) VALUES (?, ?, ?)",
                     (username, hash_password(password), full_name))
        conn.commit()
        conn.close()
        return True, "Реєстрація успішна"
    except Exception as e:
        conn.close()
        return False, str(e)

# Завантажуємо пісні
def load_songs():
    conn = get_db_connection()
    songs = conn.execute("SELECT id, title, artist FROM songs").fetchall()
    conn.close()
    return songs

songs = load_songs()

# Стан сесії
if 'expert' not in st.session_state:
    st.session_state.expert = None

if 'selected' not in st.session_state:
    st.session_state.selected = {'first': None, 'second': None, 'third': None}

# Бічне меню
st.sidebar.title("Навігація")
menu = ["Вхід / Реєстрація", "Результати (викладач)"]
choice = st.sidebar.radio("Меню", menu)

# ------------------------------------------------------------
# Сторінка 1: Вхід / Реєстрація
# ------------------------------------------------------------
if choice == "Вхід / Реєстрація":
    st.title("🎤 Голосування Євробачення")

    if st.session_state.expert is not None:
        st.write(f"Ви увійшли як: **{st.session_state.expert['full_name']}**")

        conn = get_db_connection()
        existing_vote = conn.execute("SELECT * FROM votes WHERE expert_id = ?",
                                     (st.session_state.expert['id'],)).fetchone()
        conn.close()

        if existing_vote:
            st.warning("Ви вже проголосували. Дякуємо за участь!")
        else:
            st.subheader("Оберіть три пісні, які мають перемогти на Євробаченні")
            st.markdown("Натисніть кнопку під карткою, щоб призначити місце. Одна пісня може бути обрана тільки один раз.")

            # Відображення поточного вибору (текстом)
            cols_status = st.columns(3)
            with cols_status[0]:
                st.markdown("**🥇 Перше місце**")
                if st.session_state.selected['first']:
                    song = next(s for s in songs if s['id'] == st.session_state.selected['first'])
                    st.info(f"{song['title']} - {song['artist']}")
                else:
                    st.info("Не обрано")
            with cols_status[1]:
                st.markdown("**🥈 Друге місце**")
                if st.session_state.selected['second']:
                    song = next(s for s in songs if s['id'] == st.session_state.selected['second'])
                    st.info(f"{song['title']} - {song['artist']}")
                else:
                    st.info("Не обрано")
            with cols_status[2]:
                st.markdown("**🥉 Третє місце**")
                if st.session_state.selected['third']:
                    song = next(s for s in songs if s['id'] == st.session_state.selected['third'])
                    st.info(f"{song['title']} - {song['artist']}")
                else:
                    st.info("Не обрано")

            st.markdown("---")

            # Сітка з картками (5 колонок)
            cols_per_row = 5
            for i in range(0, len(songs), cols_per_row):
                row_songs = songs[i:i+cols_per_row]
                cols = st.columns(cols_per_row)
                for j, song in enumerate(row_songs):
                    with cols[j]:
                        # Стилізована картка (рамка, фон)
                        with st.container():
                            st.markdown(f"**{song['title']}**")
                            st.caption(song['artist'])

                            is_first = (st.session_state.selected['first'] == song['id'])
                            is_second = (st.session_state.selected['second'] == song['id'])
                            is_third = (st.session_state.selected['third'] == song['id'])
                            is_selected = is_first or is_second or is_third

                            if is_selected:
                                if is_first:
                                    st.success("🥇 Перше місце")
                                elif is_second:
                                    st.success("🥈 Друге місце")
                                elif is_third:
                                    st.success("🥉 Третє місце")
                                if st.button("✖ Скасувати", key=f"unsel_{song['id']}"):
                                    if is_first:
                                        st.session_state.selected['first'] = None
                                    elif is_second:
                                        st.session_state.selected['second'] = None
                                    elif is_third:
                                        st.session_state.selected['third'] = None
                                    st.rerun()
                            else:
                                cols_btn = st.columns(3)
                                with cols_btn[0]:
                                    if st.button("🥇", key=f"1_{song['id']}"):
                                        if st.session_state.selected['first'] is None:
                                            st.session_state.selected['first'] = song['id']
                                        else:
                                            st.warning("Перше місце зайняте!")
                                        st.rerun()
                                with cols_btn[1]:
                                    if st.button("🥈", key=f"2_{song['id']}"):
                                        if st.session_state.selected['second'] is None:
                                            st.session_state.selected['second'] = song['id']
                                        else:
                                            st.warning("Друге місце зайняте!")
                                        st.rerun()
                                with cols_btn[2]:
                                    if st.button("🥉", key=f"3_{song['id']}"):
                                        if st.session_state.selected['third'] is None:
                                            st.session_state.selected['third'] = song['id']
                                        else:
                                            st.warning("Третє місце зайняте!")
                                        st.rerun()
                            st.markdown("---")

            st.markdown("---")
            if all(st.session_state.selected.values()):
                if st.button("🗳️ Проголосувати", type="primary"):
                    ids = list(st.session_state.selected.values())
                    if len(set(ids)) == 3:
                        conn = get_db_connection()
                        try:
                            conn.execute(
                                "INSERT INTO votes (expert_id, first_choice, second_choice, third_choice) VALUES (?, ?, ?, ?)",
                                (st.session_state.expert['id'],
                                 st.session_state.selected['first'],
                                 st.session_state.selected['second'],
                                 st.session_state.selected['third'])
                            )
                            conn.commit()
                            st.success("Дякуємо! Ваш голос збережено.")
                            st.balloons()
                            st.session_state.selected = {'first': None, 'second': None, 'third': None}
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Помилка: ви вже голосували раніше?")
                        finally:
                            conn.close()
                    else:
                        st.error("Помилка: пісні мають бути різними.")
            else:
                st.info("Оберіть пісні для всіх трьох місць, щоб проголосувати.")

            if st.button("🔄 Скинути вибір"):
                st.session_state.selected = {'first': None, 'second': None, 'third': None}
                st.rerun()

        if st.button("🚪 Вийти"):
            st.session_state.expert = None
            st.session_state.selected = {'first': None, 'second': None, 'third': None}
            st.rerun()

    else:
        tab1, tab2 = st.tabs(["📥 Вхід", "📝 Реєстрація"])
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Логін")
                password = st.text_input("Пароль", type="password")
                submitted = st.form_submit_button("Увійти")
                if submitted:
                    expert = authenticate(username, password)
                    if expert:
                        st.session_state.expert = expert
                        st.success("Вхід успішний!")
                        st.rerun()
                    else:
                        st.error("Невірний логін або пароль")
        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Бажаний логін")
                new_password = st.text_input("Пароль", type="password")
                new_fullname = st.text_input("Ваше повне ім'я")
                submitted_reg = st.form_submit_button("Зареєструватися")
                if submitted_reg:
                    if new_username and new_password and new_fullname:
                        success, message = register_user(new_username, new_password, new_fullname)
                        if success:
                            st.success(message)
                            expert = authenticate(new_username, new_password)
                            if expert:
                                st.session_state.expert = expert
                                st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Будь ласка, заповніть всі поля")

# ------------------------------------------------------------
# Сторінка 2: Результати (викладач)
# ------------------------------------------------------------
elif choice == "Результати (викладач)":
    st.title("📊 Протокол та результати голосування")

    password = st.text_input("Введіть пароль викладача:", type="password")
    if password == "teacher123":
        conn = get_db_connection()

        experts_status = pd.read_sql_query('''
            SELECT 
                e.full_name,
                e.username,
                CASE WHEN v.id IS NOT NULL THEN 'Проголосував' ELSE 'Не голосував' END AS status,
                v.timestamp
            FROM experts e
            LEFT JOIN votes v ON e.id = v.expert_id
            ORDER BY e.full_name
        ''', conn)

        st.subheader("Статус експертів")
        st.dataframe(experts_status, use_container_width=True)

        votes_df = pd.read_sql_query('''
            SELECT 
                e.full_name AS expert,
                s1.title || " - " || s1.artist AS first_choice,
                s2.title || " - " || s2.artist AS second_choice,
                s3.title || " - " || s3.artist AS third_choice,
                v.timestamp
            FROM votes v
            JOIN experts e ON v.expert_id = e.id
            LEFT JOIN songs s1 ON v.first_choice = s1.id
            LEFT JOIN songs s2 ON v.second_choice = s2.id
            LEFT JOIN songs s3 ON v.third_choice = s3.id
            ORDER BY v.timestamp
        ''', conn)

        st.subheader("Детальний протокол голосування (бюлетені)")
        st.dataframe(votes_df, use_container_width=True)

        scores = pd.read_sql_query('''
            SELECT 
                s.title,
                s.artist,
                SUM(CASE WHEN v.first_choice = s.id THEN 3 ELSE 0 END +
                    CASE WHEN v.second_choice = s.id THEN 2 ELSE 0 END +
                    CASE WHEN v.third_choice = s.id THEN 1 ELSE 0 END) AS total_score
            FROM songs s
            LEFT JOIN votes v ON s.id IN (v.first_choice, v.second_choice, v.third_choice)
            GROUP BY s.id
            ORDER BY total_score DESC
        ''', conn)

        st.subheader("Рейтинг пісень (за сумою балів)")
        st.dataframe(scores, use_container_width=True)

        st.subheader("Топ-10 пісень")
        if not scores.empty:
            chart_data = scores.head(10).set_index('title')['total_score']
            st.bar_chart(chart_data)
        else:
            st.info("Поки що немає голосів")

        conn.close()
    elif password:
        st.error("Невірний пароль")