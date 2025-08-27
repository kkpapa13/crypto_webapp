from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 連接到或建立 SQLite 資料庫
def get_db_connection():
    conn = sqlite3.connect('trade_records.db')
    conn.row_factory = sqlite3.Row
    return conn

# 在啟動時建立資料表
with get_db_connection() as conn:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_capital REAL NOT NULL,
            max_loss_percentage REAL,
            max_loss_amount REAL,
            entry_price REAL NOT NULL,
            stop_loss_price REAL NOT NULL,
            take_profit_price REAL,
            margin_to_use REAL NOT NULL,
            position_size REAL NOT NULL,
            leverage REAL NOT NULL,
            stop_loss_percentage REAL,
            profit_amount REAL,
            profit_percentage REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        try:
            total_capital = float(request.form['total_capital'])
            entry_price = float(request.form['entry_price'])
            stop_loss_price = float(request.form['stop_loss_price'])
            margin_to_use = float(request.form['margin_to_use'])
        except (ValueError, TypeError):
            flash("請確認所有數值欄位皆已正確填寫。", 'error')
            return render_template('index.html')

        max_loss_percentage_input = request.form.get('max_loss_percentage', '')
        max_loss_amount_input = request.form.get('max_loss_amount', '')

        max_loss_percentage = None
        max_loss_amount = None
        
        if max_loss_amount_input:
            try:
                max_loss_amount = float(max_loss_amount_input)
                if total_capital > 0:
                    max_loss_percentage = (max_loss_amount / total_capital) * 100
                else:
                    flash("總資金必須大於0，才能計算虧損百分比。", 'error')
                    return render_template('index.html')
            except ValueError:
                flash("最大虧損金額輸入不正確。", 'error')
                return render_template('index.html')
        elif max_loss_percentage_input:
            try:
                max_loss_percentage = float(max_loss_percentage_input)
                max_loss_amount = total_capital * (max_loss_percentage / 100)
            except ValueError:
                flash("最大虧損百分比輸入不正確。", 'error')
                return render_template('index.html')
        else:
            flash("請至少輸入最大虧損百分比或最大虧損金額其中一項。", 'error')
            return render_template('index.html')

        if entry_price == 0:
            flash("開倉價格不能為0。", 'error')
            return render_template('index.html')

        stop_loss_percentage = abs((entry_price - stop_loss_price) / entry_price)

        if stop_loss_percentage == 0:
            flash("錯誤：開倉價格與止損價格相同，無法計算。", 'error')
            return render_template('index.html')

        # 根據最大虧損和止損% 計算出倉位大小
        if stop_loss_percentage == 0:
            flash("止損價格與開倉價格相同，無法計算倉位大小。", 'error')
            return render_template('index.html')
            
        position_size = max_loss_amount / stop_loss_percentage
        
        # 根據倉位大小和投入保證金 計算槓桿倍數，並四捨五入到整數
        if margin_to_use == 0:
            leverage = 0
        else:
            leverage = round(position_size / margin_to_use)

        # 處理利潤輸入
        take_profit_price_input = request.form.get('take_profit_price', '')
        profit_percentage_input = request.form.get('profit_percentage', '')
        profit_amount_input = request.form.get('profit_amount', '')

        take_profit_price = None
        profit_amount = None
        profit_percentage = None
        
        # 判斷是做多還是做空
        is_long = stop_loss_price < entry_price
        
        if take_profit_price_input:
            try:
                take_profit_price = float(take_profit_price_input)
                profit_amount = abs(take_profit_price - entry_price) / entry_price * position_size
                if margin_to_use > 0:
                    profit_percentage = (profit_amount / margin_to_use) * 100
            except ValueError:
                flash("止盈價格輸入不正確。", 'error')
                return render_template('index.html')
        elif profit_amount_input:
            try:
                profit_amount = float(profit_amount_input)
                if margin_to_use > 0:
                    profit_percentage = (profit_amount / margin_to_use) * 100
                price_change_percentage = (profit_amount / position_size) if position_size != 0 else 0
                price_change = price_change_percentage * entry_price
                take_profit_price = entry_price + price_change if is_long else entry_price - price_change
            except ValueError:
                flash("利潤金額輸入不正確。", 'error')
                return render_template('index.html')
        elif profit_percentage_input:
            try:
                profit_percentage = float(profit_percentage_input)
                profit_amount = margin_to_use * (profit_percentage / 100)
                price_change_percentage = (profit_amount / position_size) if position_size != 0 else 0
                price_change = price_change_percentage * entry_price
                take_profit_price = entry_price + price_change if is_long else entry_price - price_change
            except ValueError:
                flash("利潤百分比輸入不正確。", 'error')
                return render_template('index.html')

        # 儲存到資料庫
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO records (total_capital, max_loss_percentage, max_loss_amount, entry_price, stop_loss_price, take_profit_price, margin_to_use, position_size, leverage, stop_loss_percentage, profit_amount, profit_percentage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (total_capital, max_loss_percentage, max_loss_amount, entry_price, stop_loss_price, take_profit_price, margin_to_use, position_size, leverage, stop_loss_percentage, profit_amount, profit_percentage)
            )
            conn.commit()
        
        # 準備結果數據並返回
        result = {
            'max_loss_amount': f'{max_loss_amount:,.2f}',
            'max_loss_percentage': f'{max_loss_percentage:.2f}%',
            'stop_loss_percentage': f'{stop_loss_percentage * 100:.2f}%',
            'position_size': f'{position_size:,.2f}',
            'leverage': f'{leverage:.0f}x', # 在這裡也修改顯示格式
            'take_profit_price': f'{take_profit_price:.2f}' if take_profit_price is not None else 'N/A',
            'profit_amount': f'{profit_amount:,.2f}' if profit_amount is not None else 'N/A',
            'profit_percentage': f'{profit_percentage:.2f}%' if profit_percentage is not None else 'N/A'
        }
        
        return render_template('index.html', result=result)

    return render_template('index.html')

@app.route('/records')
def records():
    with get_db_connection() as conn:
        records = conn.execute("SELECT * FROM records ORDER BY timestamp DESC").fetchall()
    
    # 移除這裡的預處理邏輯
    # processed_records = []
    # for record in records:
    #     record_dict = dict(record)
    #     for key in ['max_loss_percentage', 'max_loss_amount', 'stop_loss_percentage', 'take_profit_price', 'profit_amount', 'profit_percentage']:
    #         if record_dict[key] is None:
    #             record_dict[key] = 'N/A'
    #     processed_records.append(record_dict)

    return render_template('records.html', records=records)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
