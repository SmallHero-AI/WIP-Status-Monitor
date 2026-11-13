import { logger } from '../logger.js';

export class MovementController {
  constructor(page, config = {}) {
    this.page = page;
    this.tickRateMs = config.tickRateMs || 100;
    this.activeKeys = new Set();
    this.currentAngle = 0;
    this.orbitRadius = config.kitingRadius || 200;
    this.step = 0;
  }

  /**
   * 根據人工勢場 / 風箏演算法更新角色移動
   * @param {Object} options 包含敵人相對位置或自適應巡航參數
   */
  async updateMovement(options = {}) {
    // 預設計算風箏軌道向量 (動態橢圓繞圈 + 擺動避障)
    this.step += 1;
    // 每 20 step 微調角速度，產生自然的走位與拉怪節奏
    const angularSpeed = 0.12 + Math.sin(this.step / 15) * 0.04;
    this.currentAngle = (this.currentAngle + angularSpeed) % (2 * Math.PI);

    // 基礎風箏向量 (圓周法線 + 切線引導)
    let vx = Math.cos(this.currentAngle);
    let vy = Math.sin(this.currentAngle);

    // 若有周遭敵人反作用力向量 (Repulsion)
    if (options.repulsion && (options.repulsion.x !== 0 || options.repulsion.y !== 0)) {
      vx += options.repulsion.x * 1.5;
      vy += options.repulsion.y * 1.5;
    }

    // 歸一化
    const len = Math.sqrt(vx * vx + vy * vy) || 1;
    vx /= len;
    vy /= len;

    // 將向量映射至 WASD 按鍵
    const targetKeys = new Set();
    const deadzone = 0.35;

    if (vx > deadzone) targetKeys.add('KeyD');
    else if (vx < -deadzone) targetKeys.add('KeyA');

    if (vy > deadzone) targetKeys.add('KeyS');
    else if (vy < -deadzone) targetKeys.add('KeyW');

    // 比對目前按下的按鍵，執行釋放 (keyup) 與按下 (keydown)
    for (const key of this.activeKeys) {
      if (!targetKeys.has(key)) {
        await this.page.keyboard.up(key).catch(() => {});
        this.activeKeys.delete(key);
      }
    }

    for (const key of targetKeys) {
      if (!this.activeKeys.has(key)) {
        await this.page.keyboard.down(key).catch(() => {});
        this.activeKeys.add(key);
      }
    }
  }

  async stopAll() {
    for (const key of this.activeKeys) {
      await this.page.keyboard.up(key).catch(() => {});
    }
    this.activeKeys.clear();
  }
}

