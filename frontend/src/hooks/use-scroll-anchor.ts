import { useCallback, useEffect, useRef, useState } from 'react'

export function useScrollAnchor() {
  const anchorRef = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)
  const [anchorEl, setAnchorEl] = useState<HTMLDivElement | null>(null)

  // Callback ref that tracks when the sentinel mounts/unmounts
  const setAnchorRef = useCallback((node: HTMLDivElement | null) => {
    (anchorRef as React.MutableRefObject<HTMLDivElement | null>).current = node
    setAnchorEl(node)
  }, [])

  useEffect(() => {
    if (!anchorEl) return

    const observer = new IntersectionObserver(
      ([entry]) => setIsAtBottom(entry.isIntersecting),
      { root: null, threshold: 0 },
    )

    observer.observe(anchorEl)
    return () => observer.disconnect()
  }, [anchorEl])

  const scrollToBottom = useCallback(() => {
    anchorRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  return { anchorRef: setAnchorRef, isAtBottom, scrollToBottom }
}
