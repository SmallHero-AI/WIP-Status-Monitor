const fs = require('fs');
const html = fs.readFileSync('E:/G-AI-1/Stock analysis/修正版_V6_Server/public/dashboard_v8_3.html', 'utf8');
console.log('tab_holding_summary:', html.includes('tab_holding_summary'));
console.log('folder_holding_summary:', html.includes('folder_holding_summary'));
console.log('value=90:', html.includes('value="90"'));
console.log('perf_filter_holding:', html.includes('perf_filter_holding'));
console.log('grids:', html.includes('holding_grid_long') && html.includes('holding_grid_short'));
console.log('ends correctly:', html.trim().endsWith('</html>'));
