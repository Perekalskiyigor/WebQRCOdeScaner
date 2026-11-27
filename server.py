
import asyncio
from pathlib import Path

from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack
)
from av import VideoFrame

from processor import process_frame


BASE_DIR = Path(__file__).resolve().parent

pcs = set()


class ProcessedVideoTrack(VideoStreamTrack):

    def __init__(self, track):
        super().__init__()
        self.track = track

    async def recv(self):

        frame = await self.track.recv()

        image = frame.to_ndarray(format="bgr24")

        image = await asyncio.to_thread(
            process_frame, image
        )

        new_frame = VideoFrame.from_ndarray(
            image,
            format="bgr24"
        )

        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame


async def index(request):
    return web.FileResponse(
        BASE_DIR / "static" / "index.html"
    )


async def health(request):
    return web.json_response({
        "status": "ok",
        "connections": len(pcs)
    })


async def offer(request):

    params = await request.json()

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():

        print("Connection:", pc.connectionState)

        if pc.connectionState in ("failed", "closed"):
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):

        print("Received track:", track.kind)

        if track.kind == "video":
            pc.addTrack(
                ProcessedVideoTrack(track)
            )

    try:
        await pc.setRemoteDescription(
            RTCSessionDescription(
                sdp=params["sdp"],
                type=params["type"]
            )
        )

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.json_response({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        })

    except Exception:
        await pc.close()
        pcs.discard(pc)
        raise


async def on_shutdown(app):

    await asyncio.gather(
        *(pc.close() for pc in pcs)
    )

    pcs.clear()


app = web.Application()

app.router.add_get("/", index)
app.router.add_get("/health", health)
app.router.add_post("/offer", offer)

app.router.add_static(
    "/static/",
    BASE_DIR / "static"
)

app.on_shutdown.append(on_shutdown)


if __name__ == "__main__":

    web.run_app(
        app,
        host="0.0.0.0",
        port=8095
    )
