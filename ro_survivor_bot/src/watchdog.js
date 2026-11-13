import { logger } from './logger.js';

export class Watchdog {
  constructor(timeoutMs = 60000) {
    this.timeoutMs = timeoutMs;
    this.lastHeartbeat = Date.now();
  }

  feed() {
    this.lastHeartbeat = Date.now();
  }

  isStuck() {
    return Date.now() - this.lastHeartbeat > this.timeoutMs;
  }

  getElapsedSec() {
    return Math.floor((Date.now() - this.lastHeartbeat) / 1000);
  }

  reset() {
    this.lastHeartbeat = Date.now();
  }
}

