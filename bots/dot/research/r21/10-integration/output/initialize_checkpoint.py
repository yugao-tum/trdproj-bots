"""Offline root-owned initializer. No network, orders, credentials or clock override.
Consumes an already locked and reserved checkpoint and a newly saved role03 interface.
All cooperating writers MUST use checkpoint-path + '.lock'.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
from decimal import Decimal, InvalidOperation


def digest(raw): return hashlib.sha256(raw).hexdigest()
def load(base, relative, name):
    spec = importlib.util.spec_from_file_location(name, base / relative)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def atomic_write(path, state):
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(state, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def initialize(base, checkpoint_path, interface_path, manifest_path, request_id):
    base, checkpoint_path, interface_path, manifest_path = map(Path, (base, checkpoint_path, interface_path, manifest_path))
    with open(str(checkpoint_path) + '.lock', 'a') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        original = checkpoint_path.read_bytes(); state = json.loads(original)
        manifest_bytes = manifest_path.read_bytes(); manifest = json.loads(manifest_bytes)
        if manifest.get('schema') != 'r21.forward-artifact-manifest.v1': raise ValueError('Invalid manifest schema')
        if digest(manifest_bytes) != state['root_lock'].get('artifact_manifest_sha256'): raise ValueError('Manifest not root-bound')
        artifacts = {}
        for rel, expected in manifest['sha256'].items():
            if Path(rel).is_absolute() or '..' in Path(rel).parts: raise ValueError('Unsafe artifact path')
            raw = (base / rel).read_bytes()
            if digest(raw) != expected: raise ValueError('Changed artifact: ' + rel)
            artifacts[rel] = raw
        own = str(Path(__file__).resolve().relative_to(base.resolve()))
        if own not in artifacts: raise ValueError('Initializer is not frozen')
        S = load(base, '06-scheduler/output/scheduler.py', 'frozen_scheduler')
        L = load(base, '04-protocol/output/virtual_ledger.py', 'frozen_ledger')
        Q = load(base, '05-quotes/output/quote_audit.py', 'frozen_quote_audit')
        now = time.time_ns() // 1_000_000
        S.verified_due_work(state, now, manifest_bytes, artifacts)
        if state['entry'] is not None: raise ValueError('Existing entry cannot be replaced')
        pending = state['source_status']['quote_pair']['inflight']
        if not pending or pending['request_id'] != request_id: raise ValueError('Missing matching persisted reservation')
        if state['stop_requested'] or state['source_status']['quote_pair']['halted']: raise ValueError('Stopped or halted')
        raw = interface_path.read_bytes()
        reference = {'path': str(interface_path), 'sha256': digest(raw)}
        try:
            n = L.normalize_public_interface(json.loads(raw))
            now = time.time_ns() // 1_000_000  # Live clock, never passed by caller or backdated.
            Q.check_pair(n['spot'], n['perp'], now, state['root_lock']['locked_at_ms'])
            ledger = L.initialize_virtual(n['spot'], n['perp'], n['spot_filter'], n['perp_filter'], state['root_lock'], now)
            q = Q.budget_quantity(n['spot'], '1250', '0.003', Q.common_step(n['spot_filter']['qty_step'], n['perp_filter']['qty_step']))
            if q != Decimal(ledger['entry']['quantity']): raise ValueError('Independent quantity mismatch')
            for book, side, entry_key in [('spot', 'asks', 'spot_vwap'), ('perp', 'bids', 'perp_vwap')]:
                audit = Q.vwap(n[book], side, q)
                if audit['notional'] / q != Decimal(ledger['entry'][entry_key]): raise ValueError('Independent VWAP mismatch')
            complete = S.complete_request(state, 'quote_pair', request_id, 'ok', time.time_ns() // 1_000_000, response_ref=reference)
            proposed = S.attach_ledger(complete, ledger)
            S.verified_due_work(proposed, time.time_ns() // 1_000_000, manifest_bytes, artifacts)
        except (ValueError, TypeError, KeyError, InvalidOperation) as exc:
            proposed = S.complete_request(state, 'quote_pair', request_id, 'invalid', time.time_ns() // 1_000_000, response_ref=reference)
            if checkpoint_path.read_bytes() != original: raise RuntimeError('Checkpoint changed despite lock')
            atomic_write(checkpoint_path, proposed)
            invalid_readback = json.loads(checkpoint_path.read_bytes())
            if invalid_readback != proposed: raise RuntimeError('Invalid checkpoint readback mismatch')
            S.validate_restored(invalid_readback)
            raise ValueError('Invalid observation persisted without entry: ' + str(exc)) from exc
        if checkpoint_path.read_bytes() != original: raise RuntimeError('Checkpoint changed despite lock')
        atomic_write(checkpoint_path, proposed)
        readback = json.loads(checkpoint_path.read_bytes())
        if readback != proposed: raise RuntimeError('Checkpoint readback mismatch')
        S.validate_restored(readback)
        return {'status': 'pure_virtual_entry_initialized', 'checkpoint_sha256': digest(checkpoint_path.read_bytes()), 'entry': readback['entry'], 'funding_events': len(readback['ledger']['funding_events'])}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('base', 'checkpoint', 'interface', 'manifest', 'request-id'): p.add_argument('--' + name, required=True)
    a = p.parse_args()
    print(json.dumps(initialize(a.base, a.checkpoint, a.interface, a.manifest, a.request_id), indent=2))
