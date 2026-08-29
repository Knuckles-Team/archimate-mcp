#!/usr/bin/env python3
import asyncio
import json
import os
import uuid

import httpx

A2A_URL = os.environ.get("A2A_URL", "http://127.0.0.1:9016/a2a/")

_TASK_IN_PROGRESS_STATES = ("submitted", "running", "working")


def _build_message_payload(query: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
                "messageId": str(uuid.uuid4()),
            }
        },
        "id": 1,
    }


def _build_poll_payload(task_id) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "tasks/get",
        "params": {"id": task_id},
        "id": 2,
    }


def _find_last_agent_message(history: list) -> dict | None:
    for msg in reversed(history):
        if msg.get("role") != "user":
            return msg
    return None


def _print_agent_response(last_msg: dict) -> None:
    if "parts" not in last_msg:
        print("Final response received without structured parts.")
        return
    print("\n--- Agent Response ---")
    for part in last_msg["parts"]:
        if "text" in part or "content" in part:
            print("Agent response content omitted.")


def _report_task_history(task_result: dict) -> None:
    history = task_result.get("history")
    if not history:
        return
    last_msg = _find_last_agent_message(history)
    if last_msg is None:
        print("\n--- No Agent Response Found in History ---")
        return
    _print_agent_response(last_msg)


def _handle_poll_result(poll_data: dict) -> bool:
    """Report on one poll response; return True once polling should stop."""
    if "result" not in poll_data:
        print("Starting polling error key check...")
        if "error" in poll_data:
            print(f"Polling JSON-RPC error code: {poll_data['error'].get('code', 'unknown')}")
        return True

    task_result = poll_data["result"]
    state = task_result["status"]["state"]
    print(f"Task State: {state}")
    if state in _TASK_IN_PROGRESS_STATES:
        return False

    print(f"\nTask Finished with state: {state}")
    if "history" in task_result:
        _report_task_history(task_result)
    print("Validation result received; body omitted.")
    return True


async def _poll_task(client: httpx.AsyncClient, url: str, task_id) -> None:
    print("\nTask submitted; polling for result...")
    while True:
        await asyncio.sleep(2)
        poll_resp = await client.post(
            url,
            json=_build_poll_payload(task_id),
            headers={"Content-Type": "application/json"},
        )
        if poll_resp.status_code != 200:
            print(f"Polling Failed: {poll_resp.status_code}")
            print(f"Polling failed with HTTP {poll_resp.status_code}.")
            return
        if _handle_poll_result(poll_resp.json()):
            return


async def _handle_message_response(client: httpx.AsyncClient, url: str, data: dict) -> None:
    print("JSON response received.")
    if "result" in data and "id" in data["result"]:
        await _poll_task(client, url, data["result"]["id"])
    if "error" in data:
        print(f"JSON-RPC error code: {data['error'].get('code', 'unknown')}")


async def _submit_query(client: httpx.AsyncClient, url: str, query: str) -> None:
    print("\nSubmitting the configured validation query.")
    print("--- Sending Request ---")
    try:
        print("Trying the configured endpoint with JSON-RPC (message/send)...")
        resp = await client.post(
            url,
            json=_build_message_payload(query),
            headers={"Content-Type": "application/json"},
        )
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error: {resp.status_code}")
            print(f"Response body omitted (HTTP {resp.status_code}).")
            return

        try:
            data = resp.json()
        except json.JSONDecodeError:
            print(f"Response body omitted (HTTP {resp.status_code}).")
            return

        await _handle_message_response(client, url, data)
    except httpx.RequestError as e:
        print(f"Operation failed: {type(e).__name__}")


async def main():
    print("Validating the configured A2A agent...")

    questions = [
        os.environ.get("A2A_VALIDATION_QUERY", "Describe your available capabilities.")
    ]

    async with httpx.AsyncClient(timeout=10000.0) as client:
        for q in questions:
            await _submit_query(client, A2A_URL, q)


if __name__ == "__main__":
    asyncio.run(main())
