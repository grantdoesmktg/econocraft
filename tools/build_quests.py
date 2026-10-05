"""
Builds the Economy Pack FTB Quests book from tools/quest_content.py.

Run:  python3 tools/build_quests.py      (after tools/make_banners.py if banners changed)
Writes config/ftbquests/quests/{data.snbt, chapter_groups.snbt, chapters/*.snbt, lang/en_us.snbt}
and checks every item id against the installed mods.

Notes on FTB Quests quirks handled here:
  - Ids are parsed as signed 64-bit hex: the first digit must be 0-7, or the object loses its title.
  - '&' starts a colour code; a literal '&' must be written as '\\&'.
  - Ids are derived from stable keys, so editing text never resets players' progress.
"""
import hashlib
import os
import re
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import quest_content as C  # noqa: E402

PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(PACK, 'config', 'ftbquests', 'quests')
BANNER_DIR = os.path.join(PACK, 'kubejs', 'assets', 'economypack', 'textures', 'quests')

COINS = [('lightmanscurrency:coin_netherite', 100000), ('lightmanscurrency:coin_diamond', 10000),
         ('lightmanscurrency:coin_emerald', 1000), ('lightmanscurrency:coin_gold', 100),
         ('lightmanscurrency:coin_iron', 10), ('lightmanscurrency:coin_copper', 1)]

used_ids = set()
referenced_items = set()

AMP = re.compile(r'&(?![0-9a-fk-orA-FK-OR])')


def qid(key):
    h = hashlib.sha1(key.encode()).hexdigest()[:16].upper()
    h = '1234567'[int(h[0], 16) % 7] + h[1:]
    assert h not in used_ids, f'id clash for {key}'
    used_ids.add(h)
    return h


def fmt(text):
    """Escape literal '&' so FTB Quests doesn't read it as a colour code."""
    return AMP.sub(r'\\&', str(text))


def s(v):
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'


def coin_split(amount):
    out = []
    for item, value in COINS:
        n, amount = divmod(amount, value)
        if n:
            out.append((item, n))
    return out


def item_snbt(item_id, count=1):
    referenced_items.add(item_id)
    return f'{{ count: {count}, id: {s(item_id)} }}'


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


# ------------------------------------------------------------------ tasks and rewards

def task_snbt(key, t):
    tid = qid(key)
    kind = t[0]
    if kind == 'item':
        item, count = t[1], t[2]
        consume = len(t) > 3 and t[3]
        extra = ' consume_items: true' if consume else ''
        return f'{{ id: {s(tid)}, type: "item", item: {item_snbt(item)}, count: {count}L{extra} }}'
    if kind == 'check':
        return f'{{ id: {s(tid)}, type: "checkmark" }}'
    if kind == 'dim':
        return f'{{ id: {s(tid)}, type: "dimension", dimension: {s(t[1])} }}'
    if kind == 'kill':
        return f'{{ id: {s(tid)}, type: "kill", entity: {s(t[1])}, value: {t[2]}L }}'
    if kind == 'adv':
        return f'{{ id: {s(tid)}, type: "advancement", advancement: {s(t[1])}, criterion: "" }}'
    if kind == 'stage':
        return f'{{ id: {s(tid)}, type: "gamestage", stage: {s(t[1])} }}'
    raise ValueError(t)


def tasks_for(qkey, q, group, index):
    tasks = list(q.get('tasks', []))
    if not tasks and (index == 0 or group == 'reference'):
        # Entry quests and reference pages: the player ticks a checkmark to confirm they read it.
        tasks = [('check',)]
    if q.get('gate'):
        tier, lifetime, fee = q['gate']
        tasks = [('adv', f'economy_core:earned/{lifetime}')]
        tasks += [('item', item, n, True) for item, n in coin_split(fee)]
    if not tasks and group.startswith('mods') and q.get('icon'):
        # Mod tabs: auto-complete when you get your hands on the thing the quest is about.
        tasks = [('item', q['icon'], 1)]
    return [task_snbt(f'{qkey}/task/{i}', t) for i, t in enumerate(tasks)]


