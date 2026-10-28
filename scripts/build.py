"""Собирает код для Тильды и превью для GitHub Pages из живой страницы
kineziofitness.online/coach-encyclopedia (снимок source-live-*.html).

Меняется только акция: даты в текстах, конец таймера и момент старта.
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "source-live-2026-10-28.html"

OLD_END = "1788469199000"            # 03.09.2026 23:59:59 МСК
START_MS = 1793264400000             # 29.10.2026 12:00:00 МСК
END_MS = 1793480399000               # 31.10.2026 23:59:59 МСК
DATE_RE = re.compile(r"3([\s ])сентября")

page = SRC.read_text(encoding="utf-8")
blocks = re.findall(r"<!-- nominify begin -->(.*?)<!-- nominify end -->", page, re.S)
kin = {n: b for b in blocks for n in "1345" if f"блок {n}/5" in b}
assert set(kin) == set("1345"), kin.keys()


CHECKOUT = "https://lk.kineziofitness.online/payments/tariff_nwn1gA/checkout"
SUPPORT = "tg://resolve?domain=KINEZIOFITNESSCARE"
NB = "\u00a0"
CLIENT_NOTE_NEW = f"Если вы{NB}уже{NB}покупали продукты KINEZIO, цена 4{NB}990{NB}₽ применится при{NB}оплате автоматически"


def client_card(b):
    """Клиентам в акцию: зачёркнуто 5 990, кнопка «Купить» на ту же оплату.
    После акции всё возвращается: зачёркнуто 14 990, «Написать в поддержку»."""
    b, n1 = re.subn(r'(<p class="[^"]*line-through decoration-solid")>14[\s\u00a0]990 ₽(</p><span[^>]*>Скидка для)',
                    r'\1 data-kin-after="14 990 ₽">5 990 ₽\2', b)
    b, n2 = re.subn(r'(<p class="[^"]*")>(Если вы[^<]*поддержку)',
                    lambda m: f'{m.group(1)} data-kin-after="{m.group(2)}">{CLIENT_NOTE_NEW}', b)
    # Кнопка «Купить» того же размера, что в соседней карточке; после акции класс возвращается
    sizes = {"h-[59px] shrink-0 font-bold px-[16px] text-[14px] tracking-[-0.42px]":
             "h-[59px] shrink-0 font-bold px-[60px] text-[16px] tracking-[-0.48px]",
             "w-full px-[24px] py-[16px] font-bold text-[16px] leading-[19px] tracking-[-0.48px]":
             "w-full px-[24px] py-[16px] font-bold text-[14px] leading-[17px] tracking-[-0.42px]"}

    def buy(m):
        cls = m.group(2)
        sale_cls = cls
        for a, z in sizes.items():
            sale_cls = sale_cls.replace(a, z)
        assert sale_cls != cls
        return (f'<a data-kin-after="Написать в{NB}поддержку" data-kin-after-href="{SUPPORT}" '
                f'data-kin-after-class="{cls}" href="{CHECKOUT}"{m.group(1)}class="{sale_cls}">Купить</a>')
    b, n3 = re.subn(r'<a href="' + re.escape(SUPPORT) + r'"([^>]*?)class="([^"]*)">Написать в\u00a0поддержку</a>', buy, b)
    assert (n1, n2, n3) == (1, 1, 1), (n1, n2, n3)
    return b


def markup(b):
    b = client_card(b)
    b = b.replace(f'data-kin-countdown="{OLD_END}"', f'data-kin-countdown="{END_MS}"')
    b = DATE_RE.sub(lambda m: f"31{m.group(1)}октября", b)
    assert "сентябр" not in b
    return b


# До старта страница выглядит как после акции (обычная цена), в момент старта
# перезагружается и показывает скидку с таймером
GATE = ("var SALE_START_MS={start};if(Date.now()<SALE_START_MS&&SALE_START_MS-Date.now()<864e5){{"
        "setTimeout(function(){{location.reload();}},SALE_START_MS-Date.now()+1000);}}")


def script(b, start=START_MS, end=END_MS):
    b = b.replace(f"var SALE_END_MS={OLD_END};", f"var SALE_END_MS={end};" + GATE.format(start=start))
    b = b.replace("if(Date.now()>SALE_END_MS)saleOver();",
                  "if(Date.now()>SALE_END_MS||Date.now()<SALE_START_MS)saleOver();")
    b = b.replace("else setTimeout(saleOver,", "else if(Date.now()<SALE_END_MS)setTimeout(saleOver,")
    b = b.replace("[].forEach.call(wrap.querySelectorAll('[data-kin-sale-only]')",
                  "[].forEach.call(wrap.querySelectorAll('[data-kin-after-href]'),function(n){n.setAttribute('href',n.getAttribute('data-kin-after-href'));var c=n.getAttribute('data-kin-after-class');if(c)n.className=c;});"
                  "[].forEach.call(wrap.querySelectorAll('[data-kin-sale-only]')", 1)
    assert "SALE_START_MS" in b and str(end) in b and "data-kin-after-href" in b
    return b


new = {"1": kin["1"], "3": markup(kin["3"]), "4": markup(kin["4"]), "5": script(kin["5"])}
stamp = "2026-10-28 · акция 29.10 12:00 – 31.10 23:59"
names = {"1": "блок-1-стили", "3": "блок-3-разметка-1440", "4": "блок-4-разметка-430", "5": "блок-5-скрипт"}
for n, body in new.items():
    body = body.replace("· 2026-09-08 -->", f"· {stamp} -->")
    (ROOT / "tilda" / f"{names[n]}.html").write_text(body.strip() + "\n", encoding="utf-8")

# --- превью ---------------------------------------------------------------
def strip_tracking(html):
    html = re.sub(r"<script[^>]*>[^<]*(mainMetrikaId|mc\.yandex)[\s\S]*?</script>", "", html)
    html = re.sub(r'<script src="https://www\.nn99\.ru/widget\.js"[^>]*></script>', "", html)
    html = re.sub(r"<noscript>\s*<div>\s*<img[^>]*mc\.yandex[^>]*>\s*</div>\s*</noscript>", "", html)
    # Рассрочка Т-Банка грузится синхронно и из некоторых сетей отвечает 30 с; в превью не нужна
    html = html.replace('<script src="https://forma.tinkoff.ru/static/onlineScriptTilda.js"></script>', "")
    # GTM и статистика Тильды — чтобы просмотры превью не попадали в аналитику Kinezio
    html = re.sub(r"<script>[^<]*googletagmanager\.com/gtm\.js[\s\S]*?</script>", "", html)
    html = re.sub(r"<noscript><iframe[^>]*googletagmanager[^>]*></iframe></noscript>", "", html)
    html = re.sub(r'<script src="https://static\.tildacdn\.com/js/tilda-events-[^"]*"[^>]*></script>', "", html)
    return html.replace("<head>", '<head><meta name="robots" content="noindex,nofollow">', 1)


def build(kind):
    p = page
    for n in "34":
        p = p.replace(kin[n], markup(kin[n]))
    if kind == "sale":       # скидка уже идёт: старт в прошлом
        s = script(kin["5"], start=0)
    elif kind == "switch":   # таймер на 60 секунд, потом автопереключение
        s = script(kin["5"], start=0).replace(f"var SALE_END_MS={END_MS};", "var SALE_END_MS=Date.now()+60000;")
        s = ("<script>[].forEach.call(document.querySelectorAll('[data-kin-countdown]'),"
             "function(t){t.setAttribute('data-kin-countdown',String(Date.now()+60000));});</script>") + s
    elif kind == "after":    # акция закончилась
        s = script(kin["5"], start=0, end=1)
    elif kind == "before":   # до старта 29.10 12:00 (реальный код из tilda/)
        s = script(kin["5"])
    p = p.replace(kin["5"], s)
    p = strip_tracking(p)
    banner = {
        "sale": "Превью: скидка идёт, таймер до 31.10 23:59",
        "switch": "Превью: таймер 60 секунд, затем страница сама переключится",
        "after": "Превью: акция закончилась (так будет с 01.11)",
        "before": "Превью: до старта акции (сегодня и завтра до 12:00)",
    }[kind]
    bar = ('<div style="position:fixed;top:0;left:0;right:0;z-index:2147483647;background:#14161a;color:#fff;'
           'font:600 13px/1.3 system-ui,sans-serif;padding:8px 12px;text-align:center">'
           f'{banner} · <a href="./" style="color:#ff7e55">все варианты</a></div>')
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + bar, p, count=1)


site = ROOT / "docs"
site.mkdir(exist_ok=True)
for kind in ("sale", "switch", "after", "before"):
    (site / f"{kind}.html").write_text(build(kind), encoding="utf-8")
print("ok")
