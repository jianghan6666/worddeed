'use strict';
(() => {
  const links = [...document.querySelectorAll('.nav a')];
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        links.forEach(a => a.removeAttribute('aria-current'));
        links.find(a => a.hash === '#' + entry.target.id)?.setAttribute('aria-current', 'location');
      }
    }, {rootMargin: '-15% 0px -65% 0px'});
    document.querySelectorAll('main > section[id]').forEach(section => observer.observe(section));
  }
  const video = document.getElementById('walkthrough-video');
  const chapters = document.getElementById('chapters');
  if (!video || !chapters) return;
  const fmt = n => `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, '0')}`;
  fetch('video/timeline.json').then(r => { if (!r.ok) throw new Error('Timeline unavailable'); return r.json(); }).then(timeline => {
    const buttons = timeline.scenes.map(scene => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'chapter';
      const time = document.createElement('time'); time.textContent = fmt(scene.start);
      const text = document.createElement('span'); text.textContent = scene.title;
      button.append(time, text);
      button.setAttribute('aria-label', `Seek to ${scene.title}, ${fmt(scene.start)}`);
      button.addEventListener('click', () => {
        video.currentTime = scene.start;
        document.getElementById('chapter-status').textContent = `Video moved to ${scene.title}. Use the player controls to play.`;
        video.focus({preventScroll: true});
      });
      return button;
    });
    chapters.replaceChildren(...buttons);
    video.addEventListener('timeupdate', () => timeline.scenes.forEach((s, i) => {
      buttons[i].setAttribute('aria-current', String(video.currentTime >= s.start && video.currentTime < s.end));
    }));
  }).catch(() => { /* The transcript and native player remain usable without a timeline. */ });
})();
