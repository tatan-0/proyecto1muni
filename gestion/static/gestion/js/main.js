(() => {
  const pathname = window.location.pathname.replace(/\/+$/, "") || "/";
  document.querySelectorAll("nav a[href]").forEach((link) => {
    const target = new URL(link.href, window.location.origin).pathname.replace(/\/+$/, "") || "/";
    const isCurrent = target === pathname || (target !== "/" && pathname.startsWith(`${target}/`));
    if (isCurrent) link.setAttribute("aria-current", "page");
  });
})();
