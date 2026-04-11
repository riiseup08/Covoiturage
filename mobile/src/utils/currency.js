/**
 * Currency formatting utility for African currencies.
 * Displays user-friendly labels (FCFA instead of XAF) with proper formatting.
 */

const CURRENCY_CONFIG = {
  XAF: { symbol: 'FCFA', decimals: 0, separator: ' ' },
  XOF: { symbol: 'FCFA', decimals: 0, separator: ' ' },
  NGN: { symbol: '₦', decimals: 0, separator: ',' },
  GHS: { symbol: 'GH₵', decimals: 2, separator: ',' },
  KES: { symbol: 'KSh', decimals: 0, separator: ',' },
  ZAR: { symbol: 'R', decimals: 2, separator: ',' },
  MAD: { symbol: 'DH', decimals: 2, separator: ' ' },
};

/**
 * Format an amount with the proper currency display.
 * @param {number} amount
 * @param {string} [currencyCode='XAF']
 * @returns {string} e.g. "5 000 FCFA"
 */
export function formatCurrency(amount, currencyCode = 'XAF') {
  const config = CURRENCY_CONFIG[currencyCode] || CURRENCY_CONFIG.XAF;
  const num = Number(amount);
  if (isNaN(num)) return `0 ${config.symbol}`;

  const fixed = num.toFixed(config.decimals);
  const [intPart, decPart] = fixed.split('.');
  const formatted = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, config.separator);
  const display = decPart ? `${formatted}.${decPart}` : formatted;
  return `${display} ${config.symbol}`;
}

/**
 * Get the user-friendly display label for a currency code.
 * @param {string} currencyCode
 * @returns {string}
 */
export function currencyLabel(currencyCode) {
  const config = CURRENCY_CONFIG[currencyCode];
  return config ? config.symbol : currencyCode;
}
