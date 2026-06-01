import pandas as pd
df = pd.read_excel("E:\\G-AI-1\\Stock analysis\\Stock original\\2360_致茂_EOM_20260505.xlsx")
for col in df.columns[1:]: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# JS simulation
trades_js = []
hold = False; bp = 0; tp = 0.189; sl = 0.08; macd = 2.1; mfi = 30; eom_off = 0
for i in range(1, len(df)-1):
    c = df.iloc[i]; n = df.iloc[i+1]
    if not hold:
        if c.iloc[4] > c.iloc[7] and c.iloc[10] > (c.iloc[11] + eom_off) and c.iloc[14] > macd and c.iloc[12] > mfi:
            hold = True; bp = n.iloc[1]
            trades_js.append(('BUY', n.iloc[0], bp))
    else:
        pnlR = (n.iloc[1] - bp) / bp
        if pnlR >= tp or pnlR <= -sl:
            hold = False; ep = n.iloc[1]; diff = (ep - bp) * 1000
            trades_js.append(('SELL', n.iloc[0], ep, diff))

# Python simulation
trades_py = []
hold = False; bp = 0
for i in range(1, len(df)-1):
    c = df.iloc[i]; n = df.iloc[i+1]
    if not hold:
        if c.iloc[4] > c.iloc[7] and c.iloc[10] > (c.iloc[11] + eom_off) and c.iloc[14] > macd and c.iloc[12] > mfi:
            hold = True; bp = n.iloc[1]
            trades_py.append(('BUY', n.iloc[0], bp))
    else:
        # EXACT python logic from build_final_high_win.py
        pnlR = (n.iloc[1] - bp) / bp
        exit_flag = False
        if pnlR >= tp or pnlR <= -sl: exit_flag = True
        if exit_flag:
            hold = False; ep = n.iloc[1]; diff = (ep - bp) * 1000
            trades_py.append(('SELL', n.iloc[0], ep, diff))

js_pnl = sum([t[3] for t in trades_js if t[0] == 'SELL'])
py_pnl = sum([t[3] for t in trades_py if t[0] == 'SELL'])

print(f"JS PnL: {js_pnl}")
print(f"PY PnL: {py_pnl}")
