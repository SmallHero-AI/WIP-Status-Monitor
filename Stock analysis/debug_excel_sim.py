import pandas as pd
import numpy as np

file_path = "E:\\G-AI-1\\Stock analysis\\Stock original\\2360_致茂_EOM_20260505.xlsx"
df = pd.read_excel(file_path)
df.columns = [str(c) for c in df.columns]
for col in df.columns[1:]:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Simulate Excel formulas
tp = 0.189
sl = 0.08
macd = 2.1
mfi = 30
eom_off = 0.0

excel_P = [False] * (len(df) + 9)
excel_Q = [False] * (len(df) + 9)
excel_R = [False] * (len(df) + 9)
excel_T = [""] * (len(df) + 9)
excel_U = [0.0] * (len(df) + 9)
excel_V = [0.0] * (len(df) + 9)
excel_W = [0.0] * (len(df) + 9)
excel_S = [0.0] * (len(df) + 9)

# Rows in Excel start at 9 for data
# df index 0 is row 9.
for idx in range(len(df)):
    r = idx + 9
    if r == 9:
        excel_P[r] = False
        excel_Q[r] = False
        excel_R[r] = False
        excel_S[r] = 0.0
        excel_W[r] = 0.0
        continue
    
    pR = excel_R[r-1]
    pP = excel_P[r-1]
    pS = excel_S[r-1]
    pW = excel_W[r-1]
    
    # E: Close (4), B: Open (1), H: MA20 (7), I: MA60 (8), K: EOM (10), L: EOMSig (11), O: MACD (14), M: MFI (12)
    B_r = df.iloc[idx, 1]
    E_r = df.iloc[idx, 4]
    H_r = df.iloc[idx, 7]
    K_r = df.iloc[idx, 10]
    L_r = df.iloc[idx, 11]
    O_r = df.iloc[idx, 14]
    M_r = df.iloc[idx, 12]
    
    # Q
    if pR:
        Q_r = ((B_r - pS) / pS >= tp) or ((B_r - pS) / pS <= -sl)
    else:
        Q_r = False
    excel_Q[r] = Q_r
    
    # R needs to be evaluated BEFORE P!
    if not pR:
        R_r = True if pP else False
    else:
        R_r = False if Q_r else True
    excel_R[r] = R_r

    # P
    if df.iloc[idx, 4] == 0 and df.iloc[idx, 1] == 0: # ISBLANK approx
        P_r = False
    else:
        P_r = (E_r > H_r) and (K_r > L_r + eom_off) and (O_r > macd) and (M_r > mfi) and (not R_r)
    excel_P[r] = P_r
    
    # T
    if (not pR) and pP:
        T_r = "買進"
    elif Q_r:
        T_r = "賣出"
    else:
        T_r = ""
    excel_T[r] = T_r
    
    # U
    if T_r == "買進" or T_r == "賣出":
        U_r = B_r
    else:
        U_r = 0.0
    excel_U[r] = U_r
    
    # S
    if (not pR) and pP:
        S_r = B_r
    elif pR and not Q_r:
        S_r = pS
    else:
        S_r = 0.0
    excel_S[r] = S_r
    
    # V
    if T_r == "賣出":
        V_r = (U_r - pS) * 1000
    else:
        V_r = 0.0
    excel_V[r] = V_r
    
    # W
    excel_W[r] = pW + V_r

for r in range(9, len(df)+9):
    if excel_T[r] != "":
        print(f"Row {r} (Idx {r-9}): {excel_T[r]} at {excel_U[r]}. PnL: {excel_V[r]}")

print(f"Excel Final PnL: {excel_W[len(df)+8]}")
