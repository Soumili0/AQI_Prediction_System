import { useState, useEffect } from 'react';

/**
 * Delays updating a value until the user stops changing it.
 * Useful for search inputs to avoid firing an API call on every keystroke.
 *
 * @param {any}    value - The value to debounce
 * @param {number} delay - Delay in milliseconds (default 400)
 * @returns debounced value
 */
export function useDebounce(value, delay = 400) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
