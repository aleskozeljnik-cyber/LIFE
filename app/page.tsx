"use client";

import { useEffect, useMemo, useState } from "react";

type View = "Today" | "Needs attention" | "Inbox" | "Calendar" | "Projects" | "Documents";
type Item = {
  id: string; title: string; summary: string; source: string; sourceType: "Email"|"Calendar"|"Document"|"Project";
  priority: "High"|"Medium"|"Low"; due: string; view: View;
};

const items: Item[] = [
  {id:"a1",title:"Reply to SIJ — contract comment",summary:"Legal team sent 3 comments. They are waiting for your response before the next contract version.",source:"Gmail · Luka",sourceType:"Email",priority:"High",due:"Today · 16:00",view:"Needs attention"},
  {id:"a2",title:"15:00 meeting — prepare 3 decisions",summary:"Energy portfolio meeting. LIFE identified three open decisions from the previous meeting notes.",source:"Calendar · Energy",sourceType:"Calendar",priority:"High",due:"Today · 15:00",view:"Needs attention"},
  {id:"a3",title:"Invoice €518k still outstanding",summary:"Invoice was issued 9 days ago and is still marked unpaid in the demo finance documents.",source:"Documents · Finance",sourceType:"Document",priority:"High",due:"Today",view:"Needs attention"},
  {id:"a4",title:"Review TAB BESS performance",summary:"5 MWh / 2 MW asset. Monthly performance pack is ready for review.",source:"Project · TAB Prevalje",sourceType:"Project",priority:"Medium",due:"Tomorrow",view:"Projects"},
  {id:"a5",title:"Board material — final comments",summary:"Draft board pack has two unresolved comments.",source:"Documents · Board",sourceType:"Document",priority:"Medium",due:"Thu",view:"Documents"},
  {id:"a6",title:"Follow up with partner",summary:"Waiting for a response after the last commercial discussion.",source:"Gmail · Partner",sourceType:"Email",priority:"Medium",due:"Fri",view:"Inbox"},
  {id:"a7",title:"Daily planning",summary:"Review priorities and protect focus time.",source:"Calendar · Personal",sourceType:"Calendar",priority:"Low",due:"09:00",view:"Calendar"},
  {id:"a8",title:"Focus block",summary:"Protected deep-work block.",source:"Calendar · Personal",sourceType:"Calendar",priority:"Low",due:"11:30",view:"Calendar"}
];

const events = [
  ["09:00","Daily planning","Personal"],
  ["11:30","Focus block","90 min"],
  ["15:00","Energy portfolio meeting","3 decisions"],
  ["17:30","Family time","Personal"]
];

