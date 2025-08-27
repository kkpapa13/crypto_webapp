import sqlite3

conn = sqlite3.connect("data.sqlite")
cursor = conn.cursor()

# 歸零錢包資料，重新計算（避免重複）
cursor.execute("UPDATE wallets SET total_amount = 0, avg_cost = 0")

# 查詢所有交易
cursor.execute("SELECT coin_id, trade_type, price, amount FROM trades")
trades = cursor.fetchall()

# 暫存每個幣的加總資料
wallet_data = {}

for coin_id, trade_type, price, amount in trades:
    if coin_id not in wallet_data:
        wallet_data[coin_id] = {"total": 0, "cost_total": 0}

    if trade_type == "buy":
        wallet_data[coin_id]["cost_total"] += price * amount
        wallet_data[coin_id]["total"] += amount
    elif trade_type == "sell":
        wallet_data[coin_id]["total"] -= amount
        # 賣出不影響平均成本

# 將結果寫回 wallets 表
for coin_id, data in wallet_data.items():
    total = data["total"]
    avg_cost = data["cost_total"] / total if total > 0 else 0

    cursor.execute(
        "UPDATE wallets SET total_amount = ?, avg_cost = ? WHERE coin_id = ?",
        (total, avg_cost, coin_id)
    )

conn.commit()
conn.close()
print("✅ 錢包資料已更新完畢！")
