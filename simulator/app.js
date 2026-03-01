// --- Premium iOS UI V2 Logic (Polished) ---

let audioContext;
let processor;
let input;
let audioChunks = [];

// Elements
const dynamicIsland = document.getElementById('dynamic-island');
const islandContent = document.getElementById('island-content');
const recordBtn = document.getElementById('record-btn');
const appStatus = document.getElementById('app-status');
const mainPlantImg = document.getElementById('main-plant-img');
const plantSelect = document.getElementById('plant-species-select');

// Sliders
const moistureSlider = document.getElementById('moisture');
const tempSlider = document.getElementById('temperature');
const lightSlider = document.getElementById('light');

// Rings and Labels
const moistureRing = document.getElementById('moisture-ring');
const moistureVal = document.getElementById('moisture-val');
const lightRing = document.getElementById('light-ring');
const lightVal = document.getElementById('light-val');
const tempRing = document.getElementById('temp-ring');
const actualTempLabel = document.getElementById('actual-temp-val');
const chatContainer = document.getElementById('chat-container');

const circleRadius = 25;
const circumference = 2 * Math.PI * circleRadius;

// Plant Image Map
const plantImages = {
    'basil': 'basil.png',
    'lavender': 'lavender.png',
    'cactus': 'cactus.png',
    'aloe': 'aloe.png',
    'spider': 'spider.png',
    'peace': 'peacelily.png'
};

function setProgress(circle, percentage) {
    const offset = circumference - (percentage / 100 * circumference);
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = offset;
}

function updateUIFromSensors() {
    const m = moistureSlider.value;
    const t = tempSlider.value;
    const l = lightSlider.value;

    setProgress(moistureRing, m);
    moistureVal.innerText = `${m}%`;

    setProgress(lightRing, l);
    lightVal.innerText = `${l}%`;

    // Temperature scaled to 100% for the ring (0-50 range)
    const tPercent = Math.min(100, (t / 50) * 100);
    setProgress(tempRing, tPercent);
    actualTempLabel.innerText = `${Math.round(tPercent)}%`;

    updateStatusBar();
}

function updateStatusBar() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    const timeEl = document.getElementById('status-time');
    if (timeEl) timeEl.innerText = timeStr;
}

// Initial Sync
updateUIFromSensors();
moistureSlider.oninput = updateUIFromSensors;
tempSlider.oninput = updateUIFromSensors;
lightSlider.oninput = updateUIFromSensors;

// Plant Selection Change
plantSelect.onchange = async () => {
    const species = plantSelect.value;
    const speciesLabel = plantSelect.options[plantSelect.selectedIndex].text.split(': ')[1];

    // Change Image
    mainPlantImg.src = plantImages[species] || 'pothos.png';

    // Update Backend
    appStatus.innerText = 'Syncing...';
    try {
        await fetch(`/v1/device/pot_simulator_001/species?species=${speciesLabel}`, {
            method: 'POST'
        });
        appStatus.innerText = 'Healthy & Syncing';
    } catch (e) {
        appStatus.innerText = 'Sync Error';
    }
};

// Dynamic Island Helper
function setIsland(msg, expanded = false) {
    islandContent.innerText = msg;
    if (expanded) dynamicIsland.classList.add('expanded');
    else dynamicIsland.classList.remove('expanded');
}

// --- Voice Capture ---

recordBtn.onclick = async () => {
    if (!audioContext || audioContext.state === 'closed') {
        startRecording();
    } else {
        stopRecording();
    }
};

async function startRecording() {
    try {
        setIsland("Listening...", true);
        recordBtn.classList.add('recording');

        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        input = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        audioChunks = [];
        processor.onaudioprocess = (e) => audioChunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
        input.connect(processor);
        processor.connect(audioContext.destination);
    } catch (e) {
        setIsland("Mic Error");
        recordBtn.classList.remove('recording');
    }
}

async function stopRecording() {
    setIsland("Processing...", true);
    recordBtn.classList.remove('recording');

    if (processor) { processor.disconnect(); input.disconnect(); }
    if (audioChunks.length === 0) { setIsland(""); return; }

    let finalBuffer = mergeBuffers(audioChunks);
    if (audioContext.sampleRate !== 16000) finalBuffer = await resampleBuffer(finalBuffer, audioContext.sampleRate, 16000);
    const wavBlob = encodeWAV(finalBuffer, 16000);
    await audioContext.close();

    sendAudioToServer(wavBlob);
}

// --- Server Communication ---

