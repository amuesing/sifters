"""Run directly, including from the parenthesized directory, without import collisions."""
import argparse
import hashlib
import json
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
    config, engine, midi = components()
    parser = argparse.ArgumentParser(description='Sieve-derived pitched music; ordinary MIDI folders for Ableton.')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true', help='validate without writing')
    group.add_argument('--verify-only', action='store_true', help='verify current MIDI and manifest')
    group.add_argument('--diagnostics', action='store_true', help='print musical diagnostics as JSON')
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--preset', choices=config.preset_names, help='default: creative')
    selection.add_argument('--all', action='store_true', help='process all four comparison presets')
    parser.add_argument('--output-dir', type=Path, help='export root, with one subfolder per preset; default: mid/')
    parser.add_argument('--initial-pitch', action='store_true', help='render the initial pitch mapping into mid-initial/')
    args = parser.parse_args(argv)
    try:
        names = config.preset_names if args.all else (args.preset or 'creative',)
        # Reject any invalid musical plan before writing any of the selected presets.
        settings = config.initial_pitch_settings if args.initial_pitch else config.settings
        plans = [(name, engine.build_plan(settings(name))) for name in names]
        root = args.output_dir if args.output_dir is not None else (config.OUTPUT_DIR.with_name('mid-initial') if args.initial_pitch else config.OUTPUT_DIR)
        if args.diagnostics:
            print(json.dumps({name: engine.diagnostics(plan) for name, plan in plans}, indent=2))
            return 0
        for name, plan in plans:
            output = root / name
            print(f'{name}: {plan.parity} ticks; {plan.meter[0]}/{plan.meter[1]}; '
                  f'{sum(len(v.notes) for v in plan.voices)} notes')
            for v in plan.voices:
                print(f'  {v.name}: {v.unit} ticks/step; {len(v.velocities)//len(v.layer)} distinct passes; {len(v.notes)} notes; MIDI channel {v.channel + 1}; pitch range {min(n.pitch for n in v.notes)}–{max(n.pitch for n in v.notes)}')
            if args.verify_only:
                midi.verify_files(plan, output)
                midi.verify_manifest(plan, output)
                print(f'Verified: {output}')
            elif not args.dry_run:
                midi.publish(plan, output)
                print(f'MIDI for Ableton: {output}')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'Render rejected: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
