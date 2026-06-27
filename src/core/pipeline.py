from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair, LLMUserAggregatorParams
from pipecat.turns.user_start import VADUserTurnStartStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies, default_user_turn_stop_strategies
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineWorker
from pipecat.workers.runner import WorkerRunner
from pipecat.transports.livekit.transport import LiveKitTransport
from pipecat.processors.logger import FrameLogger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.processors.aggregators.llm_context import LLMContext
from src.services.tts import configure_tts
from src.services.stt import configure_stt
from src.services.llm import configure_llm
from src.core.language_switcher import LanguageSwitcher
import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "data"))
from data.scheme_tool import register_scheme_tool, SCHEME_TOOLS, SYSTEM_PROMPT


async def create_pipeline(transport: LiveKitTransport) -> tuple[WorkerRunner, PipelineWorker]:
    stt = configure_stt()
    tts = configure_tts()
    llm = configure_llm()
    register_scheme_tool(llm)

    initial_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    context = LLMContext(messages=initial_messages, tools=SCHEME_TOOLS)

    context_aggregator = LLMContextAggregatorPair(
        context=context,
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                start=[VADUserTurnStartStrategy()],  # only the mic/VAD starts a turn
                stop=default_user_turn_stop_strategies(),  # keep Smart Turn for turn-end
            ),
        ),
    )

    vad_processor = VADProcessor(
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.8))
    )

    language_switcher = LanguageSwitcher()

    pipeline = Pipeline([
        transport.input(), # Receives user audio
        vad_processor, # Bytes are chunked into sentences
        stt,
        language_switcher,  # detects spoken language -> switches TTS language
        context_aggregator.user(),
        llm, # LLM reads memory, generates reply
        tts, # TTS turns text reply into audio bytes
        transport.output(),  # Audio bytes sent to the speaker
        context_aggregator.assistant() # LLM's text saved to memory as "assistant"
    ])

    worker = PipelineWorker(pipeline)
    runner = WorkerRunner()

    return runner, worker