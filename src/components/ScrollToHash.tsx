import { useEffect } from "react";
import { useLocation } from "react-router-dom";

/**
 * Client-side navigation keeps the old scroll position, so a link to another
 * page lands mid-content. Scroll to the anchor when there is one, to the top
 * otherwise.
 */
export function ScrollToHash() {
  const { pathname, hash } = useLocation();

  useEffect(() => {
    if (hash) {
      const target = document.getElementById(hash.slice(1));
      if (target) {
        target.scrollIntoView();
        return;
      }
    }
    window.scrollTo(0, 0);
  }, [pathname, hash]);

  return null;
}
