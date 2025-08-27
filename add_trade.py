import sqlite3

def get_trade_input():
    print("請依序輸入交易資料，輸入 q 可結束。")
    trades = []

    while True:
        coin_id = input("幣種（例如 BTC)(q 結束):").upper()
        if coin_id == "Q":
            break
        if not coin_id:
            print("❗ 幣種不能空白，請重新輸入。")
            continue

        trade_type = input("交易類型(buy 或 sell):").lower()
        if trade_type not in ("buy", "sell"):
            print("❗ 錯誤：請輸入 buy 或 sell。")
            continue

        try:
            price = float(input("價格："))
            if price <= 0:
                print("❗ 價格必須為正數。")
                continue
        except ValueError:
            print("❗ 價格輸入錯誤，請輸入數字。")
            continue

        try:
            amount = float(input("數量："))
            if amount <= 0:
                print("❗ 數量必須為正數。")
                continue
        except ValueError:
            print("❗ 數量輸入錯誤，請輸入數字。")
            continue

        note = input("備註（可空白）：")
        trades.append((coin_id, trade_type, price, amount, note))
    
    return trades

def insert_trades(trades):
    conn = sqlite3.connect("data.sqlite")
    cursor = conn.cursor()

    for coin_id, trade_type, price, amount, note in trades:
        cursor.execute("INSERT OR IGNORE INTO coins (coin_id, name) VALUES (?, ?)", (coin_id, coin_id))
        cursor.execute("INSERT OR IGNORE INTO wallets (coin_id) VALUES (?)", (coin_id,))
        cursor.execute("""
            INSERT INTO trades (coin_id, trade_type, price, amount, note)
            VALUES (?, ?, ?, ?, ?)
        """, (coin_id, trade_type, price, amount, note))

    # 重算錢包
    cursor.execute("UPDATE wallets SET total_amount = 0, avg_cost = 0")
    cursor.execute("SELECT coin_id, trade_type, price, amount FROM trades")
    all_trades = cursor.fetchall()

    wallet_data = {}
    for c_id, t_type, p, a in all_trades:
        if c_id not in wallet_data:
            wallet_data[c_id] = {"total": 0, "cost_total": 0}
        if t_type == "buy":
            wallet_data[c_id]["cost_total"] += p * a
            wallet_data[c_id]["total"] += a
        elif t_type == "sell":
            wallet_data[c_id]["total"] -= a

    for c_id, data in wallet_data.items():
        total = data["total"]
        avg_cost = data["cost_total"] / total if total > 0 else 0
        cursor.execute(
            "UPDATE wallets SET total_amount = ?, avg_cost = ? WHERE coin_id = ?",
            (total, avg_cost, c_id)
        )

    conn.commit()
    conn.close()
    print("✅ 所有交易已新增，錢包也已更新完成！")

# 主程式
trades = get_trade_input()
if trades:
    insert_trades(trades)
else:
    print("❗ 沒有輸入任何交易。")
