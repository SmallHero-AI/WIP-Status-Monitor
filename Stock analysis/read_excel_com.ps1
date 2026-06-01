$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
$workbook = $excel.Workbooks.Open("E:\G-AI-1\Stock analysis\2360_致茂_V4_高勝率回測.xlsx")
$sheet = $workbook.Sheets.Item("Top1_回測")

$lastRow = $sheet.Cells.SpecialCells(11).Row

$wValue = $sheet.Range("W$lastRow").Value()
$vValue = $sheet.Range("V$lastRow").Value()

Write-Host "Last Row: $lastRow"
Write-Host "V value: $vValue"
Write-Host "W value: $wValue"

$workbook.Close($false)
$excel.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($excel) | Out-Null
