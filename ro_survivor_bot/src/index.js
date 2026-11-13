import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { BrowserManager } from './browser.js';
import { AuthManager } from './auth.js';
import { Navigator } from './navigator.js';
import { StateDetector } from './combat/stateDetector.js';
import { MovementController } from './combat/movement.js';
import { SkillPicker } from './combat/skillPicker.js';
import { SettlementHandler } from './settlement.js';
import { Watchdog } from './watchdog.js';
import { logger } from './logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  console.clear();
  logger.info('=============================================');
  logger.info('   RO Survivors 自動遊玩機器人 啟動中...      ');
  logger.info('=============================================');

  // 讀取設定檔
  const configPath = path.resolve(__dirname, '../config.json');
  let config = {};
  if (fs.existsSync(configPath)) {
    try {
      config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch (e) {
      logger.warn('讀取 config.json 失敗，使用預設配置');
    }
  }

  const browserManager = new BrowserManager();
  const page = await browserManager.launch();

  const authManager = new AuthManager(page);
  const navigator = new Navigator(page, config.progression);
  const stateDetector = new StateDetector(page);
  const movement = new MovementController(page, config.combat);
  const skillPicker = new SkillPicker(page, config.skills);
  const settlement = new SettlementHandler(page, navigator, config.progression);
  const watchdog = new Watchdog(config.watchdog?.timeoutMs || 60000);

  // 確保登入與大廳就緒
  let loggedIn = false;
  while (!loggedIn) {
    try {
      loggedIn = await authManager.ensureLoggedIn();
      if (!loggedIn) {
        logger.warn('登入未完成，5 秒後重新嘗試...');
        await page.waitForTimeout(5000);
      }
    } catch (e) {
      logger.error('登入過程異常: ' + e.message);
      await page.waitForTimeout(5000);
    }
  }

  logger.success('登入與角色就緒，進入自動掛機主迴圈！');
  watchdog.feed();

  let isInRun = false;

  // 主運作迴圈
  while (true) {
    try {
      // 檢查看門狗
      if (watchdog.isStuck()) {
        logger.warn(`偵測到畫面停滯超過 ${watchdog.getElapsedSec()} 秒，觸發看門狗保護重啟！`);
        await movement.stopAll();
        isInRun = false;
        await page.reload({ waitUntil: 'domcontentloaded' }).catch(() => {});
        await page.waitForTimeout(5000);
        await authManager.ensureLoggedIn().catch(() => {});
        watchdog.reset();
        continue;
      }

      // 偵測遊戲當前狀態
      const stateInfo = await stateDetector.detectState();

      switch (stateInfo.state) {
        case 'ENTERING':
          // 正在傳送加載地圖
          await movement.stopAll();
          logger.info('地圖傳送加載中 (Entering...)');
          watchdog.feed();
          await page.waitForTimeout(1500);
          break;

        case 'LOBBY':
          // 角色大廳介面
          await movement.stopAll();
          isInRun = false;
          logger.info('角色處於大廳介面，點擊「Play」進入城鎮...');
          await navigator.enterBattle();
          watchdog.feed();
          await page.waitForTimeout(2000);
          break;

        case 'IN_TOWN':
          // 角色在城鎮噴水池廣場中，執行 NPC 出發對話流程
          await movement.stopAll();
          isInRun = false;
          logger.info('角色處於普隆德拉城鎮，觸發遠征隊長出發流程...');
          const dispatched = await navigator.enterBattlefieldFromTown();
          if (dispatched) {
            watchdog.feed();
          }
          await page.waitForTimeout(2000);
          break;

        case 'LEVEL_UP':
          // 戰鬥升級選技能 (.pk-card)
          await movement.stopAll();
          logger.info('★ 偵測到升級畫面 (.pk-card)，呼叫 AI 技能評分引擎選卡...');
          await skillPicker.selectBestSkill(stateInfo.options);
          watchdog.feed();
          break;

        case 'PLAYING':
          // 野外戰鬥進行中
          if (!isInRun) {
            isInRun = true;
            logger.startRun(navigator.getStage());
          }
          await movement.updateMovement();
          logger.combatPulse(navigator.getStage());
          watchdog.feed();
          break;

        case 'VICTORY':
          // 通關結算
          await movement.stopAll();
          isInRun = false;
          logger.info('戰鬥結束：勝利通關！');
          await settlement.handleOutcome(true);
          watchdog.feed();
          await page.waitForTimeout(3000);
          break;

        case 'GAME_OVER':
          // 戰鬥失敗
          await movement.stopAll();
          isInRun = false;
          logger.info('戰鬥結束：挑戰結束/陣亡！');
          await settlement.handleOutcome(false);
          watchdog.feed();
          await page.waitForTimeout(3000);
          break;

        default:
          await page.waitForTimeout(500);
          break;
      }

      await page.waitForTimeout(config.combat?.tickRateMs || 100);
    } catch (loopError) {
      logger.error('主迴圈單次 Tick 異常: ' + loopError.message);
      await page.waitForTimeout(1000);
    }
  }
}

// 攔截中斷信號 (Ctrl+C)
process.on('SIGINT', async () => {
  logger.info('\n收到結束訊號，正在安全退出...');
  process.exit(0);
});

main().catch(err => {
  logger.error('主程式崩潰退出: ' + err.message, err);
  process.exit(1);
});
