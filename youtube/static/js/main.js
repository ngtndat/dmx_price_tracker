let currentTaskId = null;
let currentSegments = [];
let pollInterval = null;

function getAntiCopyrightSettings() {
    return {
        anti_crop: document.getElementById('antiCrop')?.checked || false,
        anti_color: document.getElementById('antiColor')?.checked || false,
        anti_speed: document.getElementById('antiSpeed')?.checked || false,
        anti_mirror: document.getElementById('antiMirror')?.checked || false
    };
}

document.getElementById('processForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const videoSource = document.getElementById('videoSource').value.trim();
    const subLang = document.getElementById('subLang').value;
    const voiceLang = document.getElementById('voiceLang').value;
    const voiceKey = document.getElementById('voiceKey').value;
    const ttsRate = document.getElementById('ttsRate')?.value || "0%";
    const origAudioVol = parseFloat(document.getElementById('origAudioVol').value);
    const antiCopyright = getAntiCopyrightSettings();

    if (!videoSource) return;

    // Reset UI
    document.getElementById('btnStart').disabled = true;
    document.getElementById('statusBadge').innerText = "Đang khởi tạo...";
    document.getElementById('progressBar').style.width = "5%";
    document.getElementById('progressText').innerText = "Đang tải video & trích xuất lời thoại...";
    
    document.getElementById('editorSection').classList.add('hidden');
    document.getElementById('resultSection').classList.add('hidden');

    try {
        const res = await fetch('/api/process-video', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                source: videoSource,
                sub_lang: subLang,
                voice_lang: voiceLang,
                voice_key: voiceKey,
                tts_rate: ttsRate,
                orig_audio_vol: origAudioVol,
                anti_copyright: antiCopyright
            })
        });

        const data = await res.json();
        if (data.task_id) {
            currentTaskId = data.task_id;
            startPolling(currentTaskId);
        } else {
            alert('Lỗi: ' + (data.error || 'Không thể tạo task.'));
            document.getElementById('btnStart').disabled = false;
        }
    } catch (err) {
        alert('Lỗi kết nối server: ' + err.message);
        document.getElementById('btnStart').disabled = false;
    }
});

function startPolling(taskId) {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
        try {
            const res = await fetch(`/api/task-status/${taskId}`);
            const statusData = await res.json();

            document.getElementById('statusBadge').innerText = statusData.status.toUpperCase();
            document.getElementById('progressBar').style.width = statusData.progress + "%";
            document.getElementById('progressText').innerText = statusData.message;

            if (statusData.status === 'transcribed' || statusData.status === 'completed') {
                clearInterval(pollInterval);
                document.getElementById('btnStart').disabled = false;
                
                if (statusData.segments) {
                    currentSegments = statusData.segments;
                    renderSubTable(currentSegments);
                    document.getElementById('editorSection').classList.remove('hidden');
                    document.getElementById('editorSection').scrollIntoView({ behavior: 'smooth' });
                }

                if (statusData.status === 'completed' && statusData.video_url) {
                    showResults(statusData);
                }
            } else if (statusData.status === 'error') {
                clearInterval(pollInterval);
                document.getElementById('btnStart').disabled = false;
                alert("Lỗi xử lý: " + statusData.message);
            }
        } catch (err) {
            console.error("Polling error", err);
        }
    }, 2000);
}

function renderSubTable(segments) {
    const tbody = document.getElementById('subTableBody');
    tbody.innerHTML = '';

    segments.forEach((seg, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${seg.id}</td>
            <td><code>${seg.start}s - ${seg.end}s</code></td>
            <td><input type="text" value="${escapeHtml(seg.text)}" onchange="updateSegment(${idx}, 'text', this.value)"></td>
            <td><input type="text" value="${escapeHtml(seg.text_vi || '')}" onchange="updateSegment(${idx}, 'text_vi', this.value)"></td>
            <td><input type="text" value="${escapeHtml(seg.text_en || '')}" onchange="updateSegment(${idx}, 'text_en', this.value)"></td>
        `;
        tbody.appendChild(tr);
    });
}

function updateSegment(idx, field, value) {
    if (currentSegments[idx]) {
        currentSegments[idx][field] = value;
    }
}

function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

document.getElementById('btnRenderFinal').addEventListener('click', async () => {
    if (!currentTaskId) return;

    document.getElementById('btnRenderFinal').disabled = true;
    document.getElementById('statusBadge').innerText = "RENDERING...";
    document.getElementById('progressText').innerText = "Đang tổng hợp giọng lồng tiếng, bộ lọc chống bản quyền & render video final...";
    document.getElementById('progressBar').style.width = "75%";

    const ttsRate = document.getElementById('ttsRate')?.value || "0%";
    const antiCopyright = getAntiCopyrightSettings();

    try {
        const res = await fetch('/api/render-video', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                task_id: currentTaskId,
                segments: currentSegments,
                tts_rate: ttsRate,
                anti_copyright: antiCopyright
            })
        });

        const rawText = await res.text();
        let data = {};
        try {
            data = JSON.parse(rawText);
        } catch (err) {
            data = { error: rawText.substring(0, 300) };
        }

        if (data.video_url) {
            document.getElementById('progressBar').style.width = "100%";
            document.getElementById('statusBadge').innerText = "HOÀN THÀNH";
            showResults(data);
        } else {
            alert("Lỗi render video: " + (data.error || "Không xác định"));
            document.getElementById('statusBadge').innerText = "LỖI RENDER";
        }
    } catch (err) {
        alert("Lỗi kết nối render: " + err.message);
    } finally {
        document.getElementById('btnRenderFinal').disabled = false;
    }
});

function showResults(data) {
    const resultSection = document.getElementById('resultSection');
    const player = document.getElementById('finalVideoPlayer');
    const downloadBtn = document.getElementById('downloadVideoBtn');

    player.src = data.video_url;
    downloadBtn.href = data.video_url;

    if (data.metadata) {
        document.getElementById('ytTitle').value = data.metadata.title || '';
        document.getElementById('ytDesc').value = data.metadata.description || '';
        document.getElementById('ytTags').value = data.metadata.tags || '';
    }

    resultSection.classList.remove('hidden');
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

function copyField(id) {
    const el = document.getElementById(id);
    el.select();
    document.execCommand('copy');
    alert('Đã sao chép nội dung!');
}
