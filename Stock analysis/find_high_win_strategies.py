import pandas as pd
import numpy as np
import itertools
import os

input_dir = "E:\\G-AI-1\\Stock analysis\\Stock original"
stock_data = {}
for file in os.listdir(input_dir):
    if file.endswith(".xlsx"):
        code = file.split('_')[0]
        df = pd.read_excel(os.path.join(input_dir, file))
        df.columns = [str(c) for c in df.columns]
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        stock_data[code] = {'df': df, 'file': file}

def evaluate_strategy(df, params, strat_type):
    close_arr, open_arr, high_arr = df.iloc[:, 4].values, df.iloc[:, 1].values, df.iloc[:, 2].values
    ma20_arr, ma60_arr = df.iloc[:, 7].values, df.iloc[:, 8].values
    eom_arr, eomsig_arr = df.iloc[:, 10].values, df.iloc[:, 11].values
    mfi_arr, macd_arr = df.iloc[:, 12].values, df.iloc[:, 14].values
    
    hold = False; buy_price = 0.0; pnls = []; entry_prices = []; mPrf = 0
    
    for i in range(2, len(df)-1):
        c_close, n_open = close_arr[i], open_arr[i+1]
        c_ma20, c_ma60 = ma20_arr[i], ma60_arr[i]
        c_eom, c_eomsig = eom_arr[i], eomsig_arr[i]
        c_mfi, c_macd = mfi_arr[i], macd_arr[i]
        p_eom, p_eomsig = eom_arr[i-1], eomsig_arr[i-1]
        p_high, p_macd = high_arr[i-1], macd_arr[i-1]
        
        if not hold:
            entry = False
            if strat_type == 'V4': entry = c_close > c_ma20 and c_eom > (c_eomsig + params.get('eom_off',0)) and c_macd > params['macd'] and c_mfi > params['mfi']
            elif strat_type == 'V38': entry = (c_eom > (c_eomsig + params.get('eom_sens',0.5)) and p_eom <= (p_eomsig + params.get('eom_sens',0.5))) and c_close > c_ma20 and c_close > p_high and c_macd > p_macd
            elif strat_type == 'V_Rebound': entry = c_close < c_ma20 and c_mfi < params['mfi_s'] and c_macd > p_macd
            elif strat_type == 'V_Trend_Catch': entry = c_close > c_ma60 and c_eom > c_eomsig and c_macd > params['macd']
            elif strat_type == 'V_Dip_Buy': entry = c_mfi < params['mfi_s'] and c_eom > p_eom and c_macd > 0

            if entry:
                hold = True; buy_price = n_open; mPrf = 0; entry_prices.append(buy_price)
        else:
            pnlR = (n_open - buy_price) / buy_price
            curR = (c_close - buy_price) / buy_price
            mPrf = max(mPrf, curR)
            exit_flag = False
            
            if strat_type in ['V38']:
                if mPrf >= params['tri'] and pnlR <= params['lock']: exit_flag = True
                elif c_eom < c_eomsig: exit_flag = True
                elif pnlR <= -params['sl']: exit_flag = True
            elif strat_type in ['V_Rebound', 'V_Dip_Buy']:
                if c_mfi > params.get('mfi_b', 80) or pnlR >= params['tp'] or pnlR <= -params['sl']: exit_flag = True
            else:
                if pnlR >= params['tp'] or pnlR <= -params['sl']: exit_flag = True
                
            if exit_flag:
                hold = False
                pnls.append((n_open - buy_price) * 1000)
    
    if len(pnls) < 2: return -999999, {}
    cp = sum(pnls)
    win_rate = len([p for p in pnls if p > 0]) / len(pnls)
    return cp, {'勝率': win_rate, '交易次數': len(pnls), '累積淨損益': cp}

strats_to_test = {
    'V4': [dict(tp=t,sl=s,macd=md,mfi=mf,eom_off=eo) for t,s,md,mf,eo in itertools.product(np.arange(0.05, 0.25, 0.01), np.arange(0.03, 0.10, 0.01), [-0.5, 0.0, 0.5, 1.0, 2.0, 2.1], [30, 35, 40, 45], [0.0, 0.5])],
    'V38': [dict(tri=t,lock=l,sl=s,eom_sens=e) for t,l,s,e in itertools.product(np.arange(0.02, 0.15, 0.01), np.arange(0.01, 0.10, 0.01), np.arange(0.03, 0.10, 0.01), [0.0, 0.5]) if t > l],
    'V_Rebound': [dict(tp=t,sl=s,mfi_s=mf,mfi_b=mb) for t,s,mf,mb in itertools.product(np.arange(0.05, 0.20, 0.01), np.arange(0.03, 0.10, 0.01), [20, 25, 30, 35], [75, 80, 85])],
    'V_Trend_Catch': [dict(tp=t,sl=s,macd=md) for t,s,md in itertools.product(np.arange(0.05, 0.25, 0.01), np.arange(0.03, 0.10, 0.01), [0.0, 0.5, 1.0])],
    'V_Dip_Buy': [dict(tp=t,sl=s,mfi_s=mf) for t,s,mf in itertools.product(np.arange(0.05, 0.25, 0.01), np.arange(0.03, 0.10, 0.01), [20, 25, 30, 35])]
}

print("Testing all strategies for all stocks to find best combination...")
results = {}

for code, data in stock_data.items():
    if code not in ['2330', '3443', '2360', '6669', '3455', '3535', '4746', '4908', '3189', '6205', '6261', '6269']: continue
    
    df = data['df']
    best_overall_wr = -1
    best_overall_pnl = -999999
    best_strat = None
    best_p = None
    
    # 針對 user 特別指定的 2360 測試他的參數
    if code == '2360':
        pnl, stat = evaluate_strategy(df, {'tp':0.189, 'sl':0.08, 'macd':2.1, 'mfi':30, 'eom_off':0.0}, 'V4')
        print(f"2360 User Param Test: PnL={pnl}, WR={stat.get('勝率')}, Trades={stat.get('交易次數')}")
        
    for strat_name, grid in strats_to_test.items():
        # 如果是 2330, 強制 V4
        if code == '2330' and strat_name != 'V4': continue
        if code == '3443' and strat_name != 'V38': continue
        
        # 為了加速，取部分 sample，但在這裡我們全跑因為要挑最好
        for p in grid:
            pnl, stat = evaluate_strategy(df, p, strat_name)
            wr = stat.get('勝率', -1)
            # 以勝率為第一優先，若勝率 >= 0.65，再看 PnL
            # 但若所有勝率都小於 0.65，挑最高的
            if pnl > 0 and stat.get('交易次數', 0) >= 3:
                # 複合評分：(勝率) * 10000000 + PnL
                score = wr * 10000000 + pnl
                best_score = best_overall_wr * 10000000 + best_overall_pnl
                if score > best_score:
                    best_overall_wr = wr
                    best_overall_pnl = pnl
                    best_strat = strat_name
                    best_p = p.copy()
                    
    results[code] = {'strat': best_strat, 'wr': best_overall_wr, 'pnl': best_overall_pnl, 'params': best_p}
    print(f"{code}: Best Strat = {best_strat}, WR = {best_overall_wr:.2%}, PnL = {best_overall_pnl}, Params = {best_p}")

