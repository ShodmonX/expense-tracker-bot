from __future__ import annotations

import asyncio
import os
import re
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.engine.url import make_url

from config import config
from database import async_engine


@dataclass(slots=True)
class BackupMeta:
    filename: str
    kind: str
    size_bytes: int
    created_at: datetime


@dataclass(slots=True)
class RestoreResult:
    restored_from: BackupMeta
    safety_backup: BackupMeta


@dataclass(slots=True)
class PostgresParams:
    host: str
    port: int
    user: str
    password: str
    database: str


class DBBackupEngine:
    VALID_KINDS = ("auto", "manual", "pre_restore")
    TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S-%f"

    def __init__(self) -> None:
        backup_dir = Path(config.BACKUP_DIR).expanduser()
        if not backup_dir.is_absolute():
            backup_dir = (Path.cwd() / backup_dir).resolve()

        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

        self._prefix_by_kind = {
            "auto": config.AUTO_BACKUP_PREFIX,
            "manual": config.MANUAL_BACKUP_PREFIX,
            "pre_restore": config.PRE_RESTORE_BACKUP_PREFIX,
        }
        self._pattern_by_kind = {
            kind: re.compile(
                rf"^{re.escape(prefix)}(?P<stamp>\d{{4}}-\d{{2}}-\d{{2}}_\d{{2}}-\d{{2}}(?:-\d{{2}}(?:-\d{{6}})?)?)\.dump$"
            )
            for kind, prefix in self._prefix_by_kind.items()
        }

    def _validate_kind(self, kind: str) -> None:
        if kind not in self.VALID_KINDS:
            raise ValueError(f"Noto'g'ri backup turi: {kind}")

    def _postgres_params(self) -> PostgresParams:
        db_url = make_url(config.DATABASE_URL)
        if db_url.get_backend_name() != "postgresql":
            raise RuntimeError("DB backup faqat PostgreSQL bilan qo'llaniladi")

        database = db_url.database
        if not database:
            raise RuntimeError("DATABASE_URL ichida database nomi topilmadi")

        return PostgresParams(
            host=db_url.host or "db",
            port=int(db_url.port or 5432),
            user=db_url.username or "postgres",
            password=db_url.password or "",
            database=database,
        )

    def _build_filename(self, kind: str) -> str:
        self._validate_kind(kind)
        stamp = datetime.now(timezone.utc).strftime(self.TIMESTAMP_FORMAT)
        return f"{self._prefix_by_kind[kind]}{stamp}.dump"

    def _parse_filename(self, filename: str) -> tuple[str, datetime] | None:
        for kind, pattern in self._pattern_by_kind.items():
            match = pattern.match(filename)
            if not match:
                continue

            stamp_value = match.group("stamp")
            parsed_stamp: datetime | None = None
            for fmt in (
                "%Y-%m-%d_%H-%M-%S-%f",
                "%Y-%m-%d_%H-%M-%S",
                "%Y-%m-%d_%H-%M",
            ):
                try:
                    parsed_stamp = datetime.strptime(stamp_value, fmt)
                    break
                except ValueError:
                    continue

            if parsed_stamp is None:
                continue

            stamp = parsed_stamp.replace(tzinfo=timezone.utc)
            return kind, stamp

        return None

    def _resolve_backup_path(self, filename: str) -> Path:
        if Path(filename).name != filename:
            raise ValueError("Backup filename noto'g'ri")

        parsed = self._parse_filename(filename)
        if parsed is None:
            raise ValueError("Backup filename noto'g'ri")

        return self.backup_dir / filename

    def _pg_env(self, password: str) -> dict[str, str]:
        env = dict(os.environ)
        if password:
            env["PGPASSWORD"] = password
        else:
            env.pop("PGPASSWORD", None)
        return env

    async def _run_command(
        self,
        cmd: list[str],
        timeout: int,
        env: dict[str, str],
    ) -> tuple[int | None, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        try:
            out_raw, err_raw = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError as exc:
            proc.kill()
            await proc.communicate()
            raise RuntimeError(f"Command timeout ({timeout}s): {' '.join(cmd)}") from exc

        stdout = out_raw.decode("utf-8", errors="replace").strip()
        stderr = err_raw.decode("utf-8", errors="replace").strip()
        return proc.returncode, stdout, stderr

    def _is_ignorable_restore_error(self, stderr: str) -> bool:
        text = stderr.lower()
        return (
            "transaction_timeout" in text
            and "unrecognized configuration parameter" in text
        )

    def _build_meta(self, path: Path, kind: str) -> BackupMeta:
        stat = path.stat()
        return BackupMeta(
            filename=path.name,
            kind=kind,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )

    @asynccontextmanager
    async def _operation_lock(self):
        try:
            await asyncio.wait_for(
                self._lock.acquire(), timeout=config.BACKUP_LOCK_TIMEOUT_SECONDS
            )
        except TimeoutError as exc:
            raise RuntimeError("Backup lock timeout") from exc

        try:
            yield
        finally:
            self._lock.release()

    async def _create_backup_unlocked(
        self,
        kind: str,
        params: PostgresParams,
    ) -> BackupMeta:
        self._validate_kind(kind)
        filename = self._build_filename(kind)

        target_path = self.backup_dir / filename
        temp_path = self.backup_dir / f"{filename}.tmp"
        if temp_path.exists():
            temp_path.unlink()

        cmd = [
            "pg_dump",
            "-Fc",
            "-f",
            str(temp_path),
            "-h",
            params.host,
            "-U",
            params.user,
            "-p",
            str(params.port),
            "-d",
            params.database,
        ]
        rc, _, stderr = await self._run_command(
            cmd,
            timeout=120,
            env=self._pg_env(params.password),
        )
        if rc != 0:
            try:
                temp_path.unlink(missing_ok=True)
            except TypeError:
                if temp_path.exists():
                    temp_path.unlink()
            detail = stderr or "pg_dump xato bilan tugadi"
            raise RuntimeError(f"Backup yaratilmadi: {detail}")

        temp_path.replace(target_path)
        return self._build_meta(target_path, kind)

    async def create_backup(self, kind: str = "manual") -> BackupMeta:
        async with self._operation_lock():
            params = self._postgres_params()
            return await self._create_backup_unlocked(kind, params)

    async def list_backups(self, kind: str | None = None) -> list[BackupMeta]:
        if kind is not None:
            self._validate_kind(kind)

        items: list[tuple[datetime, BackupMeta]] = []
        for file_path in self.backup_dir.glob("*.dump"):
            parsed = self._parse_filename(file_path.name)
            if parsed is None:
                continue

            item_kind, stamp = parsed
            if kind and item_kind != kind:
                continue

            items.append((stamp, self._build_meta(file_path, item_kind)))

        items.sort(key=lambda pair: pair[0], reverse=True)
        return [meta for _, meta in items]

    async def delete_backup(self, filename: str) -> bool:
        async with self._operation_lock():
            backup_path = self._resolve_backup_path(filename)
            if not backup_path.exists():
                return False

            backup_path.unlink()
            return True

    async def restore_backup(self, filename: str) -> RestoreResult:
        async with self._operation_lock():
            backup_path = self._resolve_backup_path(filename)
            if not backup_path.exists():
                raise FileNotFoundError("Backup fayli topilmadi")

            parsed = self._parse_filename(filename)
            if parsed is None:
                raise ValueError("Backup filename noto'g'ri")

            params = self._postgres_params()
            pg_env = self._pg_env(params.password)

            safety_backup = await self._create_backup_unlocked("pre_restore", params)
            restored_from = self._build_meta(backup_path, parsed[0])

            await async_engine.dispose()

            reset_cmd = [
                "psql",
                "-h",
                params.host,
                "-U",
                params.user,
                "-p",
                str(params.port),
                "-d",
                params.database,
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                "DROP SCHEMA public CASCADE; CREATE SCHEMA public;",
            ]
            rc, _, stderr = await self._run_command(reset_cmd, timeout=45, env=pg_env)
            if rc != 0:
                raise RuntimeError(f"Schema reset xatosi: {stderr or 'psql xato'}")

            restore_cmd = [
                "pg_restore",
                "-Fc",
                "--no-owner",
                "--no-privileges",
                "-h",
                params.host,
                "-U",
                params.user,
                "-p",
                str(params.port),
                "-d",
                params.database,
                str(backup_path),
            ]
            rc, _, stderr = await self._run_command(restore_cmd, timeout=240, env=pg_env)
            if rc != 0 and not self._is_ignorable_restore_error(stderr):
                raise RuntimeError(f"Restore xatosi: {stderr or 'pg_restore xato'}")

            health_cmd = [
                "psql",
                "-h",
                params.host,
                "-U",
                params.user,
                "-p",
                str(params.port),
                "-d",
                params.database,
                "-tAc",
                "SELECT 1;",
            ]
            rc, stdout, stderr = await self._run_command(health_cmd, timeout=20, env=pg_env)
            if rc != 0 or stdout.strip() != "1":
                raise RuntimeError(f"Restore healthcheck xatosi: {stderr or stdout or 'unknown'}")

            await async_engine.dispose()
            return RestoreResult(restored_from=restored_from, safety_backup=safety_backup)

    async def cleanup_auto_backups(self, retention_count: int | None = None) -> int:
        keep_count = (
            config.AUTO_BACKUP_RETENTION_COUNT
            if retention_count is None
            else retention_count
        )
        if keep_count <= 0:
            return 0

        removed = 0
        async with self._operation_lock():
            auto_backups: list[tuple[datetime, Path]] = []
            for file_path in self.backup_dir.glob("*.dump"):
                parsed = self._parse_filename(file_path.name)
                if parsed is None:
                    continue

                kind, stamp = parsed
                if kind != "auto":
                    continue
                auto_backups.append((stamp, file_path))

            auto_backups.sort(key=lambda item: item[0], reverse=True)
            for _, old_path in auto_backups[keep_count:]:
                try:
                    old_path.unlink()
                    removed += 1
                except FileNotFoundError:
                    continue

        return removed


backup_engine = DBBackupEngine()