def rewards_for(qkey, q):
    out = []
    for i, (item, n) in enumerate(coin_split(q.get('coins', 0))):
        out.append(f'{{ id: {s(qid(f"{qkey}/coin/{i}"))}, type: "item", item: {item_snbt(item, n)} }}')
    personal = ' team_reward: false' if q.get('personal_rewards') else ''
    for i, (item, n) in enumerate(q.get('items', [])):
        out.append(f'{{ id: {s(qid(f"{qkey}/item/{i}"))}, type: "item", item: {item_snbt(item, n)}{personal} }}')
    if q.get('gate'):
        tier = q['gate'][0]
        out.append(f'{{ id: {s(qid(f"{qkey}/stage"))}, type: "gamestage", stage: "economy:tier_{tier}" }}')
        out.append(f'{{ id: {s(qid(f"{qkey}/tiercmd"))}, type: "command", command: "/market tier set {tier} @p", '
                   f'elevate_perms: true, silent: true }}')
    return out


# ------------------------------------------------------------------ design

def style(q, ch, index):
    """Shape, size and title colour by role: start, main, side, milestone, gate, reference."""
    theme = ch['theme']
    tasks = q.get('tasks', [])
    is_milestone = any(t[0] == 'adv' and ('sale/' in t[1] or 'earned/4' in t[1]) for t in tasks)
    if q.get('gate'):
        return 'gear', 2.25, f'&6&l{q["title"]}'
    if ch['group'] == 'reference':
        return 'rsquare', 1.0, f'&{theme}{q["title"]}'
    if index == 0:
        return 'octagon', 1.75, f'&{theme}&l{q["title"]}'
    if is_milestone:
        return 'diamond', 1.5, f'&d&l{q["title"]}'
    if q.get('side') or q.get('optional'):
        return 'rsquare', 1.0, f'&7{q["title"]}'
    return 'hexagon', 1.25, f'&{theme}{q["title"]}'


def styled_text(lines, theme):
    """First line in the chapter colour, the rest as written; a quiet rule before tips."""
    out = []
    for i, line in enumerate(lines):
        line = fmt(line)
        if i == 0 and line:
            line = f'&{theme}{line}'
        out.append(line)
    return out


def layout(quests):
    """Main line snakes left-to-right in rows of 6; side quests hang below their parent."""
    pos, main_i, side_count = {}, 0, {}
    for q in quests:
        if q.get('side') and q['side'] in pos:
            px, py = pos[q['side']]
            k = side_count.get(q['side'], 0)
            side_count[q['side']] = k + 1
            pos[q['key']] = (px + k * 1.5, py + 2.0)
        else:
            row, col = divmod(main_i, 6)
            if row % 2:
                col = 5 - col
            pos[q['key']] = (col * 2.25, row * 4.0)
            main_i += 1
    return pos


def banner_image(ch, pos):
    path = os.path.join(BANNER_DIR, f'{ch["key"]}.png')
    if not os.path.exists(path):
        return None
    pw, ph = png_size(path)
    height = ph / 62.0
    width = pw / 62.0
    if width > 12.0:
        height, width = height * 12.0 / width, 12.0
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    cx = (min(xs) + max(xs)) / 2
    top = min(ys) - 1.6 - height / 2
    return (f'{{ x: {cx:.3f}d, y: {top:.3f}d, width: {width:.3f}d, height: {height:.3f}d, rotation: 0.0d, '
            f'image: "economypack:textures/quests/{ch["key"]}.png", hover: [ ], click: "", dev: false, corner: false }}')


# ------------------------------------------------------------------ build

