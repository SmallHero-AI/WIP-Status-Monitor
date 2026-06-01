import win32com.client
import os

excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = False
file_path = r"E:\G-AI-1\Stock analysis\2360_致茂_V4_高勝率回測.xlsx"

if os.path.exists(file_path):
    wb = excel.Workbooks.Open(file_path)
    ws = wb.Sheets("Top1_回測")
    last_row = ws.Cells(ws.Rows.Count, "W").End(-4162).Row # xlUp
    
    val_w = ws.Range(f"W{last_row}").Value
    
    print(f"Last Row: {last_row}")
    print(f"Value in W: {val_w}")
    
    wb.Close(False)
else:
    print(f"File not found: {file_path}")

excel.Quit()
