from src.scenes.GreetingScene import GreetingScene
from miniaudio import PlaybackDevice, SampleFormat
from libxmplite import Xmp, XmpError
from src import config, Chat
from redis import Redis


def stream_module(xmp: Xmp):
    required_frames = yield b""
    try:
        while True:
            required_frames = yield xmp.play_buffer(required_frames * 2 * 2)
    except XmpError as x:
        print("XMP Playback error!!", x)


def main():
    redis = Redis(
        host=config.redis_config["host"],
        port=config.redis_config["port"],
        db=config.redis_config["db"],
        charset="utf-8",
        decode_responses=True,
    )

    session = {"chat": Chat(redis)}

    device = PlaybackDevice(
        output_format=SampleFormat.SIGNED16, nchannels=2, sample_rate=44100
    )

    xmp = Xmp()

    xmp.load("background.mod")
    xmp.start(device.sample_rate)

    stream = stream_module(xmp)
    next(stream)  # start the generator

    device.start(stream)

    GreetingScene(session, redis).enter()

    xmp.stop()
    xmp.release()
    device.close()


if __name__ == "__main__":
    main()
