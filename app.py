from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Expanded to 26 emojis each
FULL_EMOJI_POOL_STEP_1 = ['😺', '⭐', '🌳', '🐶', '🌙', '🍎', '🚀', '🎉', '🦄', '🌈', '🍕', '🎸', '⚡', '🦋', '🌟', '🐳', '🐱', '🌞', '🍉',
                          '🎵', '🦁', '🌼', '🚗', '🎤', '🐢', '🍋']
FULL_EMOJI_POOL_STEP_2 = ['🍒', '🔔', '🌸', '🎁', '🌍', '🍦', '🎨', '⚽', '🍩', '🐧', '🌵', '🦉', '🍄', '🦖', '🌺', '🦜', '🍓', '🎲', '🌴',
                          '🐸', '🍰', '🎻', '🦷', '🌊', '🐙', '🍇']

ADD_RULES = [1, 2, 3, 5, 7]

DATABASE_PATH = 'users.db'


def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS users")
        c.execute('''CREATE TABLE users 
                     (username TEXT PRIMARY KEY, password TEXT, emoji1 TEXT, emoji2 TEXT, trust_emoji TEXT, grid_size INTEGER)''')
        conn.commit()
        logger.debug("Database initialized with 6-column schema")
        c.execute("PRAGMA table_info(users)")
        schema = c.fetchall()
        logger.debug(f"Users table schema: {schema}")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()


