import os
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
import psycopg2.extras

app = Flask(__name__)
# 使用環境變數來取得資料庫連接字串，這是一個好習慣
DATABASE_URL = os.environ.get('DATABASE_URL')
app.secret_key = 'your_secret_key'

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# 在啟動時建立資料表
def init_db():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS coins (
              coin_id TEXT PRIMARY KEY,
              name TEXT NOT NULL
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS trades (
              trade_id SERIAL PRIMARY KEY,
              coin_id TEXT,
              trade_type TEXT,
              price REAL,
              amount REAL,
              take_profit REAL,
              stop_loss REAL,
              trade_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              note TEXT,
              FOREIGN KEY (coin_id) REFERENCES coins(coin_id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
              coin_id TEXT PRIMARY KEY,
              total_amount REAL DEFAULT 0,
              avg_cost REAL DEFAULT 0,
              FOREIGN KEY (coin_id) REFERENCES coins(coin_id)
            )
        ''')
    conn.commit()
    conn.close()

# 這會在程式啟動時執行，以確保資料庫表存在
init_db()

def calculate_coin_pnl(conn):
    """
    根據所有交易紀錄，計算每個幣種的總盈虧。
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT coin_id, trade_type, price, amount FROM trades")
        trades = cur.fetchall()

    coin_pnl = {}
    for trade in trades:
        coin_id = trade['coin_id']
        cost = trade['price'] * trade['amount']

        if coin_id not in coin_pnl:
            coin_pnl[coin_id] = 0.0

        if trade['trade_type'] == 'buy':
            coin_pnl[coin_id] -= cost
        elif trade['trade_type'] == 'sell':
            coin_pnl[coin_id] += cost

    return coin_pnl

# --- 主要路由 ---

@app.route("/")
def index():
    conn = get_db()
    coin_pnl = calculate_coin_pnl(conn)
    conn.close()
    return render_template("index.html", coin_pnl=coin_pnl)

@app.route("/trade", methods=["POST"])
def trade():
    conn = get_db()
    try:
        coin_id = request.form['coin'].upper()
        trade_type = request.form['type'].lower()
        price = float(request.form['price'])
        amount = float(request.form['amount'])
        note = request.form.get('note', '')

        with conn.cursor() as cur:
            # 確保幣種存在
            cur.execute("INSERT INTO coins (coin_id, name) VALUES (%s, %s) ON CONFLICT (coin_id) DO NOTHING", (coin_id, coin_id))
            conn.commit()
            
            # 插入新交易紀錄
            cur.execute(
                "INSERT INTO trades (coin_id, trade_type, price, amount, note) VALUES (%s, %s, %s, %s, %s)",
                (coin_id, trade_type, price, amount, note)
            )
            conn.commit()

        flash("✅ 交易新增成功！")
    except Exception as e:
        conn.rollback()
        flash(f"❌ 發生錯誤: {e}")
    finally:
        conn.close()
    return redirect(url_for("index"))

@app.route("/trades")
def trades():
    conn = get_db()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT trade_id, * FROM trades ORDER BY trade_time DESC")
        trades_list = cur.fetchall()
    conn.close()
    return render_template("trades.html", trades=trades_list)

@app.route("/edit/<int:trade_id>", methods=["GET", "POST"])
def edit_trade(trade_id):
    conn = get_db()
    if request.method == "POST":
        # 處理編輯表單提交
        coin_id = request.form['coin'].upper()
        trade_type = request.form['type'].lower()
        price = float(request.form['price'])
        amount = float(request.form['amount'])
        take_profit = request.form.get('take_profit') or None
        stop_loss = request.form.get('stop_loss') or None
        note = request.form.get('note', '')

        with conn.cursor() as cur:
            cur.execute(
                "UPDATE trades SET coin_id=%s, trade_type=%s, price=%s, amount=%s, take_profit=%s, stop_loss=%s, note=%s WHERE trade_id=%s",
                (coin_id, trade_type, price, amount, take_profit, stop_loss, note, trade_id)
            )
            conn.commit()
        conn.close()
        flash("✅ 交易更新成功！")
        return redirect("/trades")
    else:
        # 顯示編輯表單
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT trade_id, * FROM trades WHERE trade_id=%s", (trade_id,))
            trade = cur.fetchone()
        conn.close()
        if trade is None:
            flash("❌ 找不到此筆交易！")
            return redirect("/trades")
        return render_template("edit.html", trade=trade)

@app.route("/delete/<int:trade_id>")
def delete_trade(trade_id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM trades WHERE trade_id=%s", (trade_id,))
    conn.commit()
    conn.close()
    flash("✅ 交易刪除成功！")
    return redirect("/trades")
