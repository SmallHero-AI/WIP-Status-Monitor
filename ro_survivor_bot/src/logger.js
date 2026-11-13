import chalk from 'chalk';

class Logger {
  constructor() {
    this.stats = {
      startTime: Date.now(),
      runs: 0,
      victories: 0,
      defeats: 0,
      currentStage: 1,
      currentLevel: 1,
      currentRunStart: 0,
      bestSurvivalSec: 0
    };
    this.lastPulseSec = -1;
  }

  formatTime(ms) {
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60).toString().padStart(2, '0');
    const s = (totalSec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }

  info(msg) {
    console.log(chalk.cyan(`[INFO  ${this.formatTime(Date.now() - this.stats.startTime)}] `) + msg);
  }

  success(msg) {
    console.log(chalk.green(`[OK    ${this.formatTime(Date.now() - this.stats.startTime)}] `) + chalk.bold(msg));
  }

  warn(msg) {
    console.log(chalk.yellow(`[WARN  ${this.formatTime(Date.now() - this.stats.startTime)}] `) + msg);
  }

  error(msg, err) {
    console.log(chalk.red(`[ERROR ${this.formatTime(Date.now() - this.stats.startTime)}] `) + chalk.bold(msg));
    if (err) console.error(err);
  }

  combat(msg) {
    console.log(chalk.magenta(`[GAME  ${this.formatTime(Date.now() - this.stats.startTime)}] `) + msg);
  }

  skill(msg) {
    console.log(chalk.yellowBright(`[SKILL ${this.formatTime(Date.now() - this.stats.startTime)}] `) + chalk.bold(msg));
  }

  startRun(stage) {
    this.stats.runs += 1;
    this.stats.currentStage = stage;
    this.stats.currentRunStart = Date.now();
    this.stats.currentLevel = 1;
    this.lastPulseSec = -1;
    console.log('\n' + chalk.bgBlue.white.bold(` === 第 ${this.stats.runs} 局開始 (關卡: ${stage}) === `));
  }

  combatPulse(stage) {
    const elapsedSec = Math.floor((Date.now() - this.stats.currentRunStart) / 1000);
    if (elapsedSec > 0 && elapsedSec % 10 === 0 && elapsedSec !== this.lastPulseSec) {
      this.lastPulseSec = elapsedSec;
      this.combat(`⚔ 戰鬥風箏走位進行中 (關卡: ${stage}) | 存活時間: ${elapsedSec} 秒`);
    }
  }

  recordEnd(isVictory) {
    const durationSec = Math.floor((Date.now() - this.stats.currentRunStart) / 1000);
    if (durationSec > this.stats.bestSurvivalSec) {
      this.stats.bestSurvivalSec = durationSec;
    }
    if (isVictory) {
      this.stats.victories += 1;
      console.log(chalk.bgGreen.black.bold(` ★ 通關成功！存活時間: ${durationSec} 秒 ★ `));
    } else {
      this.stats.defeats += 1;
      console.log(chalk.bgRed.white.bold(` ☠ 挑戰結束 (陣亡/超時)！存活時間: ${durationSec} 秒 `));
    }
    this.printDashboard();
  }

  printDashboard() {
    const totalRuns = this.stats.runs || 1;
    const winRate = ((this.stats.victories / totalRuns) * 100).toFixed(1);
    console.log(chalk.gray('----------------------------------------------------'));
    console.log(chalk.bold.cyan('📊 [RO Survivors 戰況儀表板]'));
    console.log(
      `總局數: ${chalk.yellow(this.stats.runs)} | ` +
      `勝場: ${chalk.green(this.stats.victories)} | ` +
      `敗場: ${chalk.red(this.stats.defeats)} | ` +
      `勝率: ${chalk.magenta(winRate + '%')}`
    );
    console.log(
      `當前關卡: ${chalk.cyan(this.stats.currentStage)} | ` +
      `最佳存活: ${chalk.yellow(this.stats.bestSurvivalSec + 's')} | ` +
      `累計運行: ${chalk.white(this.formatTime(Date.now() - this.stats.startTime))}`
    );
    console.log(chalk.gray('----------------------------------------------------\n'));
  }
}

export const logger = new Logger();
