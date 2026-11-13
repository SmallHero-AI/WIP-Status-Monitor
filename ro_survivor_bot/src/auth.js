import { logger } from './logger.js';

export class AuthManager {
  constructor(page, config = {}) {
    this.page = page;
    this.account = config.account || process.env.GAME_ACCOUNT || 'SmallHero';
    this.password = config.password || process.env.GAME_PASSWORD || '0982286057';
    this.gameUrl = config.url || process.env.GAME_URL || 'https://ro-survivors.com/#playinnow-ro-zh-tw';
  }

  async ensureLoggedIn() {
    logger.info(`正在連線至遊戲網頁: ${this.gameUrl}...`);
    await this.page.goto(this.gameUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await this.page.waitForTimeout(3000);

    // 檢查是否已在遊戲大廳 (已存在 #btn-play 或 #lobby-friends)
    const isAlreadyInLobby = await this.page.evaluate(() => {
      const playBtn = document.querySelector('#btn-play');
      const lobbyFriends = document.querySelector('#lobby-friends');
      return !!(playBtn && playBtn.offsetParent !== null) || !!(lobbyFriends && lobbyFriends.offsetParent !== null);
    });

    if (isAlreadyInLobby) {
      logger.success('已偵測到大廳狀態，準備就緒！');
      await this.handleLobbyOrCharacterCreation();
      return true;
    }

    // 檢查是否已有登入身分
    const hasAccountActive = await this.page.evaluate((acc) => {
      const activeBtns = Array.from(document.querySelectorAll('button.active, .sp-user'));
      return activeBtns.some(b => b.innerText.includes(acc));
    }, this.account);

    if (!hasAccountActive) {
      logger.info('未偵測到已登入帳號，準備執行登入流程...');
      await this.performLogin();
    } else {
      logger.success(`帳號 [${this.account}] 已登入`);
    }

    // 等待資源載入與 #sp-play
    await this.waitForAssetLoadingAndEnter();

    // 處理創角或就緒確認
    await this.handleLobbyOrCharacterCreation();

    return true;
  }

  async performLogin() {
    try {
      const haveAccountBtn = await this.page.$(
        'button:has-text("I have an account"), button:has-text("已有帳號"), button:has-text("我有帳號")'
      );
      if (haveAccountBtn && await haveAccountBtn.isVisible()) {
        logger.info('點擊「I have an account」開啟登入面板...');
        await haveAccountBtn.click();
        await this.page.waitForTimeout(1000);
      }

      const userInput = await this.page.locator('input[name="username"]:visible').first();
      const passInput = await this.page.locator('input[name="password"]:visible').first();

      if (await userInput.count() > 0 && await passInput.count() > 0) {
        logger.info(`填入帳號: ${this.account}`);
        await userInput.fill(this.account);

        logger.info('填入密碼...');
        await passInput.fill(this.password);

        await this.page.waitForTimeout(500);

        const submitBtn = await this.page.locator('#sp-login button[type="submit"], button:visible:has-text("Enter")').first();
        if (await submitBtn.count() > 0) {
          logger.info('點擊 Enter 送出登入...');
          await submitBtn.click();
        } else {
          await passInput.press('Enter');
        }

        await this.page.waitForTimeout(3000);
        return true;
      }
    } catch (err) {
      logger.warn('登入表單輸入異常: ' + err.message);
    }
    return false;
  }

  async waitForAssetLoadingAndEnter() {
    logger.info('等待資源快取檢查與 #sp-play 按鈕...');
    try {
      await this.page.waitForSelector('#sp-play', { timeout: 15000 });
    } catch (e) {
      logger.warn('未見 #sp-play，可能已直接進入大廳');
      return;
    }

    let lastProgressText = '';
    const startTime = Date.now();

    while (Date.now() - startTime < 120000) {
      const spInfo = await this.page.evaluate(() => {
        const btn = document.querySelector('#sp-play');
        if (!btn || btn.offsetParent === null) return { visible: false, text: '' };
        return { visible: true, text: btn.innerText.trim() };
      });

      if (!spInfo.visible) break;

      const text = spInfo.text;
      if (text.includes('Loading') || text.includes('載入')) {
        if (text !== lastProgressText) {
          logger.info(`資源加載進度: ${text}`);
          lastProgressText = text;
        }
        await this.page.waitForTimeout(1500);
      } else {
        logger.success(`資源載入完成！按鈕狀態: "${text}"`);
        logger.info('點擊進入遊戲世界...');
        await this.page.click('#sp-play');
        await this.page.waitForTimeout(3000);
        break;
      }
    }
  }

  async handleLobbyOrCharacterCreation() {
    await this.page.waitForTimeout(2000);

    // 檢查是否處於角色創建視窗 (#cc-name)
    const ccName = await this.page.$('#cc-name');
    if (ccName && await ccName.isVisible()) {
      logger.info('目前處於創角介面，輸入角色名稱建立初始角色...');
      await ccName.fill(this.account);
      await this.page.click('#cc-ok');
      await this.page.waitForTimeout(2500);
    } else {
      // 檢查是否真的 0 個角色 (Characters 0/15)
      const isZeroChars = await this.page.evaluate(() => {
        const body = document.body ? document.body.innerText : '';
        return body.includes('0/15');
      });

      if (isZeroChars) {
        const btnCreate = await this.page.$('#btn-create');
        if (btnCreate && await btnCreate.isVisible()) {
          logger.info('帳號尚未有角色 (0/15)，點擊「Create」建立角色...');
          await btnCreate.click();
          await this.page.waitForTimeout(1500);
          const nameInput = await this.page.$('#cc-name');
          if (nameInput) {
            await nameInput.fill(this.account);
            await this.page.click('#cc-ok');
            logger.success(`初始角色 [${this.account}] 建立完成！`);
            await this.page.waitForTimeout(2500);
          }
        }
      }
    }

    // 點選第一個角色欄位以確保選取
    await this.page.evaluate(() => {
      const slots = document.querySelectorAll('button:has-text("Empty slot"), .slot, [class*="character"]');
      if (slots.length > 0) slots[0].click();
    }).catch(() => {});

    // 檢查大廳 Play 按鈕
    const playBtn = await this.page.$('#btn-play');
    if (playBtn && await playBtn.isVisible()) {
      logger.success('大廳就緒，Play 按鈕已可點擊！');
    }
  }
}