async function sendAudioToServer(blob) {
    const params = new URLSearchParams({
        device_id: 'pot_simulator_001',
        temperature: parseFloat(tempSlider.value),
        moisture: parseFloat(moistureSlider.value),
        light: parseFloat(lightSlider.value),
        event: 'wake_word'
    });
    const formData = new FormData();
    formData.append('audio', blob, 'capture.wav');
    try {
        const resp = await fetch(`/v1/ingest?${params}`, { method: 'POST', body: formData });
        handleResponse(await resp.json());
    } catch (e) { setIsland("Error"); }
}

function handleResponse(data) {
    setIsland("Speaking", true);
    const div = document.createElement('div');
    div.style.marginBottom = '10px';
    div.innerHTML = `<span style="color:#007aff">You:</span> ${data.user_query}<br><span style="color:#4caf50">Plant:</span> ${data.reply_text}`;
    chatContainer.prepend(div);

    const audio = new Audio(data.audio_url);
    audio.play();
    audio.onended = () => {
        setIsland("");
    };
}

// Low Moisture Simulation
document.getElementById('low-moisture-btn').onclick = async () => {
    moistureSlider.value = 10;
    updateUIFromSensors();
    setIsland("Low Moisture Alert", true);

    // Play alert sound
    const alertSound = new Audio('alert.wav');
    alertSound.play().catch(e => console.log("Audio play failed:", e));

    await fetch(`/v1/ingest?device_id=pot_simulator_001&event=low_moisture_alert`, { method: 'POST' });
    setTimeout(() => setIsland(""), 3000);
};

// Text Query
document.getElementById('send-text-btn').onclick = sendTextQuery;
document.getElementById('text-query').onkeydown = (e) => { if (e.key === 'Enter') sendTextQuery(); };

async function sendTextQuery() {
    const query = document.getElementById('text-query').value.trim();
    if (!query) return;
    document.getElementById('text-query').value = '';

    setIsland("Thinking...", true);
    const params = new URLSearchParams({
        device_id: 'pot_simulator_001',
        user_query: query,
        temperature: parseFloat(tempSlider.value),
        moisture: parseFloat(moistureSlider.value),
        light: parseFloat(lightSlider.value)
    });
    try {
        const resp = await fetch(`/v1/ingest?${params}`, { method: 'POST' });
        handleResponse(await resp.json());
    } catch (e) { setIsland("Error"); }
}

// Polling for Hardware Sync
async function startPolling() {
    setInterval(async () => {
        try {
            const resp = await fetch('/v1/device/pot_simulator_001/poll');
            const data = await resp.json();
            if (data.latest_sensors && data.latest_sensors.temperature) {
                tempSlider.value = data.latest_sensors.temperature;
                updateUIFromSensors();
            }
        } catch (e) { }
    }, 5000);
}
startPolling();

// --- Audio Utils ---
async function resampleBuffer(buffer, fromRate, toRate) {
    const offlineCtx = new OfflineAudioContext(1, (buffer.length * toRate) / fromRate, toRate);
    const source = offlineCtx.createBufferSource();
    const audioBuffer = offlineCtx.createBuffer(1, buffer.length, fromRate);
    audioBuffer.getChannelData(0).set(buffer);
    source.buffer = audioBuffer;
    source.connect(offlineCtx.destination);
    source.start(0);
    const resampled = await offlineCtx.startRendering();
    return resampled.getChannelData(0);
}
function mergeBuffers(chunks) {
    let totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    let result = new Float32Array(totalLength);
    let offset = 0;
    for (let chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
    return result;
}
function encodeWAV(samples, sampleRate) {
    let buffer = new ArrayBuffer(44 + samples.length * 2);
    let view = new DataView(buffer);
    const writeString = (v, o, s) => { for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); };
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);
    for (let i = 0; i < samples.length; i++) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([view], { type: 'audio/wav' });
}

lucide.createIcons();
setInterval(updateStatusBar, 1000);
updateStatusBar();

// --- Tab Switching Logic ---
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page-content');

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const pageId = item.getAttribute('data-page');

        // Update Nav
        navItems.forEach(i => i.classList.remove('active'));
        item.classList.add('active');

        // Update Pages
        pages.forEach(p => p.classList.remove('active'));
        document.getElementById(`${pageId}-page`).classList.add('active');

        // Re-create icons for new content if needed
        lucide.createIcons();
    });
});

// --- Community Plot Modal ---
function showPlotInfo(title, name, date, tips) {
    document.getElementById('modal-title').innerText = title;
    document.getElementById('modal-name').innerText = name;
    document.getElementById('modal-date').innerText = date;
    document.getElementById('modal-tips').innerText = tips;
    document.getElementById('plot-modal').classList.remove('hidden');
}

function hidePlotInfo() {
    document.getElementById('plot-modal').classList.add('hidden');
}

window.showPlotInfo = showPlotInfo;
window.hidePlotInfo = hidePlotInfo;
