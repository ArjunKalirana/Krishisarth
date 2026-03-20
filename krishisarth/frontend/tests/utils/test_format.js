import { formatDate, formatLitres, roundTo, getMoistureStatus } from '../../src/utils/format.js';

describe('Format Utilities', () => {
    test('formatDate returns correct locale string', () => {
        const date = '2026-03-18T08:30:00Z';
        // Mocking toLocaleDateString might be needed in some environments, 
        // but testing for inclusion of key parts is a safe baseline.
        const formatted = formatDate(date);
        expect(formatted).toContain('18');
        expect(formatted).toContain('Mar');
    });

    test('formatLitres formats 1000+ with comma separator', () => {
        expect(formatLitres(1240)).toBe('1,240 L');
        expect(formatLitres(42)).toBe('42 L');
    });

    test('roundTo prevents float artifacts', () => {
        // 0.1 + 0.2 = 0.30000000000000004
        expect(roundTo(0.1 + 0.2, 1)).toBe(0.3);
    });

    test('getMoistureStatus returns correct semantic labels', () => {
        expect(getMoistureStatus(18).label).toBe('CRITICAL');
        expect(getMoistureStatus(45).label).toBe('OPTIMAL');
        expect(getMoistureStatus(85).label).toBe('SATURATED');
    });
});
