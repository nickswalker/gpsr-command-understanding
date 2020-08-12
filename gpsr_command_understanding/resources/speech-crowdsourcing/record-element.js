var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var _a;
window.AudioContext = (_a = window.AudioContext) !== null && _a !== void 0 ? _a : window.webkitAudioContext;
function getStream() {
    var _a, _b;
    return __awaiter(this, void 0, void 0, function* () {
        if (((_a = window.sharedAudioStream) === null || _a === void 0 ? void 0 : _a.active) === false) {
            window.sharedAudioStream = null;
            window.sharedAudioContext = null;
        }
        return (_b = window.sharedAudioStream) !== null && _b !== void 0 ? _b : yield function () {
            return __awaiter(this, void 0, void 0, function* () {
                window.sharedAudioContext = new AudioContext();
                try {
                    window.sharedAudioStream = yield navigator.mediaDevices.getUserMedia({
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
                    return window.sharedAudioStream;
                }
                catch (e) {
                    alert('getUserMedia threw exception :' + e);
                    return null;
                }
            });
        }();
    });
}
export class AudioRecorderElement extends HTMLElement {
    constructor() {
        super();
        this.recordedChunks = [];
        this.shouldStop = false;
        let shadow = this.attachShadow({ mode: 'open' });
        let startStopButton = document.createElement("button");
        startStopButton.innerText = "Record";
        startStopButton.classList.add("record");
        startStopButton.style.verticalAlign = "top";
        startStopButton.style.marginRight = "6px";
        shadow.appendChild(startStopButton);
        startStopButton.onclick = () => { this.startStopResetClicked(); };
        this.startStopResetButton = startStopButton;
        this.audioPlayback = document.createElement("audio");
        this.audioPlayback.setAttribute('controls', '');
        shadow.appendChild(this.audioPlayback);
        this.audioPlayback.addEventListener("loadedmetadata", () => { this.dispatchEvent(new Event("recordingchanged")); });
        this.textDisplay = document.createElement("p");
        this.shadowRoot.append(this.textDisplay);
        let levels = document.createElement("canvas");
    }
    get recording() {
        if (this.audioPlayback.src === "" || this.audioPlayback.src.slice(-1) === '/') {
            return null;
        }
        else {
            return this.audioPlayback.src;
        }
    }
    get isRecording() {
        var _a;
        return ((_a = this.recorder) === null || _a === void 0 ? void 0 : _a.state) === "recording";
    }
    startStopResetClicked() {
        if (this.isRecording) {
            this.stop();
        }
        else if (this.recording) {
            this.reset();
        }
        else {
            this.record();
        }
    }
    record() {
        var _a, _b;
        return __awaiter(this, void 0, void 0, function* () {
            if (((_a = this.recorder) === null || _a === void 0 ? void 0 : _a.state) === "inactive") {
                this.recorder = null;
            }
            this.recorder = (_b = this.recorder) !== null && _b !== void 0 ? _b : yield (() => __awaiter(this, void 0, void 0, function* () {
                let stream = yield getStream();
                if (stream === null || !stream.active) {
                    this.textDisplay.innerHTML = "<b>Cannot access microphone. Either this browser is not supported, or the user denied permission.</b>";
                    return null;
                }
                if (typeof MediaRecorder === "undefined") {
                    this.textDisplay.innerHTML = "<b>Cannot record media in this browser. Please use a supported browser.</b>";
                    return null;
                }
                let rec = new MediaRecorder(stream);
                rec.addEventListener('dataavailable', (e) => { this.dataAvailable(e); });
                rec.addEventListener('stop', () => { this.stopped(); });
                rec.addEventListener('start', () => { this.started(); });
                return rec;
            }))();
            if (this.recorder === null) {
                return;
            }
            this.shouldStop = false;
            this.recorder.start();
            this.textDisplay.innerHTML = "";
        });
    }
    started() {
        this.startStopResetButton.innerText = "Stop";
        this.dispatchEvent(new CustomEvent("recordingStarted", { bubbles: true, composed: true }));
    }
    stop() {
        this.recorder.stop();
        this.shouldStop = true;
    }
    stopped() {
        this.startStopResetButton.innerText = "Record";
        this.recordedBlob = new Blob(this.recordedChunks);
        this.audioPlayback.src = window.URL.createObjectURL(this.recordedBlob);
        this.startStopResetButton.innerText = "Reset";
        this.dispatchEvent(new CustomEvent("recordingStopped", { bubbles: true, composed: true }));
    }
    reset() {
        window.URL.revokeObjectURL(this.audioPlayback.src);
        this.audioPlayback.src = "/";
        this.recordedBlob = null;
        this.recordedChunks = [];
        this.startStopResetButton.innerText = "Start";
    }
    dataAvailable(e) {
        if (e.data.size > 0) {
            this.recordedChunks.push(e.data);
        }
        if (this.shouldStop === true && this.recorder.state !== "inactive") {
            this.recorder.stop();
        }
    }
}
window.customElements.define("audio-recorder", AudioRecorderElement);
//# sourceMappingURL=record-element.js.map