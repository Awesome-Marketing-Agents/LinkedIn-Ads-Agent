const LOG_LEVELS = { DEBUG: 0, INFO: 1, WARN: 2, ERROR: 3 } as const;

type LogLevel = keyof typeof LOG_LEVELS;

const currentLevel: LogLevel = import.meta.env.DEV ? "DEBUG" : "INFO";

function log(
  level: LogLevel,
  module: string,
  message: string,
  data?: Record<string, unknown>,
) {
  if (LOG_LEVELS[level] < LOG_LEVELS[currentLevel]) return;

  const method =
    level === "ERROR"
      ? console.error
      : level === "WARN"
        ? console.warn
        : level === "DEBUG"
          ? console.debug
          : console.info;

  method(`[${level}] ${module}:`, message, data ?? "");
}

export function createLogger(module: string) {
  return {
    debug: (msg: string, data?: Record<string, unknown>) =>
      log("DEBUG", module, msg, data),
    info: (msg: string, data?: Record<string, unknown>) =>
      log("INFO", module, msg, data),
    warn: (msg: string, data?: Record<string, unknown>) =>
      log("WARN", module, msg, data),
    error: (msg: string, data?: Record<string, unknown>) =>
      log("ERROR", module, msg, data),
  };
}
