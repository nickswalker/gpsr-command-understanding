declare global {
    interface Window {
        sharedAudioContext: any;
        sharedAudioStream: MediaStream;
        webkitAudioContext: any;
    }
}
export declare class AudioRecorderElement extends HTMLElement {
    private recorder;
    private audioPlayback;
    private recordedChunks;
    private shouldStop;
    private startStopResetButton;
    private textDisplay;
    recordedBlob: Blob;
    constructor();
    get recording(): string;
    get isRecording(): boolean;
    startStopResetClicked(): void;
    record(): Promise<void>;
    started(): void;
    stop(): void;
    stopped(): void;
    reset(): void;
    dataAvailable(e: any): void;
}
