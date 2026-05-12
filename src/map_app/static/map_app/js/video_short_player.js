document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-short-player]");
  if (!root) {
    return;
  }

  const video = root.querySelector("[data-short-video]");
  const toggle = root.querySelector("[data-short-toggle]");
  const inlineToggle = root.querySelector("[data-short-toggle-inline]");
  const muteToggle = root.querySelector("[data-short-mute-toggle]");
  const icon = root.querySelector("[data-short-icon]");
  const inlineIcon = root.querySelector("[data-short-inline-icon]");
  const muteIcon = root.querySelector("[data-short-mute-icon]");
  const sheet = root.querySelector("[data-short-sheet]");
  const openSheet = root.querySelector("[data-short-open-sheet]");
  const closeSheetButtons = root.querySelectorAll("[data-short-close-sheet]");
  const seek = root.querySelector("[data-short-seek]");
  const volume = root.querySelector("[data-short-volume]");
  const volumePill = root.querySelector("[data-short-volume-pill]");
  const currentTime = root.querySelector("[data-short-current-time]");
  const duration = root.querySelector("[data-short-duration]");
  let uiUpdateFrame = 0;
  let lastRenderedSecond = -1;
  let controlsHideTimer = 0;
  let progressSyncTimer = 0;

  const icons = {
    play: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 6.5v11l9-5.5-9-5.5Z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h3v14H7zM14 5h3v14h-3z"/></svg>',
    volumeOn: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 6 8.3 8.7H5v6.6h3.3L11 18V6Z"/><path d="M15.2 9.2a4 4 0 0 1 0 5.6"/><path d="M17.9 6.5a7.8 7.8 0 0 1 0 11"/></svg>',
    volumeOff: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 6 8.3 8.7H5v6.6h3.3L11 18V6Z"/><path d="m16 9 5 5"/><path d="m21 9-5 5"/></svg>',
  };

  const setIcon = (element, markup) => {
    if (!element) {
      return;
    }
    element.innerHTML = markup;
  };

  const setRangeFill = (element, value, max = 100) => {
    if (!element) {
      return;
    }
    const safeMax = Math.max(Number(max) || 0, 0.0001);
    const safeValue = Math.min(Math.max(Number(value) || 0, 0), safeMax);
    element.style.setProperty("--range-fill", `${(safeValue / safeMax) * 100}%`);
  };

  const formatTime = (seconds) => {
    const safeSeconds = Math.max(0, Math.floor(Number(seconds) || 0));
    const minutes = Math.floor(safeSeconds / 60);
    const remainder = safeSeconds % 60;
    return `${minutes}:${String(remainder).padStart(2, "0")}`;
  };

  const syncPlayState = () => {
    const paused = !video || video.paused || video.ended;
    root.classList.toggle("is-paused", paused);
    root.classList.toggle("is-controls-visible", paused);
    setIcon(icon, paused ? icons.play : icons.pause);
    setIcon(inlineIcon, paused ? icons.play : icons.pause);
    if (toggle) {
      toggle.setAttribute("aria-label", paused ? "再生" : "一時停止");
    }
    if (inlineToggle) {
      inlineToggle.setAttribute("aria-label", paused ? "再生" : "一時停止");
    }
    if (!paused) {
      window.clearTimeout(controlsHideTimer);
      controlsHideTimer = window.setTimeout(() => {
        root.classList.remove("is-controls-visible");
      }, 1800);
    }
  };

  const syncMuteState = () => {
    if (!video || !muteToggle || !muteIcon) {
      return;
    }
    const muted = !!video.muted || Number(video.volume || 0) <= 0;
    setIcon(muteIcon, muted ? icons.volumeOff : icons.volumeOn);
    muteToggle.setAttribute("aria-label", muted ? "ミュートをオフ" : "ミュートをオン");
    if (volume) {
      volume.value = String(muted ? 0 : (video.volume || 1));
      setRangeFill(volume, Number(volume.value || 0), 1);
    }
  };

  const syncTimeline = () => {
    if (!video) {
      return;
    }
    const durationSeconds = Number.isFinite(video.duration) ? video.duration : 0;
    const currentSeconds = Number.isFinite(video.currentTime) ? video.currentTime : 0;
    if (seek) {
      seek.max = durationSeconds > 0 ? String(durationSeconds) : "100";
      seek.value = String(Math.min(currentSeconds, durationSeconds || 100));
      setRangeFill(seek, Number(seek.value || 0), Number(seek.max || 100));
    }
    if (currentTime) {
      currentTime.textContent = formatTime(currentSeconds);
    }
    if (duration) {
      duration.textContent = formatTime(durationSeconds);
    }
  };

  const scheduleTimelineSync = (force = false) => {
    if (!video) {
      return;
    }
    if (!force && !root.classList.contains("is-controls-visible")) {
      return;
    }
    const currentSecond = Math.floor(Number(video.currentTime) || 0);
    if (!force && currentSecond === lastRenderedSecond) {
      return;
    }
    lastRenderedSecond = currentSecond;
    if (uiUpdateFrame) {
      window.cancelAnimationFrame(uiUpdateFrame);
    }
    uiUpdateFrame = window.requestAnimationFrame(() => {
      uiUpdateFrame = 0;
      syncTimeline();
    });
  };

  const togglePlayback = async () => {
    if (!video) {
      return;
    }
    if (video.paused || video.ended) {
      try {
        await video.play();
      } catch (_) {
        syncPlayState();
      }
      return;
    }
    video.pause();
  };

  const showControlsTemporarily = () => {
    root.classList.add("is-controls-visible");
    scheduleTimelineSync(true);
    if (!video || video.paused || video.ended) {
      return;
    }
    window.clearTimeout(controlsHideTimer);
    controlsHideTimer = window.setTimeout(() => {
      root.classList.remove("is-controls-visible");
    }, 1800);
  };

  const setSheetOpen = (open) => {
    if (!sheet) {
      return;
    }
    sheet.hidden = !open;
    sheet.setAttribute("aria-hidden", open ? "false" : "true");
    document.body.classList.toggle("is-short-sheet-open", open);
  };

  const toggleMute = () => {
    if (!video) {
      return;
    }
    volumePill?.classList.add("is-volume-open");
    video.muted = !video.muted;
    if (!video.muted && video.volume === 0) {
      video.volume = 1;
    }
    syncMuteState();
  };

  toggle?.addEventListener("click", togglePlayback);
  inlineToggle?.addEventListener("click", togglePlayback);
  muteToggle?.addEventListener("click", toggleMute);
  video?.addEventListener("click", () => {
    if (!root.classList.contains("is-controls-visible") && video && !video.paused && !video.ended) {
      showControlsTemporarily();
      return;
    }
    togglePlayback();
  });
  video?.addEventListener("play", syncPlayState);
  video?.addEventListener("pause", syncPlayState);
  video?.addEventListener("ended", syncPlayState);
  video?.addEventListener("volumechange", syncMuteState);
  video?.addEventListener("loadedmetadata", () => {
    syncPlayState();
    scheduleTimelineSync(true);
    syncMuteState();
  });
  video?.addEventListener("timeupdate", () => scheduleTimelineSync(false));
  video?.addEventListener("seeking", () => scheduleTimelineSync(true));
  video?.addEventListener("seeked", () => scheduleTimelineSync(true));
  video?.addEventListener("durationchange", () => scheduleTimelineSync(true));
  video?.addEventListener("play", () => {
    window.clearInterval(progressSyncTimer);
    progressSyncTimer = window.setInterval(() => {
      scheduleTimelineSync(false);
    }, 250);
  });
  video?.addEventListener("pause", () => {
    window.clearInterval(progressSyncTimer);
    scheduleTimelineSync(true);
  });
  video?.addEventListener("ended", () => {
    window.clearInterval(progressSyncTimer);
    scheduleTimelineSync(true);
  });
  seek?.addEventListener("input", () => {
    if (!video) {
      return;
    }
    video.currentTime = Number(seek.value || 0);
    scheduleTimelineSync(true);
  });
  volume?.addEventListener("input", () => {
    if (!video) {
      return;
    }
    const nextVolume = Number(volume.value || 0);
    video.volume = nextVolume;
    video.muted = nextVolume <= 0;
    volumePill?.classList.add("is-volume-open");
    syncMuteState();
  });
  volumePill?.addEventListener("pointerenter", () => {
    volumePill.classList.add("is-volume-open");
  });
  volumePill?.addEventListener("pointerleave", () => {
    volumePill.classList.remove("is-volume-open");
  });
  volumePill?.addEventListener("focusin", () => {
    volumePill.classList.add("is-volume-open");
  });
  volumePill?.addEventListener("focusout", () => {
    window.setTimeout(() => {
      if (!volumePill.contains(document.activeElement)) {
        volumePill.classList.remove("is-volume-open");
      }
    }, 0);
  });
  openSheet?.addEventListener("click", () => setSheetOpen(true));
  closeSheetButtons.forEach((button) => {
    button.addEventListener("click", () => setSheetOpen(false));
  });
  root.addEventListener("pointermove", showControlsTemporarily, { passive: true });
  root.addEventListener("touchstart", showControlsTemporarily, { passive: true });

  syncPlayState();
  scheduleTimelineSync(true);
  syncMuteState();
  if (seek) {
    setRangeFill(seek, Number(seek.value || 0), Number(seek.max || 100));
  }
});
