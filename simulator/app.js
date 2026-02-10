let mediaRecorder;
let audioChunks = [];
const recordBtn = document.getElementById('record-btn');
const statusBadge = document.getElementById('app-status');
const plantReply = document.getElementById('plant-reply');
const plantAvatar = document.getElementById('plant-avatar');
const moistureSlider = document.getElementById('moisture');
const moistureVal = document.getElementById('moisture-val');

moistureSlider.oninput = () => {
    moistureVal.innerText = `${moistureSlider.value}%`;
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
        temperature: 25.0,
        moisture: moistureSlider.value,
        light: 450.0,
        event: 'wake_word' // Simulating the hardware wake word trigger
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
    plantReply.innerText = `"${data.reply_text}"`;

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
