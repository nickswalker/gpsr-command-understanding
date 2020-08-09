declare global {
    interface Window {
        sharedAudioContext: any;
        sharedAudioStream: MediaStream;
        webkitAudioContext: any;
    }
}

window.AudioContext = window.AudioContext ?? window.webkitAudioContext;

declare var MediaRecorder: any;

async function getStream(){
    if (window.sharedAudioStream?.active === false) {
        window.sharedAudioStream = null
        window.sharedAudioContext = null
    }
    return window.sharedAudioStream ?? await async function () {
        // grab an audio context
        window.sharedAudioContext = new AudioContext();

        // Attempt to get audio input
        try {
            // ask for an audio input
            window.sharedAudioStream = await (<any> navigator.mediaDevices).getUserMedia(
                {
                    "audio": {
                        autoGainControl: false,
                        channelCount: 2,
                        echoCancellation: false,
                        latency: 0,
                        noiseSuppression: false,
                        sampleRate: 48000,
                        sampleSize: 16,
                        bitsPerSecond: 192000,
                        volume: 1.0
                    },
                });
            return  window.sharedAudioStream;
        } catch (e) {
            alert('getUserMedia threw exception :' + e);
            return null
        }
    }();

}

export class AudioRecorderElement extends HTMLElement {
    private recorder: any
    private audioPlayback: HTMLAudioElement
    private recordedChunks: Blob[] = []
    private shouldStop: boolean = false
    private startStopResetButton: HTMLButtonElement
    private textDisplay: HTMLParagraphElement

    recordedBlob: Blob

    constructor() {
        super();
        // Create a shadow root
        let shadow = this.attachShadow({mode: 'open'});
        let startStopButton = document.createElement("button")
        startStopButton.innerText = "Record"
        startStopButton.classList.add("record")
        startStopButton.style.verticalAlign = "top"
        startStopButton.style.marginRight = "6px"
        shadow.appendChild(startStopButton)
        startStopButton.onclick = () => {this.startStopResetClicked()}
        this.startStopResetButton = startStopButton


        this.audioPlayback = document.createElement("audio")
        this.audioPlayback.setAttribute('controls', '');
        shadow.appendChild(this.audioPlayback)
        // TODO: May need to check that this only fires for new audio URL...
        this.audioPlayback.addEventListener("loadedmetadata", () => {this.dispatchEvent(new Event("recordingchanged"))})

        this.textDisplay = document.createElement("p")
        this.shadowRoot.append(this.textDisplay)
        let levels = document.createElement("canvas")
        // TODO: Implement this as audio worklet if needed
    }

    get recording() : string{
        // null is a more predictable default state
        // Defalut is "", reset will end with /
        if (this.audioPlayback.src === "" || this.audioPlayback.src.slice(-1) === '/') {
            return null
        } else {
            return this.audioPlayback.src
        }
    }

    get isRecording() : boolean {
        return this.recorder?.state === "recording"
    }

     startStopResetClicked() {
        if (this.isRecording) {
            this.stop()
        } else if (this.recording) {
             this.reset()
        } else {
            this.record()
        }
    }

    async record() {
        // Happens when user revokes permission
        if (this.recorder?.state === "inactive") {
            this.recorder = null
        }
        this.recorder = this.recorder ??   await ( async() => {
            let stream = await getStream()
            if (stream === null || !stream.active) {
                this.textDisplay.innerHTML = "<b>Cannot access microphone. Either this browser is not supported, or the user denied permission.</b>"
                return null;
            }
            if (typeof MediaRecorder === "undefined") {
                this.textDisplay.innerHTML = "<b>Cannot record media in this browser. Please use a supported browser.</b>"
                return null;
            }
            let rec = new MediaRecorder(stream);
            rec.addEventListener('dataavailable',  (e: any) => {this.dataAvailable(e)})
            rec.addEventListener('stop', () => {this.stopped()})
            rec.addEventListener('start', () => {this.started()})
            return rec;
        })()
        if (this.recorder === null) {
            return;
        }
        this.shouldStop = false
        this.recorder.start()
        this.textDisplay.innerHTML = ""
    }

    started() {
        this.startStopResetButton.innerText = "Stop";
        this.dispatchEvent(new CustomEvent("recordingStarted", {bubbles: true, composed: true}))
    }

    stop() {
        this.recorder.stop()
        this.shouldStop = true
    }

    stopped() {
        this.startStopResetButton.innerText = "Record"
        this.recordedBlob = new Blob(this.recordedChunks);
        // NOTE(nickswalker): As of 6-2020, only Safari allows direct play of blobs
        this.audioPlayback.src = window.URL.createObjectURL(this.recordedBlob)
        this.startStopResetButton.innerText = "Reset"
        this.dispatchEvent(new CustomEvent("recordingStopped", {bubbles: true, composed: true}))
    }

    reset() {
        // Release memory tied up by blob
        window.URL.revokeObjectURL(this.audioPlayback.src)
        // Note that the value has the absolute URL of the html as a prefix now
        this.audioPlayback.src = "/"
        this.recordedBlob = null
        this.recordedChunks = []
        this.startStopResetButton.innerText = "Start"
    }

     dataAvailable(e: any) {
        if (e.data.size > 0) {
            this.recordedChunks.push(e.data);
        }

        if(this.shouldStop === true && this.recorder.state !== "inactive") {
            this.recorder.stop();
        }
    }


}

window.customElements.define("audio-recorder", AudioRecorderElement)