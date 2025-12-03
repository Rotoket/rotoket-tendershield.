import { describe, it, expect, vi, afterEach } from 'vitest';
import { logEvent } from './logger';

describe('logEvent', () => {
  const originalLog = console.log;

  afterEach(() => {
    console.log = originalLog;
  });

  it('логирует сообщение без ошибок', () => {
    const spy = vi.fn();
    console.log = spy as unknown as typeof console.log;

    logEvent('TEST', 'Нажали на кнопку');

    expect(spy).toHaveBeenCalledTimes(1);
    const [prefix, message] = spy.mock.calls[0];
    expect(String(prefix)).toContain('[LOG][');
    expect(String(message)).toContain('Нажали на кнопку');
  });

  it('передаёт extra в console.log третьим аргументом', () => {
    const spy = vi.fn();
    console.log = spy as unknown as typeof console.log;

    logEvent('TEST', 'Сообщение с данными', 'info', { ok: true });

    expect(spy).toHaveBeenCalledTimes(1);
    const call = spy.mock.calls[0];
    expect(call[1]).toContain('Сообщение с данными');
    expect(call[2]).toEqual({ ok: true });
  });
});
