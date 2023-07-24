from tempos import g, sched, set_local_time, rtc, prtc, settings, pm
from graphics import rgb, WHITE, BLACK, YELLOW
from fonts import roboto18
from button import Button, ButtonMan
from widgets import ValueDisplay, Label, SwitchPanel, Clock, StatusBar

from drivers.axp202 import LD04
import time
from machine import ADC, Pin, I2S
import ustruct

# doc:
# https://github.com/Xinyuan-LilyGO/TTGO_TWatch_Library/blob/master/docs/watch_2020_v3.md
# https://github.com/Xinyuan-LilyGO/TTGO_TWatch_Library/
# https://docs.micropython.org/en/latest/library/machine.I2S.html#machine-i2s
# https://github.com/uraich/twatch2020_firmware/blob/6258eee0021351521da70d63a00d063e7a0acde7/hardware/sound/play-mono-wav-uasyncio.py
# https://github.com/OPHoperHPO/lilygo-ttgo-twatch-2020-micropython/issues/5
# https://github.com/miketeachman/micropython-i2s-examples
    # https://github.com/miketeachman/micropython-esp32-i2s-examples

# RECORDING SOUND
# the microphone supports PDM input according to the datasheet
# PDM DATA 	2
# PDM CLK 	0
microphone = ADC(Pin(2))
clock = Pin(0, Pin.OUT)

def start_recording():
    status.update("Started", False)
    t = time.ticks_ms()
    samples = []
    try:
        while time.ticks_diff(time.ticks_ms(), t) < 1000:
            sample = microphone.read_u16()
            clock.value(1)
            time.sleep_us(5)
            clock.value(0)
            samples.append(sample)

        status.update("Saving", False)
        with open("recording.wav", "wb") as f:
            # WAV file header
            f.write(b"RIFF")
            f.write(ustruct.pack("<I", 36 + len(samples) * 2))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(ustruct.pack("<IHHIIHH", 16, 1, 1, 44100, 44100 * 2, 2, 16))
            f.write(b"data")
            f.write(ustruct.pack("<I", len(samples) * 2))
            for s in samples:
                f.write(ustruct.pack("<h", s))

        status.update("Done", False)
    except Exception as err:
        status.update(str(err), False)
        #raise

# PLAYING SOUND
# I2S BCK 	26  clock signal
# I2S WS 	25  word select, used to specify number of bits of audio sample apparently
# I2S DOUT 	33  data output
bck_pin = Pin(26, Pin.OUT)
ws_pin = Pin(25, Pin.OUT)
dout_pin = Pin(33, Pin.OUT)
audio_out = I2S(1,
        sck=bck_pin,
        ws=ws_pin,
        sd=dout_pin,
        mode=I2S.TX,
        bits=16,
        format=I2S.MONO,
        rate=44100,
        ibuf=20000,
        )


def start_playing():
    status.update("Playing", False)
    try:
        with open("recording.wav", "rb") as f:
            # Read WAV file header
            header = f.read(44)

            # Read and send audio data
            while True:
                data = f.read(128)
                if not data:
                    break
                audio_out.write(data)

        status.update("Done", False)
    except Exception as err:
        status.update(str(err), False)
        #raise




# UI
bar = StatusBar()
status = Label(20, 200, 160, 40, roboto18, YELLOW)

buttons = ButtonMan()

start = Button("Record", 20, 100, 200, 40, theme=ValueDisplay.theme)
start.callback(start_recording)


play = Button("Play", 20, 140, 200, 40, theme=ValueDisplay.theme)
play.callback(start_playing)

buttons.add(start)
buttons.add(play)



def app_init():
    pm.setPower(LD04, 1)
    status.update("Idle", False)
    buttons.start()
    bar.draw()
    sched.setInterval(1000, bar.update)

def app_end():
    pm.setPower(LD04, 0)
    buttons.stop()
    sched.clearInterval(bar.update)
    g.fill(BLACK)
