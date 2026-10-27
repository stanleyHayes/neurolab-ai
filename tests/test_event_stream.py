"""Streaming authorization must survive reconnects and idle polling."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from neurolab import api


class ConnectedRequest:
    async def is_disconnected(self):
        return False


class EventStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_revoked_session_stops_idle_stream_before_next_poll(self):
        user = {"user_id": "owner", "session_id": "session"}
        with (
            patch.object(api.STORE, "get_run", return_value={"status": "RUNNING"}),
            patch.object(
                api.STORE, "get_active_auth_session", side_effect=[{"session_id": "session"}, None]
            ) as session,
            patch.object(api.STORE, "list_events", return_value=[]) as events,
        ):
            frames = [
                frame async for frame in api._stream_run_events("run", ConnectedRequest(), user, 0)
            ]
        self.assertEqual(frames, [": keep-alive\n\n"])
        self.assertEqual(session.call_count, 2)
        self.assertEqual(events.call_count, 1)

    async def test_owner_removal_stops_stream_at_next_poll_boundary(self):
        user = {"user_id": "owner", "session_id": "session"}
        with (
            patch.object(
                api.STORE,
                "get_run",
                side_effect=[{"status": "RUNNING"}, {"status": "RUNNING"}, None],
            ) as owned_run,
            patch.object(
                api.STORE, "get_active_auth_session", return_value={"session_id": "session"}
            ),
            patch.object(api.STORE, "list_events", return_value=[]) as events,
        ):
            frames = [
                frame async for frame in api._stream_run_events("run", ConnectedRequest(), user, 0)
            ]
        self.assertEqual(frames, [": keep-alive\n\n"])
        self.assertEqual(owned_run.call_count, 3)
        self.assertEqual(events.call_count, 1)
        for call in owned_run.call_args_list:
            self.assertEqual(call.kwargs["owner_user_id"], "owner")
