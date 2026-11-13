import { logger } from './logger.js';

export class Navigator {
  constructor(page, config = {}) {
    this.page = page;
    this.currentStage = config.currentStage || 1;
    this.adaptive = config.adaptive !== false;
  }

  setStage(stage) {
    this.currentStage = stage;
  }

  getStage() {
    return this.currentStage;
  }

  /**
   * 進入大廳並出發至戰場的完整管道
   */
  async enterBattle() {
    try {
      // 1. 若目前在大廳角色選擇畫面，點擊 Play
      const playBtn = await this.page.$('#btn-play');
      if (playBtn && await playBtn.isVisible()) {
        const isDisabled = await playBtn.isDisabled().catch(() => false);
        if (!isDisabled) {
          logger.info('在大廳點擊「Play」進入城鎮...');
          await playBtn.click();
          await this.page.waitForTimeout(3000);
        } else {
          // 點選第一個角色欄位
          const firstSlot = await this.page.$('[class*="slot"], [class*="character"]');
          if (firstSlot) {
            await firstSlot.click();
            await this.page.waitForTimeout(1000);
          }
        }
      }

      // 等待城鎮載入完成
      await this.page.waitForFunction(() => {
        const text = document.body ? document.body.innerText : '';
        return !text.includes('Entering Prontera') && !text.includes('Entering...');
      }, { timeout: 25000 }).catch(() => {});
      await this.page.waitForTimeout(2000);

      // 2. 從城鎮進入野外戰場
      return await this.enterBattlefieldFromTown();
    } catch (err) {
      logger.error('進入戰鬥流程錯誤: ' + err.message);
      return false;
    }
  }

  /**
   * 在普隆德拉城鎮中：關閉分流彈窗 -> 與遠征隊長對話 -> 選關 -> 點擊出發與進入原野
   */
  async enterBattlefieldFromTown() {
    try {
      // 步驟 1: 等待城鎮 UI 或分流彈窗就緒
      await this.page.waitForSelector('.ch-row.lb, button:has-text("Play offline"), #lobby-prompt, #stg-go', { timeout: 10000 }).catch(() => {});

      // 步驟 2: 若有分流選擇彈窗 (Choose a lobby)，點擊分流關閉它
      const lobbyBtn = await this.page.$('.ch-row.lb, button:has-text("Play offline"), button:has-text("Asgard")');
      if (lobbyBtn && await lobbyBtn.isVisible()) {
        logger.info('點擊分流關閉 Choose a lobby 視窗...');
        await lobbyBtn.click();
        await this.page.waitForTimeout(1200);
      }

      // 步驟 3: 若已在 Difficulty 彈窗，直接點擊 Go to the field
      const directGoField = await this.page.$('button:has-text("Go to the field"), .ro-btn.primary:has-text("Go to")');
      if (directGoField && await directGoField.isVisible()) {
        logger.info('偵測到難度視窗，點擊「Go to the field」...');
        await directGoField.click();
        await this.waitForBattlefieldLoad();
        return true;
      }

      // 步驟 4: 若已在 Expeditions 視窗，直接點擊 Set out
      const directSetOut = await this.page.$('#stg-go, .stg-go');
      if (directSetOut && await directSetOut.isVisible()) {
        logger.info('偵測到關卡視窗，點擊「Set out」出發...');
        await directSetOut.click();
        await this.page.waitForTimeout(1500);

        const fieldBtn = await this.page.$('button:has-text("Go to the field"), .ro-btn.primary:has-text("Go to")');
        if (fieldBtn && await fieldBtn.isVisible()) {
          await fieldBtn.click();
          await this.waitForBattlefieldLoad();
          return true;
        }
      }

      // 步驟 5: 與遠征隊長對話
      logger.info('等待遠征隊長提示按鈕 (#lobby-prompt)...');
      await this.page.waitForSelector('#lobby-prompt', { timeout: 8000 }).catch(() => {});
      const promptBtn = await this.page.$('#lobby-prompt');
      if (promptBtn && await promptBtn.isVisible()) {
        logger.info('點擊畫面提示按鈕與遠征隊長對話...');
        await promptBtn.click().catch(async () => {
          await this.page.keyboard.press('Space');
        });
      } else {
        logger.info('未見按鈕，直接發送 Space 鍵對話...');
        await this.page.keyboard.press('Space');
      }

      // 步驟 6: 等待 Expeditions 關卡視窗出現並點擊 Set out (#stg-go)
      logger.info('等待 Expeditions 關卡選單出現 (#stg-go)...');
      await this.page.waitForSelector('#stg-go', { timeout: 10000 }).catch(() => {});
      const stgGoBtn = await this.page.$('#stg-go, .stg-go');
      if (stgGoBtn && await stgGoBtn.isVisible()) {
        logger.info('點擊「Set out」出發...');
        await stgGoBtn.click();
        await this.page.waitForTimeout(1500);

        // 步驟 7: 點擊 Go to the field 確認進入
        logger.info('等待難度視窗並點擊「Go to the field」...');
        await this.page.waitForSelector('button:has-text("Go to the field")', { timeout: 8000 }).catch(() => {});
        const confirmBtn = await this.page.$('button:has-text("Go to the field"), .ro-btn.primary:has-text("Go to")');
        if (confirmBtn && await confirmBtn.isVisible()) {
          logger.info('點擊「Go to the field」確認進入野外戰場！');
          await confirmBtn.click();
          await this.waitForBattlefieldLoad();
          return true;
        }
      }

      return false;
    } catch (e) {
      logger.warn('城鎮出發異常: ' + e.message);
      return false;
    }
  }

  async waitForBattlefieldLoad() {
    logger.info('等待野外戰場載入中 (Entering battlefield...)...');
    await this.page.waitForFunction(() => {
      const text = document.body ? document.body.innerText : '';
      return !text.includes('Entering');
    }, { timeout: 30000 }).catch(() => {});
    await this.page.waitForTimeout(2000);
    logger.success('★ 已正式傳送進入野外戰場！');
  }
}
