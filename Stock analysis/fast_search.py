import pandas as pd
import numpy as np
import itertools
import os

input_dir = "E:\\G-AI-1\\Stock analysis\\Stock original"
stock_data = {}
for file in os.listdir(input_dir):
    if file.endswith(".xlsx"):
        code = file.split('_')[0]
        if code not in ['2330', '3443', '2360', '6669', '3455', '3535', '4746', '4908', '3189', '6205', '6261', '6269']: continue
        df = pd.read_excel(os.path.join(input_dir, file))
        df.columns = [str(c) for c in df.columns]
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Precompute arrays for speed
        stock_data[code] = {
            'c_arr': df.iloc[:, 4].values,
            'o_arr': df.iloc[:, 1].values,
            'h_arr': df.iloc[:, 2].values,
            'ma20_arr': df.iloc[:, 7].values,
            'ma60_arr': df.iloc[:, 8].values,
            'eom_arr': df.iloc[:, 10].values,
            'eomsig_arr': df.iloc[:, 11].values,
            'mfi_arr': df.iloc[:, 12].values,
            'macd_arr': df.iloc[:, 14].values,
            'n_len': len(df)
        }

def evaluate_fast(data, params, strat_type):
    c_arr, o_arr, h_arr = data['c_arr'], data['o_arr'], data['h_arr']
    ma20_arr, ma60_arr = data['ma20_arr'], data['ma60_arr']
    eom_arr, eomsig_arr = data['eom_arr'], data['eomsig_arr']
    mfi_arr, macd_arr = data['mfi_arr'], data['macd_arr']
    
    hold = False; buy_price = 0.0; pnls = []; mPrf = 0
    
    tp = params.get('tp')
    sl = params.get('sl')
    macd_p = params.get('macd')
    mfi_p = params.get('mfi')
    eom_off = params.get('eom_off')
    eom_sens = params.get('eom_sens')
    mfi_s = params.get('mfi_s')
    mfi_b = params.get('mfi_b')
    tri = params.get('tri')
    lock = params.get('lock')
    
    for i in range(2, data['n_len']-1):
        if not hold:
            if strat_type == 'V4':
                entry = c_arr[i] > ma20_arr[i] and eom_arr[i] > (eomsig_arr[i] + eom_off) and macd_arr[i] > macd_p and mfi_arr[i] > mfi_p
            elif strat_type == 'V38':
                entry = (eom_arr[i] > (eomsig_arr[i] + eom_sens) and eom_arr[i-1] <= (eomsig_arr[i-1] + eom_sens)) and c_arr[i] > ma20_arr[i] and c_arr[i] > h_arr[i-1] and macd_arr[i] > macd_arr[i-1]
            elif strat_type == 'V_Rebound':
                entry = c_arr[i] < ma20_arr[i] and mfi_arr[i] < mfi_s and macd_arr[i] > macd_arr[i-1]
            elif strat_type == 'V_Trend_Catch':
                entry = c_arr[i] > ma60_arr[i] and eom_arr[i] > eomsig_arr[i] and macd_arr[i] > macd_p
            elif strat_type == 'V_Dip_Buy':
                entry = mfi_arr[i] < mfi_s and eom_arr[i] > eom_arr[i-1] and macd_arr[i] > 0

            if entry: hold = True; buy_price = o_arr[i+1]; mPrf = 0
        else:
            pnlR = (o_arr[i+1] - buy_price) / buy_price
            curR = (c_arr[i] - buy_price) / buy_price
            if curR > mPrf: mPrf = curR
            
            if strat_type == 'V38':
                if (mPrf >= tri and pnlR <= lock) or (eom_arr[i] < eomsig_arr[i]) or (pnlR <= -sl):
                    hold = False; pnls.append(o_arr[i+1] - buy_price)
            elif strat_type in ['V_Rebound', 'V_Dip_Buy']:
                if mfi_arr[i] > mfi_b or pnlR >= tp or pnlR <= -sl:
                    hold = False; pnls.append(o_arr[i+1] - buy_price)
            else:
                if pnlR >= tp or pnlR <= -sl:
                    hold = False; pnls.append(o_arr[i+1] - buy_price)
    
    if len(pnls) < 3: return -999999, 0
    return sum(pnls)*1000, len([p for p in pnls if p > 0]) / len(pnls)

strats_to_test = {
    'V4': [dict(tp=t,sl=s,macd=md,mfi=mf,eom_off=eo) for t,s,md,mf,eo in itertools.product(np.arange(0.08, 0.22, 0.02), np.arange(0.04, 0.10, 0.02), [0.0, 1.0, 2.1], [30, 40], [0.0])],
    'V38': [dict(tri=t,lock=l,sl=s,eom_sens=e) for t,l,s,e in itertools.product(np.arange(0.03, 0.12, 0.02), np.arange(0.02, 0.08, 0.02), np.arange(0.04, 0.09, 0.02), [0.5]) if t > l],
    'V_Rebound': [dict(tp=t,sl=s,mfi_s=mf,mfi_b=mb) for t,s,mf,mb in itertools.product(np.arange(0.08, 0.20, 0.02), np.arange(0.04, 0.10, 0.02), [25, 30, 35], [75, 80])],
    'V_Trend_Catch': [dict(tp=t,sl=s,macd=md) for t,s,md in itertools.product(np.arange(0.08, 0.22, 0.02), np.arange(0.04, 0.10, 0.02), [0.0, 0.5])],
    'V_Dip_Buy': [dict(tp=t,sl=s,mfi_s=mf,mfi_b=80) for t,s,mf in itertools.product(np.arange(0.08, 0.22, 0.02), np.arange(0.04, 0.10, 0.02), [25, 30, 35])]
}

results = {}
for code, data in stock_data.items():
    if code == '2360':
        pnl, wr = evaluate_fast(data, {'tp':0.189, 'sl':0.08, 'macd':2.1, 'mfi':30, 'eom_off':0.0}, 'V4')
        print(f"2360 User Param Test (V4): PnL={pnl}, WR={wr}")
        
    best_overall_wr = -1; best_overall_pnl = -999999; best_strat = None; best_p = None
    
    for strat_name, grid in strats_to_test.items():
        if code == '2330' and strat_name != 'V4': continue
        if code == '3443' and strat_name != 'V38': continue
        
        for p in grid:
            pnl, wr = evaluate_fast(data, p, strat_name)
            if pnl > 0:
                score = wr * 10000000 + pnl
                if score > (best_overall_wr * 10000000 + best_overall_pnl):
                    best_overall_wr = wr; best_overall_pnl = pnl; best_strat = strat_name; best_p = p.copy()
                    
    results[code] = {'strat': best_strat, 'wr': best_overall_wr, 'pnl': best_overall_pnl, 'params': best_p}
    print(f"{code}: Best Strat = {best_strat}, WR = {best_overall_wr:.2%}, PnL = {best_overall_pnl}, Params = {best_p}")
