import asyncio, datetime, json, os, pathlib, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
import edge_tts

now=datetime.datetime.now(ZoneInfo("Australia/Sydney"))
date=now.strftime("%Y-%m-%d")
out=pathlib.Path("output"); out.mkdir(exist_ok=True)
topics=["Federal Reserve US Treasury yields dollar inflation markets","RBA Australia interest rates AUD FX bonds","Bitcoin BTC ETF institutional flows","Eldorado Gold EGO ELD Skouries production","gold price miners macro"]
sources=[]
for topic in topics:
    url="https://news.google.com/rss/search?q="+urllib.parse.quote(topic)+"&hl=en-AU&gl=AU&ceid=AU:en"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=20) as r: root=ET.fromstring(r.read())
        entries=[{"headline":i.findtext("title"),"published":i.findtext("pubDate"),"link":i.findtext("link")} for i in root.findall(".//item")[:8]]
    except Exception as e:
        print("Feed error",topic,e); entries=[]
    sources.append({"topic":topic,"items":entries})
(out/(date+"-sources.json")).write_text(json.dumps(sources,indent=2))
prompt=f"""Produce an original 950-1100 word, approximately 7-8 minute, engaging spoken financial markets podcast for a sophisticated Sydney-based rates/FX professional for {now.strftime('%A %d %B %Y')}. Discuss overnight macro, Fed/RBA, rates, FX and important upcoming events; Bitcoin with bullish/bearish scenarios; Eldorado Gold (EGO/ELD), Skouries operational risk and gold prices; conclude with an independent portfolio-focused assessment for a patient investor holding Bitcoin and Eldorado with no intention of selling for at least 18 months. Headlines below are leads ONLY, not verified full articles. Never invent prices, market moves, earnings, dates, quotes, or claim to have read articles. Explicitly qualify uncertainty, avoid unsupported specifics, and distinguish fact from analysis. Natural conversational audio prose, no markdown, URLs, bullet points or stage directions. Begin 'Good morning. This is your Morning Macro briefing.' End 'That's your Morning Macro briefing.' Headlines: {json.dumps(sources)[:32000]}"""
payload=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.45,"maxOutputTokens":3500}}).encode()
req=urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",data=payload,headers={"Content-Type":"application/json","x-goog-api-key":os.environ["GEMINI_API_KEY"]},method="POST")
with urllib.request.urlopen(req,timeout=120) as r: response=json.load(r)
script="\n".join(p.get("text","") for p in response["candidates"][0]["content"]["parts"]).strip()
if len(script)<1800: raise RuntimeError("Generated script too short")
(out/(date+"-script.txt")).write_text(script)
async def speak():
    await edge_tts.Communicate(script,voice="en-AU-WilliamNeural",rate="+4%").save(str(out/(date+"-morning-macro.mp3")))
asyncio.run(speak())
print("Produced",date,len(script.split()),"words")
