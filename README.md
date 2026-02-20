# Smart Plant Pot Backend

A voice-enabled IoT backend for an ESP32-powered smart plant pot. Powered by FastAPI, LangGraph, and Google Vertex AI.

## Agentic AI Infrastructure

The "Digital Soul" of the plant is built using **LangGraph**, orchestrating a team of LLM agents that work together to provide intelligent, botanically-accurate responses.

### Detailed Agentic Brain Architecture

The Smart Plant Pot uses a multi-layered agentic system to provide both rapid feedback and deep biological insight. The architecture bifurcates based on intent to balance latency and intelligence.

```mermaid
graph TD
    User([User Voice/Text]) --> Transcription[<b>Transcription Service</b><br/><i>(STT - OpenAI/Gemini)</i>]
    Sensors([Hardware Sensors]) --> Telemetry[<b>Telemetry Parser</b><br/><i>(ADC/1-Wire Data)</i>]

    Transcription --> Router{<b>Router Agent</b><br/><i>(Intent Classifier)</i>}
    Telemetry --> StateFusion[<b>State Manager</b><br/><i>(AgentState)</i>]

    Router -- "Simple (GREETING/JOKE)" --> ConvFast[<b>Conversation Agent</b><br/><i>(Sequential Agent)</i>]
    
    subgraph "Expert Reasoning Path (Parallel Agents)"
        Router -- "Complex (HEALTH/LORE)" --> ExpertBus{Context Dispatch}
        ExpertBus --> SenseAgent[<b>Sensor Agent</b><br/><i>(Clinical Interpretation)</i>]
        ExpertBus --> KnowAgent[<b>Knowledge Agent</b><br/><i>(RAG / Lore Retrieval)</i>]
    end

    ConvFast --> SynthAgent[<b>Persona Synthesis</b><br/><i>(Final Voice Layer)</i>]
    SenseAgent --> SynthAgent
    KnowAgent --> SynthAgent

    SynthAgent --> Loop{<b>Orchestrator Agent</b><br/><i>(The Loop Agent)</i>}
    Loop -- "Inconsistent Response" --> SynthAgent
    Loop -- "Verified" --> AudioStream([I2S Stream Ingest])
```

### Infrastructure Patterns & Agent Hierarchy

We categorize our agents based on their architectural role in the **Digital Soul** pipeline:

#### 1. Sequential Agents (Decision & Synthesis)
These agents process data in a linear stream. They are the "backbone" of the system's logic.
*   **Router Agent**: The "Front Desk." It analyzes the user's transcription to determine if the query requires a fast greeting or deep botanical research.
*   **Conversation Agent**: The "Tone-of-Voice." It takes the raw data and wraps it in the plant's unique persona (witty, grumpy, or helpful).

#### 2. Parallel Agents (Multi-Modal Perception)
When a complex query is detected, the system branches into multiple concurrent executions to maximize data fusion without increasing latency.
*   **Sensor Agent**: The "Nervous System." It clinicalizes raw voltage and temperature readings into descriptive physical states (e.g., "Critical Dehydration detected").
*   **Knowledge Agent**: The "Generational Memory." A RAG-enabled agent that scans the local SQL database and vector store for species-specific lore and care instructions.

#### 3. Loop Agents (Self-Healing & Verification)
The system employs a dynamic feedback loop to ensure honesty and accuracy.
*   **Orchestrator Agent**: The "Conscience." It performs a **Cross-Verification Loop**. If the generated response suggests the plant needs water but the `Sensor Agent` confirms the soil is saturated, the Orchestrator forces a regeneration to prevent hallucinating advice. 

---

### Core Agent Roles
*   **Router Agent**: Decides if you are asking for a simple greeting or a complex health check.
*   **Sensor Agent**: Translates raw GPIO numbers into human terms (e.g., "The soil is bone dry").
*   **Knowledge Agent**: A RAG (Retrieval Augmented Generation) agent that searches the database for specific botanical facts.
*   **Conversation Agent**: The voice of the plant that crafts the final, witty response.

---

## Prerequisites
- Python 3.9+
- API Keys: Google Gemini / Vertex AI (for LLM, STT, and TTS)

## Setup

1. **Clone and Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in your API keys.
   ```bash
   cp .env.example .env
   ```
   
   **Key Descriptions:**
   - `GOOGLE_API_KEY`: A single key used for the multi-agent system (LLM), Google Cloud STT, and Google Cloud TTS.

3. **Database Initialization**
   The database (SQLite by default) will be automatically created on the first run.

## Running the Server
```bash
python main.py
# or
uvicorn main:app --reload
```

## Testing & Simulation

### 1. Web Simulator
Open `http://localhost:8000/simulator/index.html` in your browser to interact with the plant using your microphone and simulated sensor sliders.

### 2. Manual Simulation Script
To simulate a device sending structured data:
```bash
python tests/simulate_device.py
```

## Example Test Queries

Try asking these questions to see how the agents coordinate:

