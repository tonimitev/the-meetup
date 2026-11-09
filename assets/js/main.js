// The Meetup — small progressive enhancements (no dependencies)
(function () {
  "use strict";

  // Photo slots: show the image if the file exists, otherwise keep the placeholder.
  document.querySelectorAll(".slot img").forEach(function (img) {
    var slot = img.closest(".slot");
    function ok() { slot.classList.add("has-image"); }
    function fail() { img.remove(); }
    if (img.complete) {
      img.naturalWidth > 0 ? ok() : fail();
    } else {
      img.addEventListener("load", ok);
      img.addEventListener("error", fail);
    }
  });

  // Nav background on scroll
  var nav = document.querySelector(".nav");
  if (nav && !nav.classList.contains("is-solid")) {
    var onScroll = function () { nav.classList.toggle("is-scrolled", window.scrollY > 40); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // Reveal on scroll
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-visible"); });
  }

  // Lightbox for gallery pages: any <a class="gallery__item" href="photo.jpg">
  var items = Array.prototype.slice.call(document.querySelectorAll("a.gallery__item"));
  if (!items.length) return;

  var box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.innerHTML =
    '<button class="lightbox__close" aria-label="Close">&times;</button>' +
    '<button class="lightbox__prev" aria-label="Previous">&#8249;</button>' +
    '<img alt="">' +
    '<button class="lightbox__next" aria-label="Next">&#8250;</button>' +
    '<div class="lightbox__count"></div>';
  document.body.appendChild(box);

  var big = box.querySelector("img");
  var count = box.querySelector(".lightbox__count");
  var index = 0;

  function show(i) {
    index = (i + items.length) % items.length;
    var a = items[index];
    big.src = a.getAttribute("href");
    var thumb = a.querySelector("img");
    big.alt = thumb ? thumb.alt : "";
    count.textContent = (index + 1) + " / " + items.length;
  }
  function open(i) { show(i); box.classList.add("is-open"); document.body.style.overflow = "hidden"; }
  function close() { box.classList.remove("is-open"); document.body.style.overflow = ""; }

  items.forEach(function (a, i) {
    a.addEventListener("click", function (e) { e.preventDefault(); open(i); });
  });
  box.querySelector(".lightbox__close").addEventListener("click", close);
  box.querySelector(".lightbox__prev").addEventListener("click", function () { show(index - 1); });
  box.querySelector(".lightbox__next").addEventListener("click", function () { show(index + 1); });
  box.addEventListener("click", function (e) { if (e.target === box) close(); });
  document.addEventListener("keydown", function (e) {
    if (!box.classList.contains("is-open")) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowLeft") show(index - 1);
    if (e.key === "ArrowRight") show(index + 1);
  });

  // Swipe on touch devices
  var startX = null;
  box.addEventListener("touchstart", function (e) { startX = e.touches[0].clientX; }, { passive: true });
  box.addEventListener("touchend", function (e) {
    if (startX === null) return;
    var dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
    startX = null;
  });
})();