if not os.path.exists(DATABASE_PATH):
    init_db()


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        logger.debug(f"Login attempt: username={username}")

        if not username or not password:
            error = "Username and password are required!"
            logger.debug("Missing username or password")
            return render_template('login.html', error=error)

        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            c.execute("SELECT password, grid_size, emoji1, emoji2 FROM users WHERE username = ?", (username,))
            result = c.fetchone()
            logger.debug(f"Database result: {result}")

            if result:
                stored_password, grid_size, emoji1, emoji2 = result
                if check_password_hash(stored_password, password):
                    logger.debug("Password verified, setting session")
                    session['username'] = username
                    session['step'] = 1
                    session['add_rule'] = random.choice(ADD_RULES)
                    session['tries_left'] = 2
                    session['grid_size'] = grid_size
                    session['emoji1'] = emoji1
                    session['emoji2'] = emoji2
                    session.pop('grid_step_1', None)
                    session.pop('grid_step_2', None)
                    logger.debug(f"Session set: {session}")
                    return redirect(url_for('emoji_grid'))
                else:
                    error = "Invalid username or password!"
                    logger.debug("Password mismatch")
            else:
                error = "Invalid username or password!"
                logger.debug("User not found")
        except sqlite3.Error as e:
            logger.error(f"Database error during login: {e}")
            error = f"An error occurred: Database issue - {str(e)}. Please try again."
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed")

    return render_template('login.html', error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        grid_size = int(request.form.get('grid_size', 4))

        if not username or not password:
            error = "Username and password are required!"
            return render_template('signup.html', error=error)

        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            c.execute("SELECT username FROM users WHERE username = ?", (username,))
            if c.fetchone():
                error = "Username already taken!"
            else:
                hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
                session['new_user'] = {'username': username, 'password': hashed_pw, 'grid_size': grid_size}
                logger.debug(f"Signup successful, redirecting to emoji_assignment: {session['new_user']}")
                return redirect(url_for('emoji_assignment'))
        except sqlite3.Error as e:
            logger.error(f"Database error during signup: {e}")
            error = f"An error occurred: Database issue - {str(e)}. Please try again."
        finally:
            if conn:
                conn.close()

    return render_template('signup.html', error=error)


@app.route('/emoji_assignment', methods=['GET', 'POST'])
def emoji_assignment():
    if 'new_user' not in session:
        logger.debug("No new_user in session, redirecting to signup")
        return redirect(url_for('signup'))

    if 'assigned_emojis' not in session:
        session['assigned_emojis'] = random.sample(FULL_EMOJI_POOL_STEP_1 + FULL_EMOJI_POOL_STEP_2, 3)
        session['practice_add_rule'] = random.choice(ADD_RULES)
        logger.debug(f"Assigned emojis: {session['assigned_emojis']}")

    if request.method == 'POST':
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            c = conn.cursor()
            user = session['new_user']
            emojis = session['assigned_emojis']
            grid_size = user['grid_size']

            logger.debug(f"Inserting user: {user['username']}, emojis={emojis}, grid_size={grid_size}")
            c.execute(
                "INSERT INTO users (username, password, emoji1, emoji2, trust_emoji, grid_size) VALUES (?, ?, ?, ?, ?, ?)",
                (user['username'], user['password'], emojis[0], emojis[1], emojis[2], grid_size))
            conn.commit()
            logger.debug(f"User {user['username']} inserted successfully")
            session.clear()
            logger.debug("Session cleared, redirecting to login")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            logger.error(f"Database error during emoji assignment: {e}")
            return render_template('emoji_assignment.html', emojis=session['assigned_emojis'],
                                   add_rule=session['practice_add_rule'], grid_size=session['new_user']['grid_size'],
                                   error=f"Database error: {str(e)}. Please try again.")
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed in emoji_assignment")

    return render_template('emoji_assignment.html', emojis=session['assigned_emojis'],
                           add_rule=session['practice_add_rule'], grid_size=session['new_user']['grid_size'])


@app.route('/emoji_grid', methods=['GET', 'POST'])
def emoji_grid():
    if 'username' not in session or 'step' not in session:
        logger.debug("Redirecting to login: session data missing")
        return redirect(url_for('login'))

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT emoji1, emoji2, grid_size FROM users WHERE username = ?", (session['username'],))
        user_emojis = c.fetchone()
        if not user_emojis:
            logger.debug("User not found in database")
            return redirect(url_for('login'))
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return redirect(url_for('login', error="Database error. Please try again."))
    finally:
        if conn:
            conn.close()

    step = session['step']
    add_rule = session['add_rule']
    grid_size = user_emojis[2]
    required_size = grid_size * grid_size
    key_emoji = user_emojis[0] if step == 1 else user_emojis[1]
    other_key_emoji = user_emojis[1] if step == 1 else user_emojis[0]

    grid_key = f'grid_step_{step}'
    if request.method == 'GET' or grid_key not in session:
        base_pool = FULL_EMOJI_POOL_STEP_1 if step == 1 else FULL_EMOJI_POOL_STEP_2
        available_emojis = [e for e in base_pool if e != other_key_emoji and e != key_emoji]

        if len(available_emojis) < required_size - 1:
            logger.error(
                f"Not enough unique emojis in pool for step {step}: {len(available_emojis)} available, {required_size} needed")
            return redirect(url_for('login', error="Internal error: Insufficient emoji pool."))

        grid_emojis = random.sample(available_emojis, required_size - 1) + [key_emoji]
        random.shuffle(grid_emojis)

        if len(set(grid_emojis)) != required_size:
            logger.error(f"Duplicate emojis detected in grid: {grid_emojis}")
            return redirect(url_for('login', error="Internal error: Duplicate emojis in grid."))

        grid_with_positions = [(i + 1, emoji) for i, emoji in enumerate(grid_emojis)]
        grid_2d = [grid_with_positions[i:i + grid_size] for i in range(0, len(grid_with_positions), grid_size)]

        try:
            correct_pos = next(pos for pos, emoji in grid_with_positions if emoji == key_emoji)
        except StopIteration:
            logger.error(f"Key emoji {key_emoji} not found in grid: {grid_emojis}")
            return redirect(url_for('login', error="Internal error: Emoji not found. Please try again."))

        correct_num = correct_pos + add_rule

        session[grid_key] = {
            'grid_2d': grid_2d,
            'correct_pos': correct_pos,
            'correct_num': correct_num,
            'key_emoji': key_emoji
        }
    else:
        grid_data = session[grid_key]
        grid_2d = grid_data['grid_2d']
        correct_pos = grid_data['correct_pos']
        correct_num = grid_data['correct_num']
        key_emoji = grid_data['key_emoji']
        grid_emojis = [emoji for row in grid_2d for _, emoji in row]

    logger.debug(
        f"Step: {step}, Key Emoji: {key_emoji}, Correct Pos: {correct_pos}, Add Rule: {add_rule}, Correct Num: {correct_num}")
    logger.debug(f"Grid emojis: {grid_emojis}")

    if request.method == 'POST':
        return redirect(url_for('emoji_input'))

    return render_template('emoji_grid.html', grid=grid_2d, step=step, grid_size=grid_size, add_rule=add_rule)


@app.route('/emoji_input', methods=['GET', 'POST'])
def emoji_input():
    if 'username' not in session or 'step' not in session:
        logger.debug("Redirecting to login: session data missing")
        return redirect(url_for('login'))

    step = session['step']
    add_rule = session['add_rule']
    tries_left = session['tries_left']
    grid_key = f'grid_step_{step}'

    if grid_key not in session:
        logger.debug("Grid data missing, redirecting to emoji_grid")
        return redirect(url_for('emoji_grid'))

    grid_data = session[grid_key]
    correct_num = grid_data['correct_num']

    if request.method == 'POST':
        logger.debug(f"POST request received: {request.form}")
        input_num = request.form.get('emoji_num')
        if not input_num:
            return render_template('emoji_input.html', step=step, add_rule=add_rule, tries_left=tries_left,
                                   error="No number entered!")
        try:
            input_num = int(input_num)
            logger.debug(f"User Input: {input_num}, Expected: {correct_num}")
            if input_num == correct_num:
                logger.debug("Correct input!")
                if step == 1:
                    session['step'] = 2
                    session['add_rule'] = random.choice(ADD_RULES)
                    session['tries_left'] = 2
                    session.pop(grid_key, None)
                    return redirect(url_for('emoji_grid'))
                session.clear()
                return redirect(url_for('success'))
            else:
                session['tries_left'] -= 1
                logger.debug(f"Wrong input! Tries left: {session['tries_left']}")
                if session['tries_left'] > 0:
                    return render_template('emoji_input.html', step=step, add_rule=add_rule, tries_left=tries_left,
                                           error=f"Wrong number! {tries_left} tries left.")
                session.clear()
                return redirect(url_for('login', error="Out of tries! Please log in again."))
        except ValueError:
            return render_template('emoji_input.html', step=step, add_rule=add_rule, tries_left=tries_left,
                                   error="Please enter a valid number!")

    return render_template('emoji_input.html', step=step, add_rule=add_rule, tries_left=tries_left)


@app.route('/success')
def success():
    return render_template('success.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)