- **Health Checks**:
  - "Hey plant, how are you feeling?"
  - "Do you need more water?"
  - "Are the conditions in this room okay for you?"
- **Plant Knowledge**:
  - "What kind of plant are you?"
  - "How much sunlight should you be getting?"
  - "What's the ideal temperature for a Basil plant?"
- **Personality & Interaction**:
  - "Tell me a joke about plants."
  - "Good morning! Did you sleep well?"
  - "Who is your favorite gardener?"

## What to Test

1. **API Connectivity**: Confirm the server responds to `/health` with `status: healthy`.
2. **STT Accuracy**: Verify your speech is correctly transcribed in the server logs.
3. **Audio Streaming**: Optimized for clarity and low latency. The backend uses a pre-synthesis queue to eliminate gaps between sentences and disables muffled "small-speaker" profiles for crisper voice output.
4. **Ideal vs. Reality Logic**: Ask "How are you feeling?" or "Are you getting enough light?" and verify the plant states its botanical ideal before its current sensor reading.

## Project Structure
- `agents/`: Implementation of the **Digital Soul** (ConversationAgent).
- `services/`: STT, TTS, and storage management.
- `models.py`: Database schemas and seeding logic for botanical lore.
- `main.py`: FastAPI endpoints, streaming logic, and ingest pipeline.
- `audio_artifacts/`: Local storage for voice recordings and backchannels.
- `simulator/`: Web-based interaction frontend.

## Hardware Setup & ESP32 Code

To build the physical Smart Plant Pot, you will need:
- **MCU**: ESP32-S3 DevKitC-1 (N8R8 or similar)
- **Temperature**: DS18B20 (1-Wire)
- **Moisture**: Capacitive Soil Moisture Sensor (Analog)
- **Audio In**: INMP441 or similar I2S Microphone
- **Audio Out**: MAX98357A I2S DAC + 8Ω Speaker

### 1. Wiring Diagram (ESP32-S3 DevKitC-1)

| Component | ESP32-S3 Pin | Note |
| :--- | :--- | :--- |
| **DS18B20 (Data)** | GPIO 4 | Requires 4.7kΩ pull-up to 3.3V |
| **Soil Moisture (Aout)**| GPIO 1 | Analog Input (ADC1_CH0) |
| **I2S Mic (SCK)** | GPIO 12 | Safe Pin (not PSRAM) |
| **I2S Mic (WS)** | GPIO 11 | Safe Pin (not PSRAM) |
| **I2S Mic (SD)** | GPIO 10 | Safe Pin (not PSRAM) |
| **MAX98357A (BCLK)** | GPIO 5 | Bit Clock |
| **MAX98357A (LRC)** | GPIO 6 | Word Select / LR Clock |
| **MAX98357A (DIN)** | GPIO 7 | Data In |

### 2. Assembly Steps
1. **Power**: Connect 3.3V and GND from the ESP32-S3 to all sensors. The MAX98357A can be connected to the 5V pin for higher volume.
2. **Sensors**: 
   - **DHT11 (Temp/Humidity)**: Connect VCC to 3.3V, GND to GND, and Data to **GPIO 4**.
   - **Moisture**: Connect VCC to 3.3V, GND to GND, and **AUOT (Analog Out)** to **GPIO 1**.
3. **Small Form Factor**: The DevKitC-1 is larger than the Super Mini, so ensure your enclosure has adequate space.

### 2.1 Moisture Sensor Calibration
Cpacitive sensors vary. To calibrate:
1. Hold the sensor in the air (Dry) and note the `Raw` value in Serial Monitor.
2. Dip the sensor in water (Wet) and note the `Raw` value.
3. Update the `map(moistureRaw, DRY_VAL, WET_VAL, 0, 100)` in your code. (Default is 3000 dry, 1000 wet).

### 3. ESP32 PlatformIO Project

Create a new PlatformIO project in VS Code for the **ESP32-S3** and use the following configuration and code.

#### `platformio.ini`
Add these dependencies to your project configuration:
```ini
[env:esp32-s3-devkitc-1]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 115200
lib_ldf_mode = deep+
lib_deps =
    earlephilhower/ESP8266Audio @ ^1.9.7
    WiFi
    HTTPClient
    bblanchon/ArduinoJson @ ^6.21.3
    esphome/ESP32-audioI2S @ ^2.0.7
    adafruit/DHT sensor library @ 1.4.6
    adafruit/Adafruit Unified Sensor @ 1.1.14
build_flags =
    -D CORE_DEBUG_LEVEL=3
    -D ARDUINO_USB_MODE=1
    -D ARDUINO_USB_CDC_ON_BOOT=0 ; Set to 0 because using UART port
    -D BOARD_HAS_PSRAM
    -std=gnu++2a
board_build.arduino.memory_type = qio_opi ; REQUIRED for N8R8 (Quad Flash, Octal PSRAM)
board_build.flash_mode = qio ; REQUIRED for N8R8
board_build.partitions = huge_app.csv
```

