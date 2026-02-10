let mediaRecorder;
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

moistureSlider.oninput = () => moistureVal.innerText = `${moistureSlider.value}%`;
tempSlider.oninput = () => tempVal.innerText = `${tempSlider.value}°C`;
lightSlider.oninput = () => lightVal.innerText = `${lightSlider.value}%`;

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
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        startRecording();
    } else {
        stopRecording();
    }
};

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    // Note: We use standard web recording. For simulating 16kHz exactly,
    // we'd need more complex Web Audio API node, but for a general simulator, 
    // the system-default with subsequent backend processing is sufficient.
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = sendAudioToServer;

    mediaRecorder.start();
    recordBtn.classList.add('recording');
    recordBtn.querySelector('.label').innerText = 'Release to Activate...';
    statusBadge.innerText = 'Listening...';
}

function stopRecording() {
    mediaRecorder.stop();
    recordBtn.classList.remove('recording');
    recordBtn.querySelector('.label').innerText = 'Simulate "Hey Plant"';
    statusBadge.innerText = 'Analyzing...';
}

async function sendAudioToServer() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
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

    const chatContainer = document.getElementById('chat-container');

    // 1. Add User Message (if transcription available)
    if (data.user_query) {
        console.log("STT Output:", data.user_query); // Log for debugging
        const userDiv = document.createElement('div');
        userDiv.className = 'message user-message';
        userDiv.innerHTML = `<small style="display:block;opacity:0.7;font-size:0.7rem;">I heard:</small>${data.user_query}`;
        chatContainer.appendChild(userDiv);
    }

    // 2. Add Plant Message
    const plantDiv = document.createElement('div');
    plantDiv.className = 'message plant-message';
    plantDiv.innerText = `"${data.reply_text}"`;
    chatContainer.appendChild(plantDiv);

    // 3. Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Update visuals based on mood
    plantAvatar.className = 'plant-avatar'; // Reset
    if (data.display.mood === 'thirsty') {
        plantAvatar.classList.add('mood-thirsty');
    }

    // Animate speaking
    plantAvatar.classList.add('face-talking');

    // Play audio
    const audio = new Audio(`http://localhost:8000${data.audio_url}`);
    audio.play();

    audio.onended = () => {
        plantAvatar.classList.remove('face-talking');
        statusBadge.innerText = 'Ready';
    };
}
