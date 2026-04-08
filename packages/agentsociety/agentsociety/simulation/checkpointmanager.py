"""Checkpoint and resume state management for SimulationEngine."""

import json
from pathlib import Path
from typing import Any, Optional

from ..agent import CitizenAgentBase
from ..database.database_actor import DatabaseActor
from ..environment import EnvironmentStarter
from ..llm import LLM
from ..logger import get_logger
from ..message import Message, Messager
from ..storage.type import StorageExpInfo
from .agentmanager import AgentManager
from .datarecorder import DataRecorder

__all__ = ["CheckpointManager"]


class CheckpointManager:
    """Handle checkpoint save and resume restoration flows."""

    def __init__(
        self,
        exp_id: str,
        home_dir: str,
        start_tick: int,
    ) -> None:
        self._exp_id = exp_id
        self._home_dir = home_dir
        self._start_tick = start_tick
        self._last_mobility_safe_step = -1

    def _build_economy_checkpoint_candidates(self, raw_path: str, resume_step: int) -> list[str]:
        """Build candidate filesystem paths for economy checkpoint restore."""
        cleaned = str(raw_path or "").strip()
        if not cleaned:
            return []

        candidates: list[Path] = []

        raw = Path(cleaned).expanduser()
        candidates.append(raw)

        home_dir = Path(self._home_dir).expanduser()
        if raw.is_absolute():
            candidates.append(raw.resolve(strict=False))
        else:
            cwd = Path.cwd()
            candidates.append((cwd / raw).resolve(strict=False))
            candidates.append((home_dir / raw).resolve(strict=False))

        # Handle historical/relative forms like "data/data/checkpoints/...".
        parts = list(raw.parts)
        if len(parts) >= 2 and parts[0] == parts[1]:
            de_duplicated = Path(*parts[1:])
            candidates.append(de_duplicated)
            if not de_duplicated.is_absolute():
                candidates.append((Path.cwd() / de_duplicated).resolve(strict=False))
                candidates.append((home_dir / de_duplicated).resolve(strict=False))

        # Prefer the canonical expected location for this experiment/step.
        if resume_step >= 0:
            expected = (
                (home_dir / "checkpoints" / self._exp_id / f"econ_step_{resume_step}.bin")
                .expanduser()
                .resolve(strict=False)
            )
            candidates.append(expected)

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped

    def restore_runtime_state(
        self,
        resume_state: Optional[dict[str, Any]],
        exp_info: StorageExpInfo,
        llm: Optional[LLM],
        environment: Optional[EnvironmentStarter],
    ) -> int:
        """Restore runtime counters and simulator tick from loaded resume state."""
        if resume_state is None:
            return 0

        last_safe = int(resume_state.get("last_mobility_safe_step", -1) or -1)
        total_steps = max(1, last_safe + 1)

        latest_exp_info = resume_state.get("latest_experiment_info")
        if not isinstance(latest_exp_info, dict):
            return total_steps

        exp_info.num_day = int(latest_exp_info.get("num_day", exp_info.num_day))
        exp_info.cur_day = int(latest_exp_info.get("cur_day", exp_info.cur_day))
        exp_info.cur_t = float(latest_exp_info.get("cur_t", exp_info.cur_t))
        exp_info.input_tokens = int(latest_exp_info.get("input_tokens", exp_info.input_tokens))
        exp_info.output_tokens = int(latest_exp_info.get("output_tokens", exp_info.output_tokens))

        if llm is not None:
            llm.prompt_tokens_used = exp_info.input_tokens
            llm.completion_tokens_used = exp_info.output_tokens

        if environment is not None:
            resume_tick = int(exp_info.cur_day * 24 * 60 * 60 + exp_info.cur_t - self._start_tick)
            environment.set_tick(max(resume_tick, 0))

        self._last_mobility_safe_step = int(resume_state.get("last_mobility_safe_step", -1) or -1)

        get_logger().info(
            "Restored resume runtime state: "
            f"step={total_steps}, day={exp_info.cur_day}, "
            f"t={exp_info.cur_t}, input_tokens={exp_info.input_tokens}, "
            f"output_tokens={exp_info.output_tokens}"
        )
        return total_steps

    async def restore_external_simulator_state(
        self,
        resume_state: Optional[dict[str, Any]],
        environment: Optional[EnvironmentStarter],
        agent_manager: Optional[AgentManager],
    ) -> None:
        """Restore economy and mobility simulator state from checkpoint on resume."""
        if resume_state is None or environment is None or agent_manager is None:
            return

        resume_step = int(resume_state.get("last_mobility_safe_step", -1))
        latest_step = int(resume_state.get("latest_step", -1) or -1)

        economy_checkpoint_path = resume_state.get("economy_checkpoint_path", "")
        if economy_checkpoint_path:
            candidate_paths = self._build_economy_checkpoint_candidates(
                str(economy_checkpoint_path),
                resume_step,
            )
            restore_errors: list[str] = []
            restored_from: Optional[str] = None

            for candidate_path in candidate_paths:
                try:
                    await environment.economy_client.load(candidate_path)
                    restored_from = candidate_path
                    break
                except Exception as e:
                    restore_errors.append(f"{candidate_path}: {e}")

            if restored_from is None:
                raise RuntimeError(
                    "Failed to restore economy state from any candidate path. "
                    f"Stored path='{economy_checkpoint_path}', "
                    f"attempted={candidate_paths}, errors={restore_errors}. "
                    "Cannot continue resume safely - economy state is unavailable."
                )

            if restored_from != str(economy_checkpoint_path):
                get_logger().warning(
                    "Economy checkpoint restored using normalized path "
                    f"'{restored_from}' (stored='{economy_checkpoint_path}')"
                )
            else:
                get_logger().info(f"Economy state restored from {restored_from}")
        else:
            if latest_step > 0:
                raise RuntimeError(
                    f"Resume at step {latest_step} has no economy checkpoint path. "
                    "The economy simulator cannot be restored. "
                    "This indicates a checkpoint write failure or incomplete flush. "
                    "Cannot continue resume safely - the economy state would be corrupted."
                )
            get_logger().info(
                "No economy checkpoint (latest_step == 0, no checkpoint was ever written); "
                "economy starts fresh. Expected for experiments that crashed before their first safe step."
            )

        if resume_step < 0:
            if latest_step > 0:
                raise RuntimeError(
                    f"Resume at step {latest_step} has no mobility checkpoint step recorded. "
                    "Cannot restore mobility state safely."
                )
            get_logger().info("No mobility checkpoint step found; skipping mobility position reset")
            return

        def _parse_kv_value(
            kv_entries: list[dict[str, Any]], key: str
        ) -> Optional[dict[str, Any]]:
            raw = next((e.get("value_json") for e in kv_entries if e.get("key") == key), None)
            if raw is None:
                return None
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, TypeError):
                return None

        def _parse_kv_int(kv_entries: list[dict[str, Any]], key: str) -> Optional[int]:
            raw = next((e.get("value_json") for e in kv_entries if e.get("key") == key), None)
            if raw is None:
                return None
            try:
                value = json.loads(raw)
                return int(value)
            except (json.JSONDecodeError, TypeError, ValueError):
                return None

        def _extract_target_aoi_from_plan_step(step: dict[str, Any]) -> Optional[int]:
            if not isinstance(step, dict):
                return None
            evaluation = step.get("evaluation", {})
            if isinstance(evaluation, dict):
                to_place = evaluation.get("to_place")
                if to_place is not None:
                    try:
                        return int(to_place)
                    except (TypeError, ValueError):
                        pass
            to_place = step.get("to_place")
            if to_place is not None:
                try:
                    return int(to_place)
                except (TypeError, ValueError):
                    pass
            poi_id = step.get("poi_id")
            if poi_id is not None:
                try:
                    return int(poi_id)
                except (TypeError, ValueError):
                    pass
            if isinstance(evaluation, dict):
                poi_id = evaluation.get("poi_id")
                if poi_id is not None:
                    try:
                        return int(poi_id)
                    except (TypeError, ValueError):
                        pass
            return None

        def _extract_reset_position(
            position: dict[str, Any], current_plan: Optional[dict[str, Any]]
        ) -> Optional[tuple[str, int, Optional[float]]]:
            aoi_pos = position.get("aoi_position")
            if isinstance(aoi_pos, dict):
                aoi_id = aoi_pos.get("aoi_id")
                if aoi_id is not None:
                    try:
                        return ("aoi", int(aoi_id), None)
                    except (TypeError, ValueError):
                        pass

            lane_pos = position.get("lane_position")
            if isinstance(lane_pos, dict):
                lane_id = lane_pos.get("lane_id")
                if lane_id is not None:
                    try:
                        lane_id_int = int(lane_id)
                        s_raw = lane_pos.get("s", 0.0)
                        try:
                            s = float(s_raw)
                        except (TypeError, ValueError):
                            s = 0.0
                        return ("lane", lane_id_int, s)
                    except (TypeError, ValueError):
                        pass

            if not isinstance(current_plan, dict):
                return None
            steps = current_plan.get("steps", [])
            step_index = current_plan.get("index", 0)
            if not isinstance(steps, list):
                return None
            try:
                idx = int(step_index)
            except (TypeError, ValueError):
                idx = 0

            for i in range(min(idx, len(steps) - 1), -1, -1):
                step = steps[i]
                if not isinstance(step, dict):
                    continue
                step_position = step.get("position")
                if step_position is not None:
                    try:
                        return ("aoi", int(step_position), None)
                    except (TypeError, ValueError):
                        pass
                target_aoi = _extract_target_aoi_from_plan_step(step)
                if target_aoi is not None:
                    return ("aoi", target_aoi, None)
            return None

        kv_snapshots = resume_state.get("kv_snapshots", {})
        citizen_ids = {
            aid
            for aid, agent in agent_manager.agents.items()
            if isinstance(agent, CitizenAgentBase)
        }

        reset_count = 0
        failed_position_resets = 0
        reconstructed_count = 0
        failed_reconstructions = 0
        total_in_motion = 0
        successfully_reset: set[int] = set()

        for agent_id, kv_entries in kv_snapshots.items():
            try:
                agent_id_int = int(agent_id)
            except (TypeError, ValueError):
                continue
            if agent_id_int not in citizen_ids:
                continue

            if not isinstance(kv_entries, list):
                continue

            position = _parse_kv_value(kv_entries, "position")
            if not isinstance(position, dict):
                continue

            current_plan = _parse_kv_value(kv_entries, "current_plan")
            reset_target = _extract_reset_position(position, current_plan)
            if reset_target is None:
                raise RuntimeError(
                    f"Agent {agent_id_int}: could not extract reset position (aoi/lane) from position/current_plan. "
                    "Cannot continue resume safely because mobility position restoration is incomplete."
                    f"Plan snapshot: {current_plan}, position snapshot: {position}"
                )

            reset_kind, reset_id, reset_s = reset_target

            try:
                if reset_kind == "aoi":
                    await environment.reset_person_position(
                        agent_id_int, aoi_id=int(reset_id)
                    )
                elif reset_kind == "lane":
                    await environment.reset_person_position(
                        agent_id_int, lane_id=int(reset_id), s=reset_s
                    )
                else:
                    raise RuntimeError(
                        f"Agent {agent_id_int}: unknown reset target kind '{reset_kind}'"
                    )
                reset_count += 1
                successfully_reset.add(agent_id_int)
            except Exception as e:
                get_logger().warning(f"Failed to reset position for agent {agent_id_int}: {e}")
                failed_position_resets += 1

        if failed_position_resets > 0:
            raise RuntimeError(
                f"Mobility Phase A failed: {failed_position_resets} agent(s) could not be reset. "
                "Resume cannot continue safely."
            )

        for agent_id, kv_entries in kv_snapshots.items():
            try:
                agent_id_int = int(agent_id)
            except (TypeError, ValueError):
                continue
            if agent_id_int not in citizen_ids:
                continue

            if not isinstance(kv_entries, list):
                continue

            status = _parse_kv_int(kv_entries, "status")
            if status is None or status in {0, 1}:
                continue

            total_in_motion += 1

            if agent_id_int not in successfully_reset:
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: in-motion status={status} but position was not reset in Phase A; "
                    "cannot reconstruct trip safely. Resume cannot continue."
                )

            current_plan = _parse_kv_value(kv_entries, "current_plan")
            if not isinstance(current_plan, dict):
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: in-motion status={status} but missing current_plan; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                )

            if current_plan.get("completed") or current_plan.get("failed"):
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: in-motion status={status} but current_plan is completed/failed; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                )

            steps = current_plan.get("steps", [])
            step_index = current_plan.get("index", 0)
            if not isinstance(steps, list) or not steps:
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: in-motion status={status} but current_plan has no steps; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                )

            try:
                idx = int(step_index)
            except (TypeError, ValueError) as err:
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: invalid current_plan index={step_index}; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                ) from err

            if idx < 0 or idx >= len(steps):
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: current_plan index {idx} out of range for {len(steps)} steps; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                )

            current_step = steps[idx]
            if not isinstance(current_step, dict):
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: current_plan step at index {idx} is invalid; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                )

            target_aoi_id = _extract_target_aoi_from_plan_step(current_step)
            if target_aoi_id is None:
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: missing target AOI in current plan step {idx}; "
                    "cannot reconstruct trip. Resume cannot continue safely."
                )

            try:
                await environment.set_aoi_schedules(
                    agent_id_int,
                    [int(target_aoi_id)],
                )
                reconstructed_count += 1
                get_logger().debug(
                    f"Agent {agent_id_int}: trip re-submitted to AOI {target_aoi_id}"
                )
            except Exception as e:
                failed_reconstructions += 1
                raise RuntimeError(
                    f"Agent {agent_id_int}: failed to re-submit trip to AOI {target_aoi_id}: {e}. "
                    "Resume cannot continue safely."
                ) from e

        if failed_position_resets > 0 or failed_reconstructions > 0:
            raise RuntimeError(
                "Mobility restoration failed. "
                f"position_reset_failures={failed_position_resets}, "
                f"trip_reconstruction_failures={failed_reconstructions}. "
                "Resume cannot continue safely."
            )

        get_logger().info(
            "Mobility restoration summary at step "
            f"{resume_step}: reset={reset_count}, reset_failed={failed_position_resets}, "
            f"in_motion={total_in_motion}, reconstructed={reconstructed_count}, "
            f"reconstruction_failed={failed_reconstructions}"
        )

    async def restore_messager_state(
        self,
        resume_state: Optional[dict[str, Any]],
        messager: Optional[Messager],
    ) -> None:
        """Rehydrate Messager with pending messages from checkpoint state."""
        if resume_state is None or messager is None:
            return

        pending = resume_state.get("pending_messages", [])
        if not pending:
            return

        seeded = 0
        for row in pending:
            try:
                payload = json.loads(row.get("payload_json", "{}"))
                extra_raw = row.get("extra_json")
                extra = json.loads(extra_raw) if extra_raw else None
                msg = Message(
                    from_id=row.get("from_id"),
                    to_id=row.get("to_id"),
                    day=int(row.get("day", 0)),
                    t=float(row.get("t", 0.0)),
                    kind=row.get("kind", "social"),
                    payload=payload,
                    created_at=row.get("created_at"),
                    extra=extra,
                )
                await messager.send_message(msg)
                seeded += 1
            except Exception as e:
                get_logger().warning(f"Failed to restore pending message: {e}")

        get_logger().info(f"Seeded {seeded} pending messages from checkpoint into Messager")

    async def save_checkpoint(
        self,
        day: int,
        t: int,
        total_steps: int,
        agent_manager: Optional[AgentManager],
        messager: Optional[Messager],
        data_recorder: Optional[DataRecorder],
        db_actor: Optional[DatabaseActor],
        environment: Optional[EnvironmentStarter],
    ) -> None:
        """Snapshot agent memory and pending messages into ClickHouse for resume support."""
        if (
            db_actor is None
            or data_recorder is None
            or agent_manager is None
            or messager is None
            or environment is None
        ):
            return

        step = total_steps

        kv_records: list[dict] = []
        stream_records: list[dict] = []
        spatial_records: list[dict] = []
        all_at_aoi = True

        for agent in agent_manager.agents.values():
            agent_id = agent.id

            snapshot_records = await agent.memory.create_snapshot_records(
                exp_id=self._exp_id,
                simulation_step=step,
                agent_id=agent_id,
                day=day,
                t=t,
            )
            kv_records.extend(snapshot_records.get("kv", []))
            stream_records.extend(snapshot_records.get("stream", []))
            spatial_records.extend(snapshot_records.get("spatial", []))
            kv_data = snapshot_records.get("status", {})

            if isinstance(agent, CitizenAgentBase) and all_at_aoi:
                position = kv_data.get("position", {})
                if position and "lane_position" in position:
                    all_at_aoi = False

        msg_records: list[dict] = []
        for msg in messager._pending_messages:
            try:
                payload_json = json.dumps(msg.payload, ensure_ascii=False)
                extra_json = json.dumps(msg.extra, ensure_ascii=False) if msg.extra is not None else None
            except (TypeError, ValueError):
                payload_json = json.dumps(str(msg.payload))
                extra_json = None
            msg_records.append(
                {
                    "exp_id": self._exp_id,
                    "simulation_step": step,
                    "from_id": msg.from_id,
                    "to_id": msg.to_id,
                    "day": msg.day,
                    "t": msg.t,
                    "kind": msg.kind.value if hasattr(msg.kind, "value") else str(msg.kind),
                    "payload_json": payload_json,
                    "created_at": msg.created_at,
                    "extra_json": extra_json,
                }
            )

        if kv_records:
            await data_recorder.enqueue_kv_snapshot(kv_records)
        if stream_records:
            await data_recorder.enqueue_stream_snapshot(stream_records)
        if spatial_records:
            await data_recorder.enqueue_spatial_snapshot(spatial_records)
        if msg_records:
            await data_recorder.enqueue_message_snapshot(msg_records)

        if agent_manager.agents:
            checkpoint_dir = Path(self._home_dir).expanduser().resolve(strict=False) / "checkpoints" / self._exp_id
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            econ_path = str((checkpoint_dir / f"econ_step_{step}.bin").resolve(strict=False))
            try:
                await environment.economy_client.save(econ_path)
                prev_checkpoint = self._last_mobility_safe_step
                self._last_mobility_safe_step = step
                await db_actor.update_experiment_info_checkpoint.remote(
                    exp_id=self._exp_id,
                    last_mobility_safe_step=step,
                    prev_mobility_safe_step=prev_checkpoint,
                    economy_checkpoint_path=econ_path,
                )
                get_logger().debug(
                    f"Checkpoint step {step}: economy checkpoint saved to {econ_path} (all_at_aoi={all_at_aoi})"
                )
            except Exception as e:
                get_logger().warning(f"Economy checkpoint failed at step {step}: {e}")
