/* slides.js — 幻灯片运行时：等比缩放 / 键盘 / 触摸 / URL hash / 总览 / 全屏 / 进度条
   无依赖原生 JS。页面结构约定：
     <div id="viewport"><div id="stage"> ... <section class="slide"> ... </div></div>
     <div id="pager"></div>
     <div id="progress-track"><div id="progress"></div></div>
*/
(function () {
  "use strict";

  var DESIGN_W = 1280;
  var DESIGN_H = 720;

  var slides = Array.prototype.slice.call(document.querySelectorAll(".slide"));
  var total = slides.length;
  var current = 0;
  var overview = false;

  var stage = document.getElementById("stage");
  var pager = document.getElementById("pager");
  var progress = document.getElementById("progress");

  /* 页内右上角编号由实际顺序生成，插入或删除页面后无需手动重排。 */
  slides.forEach(function (slide, index) {
    var metaPage = slide.querySelector(".meta-page");
    if (metaPage) metaPage.textContent = String(index + 1).padStart(2, "0");
  });

  if (pager) {
    pager.setAttribute("aria-live", "polite");
    pager.setAttribute("aria-label", "当前幻灯片页码");
  }

  function clamp(i) { return Math.max(0, Math.min(total - 1, i)); }

  function parseHash() {
    var m = /^#\/(\d+)$/.exec(location.hash || "");
    if (m) return clamp(parseInt(m[1], 10) - 1);
    return 0;
  }

  /* 单页模式：1280x720 画布等比缩放居中 */
  function fit() {
    if (overview) return;
    var scale = Math.min(window.innerWidth / DESIGN_W, window.innerHeight / DESIGN_H);
    stage.style.transform = "scale(" + scale + ")";
  }

  /* 总览模式：根据视口宽度计算缩略图缩放比，写入 CSS 变量 --ov-scale */
  function fitOverview() {
    if (!overview) return;
    var cols = window.innerWidth >= 1500 ? 4 : (window.innerWidth >= 900 ? 3 : 2);
    var pad = 64;            // viewport padding（32px x 2）
    var gap = 24 * (cols - 1);
    var cellW = (window.innerWidth - pad - gap) / cols;
    var scale = Math.min(cellW / DESIGN_W, 0.45);
    stage.style.setProperty("--ov-scale", scale.toFixed(4));
  }

  function show(i, pushHash) {
    current = clamp(i);
    slides.forEach(function (s, k) {
      s.classList.toggle("active", k === current);
      s.setAttribute("aria-hidden", k === current ? "false" : "true");
    });
    if (pager) pager.textContent = (current + 1) + " / " + total;
    if (progress) progress.style.width = ((current + 1) / total * 100) + "%";
    if (pushHash !== false) {
      var h = "#/" + (current + 1);
      if (location.hash !== h) history.replaceState(null, "", h);
    }
  }

  function next() { show(current + 1); }
  function prev() { show(current - 1); }

  function toggleOverview(force) {
    overview = (typeof force === "boolean") ? force : !overview;
    document.body.classList.toggle("overview", overview);
    if (overview) {
      stage.style.transform = "";
      fitOverview();
      var el = slides[current];
      if (el && el.scrollIntoView) el.scrollIntoView({ block: "center" });
    } else {
      fit();
      show(current);
    }
  }

  function toggleFullscreen() {
    var doc = document;
    if (!doc.fullscreenElement && !doc.webkitFullscreenElement) {
      var el = doc.documentElement;
      if (el.requestFullscreen) el.requestFullscreen();
      else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
    } else {
      if (doc.exitFullscreen) doc.exitFullscreen();
      else if (doc.webkitExitFullscreen) doc.webkitExitFullscreen();
    }
  }

  document.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    switch (e.key) {
      case "ArrowRight": case "PageDown": case " ":
        e.preventDefault(); if (overview) toggleOverview(false); next(); break;
      case "ArrowLeft": case "PageUp":
        e.preventDefault(); if (!overview) prev(); break;
      case "Home": e.preventDefault(); show(0); break;
      case "End": e.preventDefault(); show(total - 1); break;
      case "f": case "F": toggleFullscreen(); break;
      case "o": case "O": toggleOverview(); break;
      case "Escape": if (overview) toggleOverview(false); break;
      case "j": case "J": e.preventDefault(); next(); break;
      case "k": case "K": e.preventDefault(); prev(); break;
    }
  });

  /* 单页模式点击画布两侧翻页；中间区域保留给图表与链接。 */
  stage.addEventListener("click", function (e) {
    if (overview) return;
    if (e.target.closest && e.target.closest("a, button, input, textarea, select")) return;
    var rect = stage.getBoundingClientRect();
    var ratio = (e.clientX - rect.left) / rect.width;
    if (ratio < 0.22) prev();
    else if (ratio > 0.78) next();
  });

  /* 总览模式点击缩略图跳转 */
  stage.addEventListener("click", function (e) {
    if (!overview) return;
    var sec = e.target.closest ? e.target.closest(".slide") : null;
    if (!sec) return;
    var idx = slides.indexOf(sec);
    toggleOverview(false);
    if (idx >= 0) show(idx);
  });

  /* 触摸左右滑动翻页 */
  var touchX = null, touchY = null;
  document.addEventListener("touchstart", function (e) {
    if (e.touches.length === 1) {
      touchX = e.touches[0].clientX;
      touchY = e.touches[0].clientY;
    }
  }, { passive: true });
  document.addEventListener("touchend", function (e) {
    if (touchX === null || overview) return;
    var dx = e.changedTouches[0].clientX - touchX;
    var dy = e.changedTouches[0].clientY - touchY;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      if (dx < 0) next(); else prev();
    }
    touchX = touchY = null;
  }, { passive: true });

  window.addEventListener("resize", function () { fit(); fitOverview(); });
  window.addEventListener("hashchange", function () { show(parseHash(), false); });

  fit();
  show(parseHash(), false);
})();
