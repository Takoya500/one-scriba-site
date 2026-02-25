document.addEventListener("DOMContentLoaded", () => {
  console.log("Scroll animation script loaded ✅");

  const elements = document.querySelectorAll(".reveal");
  console.log("Trovati elementi:", elements.length);

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        console.log("Mostro elemento:", entry.target);
        entry.target.classList.add("animate-visible");
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.15,
    rootMargin: "0px 0px -10% 0px"
  });

  elements.forEach(el => {
    observer.observe(el);

    // 👇 Failsafe: se l'elemento è già visibile al caricamento, mostrala subito
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom >= 0) {
      el.classList.add("animate-visible");
      observer.unobserve(el);
    }
  });
});
