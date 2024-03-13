import av, asyncio, fractions, time, numpy, queue, platform, pyaudio
import logging as logger
from aiortc.mediastreams import MediaStreamTrack, AUDIO_PTIME
from aiortc.contrib.media import REAL_TIME_FORMATS
from av import VideoFrame, AudioFrame
from threading import Thread, Event
from screeninfo import get_monitors
import myGlobals

# Set AV logging, useful for if a stream is erroring for some reason, usually redundant
global resolutionScaler

AUDIO_PTIME = 0.020  # 20ms audio packetization
VIDEO_CLOCK_RATE = 90000
VIDEO_PTIME = 1 / 30  # 30fps
VIDEO_TIME_BASE = fractions.Fraction(1, VIDEO_CLOCK_RATE)
resolutionScaler = 1

class VideoFramePlayerTrack(MediaStreamTrack):
    # This track is made in webRtc.py and accepts the CameraPlayer object to read buffer from
    def __init__(self, screenplayer):
        super().__init__() # Init Class
        self.screenplayer = screenplayer # CameraPlayer reference
        self.kind = 'video' # Video or audio?
        
    async def recv(self):
        # Grab frame from video frame Queue Buffer    
        frame = await self.screenplayer.videoFrameBuffer.get()
        
        # print("Returning frame: " + str(frame))
        return frame
    
class AudioCameraPlayerTrack(MediaStreamTrack):
    # This track is made in webRtc.py and accepts the CameraPlayer object to read buffer from
    def __init__(self, cameraplayer):
        super().__init__() # Init Class
        self.cameraplayer = cameraplayer # CameraPlayer reference
        self.kind = 'audio' # Video or audio?
    # Consumer wants frame, get latest from CameraPlayer.
    async def recv(self):
        frame = await self.cameraplayer.audioFrameBuffer.get()
        # Grab frame from buffer and return
        print("Returning audio: " + str(frame))
        # await asyncio.sleep(0.01)
        return frame
                      
# Modified Media Player
class ScreenPlayer():
    def __init__(self, monitorsArray, monitorSelectionIndex, captureAudioBool):
        # self.__container = av.open(file=':0.0', format='x11grab', options={'hwaccel': 'auto', 'video_size': '1920x1080'}) # Open Cam Stream
        self.__thread: Optional[threading.Thread] = None # Thread to get frames
        self.__thread_quit: Optional[threading.Event] = None # Thread end event
        # Monitor data
        self.monitorsArray = monitorsArray
        self.monitorSelectionIndex = monitorSelectionIndex
        # Define local buffers
        self.videoFrameBuffer = asyncio.Queue()
        self.audioFrameBuffer = asyncio.Queue()
        self.captureAudioBool = captureAudioBool

        # Still object creation, auto start worker thread
        self._start()

    def _start(self):
        # Create thread if None
        # Start video thread, then audio thread
        if self.__thread is None:
            self.__thread_quit = Event()
            self.__thread = Thread(
                name="screen-player-thread",
                target=pyav_DisplayCaptureThread,
                args=(
                    asyncio.get_event_loop(),
                    self,
                    'video'
                ),
            )
            self.__thread.start()
        
        if self.captureAudioBool:
            Thread(
                name="screen-player-thread-audio",
                target=pyav_DisplayCaptureThread,
                args=(
                    asyncio.get_event_loop(),
                    self,
                    'audio'
                )).start()

    # Implement when I make cameraPlayer watchdog so cameraPlayers can only exist when a cameraPlayer has at least one track attatched?
    # Monitor through CameraPlayer._parasites as int? If is 0 then run cameraPlayer._stop
    # def _stop(self, track: PlayerStreamTrack) -> None:
    #     self.__started.discard(track)

    #     if not self.__started and self.__thread is not None:
    #         self.__log_debug("Stopping worker thread")
    #         self.__thread_quit.set()
    #         self.__thread.join()
    #         self.__thread = None

    #     if not self.__started and self.__container is not None:
    #         self.__container.close()
    #         self.__container = None

# PyAV Inputs Based On OS

def pyav_InitPerOS(monitorsArray, monitorSelectionIndex, audioOrVideo):
    # Returns stream
    runningOS = platform.system()
    # Options are Linux, Darwin, and Windows
    
    videoContainer = None
    audioContainer = None
    
    # Attempt to load screen size and offset
    # Set videoSize and offset
    pyAvVideoSize = (str(monitorsArray[monitorSelectionIndex][1]) + 'x' + str(monitorsArray[monitorSelectionIndex][2]))
    pyAvVideoOffset = '+' + (str(monitorsArray[monitorSelectionIndex][3]) + ',' + str(monitorsArray[monitorSelectionIndex][4]))
    
    # If Linux, assume X11 (Sorry Wayland)
    if runningOS == "Linux":
        # Audio is seperate on linux, I think on the others as well?
    
        if audioOrVideo == 'audio':
            # Unfortunatly audio cannot be captured with pyav, ffmpeg can do it, but pyav is not made for it
            # We can use pyaudio to open a stream and 
            # Init pyaudio device
            pyaudioDevice = pyaudio.PyAudio()
            
            # Open stream
            loopbackStream = pyaudioDevice.open(format=pyaudio.paInt16, channels=2, rate=44100, input=True, frames_per_buffer=1024)
            
            # audioContainer = av.open(file='56', options={'f': 'pulse', 'ac': '2'})
            #Temp
            # audioContainer = av.open('crumb.mp3')
        else:
            videoContainer = av.open(file=':0.0' + pyAvVideoOffset, format='x11grab', options={'framerate': '30', 'hwaccel': 'auto', 'video_size': pyAvVideoSize})
    
    else:    
        print("Error, your OS is not found, trace trace trace etc ")
        sys.exit(0)
    
    # Container was opened, returning video stream and videoContainer
    if audioOrVideo == 'audio':
        return loopbackStream
    else:
        return videoContainer.streams.video[0], videoContainer


