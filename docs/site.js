'use strict';

// Let incoming links reveal content inside the technical disclosures.
function revealDestination() {
  const target = document.getElementById(location.hash.slice(1));
  if (!target) return;
  const disclosure = target.closest('details');
  if (disclosure && !disclosure.open) {
    disclosure.open = true;
    target.scrollIntoView();
  }
}
window.addEventListener('hashchange', revealDestination);
revealDestination();

const navLinks = [...document.querySelectorAll('.main-nav a')];
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      for (const link of navLinks) {
        if (link.hash === '#' + entry.target.id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      }
    }
  }, {rootMargin: '-5% 0px -72% 0px'});
  document.querySelectorAll('main > section[id]').forEach(section => observer.observe(section));
}

const formatTime = seconds => Math.floor(seconds / 60) + ':' +
  String(Math.floor(seconds % 60)).padStart(2, '0');

function connectChapters(nav) {
  const video = document.getElementById(nav.dataset.player);
  const status = nav.nextElementSibling;
  let chapters = [];
  let buttons = [];
  let pending = null;
  let active = -1;

  function setActive() {
    // A fractional chapter boundary may round down at the player's timer precision.
    const index = chapters.findLastIndex(scene => scene.start <= video.currentTime + 0.001);
    if (index === active) return;
    buttons[active]?.removeAttribute('aria-current');
    buttons[index]?.setAttribute('aria-current', 'time');
    active = index;
  }

  function seek() {
    if (!pending || !video.readyState) return;
    video.currentTime = pending.start;
    setActive();
    status.textContent = 'Moved to ' + pending.title + ', at ' + formatTime(pending.start) + '.';
    pending = null;
  }
  video.addEventListener('loadedmetadata', seek);
  video.addEventListener('timeupdate', setActive);
  video.addEventListener('seeked', setActive);

  function render(scenes) {
    chapters = scenes;
    active = -1;
    buttons = scenes.map(scene => {
      const button = document.createElement('button');
      button.className = 'chapter-button';
      button.type = 'button';
      const time = document.createElement('time');
      time.dateTime = 'PT' + scene.start + 'S';
      time.textContent = formatTime(scene.start);
      const title = document.createElement('span');
      title.textContent = scene.title;
      button.append(time, title);
      button.setAttribute('aria-label', 'Seek to ' + scene.title + ', ' + time.textContent);
      button.addEventListener('click', () => {
        pending = scene;
        if (video.readyState) seek();
        else video.load();
      });
      return button;
    });
    nav.replaceChildren(...buttons);
    setActive();
  }

  // The chapter links also work when the page opens from disk or without JavaScript.
  const fallback = [...nav.querySelectorAll('a[data-start]')].map(link => ({
    title: link.querySelector('span').textContent,
    start: Number(link.dataset.start),
  }));
  function valid(scenes) {
    return Array.isArray(scenes) && scenes.length > 0 && scenes[0].start === 0 &&
      scenes.every((scene, i) => typeof scene.title === 'string' && Number.isFinite(scene.start) &&
        (!i || scene.start > scenes[i - 1].start));
  }
  if (valid(fallback)) render(fallback);
  if (location.protocol === 'file:') return;
  fetch(nav.dataset.timeline)
    .then(response => response.ok ? response.json() : null)
    .then(timeline => {
      const scenes = timeline?.scenes;
      if (!valid(scenes)) return;
      const changed = scenes.length !== fallback.length || scenes.some((scene, i) =>
        fallback[i]?.title !== scene.title || fallback[i]?.start !== scene.start);
      if (changed) render(scenes);
    })
    .catch(() => { /* The printed chapter times remain available. */ });
}
document.querySelectorAll('nav[data-timeline]').forEach(connectChapters);
