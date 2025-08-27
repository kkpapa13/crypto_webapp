from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
DB_FILE = "data.sqlite"
app.secret_key = 'your_secret_key'

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_coin_pnl(conn):
    """
    根據所有交易紀錄，計算每個幣種的總盈虧。
    """
    trades = conn.execute("SELECT coin_id, trade_type, price, amount FROM trades").fetchall()
    
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
    
    # 計算每個幣種的總盈虧
    coin_pnl = calculate_coin_pnl(conn)
    
    return render_template("index.html", coin_pnl=coin_pnl)

@app.route("/trade", methods=["POST"])
def trade():
    # 處理新增交易的邏輯
    coin = request.form["coin"]
    trade_type = request.form["type"]
    price = request.form["price"]
    amount = request.form["amount"]
    note = request.form.get("note", "")
    take_profit = request.form.get("take_profit")
    stop_loss = request.form.get("stop_loss")

    if not all([coin, trade_type, price, amount]):
        flash("❌ 請填寫所有必填欄位！")
        return redirect("/")

    try:
        price = float(price)
        amount = float(amount)
        if price <= 0 or amount <= 0:
            flash("❌ 價格與數量必須是正數！")
            return redirect("/")
    except ValueError:
        flash("❌ 價格與數量必須是數字！")
        return redirect("/")

    conn = get_db()
    conn.execute(
        "INSERT INTO trades (coin_id, trade_type, price, amount, note, take_profit, stop_loss) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (coin, trade_type, price, amount, note, take_profit, stop_loss)
    )
    conn.commit()
    conn.close()
    flash("✅ 交易新增成功！")
    return redirect("/")

@app.route("/trades")
def trade_list():
    conn = get_db()
    trades = conn.execute("SELECT trade_id, * FROM trades ORDER BY trade_time DESC").fetchall()
    return render_template("trades.html", trades=trades)

@app.route("/edit/<int:trade_id>", methods=["GET", "POST"])
def edit_trade(trade_id):
    conn = get_db()
    if request.method == "POST":
        # 編輯交易邏輯
        coin = request.form["coin"]
        trade_type = request.form["type"]
        price = float(request.form["price"])
        amount = float(request.form["amount"])
        note = request.form.get("note", "")
        take_profit = request.form.get("take_profit")
        stop_loss = request.form.get("stop_loss")
        take_profit = float(take_profit) if take_profit else None
        stop_loss = float(stop_loss) if stop_loss else None

        conn.execute(
            "UPDATE trades SET coin_id=?, trade_type=?, price=?, amount=?, note=?, "
            "take_profit=?, stop_loss=? WHERE trade_id=?",
            (coin, trade_type, price, amount, note, take_profit, stop_loss, trade_id)
        )
        conn.commit()
        flash("✅ 交易更新成功！")
        return redirect("/trades")
    else:
        trade = conn.execute("SELECT trade_id, * FROM trades WHERE trade_id=?", (trade_id,)).fetchone()
        if trade is None:
            flash("❌ 找不到此筆交易！")
            return redirect("/trades")
        return render_template("edit.html", trade=trade)

@app.route("/delete/<int:trade_id>")
def delete_trade(trade_id):
    conn = get_db()
    conn.execute("DELETE FROM trades WHERE trade_id=?", (trade_id,))
    conn.commit()
    flash("✅ 交易刪除成功！")
    return redirect("/trades")

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS coins (
          coin_id TEXT PRIMARY KEY,
          name TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trades (
          trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
          coin_id TEXT,
          trade_type TEXT,
          price REAL,
          amount REAL,
          take_profit REAL,
          stop_loss REAL,
          trade_time TEXT DEFAULT CURRENT_TIMESTAMP,
          note TEXT,
          FOREIGN KEY (coin_id) REFERENCES coins(coin_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS wallets (
          coin_id TEXT PRIMARY KEY,
          total_amount REAL DEFAULT 0,
          avg_cost REAL DEFAULT 0,
          FOREIGN KEY (coin_id) REFERENCES coins(coin_id)
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)