// Client Application Logic - YouTube Chinese Story Dubber & Translator
const isFileProtocol = window.location.protocol === "file:" || !window.location.origin || window.location.origin === "null";
const API_BASE_URL = (isFileProtocol || window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1"))
  ? "http://localhost:8000" 
  : window.location.origin;

const WS_BASE_URL = API_BASE_URL.replace(/^http/, "ws");

document.addEventListener("DOMContentLoaded", () => {
  const dubbingForm = document.getElementById("dubbingForm");
  const youtubeUrlInput = document.getElementById("youtubeUrl");
  const targetLangSelect = document.getElementById("targetLang");
  const antiCopyrightToggle = document.getElementById("antiCopyrightToggle");
  const btnSubmit = document.getElementById("btnSubmit");

  const progressCard = document.getElementById("progressCard");
  const progressStage = document.getElementById("progressStage");
  const progressBarFill = document.getElementById("progressBarFill");
  const progressPctText = document.getElementById("progressPctText");

  const previewCard = document.getElementById("previewCard");
  const videoPreview = document.getElementById("videoPreview");
  const btnDownloadVideo = document.getElementById("btnDownloadVideo");
  const btnDownloadSrt = document.getElementById("btnDownloadSrt");
  const videoTitleText = document.getElementById("videoTitleText");

  let activeWs = null;

  dubbingForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const youtubeUrl = youtubeUrlInput.value.trim();
    if (!youtubeUrl) {
      alert("Vui lòng nhập link YouTube!");
      return;
    }

    // Reset UI states
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = "<span>⏳ Đang xử lý yêu cầu...</span>";
    progressCard.classList.add("active");
    previewCard.classList.remove("active");
    progressBarFill.style.width = "0%";
    progressPctText.innerText = "0%";
    progressStage.innerText = "Đang gửi yêu cầu tới server...";

    try {
      // 1. Post job creation request
      const response = await fetch(`${API_BASE_URL}/api/v1/dub/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          target_language: targetLangSelect.value,
          anti_copyright: antiCopyrightToggle.checked
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Không thể tạo tiến trình.");
      }

      const data = await response.json();
      const jobId = data.job_id;

      // 2. Connect WebSocket for live progress updates
      connectWebSocket(jobId);

    } catch (err) {
      alert(`Lỗi: ${err.message}`);
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = "<span>⚡ Bắt đầu Dịch & Lồng Tiếng</span>";
      progressCard.classList.remove("active");
    }
  });

  function connectWebSocket(jobId) {
    if (activeWs) {
      activeWs.close();
    }

    const wsUrl = `${WS_BASE_URL}/ws/dub/progress/${jobId}`;
    activeWs = new WebSocket(wsUrl);

    activeWs.onopen = () => {
      progressStage.innerText = "Đã kết nối server! Đang tiến hành tự động hóa...";
    };

    activeWs.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const pct = msg.progress || 0;
      const stage = msg.stage || "Đang xử lý...";

      progressBarFill.style.width = `${pct}%`;
      progressPctText.innerText = `${pct}%`;
      progressStage.innerText = stage;

      if (msg.status === "completed" || pct >= 100) {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = "<span>⚡ Bắt đầu Dịch & Lồng Tiếng</span>";
        
        // Show video preview card
        setTimeout(() => {
          showPreviewResults(jobId);
        }, 800);
      } else if (msg.status === "failed") {
        btnSubmit.disabled = false;
        btnSubmit.innerHTML = "<span>⚡ Bắt đầu Dịch & Lồng Tiếng</span>";
        alert(`Tiến trình thất bại: ${stage}`);
      }
    };

    activeWs.onerror = (err) => {
      console.warn("WebSocket error:", err);
      // Fallback polling if WebSocket drops
      pollJobStatus(jobId);
    };
  }

  async function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/dub/status/${jobId}`);
        const data = await res.json();
        
        const pct = data.progress || 0;
        progressBarFill.style.width = `${pct}%`;
        progressPctText.innerText = `${pct}%`;
        progressStage.innerText = data.stage || "Đang xửly ngầm...";

        if (data.status === "completed") {
          clearInterval(interval);
          btnSubmit.disabled = false;
          btnSubmit.innerHTML = "<span>⚡ Bắt đầu Dịch & Lồng Tiếng</span>";
          showPreviewResults(jobId);
        } else if (data.status === "failed") {
          clearInterval(interval);
          btnSubmit.disabled = false;
          btnSubmit.innerHTML = "<span>⚡ Bắt đầu Dịch & Lồng Tiếng</span>";
        }
      } catch (e) {
        console.error("Polling status error:", e);
      }
    }, 3000);
  }

  function showPreviewResults(jobId) {
    const videoUrl = `${API_BASE_URL}/export/${jobId}_final.mp4`;
    const srtUrl = `${API_BASE_URL}/subtitles/${jobId}_${targetLangSelect.value}.srt`;

    videoPreview.src = videoUrl;
    btnDownloadVideo.href = `${API_BASE_URL}/api/v1/dub/download/${jobId}/video`;
    btnDownloadSrt.href = `${API_BASE_URL}/api/v1/dub/download/${jobId}/srt`;
    
    videoTitleText.innerText = `Thành phẩm lồng tiếng ID: ${jobId} (Ready for YouTube upload)`;
    previewCard.classList.add("active");
  }
});
