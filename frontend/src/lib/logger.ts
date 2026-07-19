/**
 * Central logger. Silenced in production builds so no stray output ships.
 * Use this instead of raw console.log (which Biome forbids in committed code).
 */
const isDev = import.meta.env.DEV;

export const logger = {
  debug: (...args: unknown[]): void => {
    if (isDev) {
      // biome-ignore lint/suspicious/noConsole: dev-only diagnostic channel
      console.log("[aiea]", ...args);
    }
  },
  warn: (...args: unknown[]): void => {
    console.warn("[aiea]", ...args);
  },
  error: (...args: unknown[]): void => {
    console.error("[aiea]", ...args);
  },
};
