"""Download every mod in the pack (cached) and check:
 - each jar's declared required dependencies are provided by some jar in the pack (including jar-in-jar),
 - references to common library mods that are not declared (hidden dependencies, like Squat Grow -> Cloth Config),
 - Modrinth version type (release/beta/alpha) and loader/game version."""
import glob, json, os, re, sys, tomllib, urllib.parse, urllib.request, zipfile, io, concurrent.futures as cf

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = sys.argv[1] if len(sys.argv) > 1 else '/tmp/econ-jars'
os.makedirs(CACHE, exist_ok=True)
UA = {'User-Agent': 'economy-pack-verify'}

# package prefix in bytecode -> mod id that provides it
LIBS = {
    b'me/shedaniel/autoconfig': 'cloth_config', b'me/shedaniel/clothconfig': 'cloth_config',
    b'dev/architectury/': 'architectury', b'net/blay09/mods/balm': 'balm',
    b'com/teamresourceful/resourcefullib': 'resourcefullib', b'fuzs/puzzleslib': 'puzzleslib',
    b'software/bernie/geckolib': 'geckolib', b'top/theillusivec4/curios': 'curios',
    b'org/moddingx/libx': 'libx', b'net/darkhax/bookshelf': 'bookshelf', b'com/lothrazar/library': 'flib',
    b'dev/shadowsoffire/placebo': 'placebo', b'com/yungnickyoung/minecraft/yungsapi': 'yungsapi',
    b'dev/ftb/mods/ftblibrary': 'ftblibrary', b'com/hollingsworth/arsnouveau': 'ars_nouveau',
    b'thedarkcolour/kotlinforforge': 'kotlinforforge', b'net/minecraftforge/kotlin': 'kotlinforforge',
    b'dev/isxander/yacl': 'yet_another_config_lib_v3', b'com/supermartijn642/core': 'supermartijn642corelib',
    b'codechicken/lib': 'codechickenlib', b'com/brandon3055/brandonscore': 'brandonscore',
    b'team/creative/creativecore': 'creativecore', b'it/hurts/sskirillss/relics': 'relics',
    b'net/p3pp3rf1y/sophisticatedcore': 'sophisticatedcore', b'com/mrcrayfish/framework': 'framework',
    b'io/github/fabricators_of_create/porting_lib': 'porting_lib', b'dev/latvian/mods/kubejs': 'kubejs',
    b'snownee/jade': 'jade', b'mezz/jei': 'jei', b'dev/emi': 'emi', b'mcjty/theoneprobe': 'theoneprobe',
    b'com/simibubi/create': 'create', b'mekanism/api': 'mekanism', b'appeng/api': 'ae2',
    b'com/tterrag/registrate': 'registrate', b'it/zerono/mods/zerocore': 'zerocore',
    b'net/silentchaos512/lib': 'silentlib', b'com/cristelknight/cristellib': 'cristellib',
    b'me/fzzyhmstrs/fzzy_config': 'fzzy_config', b'com/natamus/collective': 'collective',
    b'dev/shadowsoffire/apothic_attributes': 'apothic_attributes', b'com/github/alexthe666/citadel': 'citadel',
    b'com/teamabnormals/blueprint': 'blueprint', b'xyz/przemyk/simplylib': 'simplylib',
    b'org/violetmoon/zeta': 'zeta', b'com/direwolf20/justdirethings': 'justdirethings',
    b'net/lucent/lucentlib': 'lucentlib', b'dev/kosmx/playeranim': 'playeranimator',
}
# references we consider optional integrations (never flag)
OPTIONAL_OK = {'registrate', 'jade', 'jei', 'emi', 'theoneprobe', 'kubejs', 'curios', 'create', 'mekanism', 'ae2', 'ars_nouveau', 'justdirethings'}


def get(u, binary=False):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r:
        return r.read() if binary else json.load(r)


def fetch(meta):
    t = tomllib.load(open(meta, 'rb'))
    fn = t['filename']
    path = os.path.join(CACHE, fn)
    url = t['download'].get('url')
    if not url:
        fid = t['update']['curseforge']['file-id']
        url = f'https://mediafilez.forgecdn.net/files/{fid // 1000}/{fid % 1000}/{urllib.parse.quote(fn)}'
    if not os.path.exists(path):
        open(path, 'wb').write(get(url, True))
    vtype = None
    mr = t.get('update', {}).get('modrinth')
    if mr:
        try:
            v = get(f"https://api.modrinth.com/v2/version/{mr['version']}")
            vtype = v['version_type']
        except Exception:
            pass
    return meta, fn, path, vtype


def mods_in(z, prefix=''):
    """mod ids + required deps of a jar, recursing into jar-in-jar."""
    ids, reqs = set(), []
    try:
        d = tomllib.loads(z.read('META-INF/neoforge.mods.toml').decode('utf-8', 'ignore'))
        ids |= {m['modId'] for m in d.get('mods', [])}
        for owner, deps in d.get('dependencies', {}).items():
            for x in deps:
                t = str(x.get('type', 'required' if x.get('mandatory') else 'optional')).lower()
                if t == 'required':
                    reqs.append(x['modId'])
    except KeyError:
        pass
    nested = [n for n in z.namelist() if n.startswith('META-INF/jarjar/') and n.endswith('.jar')]
    try:  # jar-in-jar paths can live anywhere; metadata.json lists them
        meta = json.loads(z.read('META-INF/jarjar/metadata.json'))
        nested += [j['path'] for j in meta.get('jars', []) if 'path' in j]
    except KeyError:
        pass
    for n in set(nested):
        if True:
            try:
                inner = zipfile.ZipFile(io.BytesIO(z.read(n)))
                i2, _ = mods_in(inner)
                ids |= i2
            except Exception:
                pass
    return ids, reqs


def main():
    metas = sorted(glob.glob(os.path.join(PACK, 'mods', '*.pw.toml')))
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(fetch, metas))
    raw = [os.path.join(PACK, 'mods', f) for f in os.listdir(os.path.join(PACK, 'mods')) if f.endswith('.jar')]
    provided = {'minecraft', 'neoforge', 'java', 'forge'}
    info = []
    for meta, fn, path, vtype in results + [(p, os.path.basename(p), p, 'local') for p in raw]:
        z = zipfile.ZipFile(path)
        ids, reqs = mods_in(z)
        provided |= ids
        refs = set()
        for n in z.namelist():
            if n.endswith('.class'):
                b = z.read(n)
                for k, v in LIBS.items():
                    if k in b:
                        refs.add(v)
        # Registrate ships as a plain library inside Create's jar (no mod id).
        if any('registrate' in n.lower() for n in z.namelist() if n.endswith('.jar')):
            ids.add('registrate')
        info.append((fn, ids, reqs, refs, vtype))
    problems = 0
    for fn, ids, reqs, refs, vtype in info:
        missing = [r for r in reqs if r not in provided]
        hidden = sorted(r for r in refs - ids - set(reqs) - OPTIONAL_OK if r not in provided)
        flag = []
        if missing: flag.append(f'MISSING required: {missing}')
        if hidden: flag.append(f'possible hidden dep: {hidden}')
        if vtype in ('beta', 'alpha'): flag.append(vtype)
        if flag:
            problems += bool(missing or hidden)
            print(f'{fn}: ' + '; '.join(flag))
    print(f'\n{len(info)} jars checked, {problems} with dependency problems')


if __name__ == '__main__':
    main()
