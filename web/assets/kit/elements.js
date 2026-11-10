// AqionLabs Design Kit — elements.js (magnetic, spotlight, split-flap). Vanilla, no deps.
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(pointer: fine)').matches;
  if (!reduce && fine) {
    document.querySelectorAll('.magnetic').forEach(el => {
      el.addEventListener('pointermove', e => {
        const r = el.getBoundingClientRect();
        el.style.setProperty('--mx', ((e.clientX - r.left - r.width / 2) * .3) + 'px');
        el.style.setProperty('--my', ((e.clientY - r.top - r.height / 2) * .4) + 'px');
      });
      el.addEventListener('pointerleave', () => { el.style.setProperty('--mx', '0px'); el.style.setProperty('--my', '0px'); });
    });
  }
  document.querySelectorAll('.spotlight').forEach(el => el.addEventListener('pointermove', e => {
    const r = el.getBoundingClientRect();
    el.style.setProperty('--x', (e.clientX - r.left) + 'px'); el.style.setProperty('--y', (e.clientY - r.top) + 'px');
  }));
  // Split-flap: <span class="flap" data-value="0482"></span>; call el.flapTo('0517')
  document.querySelectorAll('.flap').forEach(el => {
    const render = v => { el.innerHTML = [...v].map(c => `<i>${c}</i>`).join(''); };
    render(el.dataset.value || '0000');
    el.flapTo = next => {
      const cells = el.querySelectorAll('i');
      [...next].forEach((c, i) => {
        const cell = cells[i]; if (!cell || cell.textContent === c) return;
        setTimeout(() => { if (!reduce) { cell.classList.remove('flip'); void cell.offsetWidth; cell.classList.add('flip'); }
          setTimeout(() => cell.textContent = c, reduce ? 0 : 210); }, reduce ? 0 : i * 70);
      });
    };
  });
})();
