#!/usr/bin/env python3
"""訳した Markdown(Hugo)が、原文のコード・URL・リンク先・ショートコード・見出しの ID を、そのまま残しているか検査する。
使い方: python3 tools/check_md.py [パスの一部 ...]    (引数なしなら content/ の全部)
  content/<相対パス>.md と original/content/<相対パス>.md を比べる。
検査する項目: フロントマターの slug/weight、コードブロックの中身、インラインコード、URL、リンク先、画像、
  ショートコード(名前と、訳してはいけない引数)、HTML タグの数、見出しの数と {#id}、表の行数。"""
import re, sys, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^[ \t]*(```+|~~~+)(?![^\n]*`)[^\n]*\n(.*?)^[ \t]*\1[ \t]*$", re.S | re.M)
SHORT = re.compile(r"\{\{[<%]\s*(/?)\s*([A-Za-z0-9_/-]+)(.*?)[>%]\}\}", re.S)
# 引数が文章(訳してよい)のショートコードは、名前だけ比べる。resourceFigure は 1 番目(ファイル名)と 3 番目(幅)を比べる。
TEXTY = {'customFigure', 'details', 'tab', 'rawHtml'}

def front(t):
    m = re.match(r'---\n(.*?)\n---\n', t, re.S)
    fm = m.group(1) if m else ''
    keep = [l.strip() for l in fm.splitlines() if re.match(r'(slug|weight|bookCollapseSection|bookFlatSection|bookToC|bookHidden|type|layout|aliases)\s*:', l)]
    return keep, (t[m.end():] if m else t)

def shorts(body):
    out = []
    for m in SHORT.finditer(body):
        slash, name, args = m.group(1), m.group(2), m.group(3).strip()
        if name in TEXTY: out.append(f'{slash}{name}')
        elif name == 'resourceFigure':
            a = re.findall(r'"[^"]*"|\S+', args); out.append(f'{name} {a[0] if a else ""} {a[2] if len(a) > 2 else ""}')
        else: out.append(f'{slash}{name} {re.sub(chr(32)+"+", " ", args)}')
    return out

def parts(t):
    fm, t = front(t)
    blocks = [re.sub(r'(?m)^[ \t]+', '', m.group(2)) for m in FENCE.finditer(t)]
    body = FENCE.sub('', t)
    sc = shorts(body)
    inline = [m.group(2).strip() for m in re.finditer(r'(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)', SHORT.sub('', body), re.S)]
    urls = re.findall(r'https?://[^\s)>\]"\'`]+', t)
    links = re.findall(r'\]\(([^)\s]+)', t)
    imgs = re.findall(r'!\[[^\]]*\]\(([^)\s]+)', t) + re.findall(r'<img[^>]*\ssrc="([^"]+)"', t)
    tags = collections.Counter(re.findall(r'</?([a-zA-Z][a-zA-Z0-9]*)[ >/]', SHORT.sub('', body)))
    heads = collections.Counter(len(m.group(1)) for m in re.finditer(r'^(#{1,6})\s', body, re.M))
    ids = re.findall(r'\{#([^}\s]+)\}', body)
    rows = len(re.findall(r'^\s*\|.*\|\s*$', body, re.M))
    return dict(fm=fm, blocks=blocks, sc=sc, inline=inline, urls=urls, links=links, imgs=imgs, tags=tags, heads=heads, ids=ids, rows=rows)

def cdiff(a, b, label):
    ca, cb = collections.Counter(a), collections.Counter(b); out = []
    for k in (ca - cb): out.append(f'  [{label}] 訳に無い: {k[:90]!r}')
    for k in (cb - ca): out.append(f'  [{label}] 訳で増えた/変わった: {k[:90]!r}')
    return out

def check(tr, orig):
    A = parts(orig.read_text(encoding='utf-8')); B = parts(tr.read_text(encoding='utf-8')); out = []
    if A['fm'] != B['fm']: out.append(f"  [フロントマター] 原文 {A['fm']} / 訳 {B['fm']}")
    if A['blocks'] != B['blocks']:
        out.append(f"  [コードブロック] 数 {len(A['blocks'])} → {len(B['blocks'])}。違う箇所:")
        for i, (x, y) in enumerate(zip(A['blocks'], B['blocks'])):
            if x != y: out.append(f'     {i + 1} 番目: 原文 {x[:60]!r} / 訳 {y[:60]!r}'); break
    if A['sc'] != B['sc']: out += [f"  [ショートコード] 原文 {A['sc']}", f"                   訳   {B['sc']}"]
    for k, lab in (('inline', 'インラインコード'), ('urls', 'URL'), ('links', 'リンク先'), ('imgs', '画像'), ('ids', '見出しID')):
        out += cdiff(A[k], B[k], lab)
    if A['tags'] != B['tags']: out.append(f"  [HTML タグ] 原文 {dict(A['tags'])} / 訳 {dict(B['tags'])}")
    if A['heads'] != B['heads']: out.append(f"  [見出し] 原文 {dict(A['heads'])} / 訳 {dict(B['heads'])}")
    if A['rows'] != B['rows']: out.append(f"  [表の行] 原文 {A['rows']} / 訳 {B['rows']}")
    return out

if __name__ == '__main__':
    want = sys.argv[1:]; bad = 0; n = 0
    for orig in sorted((ROOT / 'original' / 'content').rglob('*.md')):
        rel = orig.relative_to(ROOT / 'original')
        if want and not any(w in rel.as_posix() for w in want): continue
        tr = ROOT / rel; n += 1
        if not tr.exists(): print(f'{rel}  ありません'); bad += 1; continue
        same = tr.read_text(encoding='utf-8') == orig.read_text(encoding='utf-8')
        pr = check(tr, orig)
        print(f'{rel.as_posix():70} ' + ('原文のまま(未訳)' if same else (f'問題 {len(pr)} 件' if pr else '一致')))
        for p in pr: print(p)
        bad += bool(pr)
    print(f'--- {n} 本中、問題のあるもの {bad} 本'); sys.exit(1 if bad else 0)
