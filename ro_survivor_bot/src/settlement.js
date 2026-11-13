import { logger } from './logger.js';

export class SettlementHandler {
  constructor(page, navigator, config = {}) {
    this.page = page;
    this.navigator = navigator;
    this.adaptive = config.adaptive !== false;
    this.maxStage = config.maxStage || 10;
  }

  async handleOutcome(isVictory) {
    logger.recordEnd(isVictory);

    if (this.adaptive) {
      if (isVictory) {
        const nextStage = Math.min(this.navigator.getStage() + 1, this.maxStage);
        this.navigator.setStage(nextStage);
        logger.info(`自適應推關：通關成功，目標提升至第 ${nextStage} 關`);
      } else {
        logger.info(`自適應推關：挑戰未完成，維持在第 ${this.navigator.getStage()} 關持續重試`);
      }
    }

    // 尋找確認/重新開始/下一關按鈕
    const confirmSelectors = [
      'button:has-text("確認")',
      'button:has-text("OK")',
      'button:has-text("重試")',
      'button:has-text("Retry")',
      'button:has-text("重新開始")',
      'button:has-text("下一關")',
      'button:has-text("Next")',
      'button:has-text("返回")',
      '.btn-confirm',
      '.btn-retry'
    ];

    for (const sel of confirmSelectors) {
      const btn = await this.page.$(sel);
      if (btn && await btn.isVisible()) {
        logger.info(`點擊結算按鈕: ${sel}`);
        await btn.click().catch(() => {});
        await this.page.waitForTimeout(2000);
        return true;
      }
    }

    // 若按鈕在 Canvas 內，嘗試點擊彈窗中央確認區域
    const canvas = await this.page.$('canvas');
    if (canvas) {
      const box = await canvas.boundingBox();
      if (box) {
        logger.info('嘗試點擊 Canvas 結算確認區域...');
        await this.page.mouse.click(box.x + box.width / 2, box.y + box.height * 0.7);
        await this.page.waitForTimeout(1500);
      }
    }

    return true;
  }
}

