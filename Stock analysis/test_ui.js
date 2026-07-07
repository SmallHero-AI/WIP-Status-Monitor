const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    console.log("Launching browser...");
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    
    // Capture console messages
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.toString()));
    
    console.log("Navigating to login...");
    await page.goto('http://localhost:8000/index.html');
    
    await page.type('#username', 'admin');
    await page.type('#password', 'admin0910');
    await page.click('button[type="submit"]');
    
    console.log("Waiting for dashboard...");
    await page.waitForNavigation();
    
    console.log("Waiting for leaderboard to render...");
    await page.waitForSelector('#perf_leaderboard_body tr');
    
    // Click 2455
    console.log("Clicking 2455...");
    await page.evaluate(() => {
        const rows = document.querySelectorAll('#perf_leaderboard_body tr');
        for (let row of rows) {
            if (row.innerText.includes('2455')) {
                row.click();
                return;
            }
        }
    });
    
    console.log("Waiting for 2455 page to render...");
    await page.waitForTimeout(3000); // Wait 3s for chart
    
    const uiData = await page.evaluate(() => {
        const tradesStr = document.querySelector('#s2455_ai_trades')?.innerText;
        const winRateStr = document.querySelector('#s2455_ai_winrate')?.innerText;
        return { trades: tradesStr, winRate: winRateStr };
    });
    console.log("UI Data 2455:", uiData);

    const uiDropdown = await page.evaluate(() => {
        return {
            entryStrat: document.querySelector('#s2455_ai_entry_strat')?.value,
            exitStrat: document.querySelector('#s2455_ai_exit_strat')?.value,
            tp: document.querySelector('#s2455_ai_tp')?.value,
            sl: document.querySelector('#s2455_ai_sl')?.value
        };
    });
    console.log("UI Dropdown 2455:", uiDropdown);
    
    await browser.close();
})();
