
let pc = null;
let stream = null;

const video = document.getElementById("remoteVideo");
const status = document.getElementById("status");

async function start() {

    if (pc) return;

    try {

        status.textContent = "Подключение...";

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: {
                    ideal: "environment"
                },
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 25 }
            },
            audio: false
        });

        pc = new RTCPeerConnection();

        pc.ontrack = (event) => {
            video.srcObject = new MediaStream([
                event.track
            ]);
        };

        pc.onconnectionstatechange = () => {
            if (pc) {
                status.textContent = pc.connectionState;
            }
        };

        stream.getTracks().forEach(track => {
            pc.addTrack(track, stream);
        });

        const offer = await pc.createOffer();

        await pc.setLocalDescription(offer);

        await new Promise(resolve => {

            if (pc.iceGatheringState === "complete") {
                resolve();
                return;
            }

            pc.addEventListener(
                "icegatheringstatechange",
                function checkState() {

                    if (pc.iceGatheringState === "complete") {

                        pc.removeEventListener(
                            "icegatheringstatechange",
                            checkState
                        );

                        resolve();
                    }
                }
            );
        });

        const response = await fetch("/offer", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(pc.localDescription)
        });

        if (!response.ok) {
            throw new Error("Ошибка сервера");
        }

        const answer = await response.json();

        await pc.setRemoteDescription(answer);

    } catch (error) {

        stop();

        status.textContent = error.message;

        console.error(error);
    }
}


function stop() {

    if (stream) {
        stream.getTracks().forEach(track => {
            track.stop();
        });

        stream = null;
    }

    if (pc) {
        pc.close();
        pc = null;
    }

    video.srcObject = null;

    status.textContent = "Отключено";
}


document.getElementById("start").onclick = start;
document.getElementById("stop").onclick = stop;
