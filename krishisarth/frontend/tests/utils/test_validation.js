import { validateEmail, validatePassword, validateDuration, validateConcentration } from '../../src/utils/validation.js';

describe('Validation Utilities', () => {
    test('email validation rejects malformed emails', () => {
        expect(validateEmail('farmer@krishi.com')).toBe(true);
        expect(validateEmail('invalid-email')).toBe(false);
        expect(validateEmail('test@com')).toBe(false);
    });

    test('password validation rejects length < 8', () => {
        expect(validatePassword('secure-pass-123')).toBe(true);
        expect(validatePassword('short')).toBe(false);
    });

    test('duration_min validation rejects values outside 1-120', () => {
        expect(validateDuration(10)).toBe(true);
        expect(validateDuration(0)).toBe(false);
        expect(validateDuration(121)).toBe(false);
    });

    test('concentration_ml validation rejects values outside 0-30', () => {
        expect(validateConcentration(12.5)).toBe(true);
        expect(validateConcentration(-1)).toBe(false);
        expect(validateConcentration(31)).toBe(false);
    });
});