#### `src/main.cpp`
```cpp
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <esp_wifi.h>
#include "AudioFileSourceHTTPStream.h"
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2S.h"
#include "driver/i2s.h"
#include "esp_heap_caps.h"


// WiFiMulti wifiMulti; // Simplified to direct WiFi.begin for better iPhone compatibility

// --- CONFIGURATION ---
#include "secrets.h"
const char* serverUrl = "http://172.20.10.4:8000/v1/ingest";
const char* deviceId = "s3_devkitc_plant_pot";

// --- PINS (Optimized for S3 DevKitC-1) ---
#define DHTPIN 4
#define DHTTYPE DHT11
#define MOISTURE_PIN 1
#define I2S_SPEAKER_BCLK 5
#define I2S_SPEAKER_LRC 6
#define I2S_SPEAKER_DIN 7
#define I2S_MIC_SD 10
#define I2S_MIC_WS 11
#define I2S_MIC_SCK 12

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastDhtReadTime = 0;
const unsigned long dhtInterval = 3000; // DHT11 needs 2-3s
float temp = 25.0;      // Persistent sensor values
float humidity = 50.0;

// --- AUDIO OBJECTS ---
AudioGeneratorMP3 *mp3 = NULL;
AudioFileSourceHTTPStream *file = NULL;
AudioOutputI2S *out = NULL;

// --- AUDIO CAPTURE SETTINGS ---
#define SAMPLE_RATE 16000
#define RECORD_TIME 5 // Seconds (S3 can easily handle 5-10s with Dual Core/PSRAM)
#define WAV_HEADER_SIZE 44
#define BUFFER_PADDING 1024 // 1KB Safety padding for hardware "slop"
uint8_t* audioBuffer = NULL;
size_t audioBufferSize = (SAMPLE_RATE * 2 * RECORD_TIME) + WAV_HEADER_SIZE + BUFFER_PADDING;
String globalAudioUrl = ""; // Persistent URL for the background streaming task
bool isPlaying = false; // Flag to prevent re-triggering during playback
unsigned long lastPollTime = 0;
const unsigned long pollInterval = 3000; // Poll every 3 seconds

// Function to generate WAV header
void generateWavHeader(uint8_t* header, uint32_t wavDataSize) {
    uint32_t totalDataSize = wavDataSize + 36;
    header[0] = 'R'; header[1] = 'I'; header[2] = 'F'; header[3] = 'F';
    *((uint32_t*)(header + 4)) = totalDataSize;
    header[8] = 'W'; header[9] = 'A'; header[10] = 'V'; header[11] = 'E';
    header[12] = 'f'; header[13] = 'm'; header[14] = 't'; header[15] = ' ';
    *((uint32_t*)(header + 16)) = 16;
    *((uint16_t*)(header + 20)) = 1;
    *((uint16_t*)(header + 22)) = 1;
    *((uint32_t*)(header + 24)) = SAMPLE_RATE;
    *((uint32_t*)(header + 28)) = SAMPLE_RATE * 2;
    *((uint16_t*)(header + 32)) = 2;
    *((uint16_t*)(header + 34)) = 16;
    header[36] = 'd'; header[37] = 'a'; header[38] = 't'; header[39] = 'a';
    *((uint32_t*)(header + 40)) = wavDataSize;
}

// Helper function to decode WiFi status codes
String getWiFiStatus(wl_status_t status) {
  switch(status) {
    case WL_IDLE_STATUS:        return "WL_IDLE_STATUS";
    case WL_NO_SSID_AVAIL:      return "WL_NO_SSID_AVAIL (SSID not found)";
    case WL_SCAN_COMPLETED:     return "WL_SCAN_COMPLETED";
    case WL_CONNECTED:          return "WL_CONNECTED";
    case WL_CONNECT_FAILED:     return "WL_CONNECT_FAILED (check SSID/password)";
    case WL_CONNECTION_LOST:    return "WL_CONNECTION_LOST";
    case WL_DISCONNECTED:       return "WL_DISCONNECTED";
    case WL_NO_SHIELD:          return "WL_NO_SHIELD";
    default:                    return "UNKNOWN_STATUS";
  }
}

void checkExternalAudio() {
  if (isPlaying || audioBuffer != NULL) return; // Don't poll while busy/recording

  WiFiClient client;
  HTTPClient http;
  
  // Use the IP from serverUrl to keep it consistent
  String serverBase = String(serverUrl).substring(0, String(serverUrl).indexOf("/v1/ingest"));
  String pollUrl = serverBase + "/v1/device/" + String(deviceId) + "/poll";
  
  http.begin(client, pollUrl);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String payload = http.getString();
    StaticJsonDocument<256> doc;
    deserializeJson(doc, payload);
    
    if (!doc["convo_id"].isNull()) {
      const char* audioUrl = doc["audio_url"];
      Serial.printf("\n[Simulator] Request received: %s\n", audioUrl);
      
      // serverBase is already calculated above
      globalAudioUrl = serverBase + String(audioUrl);
      
      if (mp3 && mp3->isRunning()) mp3->stop();
      if (file) { delete file; file = NULL; }
      if (mp3) { delete mp3; mp3 = NULL; }
      if (out) { delete out; out = NULL; }

      out = new AudioOutputI2S();
      out->SetPinout(I2S_SPEAKER_BCLK, I2S_SPEAKER_LRC, I2S_SPEAKER_DIN);
      out->SetGain(0.0);
      file = new AudioFileSourceHTTPStream(globalAudioUrl.c_str());
      file->SetReconnect(0, 0); 
      mp3 = new AudioGeneratorMP3();
      if (mp3->begin(file, out)) {
          isPlaying = true;
          delay(200);
          out->SetGain(0.5);
      }
    }
  }
  http.end();
}

void sendData(float temp, float moisture, float light, uint8_t* audioData, size_t audioSize) {
  WiFiClient client;
  
  // Robust URL Parsing (handling http://host:port/path)
  String serverStr = String(serverUrl);
  int startIdx = serverStr.indexOf("//") + 2;
  int pathIdx = serverStr.indexOf("/", startIdx);
  
  String hostPort, path;
  if (pathIdx == -1) {
    hostPort = serverStr.substring(startIdx);
    path = "/";
  } else {
    hostPort = serverStr.substring(startIdx, pathIdx);
    path = serverStr.substring(pathIdx);
  }
  
  String host;
  int port = 80; // Default HTTP port
  
  int colonIdx = hostPort.indexOf(":");
  if (colonIdx != -1) {
    host = hostPort.substring(0, colonIdx);
    port = hostPort.substring(colonIdx + 1).toInt();
  } else {
    host = hostPort;
  }
  
  // Add Query Params
  path += "?device_id=" + String(deviceId) + 
          "&temperature=" + String(temp, 2) + 
          "&moisture=" + String(moisture, 2) + 
          "&light=" + String(light, 2);

  Serial.printf("Connecting to %s:%d...\n", host.c_str(), port);
  client.setTimeout(10000); // 10 seconds timeout for slow hotspots
  
  if (!client.connect(host.c_str(), port)) {
    Serial.println("Connection FAILED! Restarting to clear RAM...");
    delay(2000);
    ESP.restart(); // Auto-restart on network failure to clear fragmentation
    return;
  }

  // Construct the multipart boundary
  String boundary = "----ESP32Boundary" + String(millis());
  String head = "--" + boundary + "\r\n" +
                "Content-Disposition: form-data; name=\"audio\"; filename=\"capture.wav\"\r\n" +
                "Content-Type: audio/wav\r\n\r\n";
  String tail = "\r\n--" + boundary + "--\r\n";

  uint32_t totalLen = head.length() + audioSize + tail.length();

  // Send HTTP Headers
  client.print("POST " + path + " HTTP/1.1\r\n");
  client.print("Host: " + host + "\r\n");
  client.print("Content-Type: multipart/form-data; boundary=" + boundary + "\r\n");
  client.print("Content-Length: " + String(totalLen) + "\r\n");
  client.print("Connection: close\r\n\r\n");

    // 4. Send Body and FREE RAM IMMEDIATELY
    client.print(head);
    size_t chunkSize = 1024;
    for (size_t i = 0; i < audioSize; i += chunkSize) {
        size_t currentChunk = (audioSize - i < chunkSize) ? audioSize - i : chunkSize;
        client.write(audioData + i, currentChunk);
    }
    client.print(tail);
    
    // Recovery: Free the large 160KB buffer as soon as it's sent to clear RAM for playback
    if (audioBuffer) { free(audioBuffer); audioBuffer = NULL; } 
    Serial.println("Sent. Waiting for response...");

    while (client.connected() && !client.available()) delay(10);
    
    String statusLine = "";
    String payload = "";
    if (client.available()) {
        statusLine = client.readStringUntil('\n');
        if (statusLine.indexOf("200") > 0) {
            // Skip Headers
            while (client.available()) {
                String line = client.readStringUntil('\n');
                if (line == "\r") break;
            }
            // Read JSON body (Wait for server to close connection)
            while (client.connected() || client.available()) {
                if (client.available()) {
                    payload += (char)client.read();
                }
            }
        } else {
            Serial.println("Post FAILED - Status: " + statusLine);
        }
    }
    
    if (payload.length() > 0) {
        Serial.println("Response Payload: " + payload);
        StaticJsonDocument<512> doc;
        DeserializationError error = deserializeJson(doc, payload);
        if (!error) {
            const char* audioUrl = doc["audio_url"];
            String serverBase = "http://" + host + ":" + String(port);
            globalAudioUrl = serverBase + String(audioUrl); 
            Serial.printf("Plant is responding: %s\n", globalAudioUrl.c_str());
            
            // --- CRITICAL: Stop current objects before new allocation ---
            if (mp3 && mp3->isRunning()) mp3->stop();
            if (file) { delete file; file = NULL; }
            if (mp3) { delete mp3; mp3 = NULL; }
            if (out) { delete out; out = NULL; }

            // Re-init Speaker output after I2S1 was used for Mic
            out = new AudioOutputI2S();
            out->SetPinout(I2S_SPEAKER_BCLK, I2S_SPEAKER_LRC, I2S_SPEAKER_DIN);
            out->SetGain(0.0); // ANTI-POP

            // Start playing the new response (MP3 is much better for streaming!)
            Serial.printf("--- INITIATING GET REQUEST: %s ---\n", globalAudioUrl.c_str());
            file = new AudioFileSourceHTTPStream(globalAudioUrl.c_str());
            // CRITICAL: Disable auto-reconnect. 
            // We rely on the PRE-GENERATED 'hmm.mp3' for instant data. 
            // If connection drops, we accept it (better than looping).
            file->SetReconnect(0, 0); 
            
            mp3 = new AudioGeneratorMP3();
            if (mp3->begin(file, out)) {
                Serial.println("MP3 Pipeline Started Success.");
                isPlaying = true; // Block recording until this finished
            } else {
                Serial.println("MP3 Pipeline FAILED to Start.");
                isPlaying = false; 
            }
            
            delay(200); 
            out->SetGain(0.5); 
            Serial.println("DEBUG: Gain set to 0.5");
        } else {
            Serial.printf("JSON Parse Error: %s\n", error.c_str());
        }
    }
    client.stop();
}

size_t recordAudio() {
    Serial.printf("\n--- MEMORY CHECK ---\n");
    Serial.printf("Total Free Heap: %u bytes\n", ESP.getFreeHeap());
    Serial.printf("Largest Free Block: %u bytes\n", heap_caps_get_largest_free_block(MALLOC_CAP_8BIT));

    // 1. Allocate buffer FIRST to ensure we have room before breaking I2S
    audioBuffer = (uint8_t*)malloc(audioBufferSize);
    if (!audioBuffer) {
        Serial.println("ERROR: Out of RAM! Try decreasing RECORD_TIME further.");
        return 0;
    }
    memset(audioBuffer, 0, audioBufferSize); // Zero out buffer

    // 2. ONLY stop speaker if malloc succeeded
    if (mp3 && mp3->isRunning()) mp3->stop();
    delay(200); 
    i2s_driver_uninstall(I2S_NUM_0); 

    // 3. Configure I2S for Mic
    i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = SAMPLE_RATE,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT, // Swapped to RIGHT to rule out driver bug
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 1024,
        .use_apll = false
    };
    i2s_pin_config_t pin_config = {
        .bck_io_num = I2S_MIC_SCK,
        .ws_io_num = I2S_MIC_WS,
        .data_out_num = -1,
        .data_in_num = I2S_MIC_SD
    };

    esp_err_t err = i2s_driver_install(I2S_NUM_1, &i2s_config, 0, NULL);
    if (err != ESP_OK) {
        Serial.printf("I2S Driver Install Error: %d\n", err);
        return 0;
    }
    i2s_set_pin(I2S_NUM_1, &pin_config);
    i2s_zero_dma_buffer(I2S_NUM_1); // Crucial: Clear DMA before starting

    Serial.printf("--- RECORDING (%d Seconds) ---\n", RECORD_TIME);
    Serial.println("Speak now...");
    
    size_t bytes_read;
    uint32_t startTime = millis();
    int offset = WAV_HEADER_SIZE;
    int32_t raw_sample;
    int debugCount = 0;

    while (millis() - startTime < (RECORD_TIME * 1000)) {
        if (offset + 2 >= audioBufferSize - BUFFER_PADDING) break;

        i2s_read(I2S_NUM_1, &raw_sample, 4, &bytes_read, portMAX_DELAY);
        
        // Use the top 16 bits of the 32-bit word (most robust for 24-bit INMP441)
        int16_t sample = (raw_sample >> 16); 
        
        // --- DEBUG: Print first 10 samples to check for signal ---
        if (debugCount < 10 && bytes_read > 0) {
            Serial.printf("Raw: 0x%08X | Sample: %d\n", raw_sample, sample);
            debugCount++;
        }

        audioBuffer[offset] = sample & 0xFF;
        audioBuffer[offset+1] = (sample >> 8) & 0xFF;
        offset += 2;
    }

    // 4. Update WAV Header with EXACT size recorded
    generateWavHeader(audioBuffer, offset - WAV_HEADER_SIZE);

    // Shutdown Mic I2S
    i2s_stop(I2S_NUM_1);
    i2s_driver_uninstall(I2S_NUM_1); // Release I2S1 for Speaker
    
    Serial.println("Recording Finished.");
    Serial.println("Stabilizing Radio for 1s...");
    delay(1000); // BREATHING ROOM: Allow radio to recover from I2S high-speed clocks
    return offset;
}

void setup() {
  // --- ABSOLUTE TOP: Initialize Serial for Safe-Boot ---
  Serial.begin(115200);
  delay(2000); // CRITICAL: Wait for USB-CDC to initialize
  Serial.println("\n\n[BOOT] Smart Plant Pot Starting...");
  Serial.printf("[BOOT] Initial Free Heap: %u bytes\n", ESP.getFreeHeap());
  
  // Initialize DHT sensor
  dht.begin();

  // --- CRITICAL: Stabilize radio BEFORE connection ---
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);    // Disable power save to prevent AUTH_EXPIRE
  // WiFi.setTxPower(WIFI_POWER_13dBm); // Let ESP32 auto-negotiate power for mejor handshake stability
  
  // Force WPA2/Disable Power Save to avoid iPhone WPA3/PMF transition issues
  // This is a common fix for "Reason: 2 - AUTH_EXPIRE"
  esp_wifi_set_ps(WIFI_PS_NONE);
  
  delay(2000); // Increased stabilization delay

  Serial.println("\n=== WiFi Debugging Info ===");
  Serial.printf("Free Heap: %u bytes\n", ESP.getFreeHeap());

  // --- Scan available networks (Disabled for speed) ---
  Serial.println("WiFi Scan skipped for speed.");

  // --- Configure WiFi ---
  Serial.println("\n=== WiFi Connection Attempt ===");
  WiFi.disconnect(true);
  delay(500);

  Serial.print("Connecting to: '"); Serial.print(hotspot_ssid);
  Serial.print("' with password: "); Serial.println(hotspot_pass);
  
  WiFi.begin(hotspot_ssid, hotspot_pass);


  Serial.println("\nConnecting... (timeout: 40sec)");

  unsigned long startTime = millis();
  unsigned long timeout = 40000; // 40 seconds
  int attemptCount = 0;

  while (WiFi.status() != WL_CONNECTED && (millis() - startTime < timeout)) {
    attemptCount++;

    // Print detailed info every 4 attempts (every 2 seconds)
    if (attemptCount % 4 == 0) {
      Serial.print("Attempt "); Serial.print(attemptCount);
      Serial.print(" | Status: "); Serial.print(getWiFiStatus(WiFi.status()));
      Serial.print(" | RSSI: "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
    } else {
      Serial.print("."); // keep showing activity
    }

    delay(500);
  }

  // Check final result
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected!");
    Serial.print("Connected SSID: "); Serial.println(WiFi.SSID());
    Serial.print("IP Address: "); Serial.println(WiFi.localIP());
    Serial.print("Signal Strength: "); Serial.print(WiFi.RSSI()); Serial.println(" dBm");
  } else {
    Serial.println("\nWiFi Connection FAILED!");
    Serial.print("Final Status: "); Serial.println(getWiFiStatus(WiFi.status()));
    Serial.println("Troubleshooting:");
    Serial.print("  - Expected SSID: '"); Serial.print(hotspot_ssid); Serial.println("'");
    Serial.println("  - Ensure hotspot is ON and using 2.4 GHz (ESP32-S3 cannot use 5 GHz)");
    Serial.println("  - Check spelling and password in secrets.h");
  }

  Serial.print("Configured (primary) SSID: "); Serial.println(hotspot_ssid);

  // --- Init sensors and audio ---
  // sensors.begin(); // Disabled for now
  out = new AudioOutputI2S();
  out->SetPinout(I2S_SPEAKER_BCLK, I2S_SPEAKER_LRC, I2S_SPEAKER_DIN);
  out->SetGain(0.0); // ANTI-POP: Build up clocks first
  delay(100);
  out->SetGain(0.5); 
}

void loop() {
  // Read Sensors (Only every 3 seconds)
  // temp and humidity are now global variables

  if (millis() - lastDhtReadTime > dhtInterval) {
    lastDhtReadTime = millis();
    temp = dht.readTemperature();
    humidity = dht.readHumidity();
    
    Serial.print("Raw Temp: "); Serial.println(temp);
    Serial.print("Raw Humidity: "); Serial.println(humidity);
    
    if (isnan(temp) || isnan(humidity)) {
      Serial.println("❌ FAILED to read from DHT sensor! Check wiring.");
      temp = 25.0;
    } else {
      Serial.println("✅ DHT11 Read Success");
    }
  }

  int moistureRaw = analogRead(MOISTURE_PIN);
  float moisture = map(moistureRaw, 3000, 1000, 0, 100);
  moisture = constrain(moisture, 0, 100); 

  // Poll for external audio requests (e.g. from simulator)
  if (millis() - lastPollTime > pollInterval) {
    lastPollTime = millis();
    checkExternalAudio();
  }

  if (Serial.available() && !isPlaying) {
    if (Serial.read() == 's') {
      size_t actualSize = recordAudio(); // Now returns the recorded payload size
      if (actualSize > WAV_HEADER_SIZE) {
          Serial.println("Stabilizing WiFi before send...");
          delay(1000); 
          sendData(temp, moisture, 5.0, audioBuffer, actualSize);
          // Memory is now freed inside sendData() for faster recovery
      }
      // Flush any accidental extra 's' presses during recording/sending
      while(Serial.available()) Serial.read(); 
    }
  }

  // [FIXED] Proper Loop Handling
  if (isPlaying && mp3 && mp3->isRunning()) {
      // Feed the MP3 decoder as fast as possible
      if (!mp3->loop()) {
          Serial.println("Playback finished. Cleaning up objects.");
          mp3->stop();
          delete mp3; mp3 = NULL;
          if (file) { delete file; file = NULL; }
          if (out) out->SetGain(0.0); // ANTI-POP
          isPlaying = false; // Allow recording again
          delay(1000); // 1s Debounce: Wait for radio noise to settle
          while(Serial.available()) Serial.read(); // Clear any 's' pressed during play
          Serial.println("--- READY FOR NEXT TALK ('s' to start) ---");
      }
  }
}
```

