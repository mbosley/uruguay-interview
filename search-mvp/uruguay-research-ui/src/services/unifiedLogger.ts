/**
 * Unified logger that sends logs to the logging server
 */

const LOGGER_URL = 'http://localhost:8001/log';

export type LogLevel = 'error' | 'warn' | 'info' | 'debug' | 'success';

class UnifiedLogger {
  private enabled: boolean = true;
  private queue: any[] = [];
  private sending: boolean = false;

  constructor() {
    // Check if we're in development
    this.enabled = process.env.NODE_ENV === 'development';
    
    // Override console methods to capture all logs
    if (this.enabled) {
      this.overrideConsole();
      // Send queued logs every 500ms
      setInterval(() => this.flushQueue(), 500);
    }
  }

  private overrideConsole() {
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;

    console.log = (...args) => {
      originalLog(...args);
      this.log('info', this.formatArgs(args));
    };

    console.error = (...args) => {
      originalError(...args);
      this.log('error', this.formatArgs(args));
    };

    console.warn = (...args) => {
      originalWarn(...args);
      this.log('warn', this.formatArgs(args));
    };
  }

  private formatArgs(args: any[]): string {
    return args.map(arg => {
      if (typeof arg === 'object') {
        try {
          return JSON.stringify(arg, null, 2);
        } catch {
          return String(arg);
        }
      }
      return String(arg);
    }).join(' ');
  }

  log(level: LogLevel, message: string, data?: any) {
    if (!this.enabled) return;

    const logEntry = {
      source: 'frontend',
      level,
      message,
      data: data || {}
    };

    this.queue.push(logEntry);
  }

  private async flushQueue() {
    if (this.sending || this.queue.length === 0) return;

    this.sending = true;
    const logsToSend = [...this.queue];
    this.queue = [];

    try {
      // Send logs in batch
      for (const log of logsToSend) {
        await fetch(LOGGER_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(log)
        }).catch(() => {
          // Silently fail if logger server is not running
        });
      }
    } finally {
      this.sending = false;
    }
  }

  // Manual logging methods
  info(message: string, data?: any) {
    this.log('info', message, data);
  }

  error(message: string, data?: any) {
    this.log('error', message, data);
  }

  debug(message: string, data?: any) {
    this.log('debug', message, data);
  }

  success(message: string, data?: any) {
    this.log('success', message, data);
  }
}

// Create singleton instance
export const logger = new UnifiedLogger();

// Export for direct use
export default logger;