export default function LifePage() {
  const [view,setView] = useState<View>("Today");
  const [selected,setSelected] = useState<Item|null>(null);
  const [done,setDone] = useState<string[]>([]);
  const [query,setQuery] = useState("");
  const [focus,setFocus] = useState(false);
  const [notice,setNotice] = useState("");
  const [seconds,setSeconds] = useState(25*60);
  const [running,setRunning] = useState(false);
  useEffect(()=>{ if(!running) return; const t=setInterval(()=>setSeconds(s=>{if(s<=1){setRunning(false);return 0} return s-1}),1000); return ()=>clearInterval(t)},[running]);
  const timerLabel=`${String(Math.floor(seconds/60)).padStart(2,"0")}:${String(seconds%60).padStart(2,"0")}`;

  const attention = items.filter(x=>x.view==="Needs attention" && !done.includes(x.id));
  const visible = useMemo(()=>{
    let list: Item[];
    if(view==="Today") list = items.filter(x=>["Needs attention","Calendar"].includes(x.view));
    else if(view==="Needs attention") list = attention;
    else list = items.filter(x=>x.view===view);
    const q=query.toLowerCase().trim();
    return q ? list.filter(x=>(x.title+" "+x.summary+" "+x.source).toLowerCase().includes(q)) : list;
  },[view,query,done]);

  const notify=(s:string)=>{setNotice(s);setTimeout(()=>setNotice(""),2200)};
  const toggle=(id:string)=>setDone(x=>x.includes(id)?x.filter(y=>y!==id):[...x,id]);

  return <main className="life">
    <style>{`
      *{box-sizing:border-box}body{margin:0;background:#f6f7f8;color:#17202a;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,system-ui,sans-serif}
      button,input{font:inherit}.life{min-height:100vh}.shell{width:min(1280px,calc(100% - 28px));margin:auto;padding:18px 0 35px}
      .top{height:48px;display:flex;align-items:center;justify-content:space-between}.brand{font-size:25px;font-weight:850;letter-spacing:-1px}.status{font-size:11px;color:#66737e;background:#e9edf0;padding:7px 10px;border-radius:99px}
      .hero{padding:48px 0 30px}.eyebrow{font-size:11px;letter-spacing:.14em;font-weight:850;color:#89949d}.hero h1{font-size:clamp(42px,6vw,70px);line-height:.94;letter-spacing:-4px;margin:9px 0 14px}.hero p{max-width:760px;color:#687681;font-size:17px;line-height:1.55;margin:0}
      .layout{display:grid;grid-template-columns:190px minmax(0,1fr) 285px;gap:14px}.card{background:#fff;border:1px solid #e1e5e8;border-radius:20px;box-shadow:0 8px 30px rgba(25,38,50,.045)}
      .nav{padding:9px}.nav h4{margin:8px 12px 5px;font-size:10px;color:#9aa3aa;text-transform:uppercase;letter-spacing:.1em}.nav button{width:100%;border:0;background:transparent;text-align:left;padding:11px 12px;border-radius:10px;color:#64727d;font-weight:720;cursor:pointer}.nav button.active{background:#17202a;color:white}.nav .attention{display:flex;justify-content:space-between}.badge{font-size:10px;background:#eef1f3;padding:3px 6px;border-radius:99px}.nav .active .badge{background:#39434b;color:#fff}
      .main{padding:19px}.head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:16px}.head h2{font-size:21px;margin:0 0 3px}.muted{font-size:12px;color:#89949d}.search{width:180px;border:1px solid #dce1e5;border-radius:10px;padding:9px 11px;outline:none;background:#fafbfc}
      .brief{border:1px solid #e4e8eb;background:#f8fafb;border-radius:14px;padding:14px;margin-bottom:14px}.brief b{font-size:13px}.brief p{margin:5px 0 0;font-size:12px;line-height:1.5;color:#6d7983}
      .item{display:flex;gap:12px;padding:15px 3px;border-top:1px solid #edf0f2;cursor:pointer}.check{width:24px;height:24px;flex:0 0 24px;border:1.5px solid #b9c2c9;border-radius:50%;background:white;display:grid;place-items:center;cursor:pointer}.check.done{background:#17202a;color:white;border-color:#17202a}.itemmain{min-width:0;flex:1}.itemtop{display:flex;justify-content:space-between;gap:10px}.title{font-size:14px;font-weight:760}.strike{text-decoration:line-through;color:#8c969e}.due{font-size:11px;color:#7a8791;white-space:nowrap}.summary{font-size:12px;color:#77848e;margin-top:4px;line-height:1.4}.source{font-size:10px;color:#9a4f58;margin-top:7px;font-weight:750}
      .side{padding:17px}.side h3{font-size:15px;margin:2px 0 12px}.metric{padding:13px 0;border-top:1px solid #edf0f2}.metric:first-of-type{border-top:0}.metric b{font-size:25px;display:block}.metric span{font-size:11px;color:#85919a}.event{display:flex;gap:12px;padding:11px 0;border-top:1px solid #edf0f2}.time{width:42px;font-size:11px;font-weight:800;color:#7b8790}.event b{font-size:12px}.event span{display:block;color:#89949d;font-size:10px;margin-top:3px}
      .cta{width:100%;border:0;background:#17202a;color:#fff;border-radius:10px;padding:11px;margin-top:12px;font-weight:750;cursor:pointer}.secondary{border:1px solid #dce1e5;background:white;border-radius:10px;padding:9px 11px;font-weight:700;cursor:pointer}
      .drawer{position:fixed;right:16px;top:16px;bottom:16px;width:min(430px,calc(100% - 32px));background:white;border:1px solid #dce1e5;border-radius:20px;box-shadow:0 20px 70px rgba(0,0,0,.18);z-index:10;padding:22px;overflow:auto}.close{float:right;border:0;background:#eef1f3;border-radius:50%;width:34px;height:34px;cursor:pointer}.drawer .label{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#909aa3;font-weight:800;margin-top:28px}.drawer h2{font-size:26px;letter-spacing:-1px;margin:9px 0}.drawer p{color:#687681;line-height:1.6;font-size:14px}.sourcebox{background:#f6f8f9;border-radius:12px;padding:13px;margin-top:16px;font-size:12px;color:#687681}.focus{position:fixed;inset:0;background:#f6f7f8;z-index:20;display:grid;place-items:center}.focusbox{text-align:center}.focusbox h2{font-size:62px;letter-spacing:-4px;margin:0}.timer{font-size:80px;font-weight:850;letter-spacing:-5px;margin:24px 0}
      .notice{position:fixed;right:18px;bottom:18px;background:#17202a;color:white;padding:11px 14px;border-radius:11px;font-size:12px;z-index:30}
      @media(max-width:1000px){.layout{grid-template-columns:155px minmax(0,1fr)}.side{grid-column:2}}@media(max-width:680px){.shell{width:calc(100% - 18px)}.hero{padding:32px 0 22px}.hero h1{letter-spacing:-2.5px}.layout{grid-template-columns:1fr}.nav{display:flex;overflow:auto;gap:3px}.nav h4{display:none}.nav button{white-space:nowrap;width:auto}.side{grid-column:auto}.head{flex-direction:column}.search{width:100%}.itemtop{flex-direction:column;gap:4px}.due{white-space:normal}}
    `}</style>

    <div className="shell">
      <header className="top"><div className="brand">LIFE</div><div className="status">PRIVATE · DEMO MODE</div></header>
      <section className="hero"><div className="eyebrow">GOOD MORNING, ALEŠ</div><h1>Your life.<br/>Under control.</h1><p>LIFE brings together what matters from your inbox, calendar, documents and projects — then shows you what actually needs your attention.</p></section>

      <div className="layout">
        <nav className="card nav">
          <h4>Workspace</h4>
          {(["Today","Needs attention","Inbox","Calendar","Projects","Documents"] as View[]).map(v=><button key={v} className={(view===v||(v==="Needs attention"&&view==="Needs attention"))?"active":""} onClick={()=>setView(v)}>{v==="Needs attention"?<span className="attention">Needs attention <span className="badge">{attention.length}</span></span>:v}</button>)}
          <h4>Tools</h4><button onClick={()=>{setSeconds(25*60);setRunning(false);setFocus(true)}}>Focus mode</button><button onClick={()=>notify("Demo settings — integrations are read-only in this demo")}>Settings</button>
        </nav>

        <section className="card main">
          <div className="head"><div><h2>{view}</h2><div className="muted">{view==="Today"?"Your day at a glance":"Demo data · click any item to explore it"}</div></div><input className="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search LIFE…" /></div>
          {view==="Today" && <div className="brief"><b>AI briefing</b><p>I found {attention.length} things that need your attention. Two are time-sensitive and one is a financial follow-up. Start with the SIJ contract response.</p></div>}
          {view==="Calendar" ? <div>{events.map(e=><div className="event" key={e[0]}><div className="time">{e[0]}</div><div><b>{e[1]}</b><span>{e[2]}</span></div></div>)}</div> :
           visible.length===0 ? <div className="muted" style={{padding:"25px 3px"}}>Nothing here in the demo.</div> :
           visible.map(x=>{const isDone=done.includes(x.id);return <div className="item" key={x.id} onClick={()=>setSelected(x)}><button className={"check "+(isDone?"done":"")} onClick={e=>{e.stopPropagation();toggle(x.id)}}>{isDone?"✓":""}</button><div className="itemmain"><div className="itemtop"><div className={"title "+(isDone?"strike":"")}>{x.title}</div><div className="due">{x.due}</div></div><div className="summary">{x.summary}</div><div className="source">{x.source}</div></div></div>})}
        </section>

        <aside className="card side">
          <h3>Your day</h3>
          <div className="metric"><b>{attention.length}</b><span>things need attention</span></div>
          <div className="metric"><b>{done.length}</b><span>completed in this session</span></div>
          <h3 style={{marginTop:20}}>Calendar</h3>{events.map(e=><div className="event" key={e[0]}><div className="time">{e[0]}</div><div><b>{e[1]}</b><span>{e[2]}</span></div></div>)}
          <button className="cta" onClick={()=>{setSeconds(25*60);setRunning(false);setFocus(true)}}>Start focus session</button>
          <button className="secondary" style={{width:"100%",marginTop:8}} onClick={()=>notify("Demo connections: Gmail · Calendar · Documents")}>Connections</button>
        </aside>
      </div>
      <div style={{textAlign:"center",fontSize:10,color:"#9aa3aa",paddingTop:24}}>LIFE · interactive product demo · sample data only · no real accounts connected</div>
    </div>

    {selected&&<div className="drawer"><button className="close" onClick={()=>setSelected(null)}>×</button><div className="label">{selected.sourceType}</div><h2>{selected.title}</h2><p>{selected.summary}</p><div className="sourcebox"><b>{selected.source}</b><br/><br/>Priority: {selected.priority}<br/>Due: {selected.due}</div><button className="cta" onClick={()=>{toggle(selected.id);notify(done.includes(selected.id)?"Marked open":"Marked complete");setSelected(null)}}>{done.includes(selected.id)?"Mark as open":"Mark as complete"}</button></div>}

    {focus&&<div className="focus"><div className="focusbox"><div className="eyebrow">FOCUS MODE</div><h2>One thing.</h2><div className="muted">Use this screen to work on the next important item.</div><div className="timer">{timerLabel}</div><div style={{display:"flex",gap:8,justifyContent:"center"}}><button className="secondary" onClick={()=>setRunning(x=>!x)}>{running?"Pause":"Start"}</button><button className="secondary" onClick={()=>{setRunning(false);setSeconds(25*60)}}>Reset</button><button className="secondary" onClick={()=>setFocus(false)}>Exit</button></div></div></div>}
    {notice&&<div className="notice">{notice}</div>}
  </main>;
}
