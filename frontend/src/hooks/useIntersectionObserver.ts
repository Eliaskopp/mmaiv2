import { useEffect, type RefObject } from 'react'

export function useIntersectionObserver(
  ref: RefObject<Element | null>,
  callback: () => void,
  options?: { enabled?: boolean },
) {
  useEffect(() => {
    if (!ref.current || options?.enabled === false) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) callback()
      },
      { rootMargin: '200px' },
    )

    observer.observe(ref.current)
    return () => observer.disconnect()
  }, [ref, callback, options?.enabled])
}
