from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import TextFrame, LLMMessagesUpdateFrame, LLMMessagesAppendFrame, Frame
from src.core.prompts import ENGLISH_AGENT_PROMPT, HINDI_AGENT_PROMPT

class LanguageRouterProcessor(FrameProcessor):
    def __init__(self, context: LLMContext):
        super().__init__()
        self._context = context
        self._has_routed = False

    async def process_frame(self, frame: Frame, direction: FrameDirection):

        await super().process_frame(frame, direction)

        if direction == FrameDirection.UPSTREAM or not isinstance(frame, TextFrame) or self._has_routed == True:
            await self.push_frame(frame, direction)
            return
        else:
            if 'HINDI' in frame.text.upper():
                self._has_routed = True
                last_user_message = self._context.messages[-1]
                updated_messages = HINDI_AGENT_PROMPT + [last_user_message]
                swap_frame = LLMMessagesUpdateFrame(updated_messages)
                await self.push_frame(swap_frame, FrameDirection.UPSTREAM)
                return
            elif 'ENGLISH' in frame.text.upper():
                self._has_routed = True
                last_user_message = self._context.messages[-1]
                updated_messages = ENGLISH_AGENT_PROMPT + [last_user_message]
                swap_frame = LLMMessagesUpdateFrame(updated_messages)
                await self.push_frame(swap_frame, FrameDirection.UPSTREAM)




