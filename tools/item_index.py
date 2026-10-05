"""Builds a set of every item id in the installed mod jars (plus vanilla) from lang and model files.
Used to check that MARKET.md / market.json only reference real items."""
import glob, json, os, re, zipfile

def build_index(jar_globs):
    ids = set()
    for pattern in jar_globs:
        for jar in glob.glob(os.path.expanduser(pattern)):
            try:
                z = zipfile.ZipFile(jar)
            except zipfile.BadZipFile:
                continue
            for n in z.namelist():
                m = re.match(r'assets/([a-z0-9_.-]+)/models/item/([a-z0-9_/.-]+)\.json$', n)
                if m:
                    ids.add(f'{m[1]}:{m[2]}')
                m = re.match(r'assets/([a-z0-9_.-]+)/lang/en_us\.json$', n)
                if m:
                    try:
                        lang = json.loads(z.read(n).decode('utf-8', 'ignore'))
                    except Exception:
                        continue
                    for k in lang:
                        km = re.match(r'(item|block)\.([a-z0-9_.-]+)\.([a-z0-9_/]+)$', k)
                        if km:
                            ids.add(f'{km[2]}:{km[3]}')
    return ids

JARS = [
    '~/Library/Application Support/PrismLauncher/instances/Economy Test/minecraft/mods/*.jar',
    '~/Library/Application Support/PrismLauncher/libraries/com/mojang/minecraft/*/*.jar',
    '~/Library/Application Support/PrismLauncher/libraries/net/minecraft/client/*/*.jar',
    '/private/tmp/claude-501/-Users-mystuff-Modpacks/*/scratchpad/**/*.jar',
]

if __name__ == '__main__':
    idx = build_index(JARS)
    print(len(idx), 'item ids;', sum(1 for i in idx if i.startswith('minecraft:')), 'vanilla')
