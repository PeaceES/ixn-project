from typing import Any
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    AsyncAgentEventHandler,
    AsyncFunctionTool,
    MessageDeltaChunk,
    MessageStatus,
    RunStatus,
    RunStep,
    RunStepDeltaChunk,
    RunStepStatus,
    ThreadMessage,
    ThreadRun,
)

from utils.utilities import Utilities
from evaluation.working_evaluator import quick_evaluate_response


class StreamEventHandler(AsyncAgentEventHandler[str]):
    """Handle LLM streaming events and tokens."""

    def __init__(self, functions: AsyncFunctionTool, project_client: AIProjectClient, utilities: Utilities) -> None:
        self.functions = functions
        self.project_client = project_client
        self.util = utilities
        self.current_thread_id = None
        self.current_run_id = None
        self.current_response_text = ""
        self.current_user_query = ""
        super().__init__()

    async def on_message_delta(self, delta: MessageDeltaChunk) -> None:
        """Handle message delta events. This will be the streamed token"""
        if delta.text:
            self.current_response_text += delta.text
        self.util.log_token_blue(delta.text)

    async def on_thread_message(self, message: ThreadMessage) -> None:
        """Handle thread message events."""
        pass
        # if message.status == MessageStatus.COMPLETED:
        #     print()
        # self.util.log_msg_purple(f"ThreadMessage created. ID: {message.id}, " f"Status: {message.status}")

        await self.util.get_files(message, self.project_client)

    async def on_thread_run(self, run: ThreadRun) -> None:
        """Handle thread run events"""
        
        # Store current run info for evaluation
        self.current_thread_id = run.thread_id
        self.current_run_id = run.id
        
        # Only reset response text at the beginning of a new run (not during completion)
        if run.status not in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            self.current_response_text = ""

        if run.status == RunStatus.FAILED:
            print(f"Run failed. Error: {run.last_error}")
            print(f"Thread ID: {run.thread_id}")
            print(f"Run ID: {run.id}")

    async def on_run_step(self, step: RunStep) -> None:
        pass
        # if step.status == RunStepStatus.COMPLETED:
        #     print()
        # self.util.log_msg_purple(f"RunStep type: {step.type}, Status: {step.status}")

    async def on_run_step_delta(self, delta: RunStepDeltaChunk) -> None:
        pass

    async def on_error(self, data: str) -> None:
        print(f"An error occurred. Data: {data}")

    async def on_done(self) -> None:
        """Handle stream completion."""
        # Auto-evaluate if enabled and we have run info
        if (os.getenv("ENABLE_AUTO_EVALUATION", "false").lower() == "true" and 
            self.current_thread_id and self.current_run_id):
            
            # Only evaluate if we have response text
            if not self.current_response_text.strip():
                return
            
            print("\n" + "="*50)
            print("🔍 EVALUATING RESPONSE...")
            
            try:
                eval_result = await quick_evaluate_response(
                    self.project_client, 
                    self.current_thread_id, 
                    self.current_run_id,
                    response_text=self.current_response_text,
                    user_query=self.current_user_query
                )
                
                if eval_result.get("enabled"):
                    if eval_result.get("error"):
                        print(f"❌ Evaluation failed: {eval_result['error']}")
                    else:
                        avg_score = eval_result.get("average_score", 0)
                        summary = eval_result.get("summary", "No summary available")
                        method = eval_result.get("method", "unknown")
                        
                        # Color-coded score display
                        if avg_score >= 4.0:
                            score_color = "🟢"
                        elif avg_score >= 3.0:
                            score_color = "🟡"
                        else:
                            score_color = "🔴"
                        
                        print(f"{score_color} Overall Score: {avg_score:.1f}/5.0")
                        print(f"📊 Details: {summary}")
                        print(f"✅ Evaluated with {eval_result.get('successful_evaluators', 0)} metrics ({method})")
                        
                else:
                    print("📋 Auto-evaluation disabled")
                    
            except Exception as e:
                print(f"⚠️ Evaluation error: {e}")
            
            print("="*50)

    async def on_unhandled_event(self, event_type: str, event_data: Any) -> None:
        """Handle unhandled events."""
        # print(f"Unhandled Event Type: {event_type}, Data: {event_data}")
        print(f"Unhandled Event Type: {event_type}")
