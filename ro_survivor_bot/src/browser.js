import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import { logger } from './logger.js';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class BrowserManager {
  constructor(options = {}) {
    this.headless = options.headless !== undefined 
      ? options.headless 
      : (process.env.HEADLESS === 'true' || process.argv.includes('--headless'));
    this.userDataDir = path.resolve(__dirname, '../user_data');
    this.context = null;
    this.page = null;
  }

  async launch() {
    logger.info(`正在啟動持久化 Chromium 瀏覽器 (Headless: ${this.headless})...`);
    logger.info(`使用者設定檔與遊戲快取目錄: ${this.userDataDir}`);

    this.context = await chromium.launchPersistentContext(this.userDataDir, {
      headless: this.headless,
      viewport: { width: 1280, height: 850 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-blink-features=AutomationControlled',
        '--window-size=1280,850'
      ]
    });

    const pages = this.context.pages();
    this.page = pages.length > 0 ? pages[0] : await this.context.newPage();

    // 注入 Hook 監聽 Canvas
    await this.page.addInitScript(() => {
      const origCreate = document.createElement.bind(document);
      document.createElement = function(tagName, ...args) {
        const el = origCreate(tagName, ...args);
        if (tagName.toLowerCase() === 'canvas') {
          window.__GAME_CANVAS__ = el;
        }
        return el;
      };
    });

    logger.success('瀏覽器啟動完成');
    return this.page;
  }

  async close() {
    if (this.context) {
      await this.context.close();
      this.context = null;
      this.page = null;
      logger.info('瀏覽器已關閉');
    }
  }

  getPage() {
    return this.page;
  }
}
