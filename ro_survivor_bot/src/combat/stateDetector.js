export class StateDetector {
  constructor(page) {
    this.page = page;
  }

  async detectState() {
    return await this.page.evaluate(() => {
      const isVisible = (el) => el && el.offsetParent !== null;

      // 0. 檢查地圖載入/傳送狀態 (Entering ...)
      const bodyText = document.body ? document.body.innerText : '';
      if (bodyText.includes('Entering')) {
        return { state: 'ENTERING' };
      }

      // 1. 檢查升級選技能彈窗 (.pk-card)
      const pkCards = Array.from(document.querySelectorAll('.pk-card, [class*="pk-card"]')).filter(isVisible);
      if (pkCards.length > 0) {
        const options = pkCards.map((card, index) => {
          const rect = card.getBoundingClientRect();
          return {
            index: index + 1, // 1, 2, 3
            text: card.innerText || '',
            x: rect.x + rect.width / 2,
            y: rect.y + rect.height / 2
          };
        });
        return { state: 'LEVEL_UP', options };
      }

      // 2. 檢查角色大廳 / 登入介面 (LOBBY)
      // 若大廳 Play 或 Create 按鈕可見，優先執行進入/選角
      const playBtn = document.querySelector('#btn-play');
      const spPlay = document.querySelector('#sp-play');
      const createBtn = document.querySelector('#btn-create');
      const loginPane = document.querySelector('#sp-login');

      if (isVisible(playBtn) || isVisible(spPlay) || isVisible(createBtn) || isVisible(loginPane)) {
        return { state: 'LOBBY' };
      }

      // 3. 檢查是否在城鎮噴水池廣場 (IN_TOWN)
      const lobbyPrompt = document.querySelector('#lobby-prompt');
      const stgGo = document.querySelector('#stg-go, .stg-go');
      const goFieldBtn = Array.from(document.querySelectorAll('button')).find(
        b => isVisible(b) && b.innerText.includes('Go to the field')
      );
      const isLobbyModalOpen = Array.from(document.querySelectorAll('.ch-row.lb')).some(isVisible);

      if (isVisible(lobbyPrompt) || isVisible(stgGo) || !!goFieldBtn || isLobbyModalOpen) {
        return { state: 'IN_TOWN' };
      }

      // 4. 檢查結算畫面 (勝利 / 失敗 / 陣亡)
      const isDefeat = /失敗|Defeat|Game Over|陣亡|復活|重新開始|重試|Revive/i.test(bodyText) &&
        Array.from(document.querySelectorAll('button')).some(b => isVisible(b) && /重試|重新開始|確認|Retry|OK|Revive|Leave/i.test(b.innerText));
      const isVictory = /勝利|通關|Victory|Stage Clear|Congratulations/i.test(bodyText) &&
        Array.from(document.querySelectorAll('button')).some(b => isVisible(b) && /下一關|Next|確認|OK/i.test(b.innerText));

      if (isVictory) return { state: 'VICTORY' };
      if (isDefeat) return { state: 'GAME_OVER' };

      // 5. 戰鬥進行中 (Canvas 渲染中且非大廳/城鎮)
      const canvas = document.querySelector('canvas');
      if (canvas) {
        const rect = canvas.getBoundingClientRect();
        return {
          state: 'PLAYING',
          canvasBox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
        };
      }

      return { state: 'LOBBY' };
    });
  }
}