### Troubleshooting: No Serial Output
If nothing is printed in the Monitor after uploading:

1. **USB Cable**: Many cables are "Charge Only". Ensure you are using a **Data Sync** cable.
2. **Baud Rate**: Ensure the **PlatformIO Serial Monitor** is set to `115200`. (Check `monitor_speed = 115200` in `platformio.ini`).
3. **USB CDC On Boot**: Since the ESP32-S3 uses an internal USB Serial, you may need to add this to your `platformio.ini`:
    ```ini
    build_flags = 
        -D ARDUINO_USB_MODE=1
        -D ARDUINO_USB_CDC_ON_BOOT=1
    ```
### 6. Troubleshooting "No matching WiFi found"
If the monitor says `[E] no matching wifi found!`:

1. **iPhone Hotspot Name**: iPhone hotspots often use a curly apostrophe (**`’`**) instead of a straight one (**`'`**). Check your "Available networks" list in the Serial Monitor. If it says `Yi Siang’s iPhone`, update your `secrets.h` to match **exactly**.
2. **Maximize Compatibility**: On your iPhone, go to **Settings -> Personal Hotspot** and turn on **"Maximize Compatibility"**. This is required to enable the 2.4GHz signal that the ESP32 uses.
3. **SSID Case Sensitivity**: Ensure your `hotspot_ssid` in `secrets.h` matches the casing (e.g., `iPhone` vs `iphone`) seen in the scan results.
4. **Distance**: Ensure your ESP32 is within 2 meters of your laptop/hotspot during setup.

