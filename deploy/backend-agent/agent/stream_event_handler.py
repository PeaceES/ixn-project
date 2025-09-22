from typing import Any
import os

from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import (
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
# Evaluation module not needed for deployment
# from evaluation.working_evaluator import quick_evaluate_response


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
        self.captured_response = None  # Add explicit response capture
        # For tool call handling, we'll submit outputs differently in hub-based API
        super().__init__()

    async def on_message_delta(self, delta: MessageDeltaChunk) -> None:
        """Handle message delta events. This will be the streamed token"""
        try:
            # Only process delta content to avoid duplicates
            if hasattr(delta, 'delta') and delta.delta:
                delta_content = delta.delta
                if hasattr(delta_content, 'content') and delta_content.content:
                    for content_item in delta_content.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            if hasattr(content_item.text, 'value'):
                                text_value = content_item.text.value
                                if text_value:  # Only add non-empty values
                                    self.current_response_text += text_value
                                    # Token streaming disabled for cleaner output
                                    # self.util.log_token_blue(text_value)
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_message_delta: {e}")

    async def on_thread_message(self, message: ThreadMessage) -> None:
        """Handle thread message events."""
        try:
            # Capture the final response when message is completed
            if message.status == MessageStatus.COMPLETED and hasattr(message, 'content'):
                response_text = ""
                for content_item in message.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        if hasattr(content_item.text, 'value'):
                            response_text += content_item.text.value
                        else:
                            response_text += str(content_item.text)
                
                if response_text.strip():
                    # Always update captured_response with the latest complete message
                    self.captured_response = response_text
                    # Also update current_response_text to ensure consistency
                    if not self.current_response_text.strip() or len(response_text) > len(self.current_response_text):
                        self.current_response_text = response_text
                    # Captured complete message
            
            # Also handle the case where role is assistant (our response)
            elif getattr(message, 'role', None) == 'assistant' and hasattr(message, 'content'):
                response_text = ""
                for content_item in message.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        if hasattr(content_item.text, 'value'):
                            response_text += content_item.text.value
                        else:
                            response_text += str(content_item.text)
                
                if response_text.strip():
                    self.captured_response = response_text
                    if not self.current_response_text.strip() or len(response_text) > len(self.current_response_text):
                        self.current_response_text = response_text
                    # Captured assistant message
            
            await self.util.get_files(message, self.project_client)
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_thread_message: {e}")

    async def on_thread_run(self, run: ThreadRun) -> None:
        """Handle thread run events"""
        try:
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
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_thread_run: {e}")

    async def on_run_step(self, step: RunStep) -> None:
        try:
            # if step.status == RunStepStatus.COMPLETED:
            #     print()
            # self.util.log_msg_purple(f"RunStep type: {step.type}, Status: {step.status}")
            pass
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_run_step: {e}")

    async def on_run_step_delta(self, delta: RunStepDeltaChunk) -> None:
        try:
            pass
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_run_step_delta: {e}")

    async def on_tool_call_created(self, tool_call) -> None:
        """Handle tool call creation."""
        try:
            # Tool call created
            pass
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_tool_call_created: {e}")

    async def on_tool_call_delta(self, delta, snapshot) -> None:
        """Handle tool call delta events."""
        try:
            if delta.type == "function":
                # Function delta event - silently handle
                pass
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_tool_call_delta: {e}")

    async def on_tool_call_done(self, tool_call) -> None:
        """Handle tool call completion - just log for now, main handler will process."""
        try:
            if tool_call.type == "function":
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                
                # Tool call completed - main handler will process
                
                # Note: Tool execution and output submission will be handled by the main agent_core
                # when it detects the REQUIRES_ACTION status
                    
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_tool_call_done: {e}")

    async def on_error(self, data: str) -> None:
        try:
            print(f"An error occurred. Data: {data}")
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_error: {e}")

    async def on_done(self) -> None:
        """Handle stream completion."""
        try:
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
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_done: {e}")

    async def on_unhandled_event(self, event_type: str, event_data: Any) -> None:
        """Handle unhandled events."""
        try:
            # print(f"Unhandled Event Type: {event_type}, Data: {event_data}")
            print(f"Unhandled Event Type: {event_type}")
        except Exception as e:
            print(f"[StreamEventHandler] Exception in on_unhandled_event: {e}")
