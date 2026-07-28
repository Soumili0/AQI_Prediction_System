import { useState, useCallback } from 'react';

/**
 * Manages pagination state — current page, per-page size, and navigation helpers.
 *
 * @param {object} options
 * @param {number} options.initialPage    - starting page (default 1)
 * @param {number} options.initialPerPage - rows per page (default 20)
 * @param {number} options.totalPages     - total page count (updated externally)
 * @returns pagination state and navigation functions
 */
export function usePagination({ initialPage = 1, initialPerPage = 20, totalPages = 1 } = {}) {
  const [page, setPage]         = useState(initialPage);
  const [perPage, setPerPage]   = useState(initialPerPage);
  const [total, setTotal]       = useState(totalPages);

  const goToPage    = useCallback((p) => setPage(Math.max(1, Math.min(p, total))), [total]);
  const nextPage    = useCallback(() => goToPage(page + 1), [page, goToPage]);
  const prevPage    = useCallback(() => goToPage(page - 1), [page, goToPage]);
  const firstPage   = useCallback(() => goToPage(1), [goToPage]);
  const lastPage    = useCallback(() => goToPage(total), [total, goToPage]);
  const resetPage   = useCallback(() => setPage(1), []);

  const changePerPage = useCallback((n) => {
    setPerPage(n);
    setPage(1);
  }, []);

  return {
    page,
    perPage,
    total,
    setTotal,
    goToPage,
    nextPage,
    prevPage,
    firstPage,
    lastPage,
    resetPage,
    changePerPage,
    hasNext: page < total,
    hasPrev: page > 1,
  };
}
