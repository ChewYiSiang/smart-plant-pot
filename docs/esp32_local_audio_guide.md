# Guide: Local Audio Storage on ESP32 (LittleFS)

Storing your alert sound on the ESP32 itself eliminates the HTTP request delay, making your plant's reactions feel instantaneous.

## 1. Project Configuration

Add the following to your `platformio.ini` to enable LittleFS:

```ini
board_build.filesystem = littlefs
```

## 2. Prepare the File

1. In your PlatformIO project, create a folder named `data` in the root directory.
2. Place your `alert.wav` file inside this `data` folder.

## 3. Upload the File to ESP32

In VS Code with PlatformIO:
1. Click the **PlatformIO icon** (the ant head) in the sidebar.
2. Expand your project environment.
3. Go to **Platform** -> **Build Filesystem Image**.
4. Then go to **Platform** -> **Upload Filesystem Image**.

## 4. Update the Code (`src/main.cpp`)

Modify your code to include LittleFS and update the playback logic.

### Header and Initialization
```cpp
#include <LittleFS.h>
#include "AudioFileSourceLittleFS.h" // You may need earlephilhower/ESP8266Audio library

void setup() {
    // ... other setup code ...
    if(!LittleFS.begin()){
        Serial.println("LittleFS Mount Failed");
        return;
    }
}
```

### Updated Playback Function
Replace your `checkExternalAudio` or alert handling logic to play from local flash:

```cpp
void playLocalAlert() {
    Serial.println("[Local] Playing alert.wav from flash...");
    
    // Stop any current audio
    if (mp3 && mp3->isRunning()) mp3->stop();
    if (wav && wav->isRunning()) wav->stop();
    if (file) { delete file; file = NULL; }

    // Use LittleFS source instead of HTTPStream
    AudioFileSourceLittleFS *localFile = new AudioFileSourceLittleFS("/alert.wav");
    wav = new AudioGeneratorWAV();
    
    if (wav->begin(localFile, out)) {
        isPlaying = true;
        out->SetGain(0.8);
        while(wav->isRunning()) {
            if (!wav->loop()) wav->stop();
        }
    }
    delete localFile; // Cleanup
}
```

## Why this improves latency:
- **No TCP Connection**: Saves ~100-300ms.
- **No HTTP Handshake**: Saves ~50-100ms.
- **No Data Streaming overhead**: Instant access to file bytes.
