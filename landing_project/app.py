from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'

# Banco de sutras
def init_db_sutras():
    with sqlite3.connect('sutras.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sutras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                conteudo TEXT NOT NULL
            )
        ''')
init_db_sutras()

# Banco admin com usuário fixo
def init_db_admin():
    with sqlite3.connect('admin.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        ''')
        cursor = conn.execute('SELECT * FROM usuarios WHERE id = 1')
        if cursor.fetchone() is None:
            conn.execute('INSERT INTO usuarios (id, username, senha) VALUES (1, ?, ?)', ('admin', 'admin123'))
init_db_admin()

# Função para checar se usuário está logado e é admin
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['username'] != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        with sqlite3.connect('admin.db') as conn:
            cursor = conn.execute('SELECT * FROM usuarios WHERE username = ? AND senha = ?', (user, pwd))
            usuario = cursor.fetchone()
        if usuario:
            session['username'] = user
            return redirect(url_for('index'))
        else:
            error = "Usuário ou senha inválidos"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Página principal: lista todos os sutras (qualquer usuário pode ver)
@app.route('/')
def index():
    with sqlite3.connect('sutras.db') as conn:
        cursor = conn.execute('SELECT id, titulo, conteudo FROM sutras')
        sutras = cursor.fetchall()
    return render_template('index.html', sutras=sutras, username=session.get('username'))

# Adicionar novo sutra (só admin)
@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        with sqlite3.connect('sutras.db') as conn:
            conn.execute('INSERT INTO sutras (titulo, conteudo) VALUES (?, ?)', (titulo, conteudo))
        return redirect(url_for('index'))
    return render_template('adicionar.html')

# Editar sutra (só admin)
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    if request.method == 'POST':
        novo_titulo = request.form['titulo']
        novo_conteudo = request.form['conteudo']
        with sqlite3.connect('sutras.db') as conn:
            conn.execute('UPDATE sutras SET titulo = ?, conteudo = ? WHERE id = ?', (novo_titulo, novo_conteudo, id))
        return redirect(url_for('index'))
    else:
        with sqlite3.connect('sutras.db') as conn:
            cursor = conn.execute('SELECT id, titulo, conteudo FROM sutras WHERE id = ?', (id,))
            sutra = cursor.fetchone()
        return render_template('editar.html', sutra=sutra)

# Remover sutra (só admin)
@app.route('/remover/<int:id>')
@login_required
def remover(id):
    with sqlite3.connect('sutras.db') as conn:
        conn.execute('DELETE FROM sutras WHERE id = ?', (id,))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5001)
