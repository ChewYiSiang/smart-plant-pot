let audioContext;
let processor;
let input;
let audioChunks = [];
const recordBtn = document.getElementById('record-btn');
const statusBadge = document.getElementById('app-status');
const plantAvatar = document.getElementById('plant-avatar');
const moistureSlider = document.getElementById('moisture');
const moistureVal = document.getElementById('moisture-val');
const tempSlider = document.getElementById('temperature');
const tempVal = document.getElementById('temperature-val');
const lightSlider = document.getElementById('light');
const lightVal = document.getElementById('light-val');
const speciesSelect = document.getElementById('plant-species');
const textQueryInput = document.getElementById('text-query');
const sendTextBtn = document.getElementById('send-text-btn');

moistureSlider.oninput = () => moistureVal.innerText = `${moistureSlider.value}%`;
tempSlider.oninput = () => tempVal.innerText = `${tempSlider.value}°C`;
lightSlider.oninput = () => lightVal.innerText = `${lightSlider.value}%`;

sendTextBtn.onclick = () => sendTextQuery();
textQueryInput.onkeydown = (e) => { if (e.key === 'Enter') sendTextQuery(); };

speciesSelect.onchange = async () => {
    statusBadge.innerText = 'Updating Species...';
    try {
        await fetch(`http://localhost:8000/v1/device/pot_simulator_001/species?species=${speciesSelect.value}`, {
            method: 'POST'
        });
        statusBadge.innerText = 'Species Updated';
        setTimeout(() => statusBadge.innerText = 'Ready', 2000);
    } catch (e) {
        statusBadge.innerText = 'Error Updating';
    }
};

recordBtn.onclick = async () => {
    if (!audioContext || audioContext.state === 'closed') {
        startRecording();
    } else {
        stopRecording();
    }
};

async function startRecording() {
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    input = audioContext.createMediaStreamSource(stream);
    processor = audioContext.createScriptProcessor(4096, 1, 1);

    audioChunks = [];
    processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Copy samples
        audioChunks.push(new Float32Array(inputData));
    };

    input.connect(processor);
    processor.connect(audioContext.destination);

    recordBtn.classList.add('recording');
    recordBtn.querySelector('.label').innerText = 'Release to Activate...';
    statusBadge.innerText = 'Listening (16kHz)...';
}

async function stopRecording() {
    if (processor) {
        processor.disconnect();
        input.disconnect();
    }

    const finalBuffer = mergeBuffers(audioChunks);
    const wavBlob = encodeWAV(finalBuffer, 16000);

    await audioContext.close();

    recordBtn.classList.remove('recording');
    recordBtn.querySelector('.label').innerText = 'Simulate "Hey Plant"';
    statusBadge.innerText = 'Analyzing...';

    sendAudioToServer(wavBlob);
}

function mergeBuffers(chunks) {
    let totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0);
    let result = new Float32Array(totalLength);
    let offset = 0;
    for (let chunk of chunks) {
        result.set(chunk, offset);
        offset += chunk.length;
    }
    return result;
}

function encodeWAV(samples, sampleRate) {
    let buffer = new ArrayBuffer(44 + samples.length * 2);
    let view = new DataView(buffer);

    /* RIFF identifier */
    writeString(view, 0, 'RIFF');
    /* file length */
    view.setUint32(4, 36 + samples.length * 2, true);
    /* RIFF type */
    writeString(view, 8, 'WAVE');
    /* format chunk identifier */
    writeString(view, 12, 'fmt ');
    /* format chunk length */
    view.setUint32(16, 16, true);
    /* sample format (raw) */
    view.setUint16(20, 1, true);
    /* channel count */
    view.setUint16(22, 1, true);
    /* sample rate */
    view.setUint32(24, sampleRate, true);
    /* byte rate (sample rate * block align) */
    view.setUint32(28, sampleRate * 2, true);
    /* block align (channel count * bytes per sample) */
    view.setUint16(32, 2, true);
    /* bits per sample */
    view.setUint16(34, 16, true);
    /* data chunk identifier */
    writeString(view, 36, 'data');
    /* data chunk length */
    view.setUint32(40, samples.length * 2, true);

    floatTo16BitPCM(view, 44, samples);

    return new Blob([view], { type: 'audio/wav' });
}

function floatTo16BitPCM(output, offset, input) {
    for (let i = 0; i < input.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, input[i]));
        output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

async function sendAudioToServer(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'simulation.wav');

    const params = new URLSearchParams({
        device_id: 'pot_simulator_001',
        temperature: parseFloat(tempSlider.value),
        moisture: parseFloat(moistureSlider.value),
        light: parseFloat(lightSlider.value),
        event: 'wake_word'
    });

    try {
        const response = await fetch(`http://localhost:8000/v1/ingest?${params}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        handlePlantResponse(data);
    } catch (error) {
        console.error('Error:', error);
        statusBadge.innerText = 'Error';
    }
}

function handlePlantResponse(data) {
    statusBadge.innerText = 'Speaking...';
    console.log("Initial Backend Response:", data);

    const chatContainer = document.getElementById('chat-container');

    // 1. Add User Message (Transcription)
    const userDiv = document.createElement('div');
    userDiv.className = 'message user-message';
    userDiv.innerHTML = `
        <div class="heard-label">I heard:</div>
        <div class="transcript-text">${data.user_query || '...ing'}</div>
    `;
    chatContainer.appendChild(userDiv);

    // 2. Add Plant Message (Placeholder)
    const plantDiv = document.createElement('div');
    plantDiv.className = 'message plant-message';
    plantDiv.id = `convo-${data.id}`;
    plantDiv.innerText = `"${data.reply_text}"`;
    chatContainer.appendChild(plantDiv);

    // 3. Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Update visuals based on mood
    plantAvatar.className = 'plant-avatar';
    if (data.display.mood === 'thirsty') {
        plantAvatar.classList.add('mood-thirsty');
    }
    plantAvatar.classList.add('face-talking');

    // 4. Play the STREAMING audio
    const audio = new Audio(`http://localhost:8000${data.audio_url}`);
    audio.play().catch(e => console.error("Audio play failed:", e));

    audio.onended = async () => {
        plantAvatar.classList.remove('face-talking');
        statusBadge.innerText = 'Ready';

        // 5. Fetch Final Text once audio is done
        const fetchText = async (retries = 3) => {
            try {
                const resp = await fetch(`http://localhost:8000/v1/history?device_id=pot_simulator_001`);
                const history = await resp.json();
                const latest = history.find(c => c.id === data.id);
                if (latest && latest.reply_text !== "...") {
                    plantDiv.innerText = `"${latest.reply_text}"`;
                } else if (retries > 0) {
                    console.log("Still thinking, retrying text fetch...");
                    setTimeout(() => fetchText(retries - 1), 500);
                }
            } catch (e) {
                console.error("Failed to fetch final text:", e);
            }
        };
        fetchText();
    };
}

async function sendTextQuery() {
    const query = textQueryInput.value.trim();
    if (!query) return;

    textQueryInput.value = '';
    statusBadge.innerText = 'Thinking...';

    const params = new URLSearchParams({
        device_id: 'pot_simulator_001',
        temperature: parseFloat(tempSlider.value),
        moisture: parseFloat(moistureSlider.value),
        light: parseFloat(lightSlider.value),
        user_query: query
    });

    try {
        const response = await fetch(`http://localhost:8000/v1/ingest?${params}`, {
            method: 'POST'
        });

        const data = await response.json();
        handlePlantResponse(data);
    } catch (error) {
        console.error('Error:', error);
        statusBadge.innerText = 'Error';
    }
}