def build():
    lang = {}
    chapter_files = {}
    group_ids = {g['key']: qid(f'group/{g["key"]}') for g in C.GROUPS}
    key_to_id = {}
    for ch in C.CHAPTERS:
        for q in ch['quests']:
            key_to_id[f'{ch["key"]}/{q["key"]}'] = qid(f'quest/{ch["key"]}/{q["key"]}')

    def resolve(ch_key, dep):
        full = dep if '/' in dep else f'{ch_key}/{dep}'
        if full not in key_to_id:
            raise KeyError(f'unknown dependency {full}')
        return key_to_id[full]

    for order, ch in enumerate(C.CHAPTERS):
        cid = qid(f'chapter/{ch["key"]}')
        if ch.get('tier_label'):
            lang[f'chapter.{cid}.title'] = f'&{ch["theme"]}&l{ch["tier_label"].title()}&r &8» &f{fmt(ch["title"])}'
        else:
            lang[f'chapter.{cid}.title'] = f'&{ch["theme"]}{fmt(ch["title"])}'
        if ch.get('subtitle'):
            lang[f'chapter.{cid}.chapter_subtitle'] = [f'&7{fmt(ch["subtitle"])}']
        pos = layout(ch['quests'])
        prev = None
        quest_snbt = []
        for index, q in enumerate(ch['quests']):
            full = f'{ch["key"]}/{q["key"]}'
            this = key_to_id[full]
            if 'deps_any' in q:
                deps = [resolve(ch['key'], d) for d in q['deps_any']]
            elif 'deps' in q:
                deps = [resolve(ch['key'], d) for d in q['deps']]
            elif q.get('side'):
                deps = [resolve(ch['key'], q['side'])]
            else:
                deps = [prev] if prev else []
            if not q.get('side'):
                prev = this
            shape, size, title = style(q, ch, index)
            lang[f'quest.{this}.title'] = fmt(title) if '&' not in q['title'] else title.replace(q['title'], fmt(q['title']))
            if q.get('subtitle'):
                lang[f'quest.{this}.quest_subtitle'] = f'&7{fmt(q["subtitle"])}'
            if q.get('text'):
                lang[f'quest.{this}.quest_desc'] = styled_text(q['text'], ch['theme'])
            x, y = pos[q['key']]
            fields = [f'id: {s(this)}', f'x: {x}d', f'y: {y}d', f'shape: {s(shape)}', f'size: {size}d']
            if q.get('icon'):
                fields.append(f'icon: {item_snbt(q["icon"])}')
            if deps:
                fields.append('dependencies: [' + ' '.join(s(d) for d in deps) + ']')
            if 'deps_any' in q:
                fields.append('dependency_requirement: "one_completed"')
            if q.get('optional'):
                fields.append('optional: true')
            tasks = tasks_for(full, q, ch['group'], index)
            fields.append('tasks: [' + ('\n\t\t\t\t' + '\n\t\t\t\t'.join(tasks) + '\n\t\t\t' if tasks else ' ') + ']')
            rw = rewards_for(full, q)
            if rw:
                fields.append('rewards: [\n\t\t\t\t' + '\n\t\t\t\t'.join(rw) + '\n\t\t\t]')
            quest_snbt.append('\t\t{\n\t\t\t' + '\n\t\t\t'.join(fields) + '\n\t\t}')
        image = banner_image(ch, pos)
        body = [
            '{',
            '\tdefault_hide_dependency_lines: false',
            '\tdefault_quest_shape: ""',
            f'\tfilename: {s(ch["key"])}',
            f'\tgroup: {s(group_ids[ch["group"]])}',
            f'\ticon: {item_snbt(ch["icon"])}',
            f'\tid: {s(cid)}',
            f'\timages: [{" " + image + " " if image else " "}]',
            f'\torder_index: {order}',
            '\tquest_links: [ ]',
            '\tquests: [',
            '\n'.join(quest_snbt),
            '\t]',
            '}',
        ]
        chapter_files[ch['key']] = '\n'.join(body) + '\n'

    groups = []
    for g in C.GROUPS:
        gid = group_ids[g['key']]
        lang[f'chapter_group.{gid}.title'] = g['title']
        groups.append(f'\t\t{{ id: {s(gid)} }}')

    chapters_dir = os.path.join(OUT, 'chapters')
    if os.path.isdir(chapters_dir):
        shutil.rmtree(chapters_dir)
    os.makedirs(chapters_dir)
    os.makedirs(os.path.join(OUT, 'lang'), exist_ok=True)
    for key, text in chapter_files.items():
        open(os.path.join(chapters_dir, f'{key}.snbt'), 'w').write(text)
    open(os.path.join(OUT, 'chapter_groups.snbt'), 'w').write('{\n\tchapter_groups: [\n' + '\n'.join(groups) + '\n\t]\n}\n')
    open(os.path.join(OUT, 'data.snbt'), 'w').write(C.DATA_SNBT)

    lines = ['{']
    for k, v in lang.items():
        if isinstance(v, list):
            lines.append(f'\t{k}: [')
            lines += [f'\t\t{s(x)}' for x in v]
            lines.append('\t]')
        else:
            lines.append(f'\t{k}: {s(v)}')
    lines.append('}')
    open(os.path.join(OUT, 'lang', 'en_us.snbt'), 'w').write('\n'.join(lines) + '\n')

    nq = sum(len(c['quests']) for c in C.CHAPTERS)
    print(f'Wrote {len(C.CHAPTERS)} chapters, {nq} quests, {len(lang)} lang entries to {OUT}')


def check_items():
    from item_index import build_index, JARS
    idx = build_index(JARS)
    missing = sorted(i for i in referenced_items if i not in idx)
    print('Unknown item ids:', missing or 'none')
    return missing


if __name__ == '__main__':
    build()
    sys.exit(1 if check_items() else 0)