### 7. Troubleshooting "Reason: 2 - AUTH_EXPIRE"
This means the iPhone timed out waiting for the ESP32 to authenticate.
1. **Forget & Reset**: On your iPhone, go to **Settings -> WiFi**, find your hotspot (or your laptop's connection), and tap **"Forget This Network"**. Then toggle the Hotspot OFF and ON again.
2. **Maximize Compatibility**: Double-check that **"Maximize Compatibility"** is ON. If it was already ON, try toggling it OFF and back ON.
3. **Power Cycle**: Unplug the ESP32, wait 5 seconds, and plug it back in. Handshake errors often persist across soft-restarts.
4. **SSID Simplification (Recommended)**: The curly apostrophe (**`’`**) is a nightmare for ESP32. If it still fails, change your iPhone name (**Settings -> General -> About -> Name**) to something simple like **`TestPot`** (no spaces, no symbols). This is the #1 way to fix all connection issues instantly.

### 8. Troubleshooting "Reason: 202 - AUTH_FAIL"
This is a standard "Wrong Password" or "Mismatched SSID" error.
1. **SSID Exact Match**: Looking at your Serial log, your iPhone name is actually **`Yi Siang’s iPhone`**. Your code had `iphone` (lower case) and a straight `'`. You **MUST** copy the name exactly as it appears in the "Available networks" scan list.
2. **Password Verification**: Re-type your password in `secrets.h` to ensure there are no trailing spaces or typos.

### 9. Hardware Tip: Temperature says -127.00
If your serial monitor shows `temperature=-127.00`:
- **Wiring**: This means the ESP32 cannot find your DS18B20 sensor.
- **Pull-up Resistor**: Ensure you have a **4.7kΩ resistor** between the `Data` pin (GPIO 1) and `3.3V`. Without this, the sensor won't communicate!

### 10. CRITICAL: "FS.h: No such file or directory"
If you still see the `FS.h` error after updating `platformio.ini`:
1. **Delete `.pio` Folder**: Close VS Code, manually delete the `.pio` folder inside your project directory, and reopen VS Code. This forces PlatformIO to re-download and re-index all libraries.
2. **Force LDF Mode**: Ensure `lib_ldf_mode = deep+` is set in your `platformio.ini`.
3. **Core Version**: Ensure your PlatformIO ESP32 platform is up to date. You can update it by running `pio platform update espressif32` in the terminal.

### 11. Troubleshooting: Silent Audio Recording
If your device records silence (zero bytes or a flat-line waveform):
1.  **Check INMP441 L/R Pin**: This pin must be connected to **GND** for `I2S_CHANNEL_FMT_ONLY_LEFT`. If it is unconnected, the microphone might not output any data.
2.  **Software Channel Swap**: If wiring is correct, try changing this line in `src/main.cpp`:
    *   **From**: `.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT`
    *   **To**: `.channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT`
    (Some ESP32-S3 driver versions have inverted channel mapping).
3.  **Check Power**: Ensure the INMP441 is getting a clean 3.3V. Low voltage can cause the digital output to stay at zero.

## Getting Started with Hardware

Follow these steps to get your physical Smart Plant Pot online and connected to the backend:

### 1. Start the Backend Server
Ensure your backend server is running and accessible from your local network:
```bash
python main.py
```
*Note: Make sure your ESP32 and the computer running the backend are on the **same WiFi network**.*

### 2. Configure project
1. Open the project folder in **VS Code** with the **PlatformIO** extension installed.
2. **Create `include/secrets.h`**: 
   Inside your PlatformIO project, create a file named `secrets.h` in the `include` folder and paste this:
   ```cpp
   #ifndef SECRETS_H
   #define SECRETS_H
   const char* hotspot_ssid = "YS"; // NOTE: USE THE CURLY ’ AND CAPITAL I/P
   const char* hotspot_pass = "addyisslim";
   #endif
   ```
3. **Find your Server IP**: 
   The ESP32 needs to know your laptop's address. Open a terminal on your laptop and type:
   - **Windows**: `ipconfig` (Look for "IPv4 Address" under your WiFi adapter, e.g., `192.168.1.50`)
   - **Mac/Linux**: `ifconfig` or `hostname -I`
4. **Update `src/main.cpp`**: 
   Replace `10.32.12.233` in `serverUrl` with your actual laptop IP:
   `const char* serverUrl = "http://192.168.x.x:8000/v1/ingest";`
5. Ensure `platformio.ini` matches your hardware (the provided config works for S3 DevKitC-1).

> **Note on IntelliSense Errors**: If VS Code shows a red squiggly line under `#include <Audio.h>`, it's likely because the library hasn't been downloaded yet. To fix this:
> 1. Click the **Build** button (check-mark icon in the bottom bar). This will download the libraries.
> 2. After building, if the error persists, open the PlatformIO sidebar (ant icon) and select **Miscellaneous -> Rebuild IntelliSense Index**.

### 3. Upload to ESP32-S3
1. Connect your ESP32-S3 DevKitC-1 to your computer via USB (use the **USB** port, not UART, if using CDC).
2. Click the **PlatformIO icon** (the ant head) in the sidebar.
3. Select **Upload and Monitor** for your environment.

### 4. Start the Interaction
1. Once the monitor opens and connects to WiFi, type the letter **`s`** into the terminal and press **Enter**.
2. This will trigger the sensor reading and data ingestion.
3. You should hear the plant's "Hmm..." backchannel immediately through the speaker, followed by its expert botanical advice!

### 5. Verifying the Connection
How to tell if your hardware is correctly communicating with the backend:

- **Check PlatformIO Serial Monitor**: You should see "WiFi Connected" and then `httpCode: 200` after pressing 's'. If the code is `-1`, the ESP32 can't reach your computer (check IP address or firewall).
- **Watch Backend Logs**: The terminal running `main.py` will print:
  `DEBUG: Received Ingest - Device: s3_devkitc_plant_pot, Text: None, Audio: None`
  If you see this, the connection is successful!
- **Speaker Check**: If the connection goes through, the ESP32 will immediately print `audio_url`. The `audio.loop()` will then start playing the "Hmm..." sound.
- **Ping Test**: From your computer, try to `ping <ESP32_IP>` (the IP is printed in the **PlatformIO Serial Monitor** on boot) to ensure they can "see" each other.

### 6. Monitor Logs
Check the backend terminal to see the incoming requests from the ESP32 and the AI agent's decision-making process.

## Hardware Integration Guide

To connect your real ESP32 sensors and microphone to this backend:

### 1. Ingest Data
Send a `POST` request to `http://<YOUR_SERVER_IP>:8000/v1/ingest` with `device_id`, `temperature`, `moisture`, `light`, and an `audio` file (16kHz WAV).

### 2. Stream Response
The `/v1/ingest` endpoint returns a JSON immediately with a `audio_url` (e.g., `/v1/audio/stream/123`). 
- **Streaming**: The `ESP32-audioI2S` library handles the `audio_url` directly. It will stream and play the audio chunks in real-time.
- **Immediate Playback**: The plant's "Hmm..." backchannel will play as soon as the stream starts, followed by the actual answer.

### 3. Parse Metadata
Use `GET /v1/history?device_id=<ID>` after the audio finishes to retrieve the final `reply_text` and `mood` for your display/LCD face.
