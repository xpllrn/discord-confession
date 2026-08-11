/** Site-wide polish: shortcuts, copy helpers. */
export function initSitePolish() {
  document.querySelectorAll<HTMLElement>("[data-copy]").forEach((el) => {
    el.addEventListener("click", async () => {
      const value = el.dataset.copy ?? "";
      try {
        await navigator.clipboard.writeText(value);
        el.dataset.copied = "true";
        window.setTimeout(() => delete el.dataset.copied, 1600);
      } catch {
        /* clipboard blocked */
      }
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const tag = (e.target as HTMLElement)?.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

    if (e.key === "?") {
      e.preventDefault();
      window.location.href = "/commands";
      return;
    }

    if (e.key === "/" && window.location.pathname.startsWith("/commands")) {
      e.preventDefault();
      const toggle = document.getElementById("search-toggle") as HTMLButtonElement | null;
      const input = document.getElementById("cmd-search") as HTMLInputElement | null;
      toggle?.click();
      input?.focus();
    }
  });
}