def pyav_DisplayCaptureThread(loop, screenplayer, audioOrVideo):
    global resolutionScaler
    # Set audio dials
    audio_samples = 0
    audio_sample_rate = 48000
    audio_time_base = fractions.Fraction(1, audio_sample_rate)
    # Keeping sample bit length and sample rate, just changing formats
    audio_resampler = av.AudioResampler(
        format="s16",
        layout="stereo",
        rate=audio_sample_rate,
        frame_size=int(audio_sample_rate * AUDIO_PTIME)
        )
    
    videoStream = None
    videoContainer = None
    loopbackStream = None
    
    # Initialize streams based on OS
    # if screenplayer.captureAudioBool == False:
    #     videoStream, videoContainer = pyav_InitPerOS(screenplayer.monitorsArray, screenplayer.monitorSelectionIndex, False)
    # else:
    #     videoStream, videoContainer, audioStream, audioContainer = pyav_InitPerOS(screenplayer.monitorsArray, screenplayer.monitorSelectionIndex, True)

    if audioOrVideo == 'audio':
        loopbackStream = pyav_InitPerOS(screenplayer.monitorsArray, screenplayer.monitorSelectionIndex, audioOrVideo)
    else:
        videoStream, videoContainer = pyav_InitPerOS(screenplayer.monitorsArray, screenplayer.monitorSelectionIndex, audioOrVideo)

    
    vFrame = VideoFrame(width=1280, height=720)
    vFrame.pts = 0
    vFrame.time_base = '1/90000'
    # aFrame = AudioFrame(samples=960)
    # aFrame.pts = 0
    # aFrame.rate = 48000
    nextAudioFrame = None
    #Init frame
    video_first_pts = None

    frame_time = None

    # While my quit event isn't set
    while True: 
        try:
            if audioOrVideo == 'audio':
                # nextAudioFrame = next(audioContainer.decode(audioStream))
            
                nextAudioFrame = loopbackStream.read(1024)
                nextAudioFrame = numpy.frombuffer(nextAudioFrame, dtype=numpy.int16)
                
                print("Old Shape: " + str(nextAudioFrame.shape))
                nextAudioFrame = (nextAudioFrame.reshape(1, -1))
                print("New Shape: " + str(nextAudioFrame.shape))
                                
                nextAudioFrame = AudioFrame.from_ndarray(nextAudioFrame, format='s16')
                print("PyDevice: " + str(nextAudioFrame))
            
                # Handeling an audio frame
                if isinstance(nextAudioFrame, AudioFrame):
                    # print("1: " + str(frame))
                    for frame in audio_resampler.resample(nextAudioFrame):
                        # fix timestamps
                        frame.pts = audio_samples
                        frame.time_base = audio_time_base
                        audio_samples += frame.samples

                        frame_time = frame.time
                        # Put into buffer
                        # print("Write to buffer: " + str(frame))
                        asyncio.run_coroutine_threadsafe(screenplayer.audioFrameBuffer.put(frame), loop)
            
            else:
                screenShotVideoFrame = next(videoContainer.decode(videoStream))
  
                # Grab video stream frames     
                # Resize video frame to send, maybe to over ffmpeg eventually?
                # resizedWidth = (screenShotVideoFrame.width / resolutionScaler)
                # resizedHeight = (screenShotVideoFrame.height / resolutionScaler)
                resizedWidth = (screenShotVideoFrame.width / 1.5)
                resizedHeight = (screenShotVideoFrame.height / 1.5)
                
                
                # Resize frame
                screenShotVideoFrame = screenShotVideoFrame.reformat(width=resizedWidth, height=resizedHeight)

                # screenShotVideoFrame = screenShotVideoFrame.reformat(width=resizedWidth, height=resizedHeight, format='yuv420p')

            
                    
                # Do PTS Adjustments
                if isinstance(screenShotVideoFrame, VideoFrame):
                    if screenShotVideoFrame.pts is None:  # pragma: no cover
                        logger.warning(
                            "ScreenPlayer(%s) Skipping video frame with no pts", videoContainer.name
                        )
                        print("No PTS")
                        continue

                    # video from a webcam doesn't start at pts 0, cancel out offset
                    if video_first_pts is None:
                        video_first_pts = screenShotVideoFrame.pts
                    screenShotVideoFrame.pts -= video_first_pts
                    frame_time = screenShotVideoFrame.time
                                                    
                    # Create video frame and put into buffer
                    asyncio.run_coroutine_threadsafe(screenplayer.videoFrameBuffer.put(screenShotVideoFrame), loop)


            
        except Exception as exc:
            print("Exception in screen capture thread: " + str(exc))
            break