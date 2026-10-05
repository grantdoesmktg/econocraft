"""Where the tools find game data, so they run on Grant's Mac and in a cloud session alike.

- The KubeJS export (recipes, tags, loot, registries from `/kubejs export debug`): the live Prism instance if it exists,
  otherwise tools/data/kubejs-export.tar.gz (a committed snapshot), unpacked on first use into tools/data/kubejs-export/.
  Override with ECON_EXPORT=/path/to/export.
- Refresh the snapshot after the game changes (new mods, recipe changes): on the Mac, run /kubejs export debug in game,
  then `python3 tools/paths.py --snapshot`.
"""
import os
import sys
import tarfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(TOOLS, 'data')
INSTANCE = os.path.expanduser('~/Library/Application Support/PrismLauncher/instances/Economy Test/minecraft')
LIVE_EXPORT = os.path.join(INSTANCE, 'local', 'kubejs', 'export')
SNAPSHOT_TAR = os.path.join(DATA, 'kubejs-export.tar.gz')
SNAPSHOT_DIR = os.path.join(DATA, 'kubejs-export')


def export_dir():
    if os.environ.get('ECON_EXPORT'):
        return os.environ['ECON_EXPORT']
    if os.path.isdir(LIVE_EXPORT):
        return LIVE_EXPORT
    if not os.path.isdir(os.path.join(SNAPSHOT_DIR, 'export')) and os.path.exists(SNAPSHOT_TAR):
        with tarfile.open(SNAPSHOT_TAR) as t:
            t.extractall(SNAPSHOT_DIR)
    return os.path.join(SNAPSHOT_DIR, 'export')


def snapshot():
    """Pack the live export (and the item id list) into tools/data for cloud sessions."""
    with tarfile.open(SNAPSHOT_TAR, 'w:gz') as t:
        t.add(LIVE_EXPORT, arcname='export')
    from item_index import build_index, JARS
    ids = build_index(JARS)
    open(os.path.join(DATA, 'item_ids.txt'), 'w').write('\n'.join(sorted(ids)) + '\n')
    print(f'Snapshot written: {SNAPSHOT_TAR} and {len(ids)} item ids')


if __name__ == '__main__':
    if '--snapshot' in sys.argv:
        snapshot()
    else:
        print(export_dir())
