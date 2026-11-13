import { logger } from '../logger.js';

export class SkillPicker {
  constructor(page, config = {}) {
    this.page = page;
    this.priorityKeywords = config.priorityKeywords || [
      'bash', '狂擊',
      'sword', '劍',
      'provoke', '挑釁',
      'arrow', '箭雨',
      'storm gust', '暴風雪',
      'meteor', '隕石',
      'thunder', '雷鳴',
      'heal', '治癒', 'hp', '生命',
      'speed', '速度', 'agi',
      'atk', 'damage', '攻擊',
      'cooldown', '冷卻',
      'crit', '暴擊'
    ];
  }

  scoreCard(cardText, index) {
    let score = 10 - index; // 預設優先靠左
    const text = (cardText || '').toLowerCase();

    // 依據關鍵字優先序加權
    for (let i = 0; i < this.priorityKeywords.length; i++) {
      const kw = this.priorityKeywords[i].toLowerCase();
      if (text.includes(kw)) {
        score += (this.priorityKeywords.length - i) * 20;
      }
    }

    // 若為升階 (Lv 2, Lv 3 等) 提升基礎武器加成
    if (text.includes('lv 2') || text.includes('lv 3') || text.includes('lv 4')) {
      score += 35;
    }

    return score;
  }

  async selectBestSkill(options = []) {
    if (!options || options.length === 0) {
      // 預設發送數字鍵 1 盲選第一張
      logger.info('未獲取到結構化卡片，發送鍵盤「1」選取第一項技能...');
      await this.page.keyboard.press('Digit1');
      await this.page.waitForTimeout(600);
      return true;
    }

    let bestChoice = options[0];
    let highestScore = -1;

    for (const opt of options) {
      const score = this.scoreCard(opt.text, opt.index);
      const cleanText = opt.text.replace(/\n/g, ' | ');
      logger.info(`評估技能 [選項 ${opt.index}]: "${cleanText}" -> 評分: ${score}`);
      if (score > highestScore) {
        highestScore = score;
        bestChoice = opt;
      }
    }

    const chosenText = bestChoice.text.replace(/\n/g, ' | ');
    logger.skill(`★ 選擇技能 [${bestChoice.index}]: "${chosenText}" (最高評分: ${highestScore})`);

    // 雙重觸發：優先發送鍵盤數字鍵 (Digit1 / Digit2 / Digit3)
    const key = `Digit${bestChoice.index}`;
    await this.page.keyboard.press(key).catch(() => {});
    await this.page.waitForTimeout(300);

    // 輔助點擊卡片元素位置
    if (bestChoice.x && bestChoice.y) {
      await this.page.mouse.click(bestChoice.x, bestChoice.y).catch(() => {});
    } else {
      await this.page.locator('.pk-card').nth(bestChoice.index - 1).click().catch(() => {});
    }

    await this.page.waitForTimeout(800);
    return true;
  }
}
