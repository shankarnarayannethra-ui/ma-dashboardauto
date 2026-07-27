#!/usr/bin/env python3
"""Fetch recent M&A headlines and write browser-ready generated-deals.js."""
from __future__ import annotations
import hashlib, html, json, os, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "generated-deals.js"
QUERY = '(acquires OR acquisition OR merger OR takeover OR buyout) when:7d'
DEFAULT_FEED = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({
    'q': QUERY, 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'
})
FEED = os.environ.get('DEALSCOPE_FEED_URL', DEFAULT_FEED)
KEYWORDS = re.compile(r'\b(acquir(?:e|es|ed|ing)|acquisition|merger|merge[sd]?|takeover|buyout|to buy|agrees to buy|deal)\b', re.I)
EXCLUDE = re.compile(r'\b(job merger|data merge|merge request|traffic merger)\b', re.I)

def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', text or ''))).strip()

def split_source(title: str) -> tuple[str, str]:
    parts = title.rsplit(' - ', 1)
    return (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else (title.strip(), 'Google News')

def infer_parties(headline: str) -> tuple[str, str]:
    patterns = [
        r'^(?P<a>.+?)\s+(?:agrees? to |plans? to |set to |will )?(?:acquire|buy|purchase|take over)\s+(?P<t>.+?)(?:\s+for\s+|\s+in\s+\$|$)',
        r'^(?P<a>.+?)\s+(?:acquisition|buyout) of\s+(?P<t>.+?)(?:\s+for\s+|$)',
        r'^(?P<a>.+?)\s+and\s+(?P<t>.+?)\s+(?:agree to )?merge',
    ]
    for pattern in patterns:
        m = re.search(pattern, headline, re.I)
        if m:
            return clean(m.group('a'))[:80], clean(m.group('t'))[:80]
    return 'Potential acquirer', 'Potential target'

def parse_value(text: str):
    m = re.search(r'\$\s*([0-9]+(?:\.[0-9]+)?)\s*(billion|bn|million|m)\b', text, re.I)
    if not m: return None
    value=float(m.group(1)); unit=m.group(2).lower()
    return round(value if unit in ('billion','bn') else value/1000, 3)

def main() -> None:
    req=urllib.request.Request(FEED, headers={'User-Agent':'DealScope/1.0 (+GitHub Actions)'})
    with urllib.request.urlopen(req, timeout=30) as response:
        xml=response.read()
    root=ET.fromstring(xml)
    items=[]; seen=set()
    for item in root.findall('./channel/item'):
        raw_title=clean(item.findtext('title',''))
        description=clean(item.findtext('description',''))
        if not KEYWORDS.search(raw_title) or EXCLUDE.search(raw_title): continue
        headline, source_name=split_source(raw_title)
        normalized=re.sub(r'[^a-z0-9]+',' ',headline.lower()).strip()
        if normalized in seen: continue
        seen.add(normalized)
        link=clean(item.findtext('link',''))
        pub_raw=clean(item.findtext('pubDate',''))
        try: pub=parsedate_to_datetime(pub_raw).astimezone(timezone.utc)
        except Exception: pub=datetime.now(timezone.utc)
        acquirer,target=infer_parties(headline)
        digest=hashlib.sha256((headline+link).encode()).hexdigest()[:12]
        summary=description or f'Automated M&A news match from {source_name}. Open the original article to confirm transaction terms.'
        items.append({
            'id': f'news-{digest}', 'date': pub.strftime('%B %-d, %Y'),
            'publishedISO': pub.isoformat(), 'acquirer': acquirer, 'target': target,
            'headline': headline, 'valueBillions': parse_value(headline+' '+description),
            'sector': 'M&A news', 'countries': ['To be confirmed'], 'status': 'News detected',
            'crossBorder': False, 'automated': True, 'sourceName': source_name,
            'summary': summary[:360],
            'intent': 'This record was detected automatically from a news headline. Review the original reporting before drawing conclusions about strategic intent.',
            'longTermGoals': ['Confirm transaction terms', 'Review management rationale', 'Track approvals and closing conditions'],
            'culture': 'Not yet researched. Compare leadership, operating models, incentives, and employee practices.',
            'geography': 'Not yet researched. Confirm headquarters, operating regions, and regulatory jurisdictions.',
            'valuation': 'Deal value was extracted only when clearly stated in the headline or feed summary.',
            'shareholderValue': 'Review offer premium, financing, dilution, debt, and the market reaction in the original reporting.',
            'scores': {'strategic': 5, 'cultural': 5, 'geographic': 5, 'valuation': 5},
            'source': link,
            'regulatoryTimeline': [
                {'stage':'News detected','status':'complete','date':pub.strftime('%b %-d, %Y')},
                {'stage':'Terms verified','status':'current','date':'Manual review needed'},
                {'stage':'Regulatory review','status':'upcoming','date':'To be confirmed'},
                {'stage':'Closing','status':'upcoming','date':'To be confirmed'}],
            'integrationTimeline': [
                {'stage':'Integration planning','status':'upcoming'},
                {'stage':'Leadership alignment','status':'upcoming'},
                {'stage':'Systems and operations','status':'upcoming'},
                {'stage':'Synergy tracking','status':'upcoming'}]
        })
        if len(items)>=30: break
    items.sort(key=lambda x:x['publishedISO'], reverse=True)
    payload='// Generated automatically. Do not edit by hand.\nwindow.generatedDeals = '+json.dumps(items, ensure_ascii=False, indent=2)+';\n'
    # repr uses single quotes, valid JavaScript; escape closing script sequences defensively
    OUTPUT.write_text(payload.replace('</','<\\/'), encoding='utf-8')
    print(f'Wrote {len(items)} news records to {OUTPUT}')

if __name__=='__main__': main()
