/**
 * KrishiSarth Validation Utility
 * Enforces strict bounds for agricultural and auth inputs.
 */

export function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

export function validatePassword(password) {
    return password && password.length >= 8;
}

export function validateDuration(minutes) {
    const val = parseInt(minutes);
    return !isNaN(val) && val >= 1 && val <= 120;
}

export function validateConcentration(ml) {
    const val = parseFloat(ml);
    return !isNaN(val) && val >= 0 && val <= 30;
}
