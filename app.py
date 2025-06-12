from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Flask-Loginの設定 ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- データベース接続 ---
DB_HOST = "db"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "mysecretpassword"


def get_connection():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)


# --- ユーザーモデル ---
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash


@login_manager.user_loader
def load_user(user_id):
    # (省略 - 以前のチュートリアルの完成版コードと同じ)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    cur.close()
    conn.close()
    if user_data:
        return User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
    return None


# --- ルーティング ---
@app.route('/')
@login_required
def index():
    # (省略 - 以前のチュートリアルの完成版コードと同じ)
    tasks = []
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, title, completed FROM tasks WHERE user_id = %s ORDER BY id", (current_user.id,))
        tasks = cur.fetchall()
    except (Exception, psycopg2.Error) as error:
        flash(f"タスクの読み込み中にエラー: {error}", "danger")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    return render_template('index.html', tasks=tasks)


@app.route('/add', methods=['POST'])
@login_required
def add_task():
    """新しいタスクの追加"""
    title = request.form.get('title')
    if title:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO tasks (title, user_id) VALUES (%s, %s)", (title, current_user.id))
            conn.commit()
            cur.close()
            conn.close()
            flash(f"タスク「{title}」を追加しました。", "success")
        except (Exception, psycopg2.Error) as error:
            print("タスクの追加中にエラーが発生しました:", error)
            flash("タスクの追加中にエラーが発生しました。", "danger")
    else:
        flash("タスクのタイトルを入力してください。", "warning")
    return redirect(url_for('index'))


@app.route('/complete/<int:task_id>')
@login_required
def complete_task(task_id):
    """タスクの完了"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET completed = TRUE WHERE id = %s AND user_id = %s", (task_id, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"タスクID {task_id} を完了にしました。", "success")
    except (Exception, psycopg2.Error) as error:
        print("タスクの完了中にエラーが発生しました:", error)
        flash(f"タスクID {task_id} の完了処理中にエラーが発生しました。", "danger")
    return redirect(url_for('index'))


# タスクの削除
@app.route('/delete/<int:task_id>')
@login_required
def delete_task(task_id):
    """タスクの削除"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"タスクID {task_id} を削除しました。", "success")
    except (Exception, psycopg2.Error) as error:
        print(f"タスク {task_id} の削除中にエラーが発生しました:", error)
        flash(f"タスクID {task_id} の削除中にエラーが発生しました。", "danger")
    return redirect(url_for('index'))


@app.route('/reactivate/<int:task_id>')
@login_required
def reactivate_task(task_id):
    """完了したタスクを未完了に戻す"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE tasks SET completed = FALSE WHERE id = %s AND user_id = %s", (task_id, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"タスクID {task_id} を未完了に戻しました。", "success")
    except (Exception, psycopg2.Error) as error:
        print("タスクの再活性化中にエラーが発生しました:", error)
        flash(f"タスクID {task_id} の再活性化中にエラーが発生しました。", "danger")
    return redirect(url_for('index'))


@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """タスクの編集"""
    if request.method == 'POST':
        new_title = request.form.get('title')
        conn_post = None
        cur_post = None
        if new_title:
            try:
                conn_post = get_connection()
                cur_post = conn_post.cursor()
                cur_post.execute("UPDATE tasks SET title = %s WHERE id = %s AND user_id = %s", 
                                 (new_title, task_id, current_user.id))
                conn_post.commit()
                message = (
                    f"タスクID {task_id} のタイトルを"
                    f"「{new_title}」に更新しました。"
                )
                flash(message, "success")
            except (Exception, psycopg2.Error) as error:
                print(f"タスクID {task_id} の更新中にエラーが発生しました: {error}")
                flash(f"タスクID {task_id} の更新中にエラーが発生しました。", "danger")
            finally:
                if cur_post:
                    cur_post.close()
                if conn_post:
                    conn_post.close()
        else:
            flash("新しいタスクのタイトルを入力してください。", "warning")
        return redirect(url_for('index'))

    conn_get = None
    cur_get = None
    task = None
    try:
        conn_get = get_connection()
        cur_get = conn_get.cursor()
        cur_get.execute("SELECT id, title, completed FROM tasks WHERE id = %s AND user_id = %s",
                         (task_id, current_user.id))
        task = cur_get.fetchone()
        if not task:
            message = (
                f"編集するタスクID {task_id} "
                "が見つかりません。"
            )
            flash(message, "warning")
            return redirect(url_for('index'))
    except (Exception, psycopg2.Error) as error:
        print(f"タスクID {task_id} の読み込み中にエラーが発生しました: {error}")
        flash(f"タスクID {task_id} の読み込み中にエラーが発生しました。", "danger")
        return redirect(url_for('index'))
    finally:
        if cur_get:
            cur_get.close()
        if conn_get:
            conn_get.close()
    return render_template('edit.html', task=task)


# --- 認証ルート ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # (省略 - 以前のチュートリアルの完成版コードと同じ)
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_exists = cur.fetchone()

        if user_exists:
            flash("そのユーザー名は既に使用されています。", "warning")
            cur.close()
            conn.close()
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cur.close()
        conn.close()

        flash("アカウントが作成されました。ログインしてください。", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # (省略 - 以前のチュートリアルの完成版コードと同じ)
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user_data = cur.fetchone()
        cur.close()
        conn.close()

        if user_data and check_password_hash(user_data[2], password):
            user = User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
            login_user(user)
            flash("ログインしました。", "success")
            return redirect(url_for('index'))
        else:
            flash("ユーザー名またはパスワードが正しくありません。", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    # (省略 - 以前のチュートリアルの完成版コードと同じ)
    logout_user()
    flash("ログアウトしました。", "info")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
