"use client";

import { useEffect, useMemo, useState } from "react";

type View = "Today" | "Needs attention" | "Inbox" | "Calendar" | "Projects" | "Documents";
type Item = {
  id: string; title: string; summary: string; source: string; sourceType: "Email"|"Calendar"|"Document"|"Project"|"Google";
  priority: "High"|"Medium"|"Low"; category?: string; due: string; view: View; reason?: string; status?: string;
};

const demoItems: Item[] = [
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

const API_BASE = process.env.NEXT_PUBLIC_LIFE_API_URL || "https://life-production-fd51.up.railway.app";

export default function LifePage() {
  const [items,setItems] = useState<Item[]>(demoItems);
  const [live,setLive] = useState(false);
  const [authChecked,setAuthChecked] = useState(false);
  const [userEmail,setUserEmail] = useState("");
  const [syncing,setSyncing] = useState(false);
  const [summary,setSummary] = useState("");
  const [view,setView] = useState<View>("Today");
  const [selected,setSelected] = useState<Item|null>(null);
  const [settingsOpen,setSettingsOpen] = useState(false);
  const [showAll,setShowAll] = useState(false);
  const [editTitle,setEditTitle] = useState("");
  const [editCategory,setEditCategory] = useState("");
  const [done,setDone] = useState<string[]>([]);
  const [query,setQuery] = useState("");
  const [focus,setFocus] = useState(false);
  const [notice,setNotice] = useState("");
  const [seconds,setSeconds] = useState(25*60);
  const [running,setRunning] = useState(false);
  const refreshLive=async()=>{
    if(!API_BASE) return;
    try{
      const d=new Date().toISOString().slice(0,10);
      const r=await fetch(API_BASE+"/obligations?date="+d,{credentials:"include"});
      if(r.ok){
        const data=await r.json();
        if(Array.isArray(data)){
          setItems(data.map((x:any)=>({id:x.id,title:x.title,summary:x.summary||"",source:x.sender||"Google",sourceType:"Google",priority:x.priority==="high"?"High":x.priority==="low"?"Low":"Medium",category:x.category||"other",due:x.due_at?new Date(x.due_at).toLocaleString():"No due date",view:x.priority==="high"?"Needs attention":"Today",reason:x.classification_reason,status:x.status})));
        }
      }
      const summaryResponse=await fetch(API_BASE+"/summaries/today",{credentials:"include"});
      if(summaryResponse.ok){
        const summaryData=await summaryResponse.json();
        if(summaryData?.content) setSummary(summaryData.content);
      }
    }catch{}
  };

  useEffect(()=>{
    if(!API_BASE) { setAuthChecked(true); return; }
    const load=async()=>{
      try{
        const statusResponse=await fetch(API_BASE+"/auth/status",{credentials:"include"});
        const auth=await statusResponse.json();
        const connected=new URLSearchParams(window.location.search).get("connected")==="1";
        if(connected){
          await Promise.allSettled([
            fetch(API_BASE+"/sources/gmail/sync",{method:"POST",credentials:"include"}),
            fetch(API_BASE+"/sources/calendar/sync",{method:"POST",credentials:"include"})
          ]);
          window.history.replaceState({},"",window.location.pathname);
        }
        if(auth?.authenticated && auth?.google_connected || connected){
          setLive(true);
          if(auth?.user?.email) setUserEmail(auth.user.email);
          await refreshLive();
        }
      }catch{}
      finally{setAuthChecked(true);}
    };
    load();
  },[]);

  useEffect(()=>{
    if(!live || !API_BASE) return;
    const t=setInterval(async()=>{
      await Promise.allSettled([
        fetch(API_BASE+"/sources/gmail/sync",{method:"POST",credentials:"include"}),
        fetch(API_BASE+"/sources/calendar/sync",{method:"POST",credentials:"include"})
      ]);
      await refreshLive();
    },15*60*1000);
    return ()=>clearInterval(t);
  },[live]);
  useEffect(()=>{ if(!running) return; const t=setInterval(()=>setSeconds(s=>{if(s<=1){setRunning(false);return 0} return s-1}),1000); return ()=>clearInterval(t)},[running]);
  const timerLabel=`${String(Math.floor(seconds/60)).padStart(2,"0")}:${String(seconds%60).padStart(2,"0")}`;

  const effectiveDone = [...done,...items.filter(x=>x.status==="done"||x.status==="dismissed").map(x=>x.id)];
  const attention = items.filter(x=>x.view==="Needs attention" && !effectiveDone.includes(x.id));
  const visible = useMemo(()=>{
    let list: Item[];
    if(view==="Today") list = items.filter(x=>["Needs attention","Calendar"].includes(x.view) && !effectiveDone.includes(x.id));
    else if(view==="Needs attention") list = attention;
    else list = items.filter(x=>x.view===view && !effectiveDone.includes(x.id));
    const q=query.toLowerCase().trim();
    const filtered = q ? list.filter(x=>(x.title+" "+x.summary+" "+x.source).toLowerCase().includes(q)) : list;
    return view==="Today" && !showAll ? filtered.slice(0,5) : filtered;
  },[items,view,query,done,showAll]);

  const notify=(s:string)=>{setNotice(s);setTimeout(()=>setNotice(""),2200)};
  const syncNow=async()=>{if(!live||syncing)return;setSyncing(true);try{await Promise.allSettled([api("/sources/gmail/sync",{method:"POST"}),api("/sources/calendar/sync",{method:"POST"})]);await refreshLive();notify("Synced just now")}finally{setSyncing(false)}};
  const api=async(path:string,init?:RequestInit)=>fetch(API_BASE+path,{...init,credentials:"include",headers:{"Content-Type":"application/json",...(init?.headers||{})}});
  const persist=async(id:string,patch:Record<string,string>)=>{
    if(!API_BASE){notify("Live API is not configured");return false}
    try{const r=await api("/obligations/"+id,{method:"PATCH",body:JSON.stringify(patch)});if(!r.ok) throw new Error(); return true}catch{notify("Connect Google first to save changes");return false}
  };
  const confirmItem=async(id:string)=>{if(await persist(id,{status:"done"})){setDone(x=>x.includes(id)?x:[...x,id]);notify("Confirmed");setSelected(null)}};
  const dismissItem=async(id:string)=>{if(await persist(id,{status:"dismissed"})){setDone(x=>x.includes(id)?x:[...x,id]);notify("Dismissed");setSelected(null)}};
  const correctItem=async(id:string)=>{const patch:Record<string,string>={};if(editCategory)patch.category=editCategory;if(editTitle.trim())patch.title=editTitle.trim();if(!Object.keys(patch).length){notify("Choose a correction first");return}if(await persist(id,patch)){setItems(xs=>xs.map(x=>x.id===id?{...x,...(editTitle.trim()?{title:editTitle.trim()}:{}),...(editCategory?{category:editCategory,reason:"User corrected classification to "+editCategory}: {})}:x));notify("Correction saved");setSelected(null)}};
  const openSettings=()=>setSettingsOpen(true);
  const exportData=async()=>{try{const r=await api("/users/me/export");if(!r.ok)throw new Error();const blob=await r.blob();const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;a.download="life-export.json";a.click();URL.revokeObjectURL(u);notify("Export downloaded")}catch{notify("Connect Google first")}};
  const revokeAccess=async()=>{if(!window.confirm("Revoke Google access and sign out?"))return;try{const r=await api("/auth/revoke",{method:"POST"});if(!r.ok)throw new Error();setLive(false);setItems(demoItems);setDone([]);setSettingsOpen(false);notify("Google access revoked")}catch{notify("Could not revoke access")}};
  const logout=async()=>{try{await api("/auth/logout",{method:"POST"});}finally{setLive(false);setItems(demoItems);setDone([]);setSettingsOpen(false);notify("Signed out")}};
  const deleteAccount=async()=>{if(!window.confirm("Delete your LIFE account and all stored data? This cannot be undone."))return;try{const r=await api("/users/me",{method:"DELETE"});if(!r.ok)throw new Error();setLive(false);setItems(demoItems);setDone([]);setSettingsOpen(false);notify("Account deleted")}catch{notify("Could not delete account")}};
  const connectGoogle=async()=>{
    if(!API_BASE){notify("LIFE API URL is not configured yet");return;}
    try{
      const r=await fetch(API_BASE+"/auth/google/start",{credentials:"include"});
      const d=await r.json();
      if(d.authorization_url) window.location.href=d.authorization_url; else notify("Google OAuth is not configured");
    }catch{notify("Cannot reach LIFE API")}
  };
  const toggle=(id:string)=>setDone(x=>x.includes(id)?x.filter(y=>y!==id):[...x,id]);

  return <main className="life">
    <style>{`
      *{box-sizing:border-box}body{margin:0;background:#f6f7f8;color:#17202a;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,system-ui,sans-serif}
      button,input{font:inherit}.life{min-height:100vh}.shell{width:min(1280px,calc(100% - 28px));margin:auto;padding:18px 0 35px}
      .top{height:48px;display:flex;align-items:center;justify-content:space-between}.brand{font-size:25px;font-weight:850;letter-spacing:-1px}.status{font-size:11px;color:#66737e;background:#e9edf0;padding:7px 10px;border-radius:99px}
      .hero{padding:48px 0 30px}.onboarding{padding:18px 20px;margin-bottom:14px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:#fff}.onboarding h3{margin:0 0 4px;font-size:17px}.onboarding p{margin:0;color:#74808a;font-size:12px;line-height:1.5}.onboarding .actions{display:flex;gap:8px;align-items:center}.eyebrow{font-size:11px;letter-spacing:.14em;font-weight:850;color:#89949d}.hero h1{font-size:clamp(42px,6vw,70px);line-height:.94;letter-spacing:-4px;margin:9px 0 14px}.hero p{max-width:760px;color:#687681;font-size:17px;line-height:1.55;margin:0}
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
      <header className="top"><div className="brand">LIFE</div><div className="status">{live?("PRIVATE · LIVE"+(userEmail?" · "+userEmail:"")):"PRIVATE · DEMO MODE"}</div></header>
      <section className="hero"><div className="eyebrow">GOOD MORNING, ALEŠ</div><h1>Your life.<br/>Under control.</h1><p>LIFE brings together what matters from your inbox, calendar, documents and projects — then shows you what actually needs your attention.</p></section>
      {authChecked && !live && <section className="card onboarding"><div><h3>Connect your Google account</h3><p>Give LIFE read-only access to Gmail and Calendar. Your live obligations will replace the sample data after connection.</p></div><div className="actions"><button className="cta" style={{marginTop:0,whiteSpace:"nowrap"}} onClick={connectGoogle}>Connect Google</button></div></section>}

      <div className="layout">
        <nav className="card nav">
          <h4>Workspace</h4>
          {(["Today","Needs attention","Inbox","Calendar","Projects","Documents"] as View[]).map(v=><button key={v} className={(view===v||(v==="Needs attention"&&view==="Needs attention"))?"active":""} onClick={()=>{setView(v);setShowAll(false)}}>{v==="Needs attention"?<span className="attention">Needs attention <span className="badge">{attention.length}</span></span>:v}</button>)}
          <h4>Tools</h4><button onClick={()=>{setSeconds(25*60);setRunning(false);setFocus(true)}}>Focus mode</button><button onClick={connectGoogle}>{live?"Google connected":"Connect Google"}</button><button onClick={openSettings}>Settings</button>
        </nav>

        <section className="card main">
          <div className="head"><div><h2>{view}</h2><div className="muted">{view==="Today"?(live?"Live data · auto-sync every 15 min":"Your day at a glance"):"Demo data · click any item to explore it"}</div></div><div style={{display:"flex",gap:8,width:"min-content",alignItems:"center"}}>{live&&<button className="secondary" onClick={syncNow} disabled={syncing}>{syncing?"Syncing…":"Sync now"}</button>}<input className="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search LIFE…" /></div></div>
          {view==="Today" && <div className="brief"><b>{live?"Today briefing":"AI briefing · demo"}</b><p>{live && summary ? summary : "I found "+attention.length+" things that need your attention. Two are time-sensitive and one is a financial follow-up. Start with the SIJ contract response."}</p></div>}
          {view==="Calendar" ? <div>{events.map(e=><div className="event" key={e[0]}><div className="time">{e[0]}</div><div><b>{e[1]}</b><span>{e[2]}</span></div></div>)}</div> :
           visible.length===0 ? <div className="muted" style={{padding:"25px 3px"}}>Nothing here in the demo.</div> :
           visible.map(x=>{const isDone=done.includes(x.id);return <div className="item" key={x.id} onClick={()=>{setEditTitle(x.title);setEditCategory("");setSelected(x)}}><button className={"check "+(isDone?"done":"")} onClick={e=>{e.stopPropagation();toggle(x.id)}}>{isDone?"✓":""}</button><div className="itemmain"><div className="itemtop"><div className={"title "+(isDone?"strike":"")}>{x.title}</div><div className="due">{x.due}</div></div><div className="summary">{x.summary}</div><div className="source">{x.source}</div><div className="muted" style={{marginTop:6}}>{x.category||"other"} · {x.reason || "No classification reason available."}</div></div></div>})}
          {view==="Today" && !showAll && visible.length===5 && <button className="secondary" style={{width:"100%",marginTop:10}} onClick={()=>setShowAll(true)}>Show all</button>}
        </section>

        <aside className="card side">
          <h3>Your day</h3>
          <div className="metric"><b>{attention.length}</b><span>things need attention</span></div>
          <div className="metric"><b>{done.length}</b><span>completed in this session</span></div>
          <h3 style={{marginTop:20}}>Calendar</h3>{events.map(e=><div className="event" key={e[0]}><div className="time">{e[0]}</div><div><b>{e[1]}</b><span>{e[2]}</span></div></div>)}
          <button className="cta" onClick={()=>{setSeconds(25*60);setRunning(false);setFocus(true)}}>Start focus session</button>
          <button className="secondary" style={{width:"100%",marginTop:8}} onClick={connectGoogle}>{live?"Google connected":"Connect Google"}</button>
        </aside>
      </div>
      <div style={{textAlign:"center",fontSize:10,color:"#9aa3aa",paddingTop:24}}>LIFE · {live ? "live Google data" : "interactive product demo · sample data only"}</div>
    </div>

    {selected&&<div className="drawer"><button className="close" onClick={()=>setSelected(null)}>×</button><div className="label">{selected.sourceType}</div><h2>{selected.title}</h2><p>{selected.summary}</p><div className="sourcebox"><b>{selected.source}</b><br/><br/>Priority: {selected.priority}<br/>Due: {selected.due}<br/><br/><b>Why LIFE flagged this</b><br/>{selected.reason || "Demo classification reason."}</div><div style={{display:"grid",gap:8,marginTop:14}}><button className="cta" onClick={()=>confirmItem(selected.id)}>Confirm</button><button className="secondary" onClick={()=>dismissItem(selected.id)}>Dismiss</button><div style={{borderTop:"1px solid #edf0f2",paddingTop:12,marginTop:4}}><div className="muted" style={{marginBottom:7}}>Correct classification</div><input className="search" style={{width:"100%"}} value={editTitle} onChange={e=>setEditTitle(e.target.value)} placeholder="Correct title (optional)" /><select className="search" style={{width:"100%",marginTop:7}} value={editCategory} onChange={e=>setEditCategory(e.target.value)}><option value="">Keep category</option><option value="finance">Finance</option><option value="legal">Legal</option><option value="meeting">Meeting</option><option value="task">Task</option><option value="personal">Personal</option></select><button className="secondary" style={{marginTop:7,width:"100%"}} onClick={()=>correctItem(selected.id)}>Save correction</button></div></div></div>}

    {settingsOpen&&<div className="drawer"><button className="close" onClick={()=>setSettingsOpen(false)}>×</button><div className="label">Account</div><h2>Settings</h2><p>Control your Google connection and your LIFE data.</p><div className="sourcebox" style={{marginBottom:12}}><b>Google</b><br/>{live?"Connected":"Not connected"}</div><button className="secondary" style={{width:"100%"}} onClick={exportData}>Export my data</button><button className="secondary" style={{width:"100%",marginTop:8}} onClick={logout}>Sign out</button><button className="secondary" style={{width:"100%",marginTop:8}} onClick={revokeAccess}>Revoke Google access</button><button className="secondary" style={{width:"100%",marginTop:8}} onClick={deleteAccount}>Delete LIFE account</button></div>}

    {focus&&<div className="focus"><div className="focusbox"><div className="eyebrow">FOCUS MODE</div><h2>One thing.</h2><div className="muted">Use this screen to work on the next important item.</div><div className="timer">{timerLabel}</div><div style={{display:"flex",gap:8,justifyContent:"center"}}><button className="secondary" onClick={()=>setRunning(x=>!x)}>{running?"Pause":"Start"}</button><button className="secondary" onClick={()=>{setRunning(false);setSeconds(25*60)}}>Reset</button><button className="secondary" onClick={()=>setFocus(false)}>Exit</button></div></div></div>}
    {notice&&<div className="notice">{notice}</div>}
  </main>;
}
