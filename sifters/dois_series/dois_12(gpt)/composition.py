"""Run directly, including from the parenthesized directory, without import collisions."""
import argparse
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys


def components():
    directory = Path(__file__).resolve().parent
    package = '_sifters_gpt_' + hashlib.sha256(str(directory).encode()).hexdigest()[:12]
    if package not in sys.modules:
        spec = importlib.util.spec_from_file_location(package, directory / '__init__.py',
                                                     submodule_search_locations=[str(directory)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module
        spec.loader.exec_module(module)
    return tuple(importlib.import_module(package + '.' + name) for name in ('config', 'engine', 'midi_io'))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Render one verified statement at the first rhythmic convergence.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true', help='validate and report the plan without writing')
    group.add_argument('--verify-only', action='store_true', help='check existing MIDI and its manifest without writing')
    parser.add_argument('--output-dir', type=Path, help='publication path; defaults to this iteration\'s mid/')
    args = parser.parse_args(argv)
    config, engine, midi = components()
    try:
        plan = engine.build_plan(config.settings())
        output = args.output_dir if args.output_dir is not None else config.OUTPUT_DIR
        print(f'{plan.title}: first parity {plan.parity} ticks; meter {plan.meter[0]}/{plan.meter[1]}')
        for voice in plan.voices:
            print(f'  {voice.name}: {len(voice.notes)} notes, {len(voice.layer)}-step rhythm, '
                  f'{len(voice.velocities) // len(voice.layer)} distinct passes, {voice.unit} ticks/step')
        print(f'  configuration {plan.fingerprint[:16]}')
        if args.verify_only:
            snapshot = Path(output).resolve(strict=True)
            midi.verify_files(plan, snapshot)
            midi.verify_manifest(plan, snapshot)
            print(f'All existing files verified: {output}')
        elif not args.dry_run:
            midi.publish(plan, output)
            print(f'Published all verified files: {output}')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'Render rejected: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
