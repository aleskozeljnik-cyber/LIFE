"use client";

import { useEffect, useMemo, useState } from "react";

type View = "Today" | "Needs attention" | "Inbox" | "Calendar" | "Projects" | "Documents";
type Item = {
  id: string; title: string; summary: string; source: string; sourceType: "Email"|"Calendar"|"Document"|"Project"|"Google";
  priority: "High"|"Medium"|"Low"; category?: string; due: string; view: View; reason?: string; status?: string; nextAction?: string; sourceCount?: number; evidence?: any[]; related_people?: {id:string;name?:string;email?:string}[]; related_projects?: {id:string;name?:string;kind?:string}[];
};

const demoItems: Item[] = [
  {id:"a1",title:"Reply to SIJ — contract comment",summary:"Legal team sent 3 comments. They are waiting for your response before the next contract version.",source:"Gmail · Luka",sourceType:"Email",priority:"High",due:"Today · 16:00",view:"Needs attention",reason:"The email requests a response before the next contract version."},
  {id:"a2",title:"15:00 meeting — prepare 3 decisions",summary:"Energy portfolio meeting. LIFE identified three open decisions from the previous meeting notes.",source:"Calendar · Energy",sourceType:"Calendar",priority:"High",due:"Today · 15:00",view:"Needs attention",reason:"The calendar commitment starts today and has open decisions attached."},
  {id:"a3",title:"Invoice €518k still outstanding",summary:"Invoice was issued 9 days ago and is still marked unpaid in the demo finance documents.",source:"Documents · Finance",sourceType:"Document",priority:"High",due:"Today",view:"Needs attention",reason:"The document contains a high-value unpaid invoice requiring follow-up."},
  {id:"a4",title:"Review TAB BESS performance",summary:"5 MWh / 2 MW asset. Monthly performance pack is ready for review.",source:"Project · TAB Prevalje",sourceType:"Project",priority:"Medium",due:"Tomorrow",view:"Projects",reason:"A performance pack is available and the review is due tomorrow."},
  {id:"a5",title:"Board material — final comments",summary:"Draft board pack has two unresolved comments.",source:"Documents · Board",sourceType:"Document",priority:"Medium",due:"Thu",view:"Documents",reason:"The draft board pack still has unresolved comments."},
  {id:"a6",title:"Follow up with partner",summary:"Waiting for a response after the last commercial discussion.",source:"Gmail · Partner",sourceType:"Email",priority:"Medium",due:"Fri",view:"Inbox",reason:"The thread is waiting for a response after the last commercial discussion."},
  {id:"a7",title:"Daily planning",summary:"Review priorities and protect focus time.",source:"Calendar · Personal",sourceType:"Calendar",priority:"Low",due:"09:00",view:"Calendar",reason:"Calendar entry identified as a personal planning commitment."},
  {id:"a8",title:"Focus block",summary:"Protected deep-work block.",source:"Calendar · Personal",sourceType:"Calendar",priority:"Low",due:"11:30",view:"Calendar",reason:"Calendar entry is a protected work commitment."}
];

const events = [
  ["09:00","Daily planning","Personal"],
  ["11:30","Focus block","90 min"],
  ["15:00","Energy portfolio meeting","3 decisions"],
  ["17:30","Family time","Personal"]
];

const API_BASE = process.env.NEXT_PUBLIC_LIFE_API_URL || "https://life-production-fd51.up.railway.app";
const CONNECT_PROVIDERS = [
  { id: "google", label: "Google", actionLabel: "Connect Google account", description: "LIFE reads Gmail and Google Calendar only. You can revoke access at any time." },
  { id: "microsoft", label: "Microsoft", actionLabel: "Connect Microsoft account", description: "LIFE reads Outlook Mail, Outlook Calendar and Teams chat after Microsoft grants access." }
] as const;

export default function LifePage() {
  const [items,setItems] = useState<Item[]>(demoItems);
  const [live,setLive] = useState(false);
  const [googleConnected,setGoogleConnected] = useState(false);
  const [microsoftConnected,setMicrosoftConnected] = useState(false);
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
  const [syncError,setSyncError] = useState("");
  const [loadingLive,setLoadingLive] = useState(false);
  const [calendarEvents,setCalendarEvents] = useState<any[]>([]);
  const [aiReady,setAiReady] = useState<boolean|null>(null);
  const [seconds,setSeconds] = useState(25*60);
  const [running,setRunning] = useState(false);
  const refreshLive=async()=>{
    if(!API_BASE) return {success:false,obligationsCount:0};
    setLoadingLive(true);
    let obligationsOk=false, summaryOk=false, calendarOk=false, obligationsCount=0;
    try{
      const now=new Date();
      const d=`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,"0")}-${String(now.getDate()).padStart(2,"0")}`;
      const [lifeResponse,obligationResponse,summaryResponse,calendarResponse]=await Promise.all([
        fetch(API_BASE+"/life-items?limit=3",{credentials:"include"}),
        fetch(API_BASE+"/obligations?date="+d,{credentials:"include"}),
        fetch(API_BASE+"/summaries/today",{credentials:"include"}),
        fetch(API_BASE+"/calendar/upcoming?days=14",{credentials:"include"})
      ]);
      obligationsOk=obligationResponse.ok && lifeResponse.ok;
      if(lifeResponse.ok){
        const lifeData=await lifeResponse.json();
        if(Array.isArray(lifeData)){
          obligationsCount=lifeData.length;
          setItems(lifeData.map((x:any)=>{const provider=x.evidence?.[0]?.provider;const dueDate=x.due_at?new Date(x.due_at):null;const hoursAway=dueDate?((dueDate.getTime()-Date.now())/3600000):null;const isCalendar=provider==="calendar";const isNearCalendar=isCalendar && hoursAway!==null && hoursAway<=48;const itemView=isCalendar&&!isNearCalendar?"Calendar":(x.priority==="high"?"Needs attention":"Today");return {id:x.id,title:x.title,summary:x.summary||"",source:x.source_count>1?`${x.source_count} connected sources`:(provider==="gmail"?"Gmail":provider==="calendar"?"Google Calendar":"Google"),sourceType:x.source_count>1?"Google":(provider==="gmail"?"Email":provider==="calendar"?"Calendar":"Google"),priority:x.priority==="high"?"High":x.priority==="low"?"Low":"Medium",category:x.category||"other",due:dueDate?dueDate.toLocaleString([], {dateStyle:"medium",timeStyle:"short"}):"No due date",view:itemView,reason:x.next_action||"LIFE found a connected commitment that may need your attention.",nextAction:x.next_action,status:x.status,sourceCount:x.source_count,evidence:x.evidence||[],related_people:x.related_people||[],related_projects:x.related_projects||[]};}));
          {const priorities=lifeData.filter((x:any)=>x.priority==="high").slice(0,3);setSummary(priorities.length?priorities.map((x:any)=>`${x.title} — ${x.next_action||"Odloči naslednji korak."}`).join(" · "):"Danes ni zaznane nujne obveznosti. LIFE spremlja tvoje povezane vire.");}
        }
      } else if(obligationResponse.ok){
        const data=await obligationResponse.json();
        if(Array.isArray(data)){
          obligationsCount=data.length;
          setItems(data.map((x:any)=>{const provider=x.provider||"google";return {id:x.id,title:x.title,summary:x.summary||"",source:x.sender||provider.charAt(0).toUpperCase()+provider.slice(1),sourceType:provider==="gmail"?"Email":provider==="calendar"?"Calendar":"Google",priority:x.priority==="high"?"High":x.priority==="low"?"Low":"Medium",category:x.category||"other",due:x.due_at?new Date(x.due_at).toLocaleString():"No due date",view:x.priority==="high"?"Needs attention":"Today",reason:x.classification_reason,status:x.status};}));
        }
      }
      summaryOk=summaryResponse.ok;
      if(summaryResponse.ok){
        const summaryData=await summaryResponse.json();
        // Do not overwrite the LIFE intelligence briefing with the legacy raw-mail summary.
        // The /life-items response is the source of truth for the live Today briefing.
        if(!lifeResponse.ok && summaryData?.content) setSummary(summaryData.content);
      }
      calendarOk=calendarResponse.ok;
      if(calendarResponse.ok){
        const eventsData=await calendarResponse.json();
        setCalendarEvents(Array.isArray(eventsData)?eventsData:[]);
      }
      const success=lifeResponse.ok && summaryOk && calendarOk;
      const privacyBlocked=[lifeResponse,summaryResponse,calendarResponse].some(r=>r.status===503) || !obligationsOk;
      setSyncError(success ? "" : privacyBlocked ? "Google source reading is blocked until LIFE AI privacy setup is complete." : "Some Google data could not be refreshed. Try Sync now.");
      return {success,obligationsCount};
    }catch{
      setSyncError("LIFE could not refresh Google data. Please retry.");
      return {success:false,obligationsCount};
    }finally{
      setLoadingLive(false);
    }
  };

  useEffect(()=>{
    if(!API_BASE) { setAuthChecked(true); return; }
    const load=async()=>{
      try{
        const [statusResponse,healthResponse]=await Promise.all([
          fetch(API_BASE+"/auth/status",{credentials:"include"}),
          fetch(API_BASE+"/health",{credentials:"include"})
        ]);
        const auth=await statusResponse.json();
        const health=await healthResponse.json().catch(()=>({}));
        setAiReady(health?.ai_data_usage==="not_used_for_training");
        const connectedProvider=new URLSearchParams(window.location.search).get("connected");
        const connected=connectedProvider==="1" || connectedProvider==="microsoft";
        setGoogleConnected(Boolean(auth?.google_connected));
        setMicrosoftConnected(Boolean(auth?.microsoft_connected));
        if(connectedProvider==="1"){
          await Promise.allSettled([
            fetch(API_BASE+"/sources/gmail/sync",{method:"POST",credentials:"include"}),
            fetch(API_BASE+"/sources/calendar/sync",{method:"POST",credentials:"include"})
          ]);
        }
        if(connectedProvider==="microsoft"){
          await Promise.allSettled([
            fetch(API_BASE+"/sources/outlook-mail/sync",{method:"POST",credentials:"include"}),
            fetch(API_BASE+"/sources/outlook-calendar/sync",{method:"POST",credentials:"include"}),
            fetch(API_BASE+"/sources/teams/sync",{method:"POST",credentials:"include"})
          ]);
          window.history.replaceState({},"",window.location.pathname);
        }
        if(auth?.authenticated && auth?.google_connected && !connected){
          const sourcesResponse=await fetch(API_BASE+"/sources",{credentials:"include"});
          const sources=await sourcesResponse.json().catch(()=>[]);
          const providers=new Set(Array.isArray(sources)?sources.map((s:any)=>s?.provider):[]);
          const missing=[];
          if(!providers.has("gmail")) missing.push("gmail");
          if(!providers.has("calendar")) missing.push("calendar");
          if(missing.length){
            await Promise.allSettled(missing.map(provider=>fetch(API_BASE+"/sources/"+provider+"/sync",{method:"POST",credentials:"include"})));
          }
        }
        if((auth?.authenticated && (auth?.google_connected || auth?.microsoft_connected)) || connected){
          setLive(true);
          setItems([]);
          setCalendarEvents([]);
          if(auth?.user?.email) setUserEmail(auth.user.email);
          const refreshed=await refreshLive();
          await telemetry("app_opened");
          if(connected && refreshed.success){
            await telemetry("authorization_first_live");
          }
          if(connected){
            const started=Number(sessionStorage.getItem("life_connect_started_at")||0);
            const elapsed=started?Math.max(0,Math.round((Date.now()-started)/1000)):0;
            sessionStorage.removeItem("life_connect_started_at");
            setNotice(refreshed.success?(elapsed?("First live Today loaded in "+elapsed+"s"):(connectedProvider==="microsoft"?"Microsoft connected":"Google connected")):(connectedProvider==="microsoft"?"Microsoft connected, but live data needs another refresh.":"Google connected, but live data needs another refresh."));
          }
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
    if(view==="Today") list = items.filter(x=>["Needs attention","Today","Calendar"].includes(x.view) && !effectiveDone.includes(x.id));
    else if(view==="Needs attention") list = attention;
    else list = items.filter(x=>x.view===view && !effectiveDone.includes(x.id));
    const q=query.toLowerCase().trim();
    const filtered = q ? list.filter(x=>(x.title+" "+x.summary+" "+x.source).toLowerCase().includes(q)) : list;
    return view==="Today" && !showAll ? filtered.slice(0,5) : filtered;
  },[items,view,query,done,showAll,live]);

  const notify=(s:string)=>{setNotice(s);setTimeout(()=>setNotice(""),2200)};
  const syncNow=async()=>{if(!live||syncing)return;setSyncing(true);setSyncError("");try{const requests=[];if(googleConnected){requests.push(api("/sources/gmail/sync",{method:"POST"}),api("/sources/calendar/sync",{method:"POST"}));}if(microsoftConnected){requests.push(api("/sources/outlook-mail/sync",{method:"POST"}),api("/sources/outlook-calendar/sync",{method:"POST"}),api("/sources/teams/sync",{method:"POST"}));}const results=await Promise.all(requests);const blocked=results.some(r=>r.status===503);if(blocked){throw new Error("privacy gate")}if(results.some(r=>!r.ok)) throw new Error("sync failed");const refreshed=await refreshLive();refreshed.success?notify("Synced just now"):notify("Sync completed with warnings")}catch(error){const message=error instanceof Error&&error.message==="privacy gate"?"Google source reading is blocked until LIFE AI privacy setup is complete.":"Google sync failed. Please retry.";setSyncError(message);notify(error instanceof Error&&error.message==="privacy gate"?"AI setup required":"Sync failed")}finally{setSyncing(false)}};
  const api=async(path:string,init?:RequestInit)=>fetch(API_BASE+path,{...init,credentials:"include",headers:{"Content-Type":"application/json",...(init?.headers||{})}});
  const telemetry=async(action:string,metadata:Record<string,string|number|boolean>={})=>{
    if(!API_BASE) return;
    try{await api("/telemetry",{method:"POST",body:JSON.stringify({action,metadata})});}catch{}
  };
  const persist=async(id:string,patch:Record<string,string>)=>{
    if(!API_BASE){notify("Live API is not configured");return false}
    try{const r=await api("/obligations/"+id,{method:"PATCH",body:JSON.stringify(patch)});if(!r.ok) throw new Error(); return true}catch{notify("Connect Google first to save changes");return false}
  };
  const confirmItem=async(id:string)=>{if(await persist(id,{status:"done"})){setDone(x=>x.includes(id)?x:[...x,id]);notify("Confirmed");setSelected(null)}};
  const dismissItem=async(id:string)=>{if(await persist(id,{status:"dismissed"})){setDone(x=>x.includes(id)?x:[...x,id]);notify("Dismissed");setSelected(null)}};
  const correctItem=async(id:string)=>{const patch:Record<string,string>={};if(editCategory)patch.category=editCategory;if(editTitle.trim())patch.title=editTitle.trim();if(!Object.keys(patch).length){notify("Choose a correction first");return}if(await persist(id,patch)){await telemetry("obligation_corrected",{obligation_id:id});setItems(xs=>xs.map(x=>x.id===id?{...x,...(editTitle.trim()?{title:editTitle.trim()}:{}),...(editCategory?{category:editCategory,reason:"User corrected classification to "+editCategory}: {})}:x));notify("Correction saved");setSelected(null)}};
  const openSettings=()=>setSettingsOpen(true);
  const exportData=async()=>{try{const r=await api("/users/me/export");if(!r.ok)throw new Error();const blob=await r.blob();const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;a.download="life-export.json";a.click();URL.revokeObjectURL(u);notify("Export downloaded")}catch{notify("Connect Google first")}};
  const revokeAccess=async()=>{if(!window.confirm("Revoke Google access and sign out?"))return;try{const r=await api("/auth/revoke",{method:"POST"});if(!r.ok)throw new Error();setLive(false);setItems(demoItems);setDone([]);setSettingsOpen(false);notify("Google access revoked")}catch{notify("Could not revoke access")}};
  const logout=async()=>{try{await api("/auth/logout",{method:"POST"});}finally{setLive(false);setItems(demoItems);setDone([]);setSettingsOpen(false);notify("Signed out")}};
  const deleteAccount=async()=>{if(!window.confirm("Delete your LIFE account and all stored data? This cannot be undone."))return;try{const r=await api("/users/me",{method:"DELETE"});if(!r.ok)throw new Error();setLive(false);setItems(demoItems);setDone([]);setSettingsOpen(false);notify("Account deleted")}catch{notify("Could not delete account")}};
  const connectProvider=async(providerId:string)=>{
    if(!API_BASE){notify("LIFE API URL is not configured yet");return;}
    sessionStorage.setItem("life_connect_started_at", String(Date.now()));
    try{
      const healthResponse=await fetch(API_BASE+"/health",{credentials:"include"});
      const health=await healthResponse.json().catch(()=>({}));
      if(providerId==="google" && health.ai_data_usage !== "not_used_for_training"){
        sessionStorage.removeItem("life_connect_started_at");
        notify("LIFE AI processing is not ready yet. Configure Cloudflare Workers AI first.");
        return;
      }
      // OAuth start is a browser redirect endpoint, not a JSON API. Navigating directly
      // preserves the Google redirect and the OAuth state cookie set by the backend.
      window.location.assign(API_BASE+"/auth/"+providerId+"/start");
    }catch{
      sessionStorage.removeItem("life_connect_started_at");
      notify("Cannot reach LIFE API");
    }
  };
  const connectGoogle=()=>connectProvider("google");
  const toggle=(id:string)=>{
    if(live){
      void confirmItem(id);
      return;
    }
    setDone(x=>x.includes(id)?x.filter(y=>y!==id):[...x,id]);
  };

  return <main className="life">
    <style>{`
      :root{--ink:#17211d;--muted:#7d8781;--line:#e4e8e2;--paper:#fcfdf9;--soft:#f1f4ef;--accent:#173b2d;--green:#5d8f70;--green-soft:#e5efe7;--amber:#b47a3c;--amber-soft:#fbf0e1;--red:#a6534b;--red-soft:#f8e9e7}
      *{box-sizing:border-box}
      html{background:#eef1ed}
      body{margin:0;background:radial-gradient(circle at 78% -8%,#fbfdf8 0,#eef2ed 45%,#e8ede8 100%);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,ui-sans-serif,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
      button,input,select{font:inherit}
      button{transition:transform .16s ease,background .16s ease,border-color .16s ease,box-shadow .16s ease}
      button:active{transform:scale(.98)}
      .life{min-height:100vh}.shell{width:min(1380px,calc(100% - 48px));margin:auto;padding:22px 0 42px}
      .top{height:42px;display:flex;align-items:center;justify-content:space-between}.brand{font-size:20px;font-weight:900;letter-spacing:-.9px}.status{font-size:10px;letter-spacing:.07em;color:#777f86;background:rgba(255,255,255,.7);border:1px solid #e4e4e0;padding:8px 12px;border-radius:99px;backdrop-filter:blur(12px)}
      .hero{padding:64px 0 42px;display:flex;justify-content:space-between;align-items:flex-end;gap:40px}.hero>div:first-child{max-width:800px}.eyebrow{font-size:10px;letter-spacing:.18em;font-weight:850;color:#92958f;text-transform:uppercase}.hero h1{font-size:clamp(52px,7vw,88px);line-height:.9;letter-spacing:-6px;margin:12px 0 20px;font-weight:850}.hero p{max-width:690px;color:#737a78;font-size:16px;line-height:1.65;margin:0}.hero:after{content:"";width:190px;height:190px;border-radius:50%;background:radial-gradient(circle at 38% 38%,#dfe8dc 0,#edf1e9 34%,transparent 70%);opacity:.85}.heroPulse{width:170px;height:170px;border-radius:50%;border:1px solid #dfe3dc;display:grid;place-items:center;position:relative;background:radial-gradient(circle,#f8faf5,#eef1eb 62%,transparent 63%);margin-bottom:4px}.heroPulse:before{content:"";position:absolute;inset:15px;border:1px solid #dfe3dc;border-radius:50%}.heroPulse span{width:10px;height:10px;border-radius:50%;background:var(--green);box-shadow:0 0 0 8px rgba(93,143,112,.10),0 0 28px rgba(93,143,112,.18)}.heroPulse small{position:absolute;bottom:33px;font-size:8px;letter-spacing:.18em;color:#89958b;font-weight:850}
      .onboarding{padding:20px 22px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;gap:18px;background:rgba(255,255,255,.78);border:1px solid var(--line);border-radius:22px;box-shadow:0 18px 50px rgba(30,35,30,.05);backdrop-filter:blur(18px)}.onboarding h3{margin:0 0 5px;font-size:16px}.onboarding p{margin:0;color:#7c837f;font-size:12px;line-height:1.5}.onboarding .actions{display:flex;gap:8px}
      .layout{display:grid;grid-template-columns:205px minmax(0,1fr) 300px;gap:18px;align-items:start}.card{background:rgba(255,255,255,.82);border:1px solid rgba(225,225,220,.9);border-radius:26px;box-shadow:0 20px 70px rgba(31,35,30,.055);backdrop-filter:blur(18px)}
      .nav{padding:12px;position:sticky;top:18px}.nav h4{margin:10px 10px 7px;font-size:9px;color:#a2a59f;text-transform:uppercase;letter-spacing:.16em}.nav button{width:100%;border:0;background:transparent;text-align:left;padding:11px 12px;border-radius:12px;color:#777f7c;font-size:12px;font-weight:720;cursor:pointer}.nav button:hover{background:#f1f1ed;color:#262a29}.nav button.active{background:var(--accent);color:#fff;box-shadow:0 8px 22px rgba(23,59,45,.16)}.nav .attention{display:flex;justify-content:space-between;align-items:center}.badge{font-size:9px;background:#eceeea;color:#5f665f;padding:3px 6px;border-radius:99px}.nav .active .badge{background:#3b413d;color:#fff}
      .main{padding:25px;min-height:620px}.head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:22px}.head h2{font-size:27px;letter-spacing:-1.4px;margin:0 0 4px}.muted{font-size:11px;color:#929995}.search{width:190px;border:1px solid #dedfdb;border-radius:12px;padding:10px 12px;outline:none;background:#fafaf7;color:#222}.search:focus{border-color:#b9bcb6;box-shadow:0 0 0 3px rgba(0,0,0,.04)}
      .briefTop{display:flex;align-items:center;justify-content:space-between;gap:12px}.briefTop span{font-size:9px;color:#8a9089;letter-spacing:.08em;text-transform:uppercase}.brief{position:relative;border:1px solid #dfe7df;background:linear-gradient(135deg,#f4f8f2,#edf3ed);border-radius:18px;padding:17px 19px;margin-bottom:12px;overflow:hidden}.brief:after{content:"";position:absolute;right:-30px;top:-40px;width:130px;height:130px;border-radius:50%;background:#e4e9df;opacity:.55}.brief b{position:relative;z-index:1;font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:#737a73}.brief p{position:relative;z-index:1;margin:7px 0 0;font-size:13px;line-height:1.6;color:#515854;max-width:850px}
      .item{display:flex;gap:14px;padding:17px 5px;border-top:1px solid #ecece8;cursor:pointer;border-radius:14px}.item:hover{background:#f7faf6}.check{width:23px;height:23px;flex:0 0 23px;border:1.5px solid #b9beb8;border-radius:50%;background:transparent;display:grid;place-items:center;cursor:pointer;margin-top:1px}.check.done{background:#191c1a;color:#fff;border-color:#191c1a}.itemmain{min-width:0;flex:1}.itemtop{display:flex;justify-content:space-between;gap:12px}.title{font-size:14px;font-weight:760;letter-spacing:-.15px}.strike{text-decoration:line-through;color:#9da29e}.due{font-size:10px;color:#8b918c;white-space:nowrap;padding-top:2px}.summary{font-size:12px;color:#858b87;margin-top:5px;line-height:1.45;max-width:760px}.actionline{display:flex;align-items:flex-start;gap:7px;margin-top:9px;color:#496453;font-size:11px;line-height:1.45;font-weight:650}.actionline:before{content:"→";color:var(--green);font-weight:900}.source{font-size:9px;color:#64806c;margin-top:8px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}
      .side{padding:21px}.wellbeing{display:flex;align-items:center;gap:13px;padding-bottom:16px;margin-bottom:7px;border-bottom:1px solid #ecece8}.wellbeing h3{margin:0 0 4px}.wellbeing p{margin:0;color:#909691;font-size:10px}.ring{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(#809a82 35%,#e8ebe6 0);position:relative;flex:0 0 58px}.ring:after{content:"";position:absolute;inset:5px;background:#fffefa;border-radius:50%}.ring span{position:relative;z-index:1;font-size:18px;font-weight:850;letter-spacing:-1px}.side h3{font-size:12px;text-transform:uppercase;letter-spacing:.13em;color:#8b908b;margin:2px 0 13px}.metric{padding:15px 0;border-top:1px solid #ecece8}.metric:first-of-type{border-top:0}.metric b{font-size:34px;line-height:1;letter-spacing:-2px;display:block}.metric span{font-size:10px;color:#929995;display:block;margin-top:5px}.event{display:flex;gap:13px;padding:12px 0;border-top:1px solid #ecece8}.time{width:45px;font-size:10px;font-weight:850;color:#8a908b;padding-top:1px}.event b{font-size:12px;font-weight:720}.event span{display:block;color:#989d99;font-size:10px;margin-top:3px}
      .cta{width:100%;border:0;background:#171918;color:#fff;border-radius:12px;padding:12px;margin-top:14px;font-weight:760;font-size:12px;cursor:pointer;box-shadow:0 9px 25px rgba(0,0,0,.11)}.cta:hover{background:#292d2a;box-shadow:0 12px 28px rgba(0,0,0,.15)}.secondary{border:1px solid #dedfdb;background:rgba(255,255,255,.75);border-radius:11px;padding:9px 11px;font-size:11px;font-weight:720;cursor:pointer;color:#4e5551}.secondary:hover{background:#f5f5f1;border-color:#cfd1cc}
      .drawer{position:fixed;right:18px;top:18px;bottom:18px;width:min(460px,calc(100% - 36px));background:#fbfdf9;border:1px solid #dddeda;border-radius:27px;box-shadow:0 30px 100px rgba(0,0,0,.2);z-index:10;padding:25px;overflow:auto}.close{float:right;border:0;background:#f0f1ed;border-radius:50%;width:34px;height:34px;cursor:pointer;color:#555}.drawer .label{font-size:9px;text-transform:uppercase;letter-spacing:.15em;color:#929791;font-weight:850;margin-top:30px}.drawer h2{font-size:29px;letter-spacing:-1.5px;margin:10px 0}.drawer p{color:#6f7772;line-height:1.65;font-size:13px}.sourcebox{background:#f4f4ef;border:1px solid #e7e7e1;border-radius:15px;padding:14px;margin-top:16px;font-size:11px;color:#69716c}
      .focus{position:fixed;inset:0;background:#f1f0eb;z-index:20;display:grid;place-items:center}.focusbox{text-align:center}.focusbox h2{font-size:70px;letter-spacing:-5px;margin:0}.timer{font-size:100px;font-weight:850;letter-spacing:-7px;margin:25px 0}.notice{position:fixed;right:20px;bottom:20px;background:var(--accent);color:white;padding:12px 16px;border-radius:13px;font-size:11px;z-index:30;box-shadow:0 12px 30px rgba(0,0,0,.18)}
      .loadingbar{margin:-6px 0 13px;background:#f0f1ed;border-radius:10px;padding:9px 11px;font-size:10px;color:#6e756f}.errorbar{display:flex;justify-content:space-between;align-items:center;gap:10px;margin:-6px 0 13px;background:#fbf2ed;border:1px solid #ecd9ce;border-radius:12px;padding:10px 11px;font-size:10px;color:#835d4d}.errorbar .secondary{padding:6px 9px;white-space:nowrap}
      .heroPulse{flex:0 0 170px}@media(max-width:1050px){.layout{grid-template-columns:180px minmax(0,1fr)}.side{grid-column:2}.hero:after{display:none}}@media(max-width:700px){.shell{width:calc(100% - 20px)}.hero{padding:42px 0 28px}.hero h1{font-size:52px;letter-spacing:-4px}.layout{grid-template-columns:1fr}.nav{position:static;display:flex;overflow:auto;gap:3px;padding:7px}.nav h4{display:none}.nav button{white-space:nowrap;width:auto}.side{grid-column:auto}.head{flex-direction:column}.search{width:100%}.itemtop{flex-direction:column;gap:4px}.due{white-space:normal}.main{padding:18px}.side{padding:18px}}
    `}</style>

    <div className="shell">
      <header className="top"><div className="brand">LIFE</div><div className="status">{live?("PRIVATE · LIVE"+(userEmail?" · "+userEmail:"")):"PRIVATE · DEMO MODE"}</div></header>
      <section className="hero"><div><div className="eyebrow">YOUR DAY · PERSONAL OS</div><h1>Good morning,<br/>Aleš.</h1><p>LIFE quietly brings together your commitments, conversations and plans — then helps you see what matters now.</p></div><div className="heroPulse"><span></span><small>{live?"LIVE":"DEMO"}</small></div></section>
      {authChecked && !live && aiReady===false && <section className="card onboarding"><div><h3>Live source access is waiting for AI privacy setup</h3><p>Google Gmail and Calendar remain blocked until LIFE has a configured AI provider with verified no-training use. Demo mode stays available meanwhile.</p></div><button className="secondary" onClick={()=>window.location.reload()}>Check again</button></section>}
      {authChecked && !live && <section className="card onboarding"><div><h3>Connect your sources</h3><p>Your data stays private. LIFE reads only the connected provider data shown below, and you can revoke access at any time.</p><div style={{display:"grid",gap:10,marginTop:14}}>{CONNECT_PROVIDERS.map(provider=><div key={provider.id} className="sourcebox" style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:16}}><div><b>{provider.label}</b><div className="muted" style={{marginTop:4}}>{provider.description}</div></div><button className="cta" style={{marginTop:0,whiteSpace:"nowrap"}} onClick={()=>connectProvider(provider.id)}>{provider.actionLabel}</button></div>)}</div></div></section>}

      <div className="layout">
        <nav className="card nav">
          <h4>Workspace</h4>
          {(["Today","Needs attention","Inbox","Calendar","Projects","Documents"] as View[]).map(v=><button key={v} className={(view===v||(v==="Needs attention"&&view==="Needs attention"))?"active":""} onClick={()=>{setView(v);setShowAll(false)}}>{v==="Needs attention"?<span className="attention">Needs attention <span className="badge">{attention.length}</span></span>:v}</button>)}
          <h4>Tools</h4><button onClick={()=>{setSeconds(25*60);setRunning(false);setFocus(true)}}>Focus mode</button><button onClick={connectGoogle}>{googleConnected?"Google connected":"Connect Google"}</button><button onClick={()=>connectProvider("microsoft")}>{microsoftConnected?"Microsoft connected":"Connect Microsoft"}</button><button onClick={openSettings}>Settings</button>
        </nav>

        <section className="card main">
          {loadingLive && <div className="loadingbar">Refreshing your live data…</div>}
          {syncError && <div className="errorbar">{syncError}<button className="secondary" onClick={syncNow} disabled={syncing}>{syncing?"Retrying…":"Retry"}</button></div>}
          <div className="head"><div><h2>{view}</h2><div className="muted">{view==="Today"?(live?"What matters now · auto-sync every 15 min":"Your day at a glance"):view==="Calendar"?(live?"Upcoming commitments · Google Calendar":"Your calendar"):"Connected information · click any item to explore it"}</div></div><div style={{display:"flex",gap:8,width:"min-content",alignItems:"center"}}>{live&&<button className="secondary" onClick={syncNow} disabled={syncing}>{syncing?"Syncing…":"Sync now"}</button>}<input className="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search LIFE…" /></div></div>
          {view==="Today" && <div className="brief"><div className="briefTop"><b>{live?"FOR YOU TODAY":"A GLIMPSE OF LIFE"}</b><span>{attention.length} {attention.length===1?"priority":"priorities"}</span></div><p>{live ? (summary || "Your day is clear. LIFE is watching your connected sources.") : "A calm view of what deserves your attention — without turning your life into another task list."}</p></div>}
          {view==="Calendar" ? <div>{live ? (calendarEvents.length ? calendarEvents.map((e:any)=><div className="event" key={e.id}><div className="time">{e.start?.dateTime?new Date(e.start.dateTime).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}):"All day"}</div><div><b>{e.summary}</b><span>{e.location || (e.start?.date || "Google Calendar")}</span></div></div>) : <div className="muted" style={{padding:"25px 3px"}}>No upcoming Google Calendar events in the next 14 days.</div>) : events.map(e=><div className="event" key={e[0]}><div className="time">{e[0]}</div><div><b>{e[1]}</b><span>{e[2]}</span></div></div>)}</div> :
           visible.length===0 ? <div className="muted" style={{padding:"25px 3px"}}>{live?"Ni zaznanih nujnih dejanj. LIFE spremlja tvoje povezane vire.":"Nothing here in the demo."}</div> :
           visible.map(x=>{const isDone=done.includes(x.id);return <div className="item" key={x.id} onClick={()=>{setEditTitle(x.title);setEditCategory("");setSelected(x)}}><button className={"check "+(isDone?"done":"")} onClick={e=>{e.stopPropagation();toggle(x.id)}}>{isDone?"✓":""}</button><div className="itemmain"><div className="itemtop"><div className={"title "+(isDone?"strike":"")}>{x.title}</div><div className="due">{x.due}</div></div><div className="summary">{x.summary}</div><div className="source">{x.source}</div><div className="actionline">{x.nextAction || x.reason || "Preglej in določi naslednji korak."}</div></div></div>})}
          {view==="Today" && !showAll && visible.length===5 && <button className="secondary" style={{width:"100%",marginTop:10}} onClick={()=>setShowAll(true)}>Show all</button>}
        </section>

        <aside className="card side">
          <h3>Your day</h3>
          <div className="metric"><b>{attention.length}</b><span>things need attention</span></div>
          <div className="metric"><b>{done.length}</b><span>completed in this session</span></div>
          <h3 style={{marginTop:20}}>Calendar</h3>{live ? (calendarEvents.slice(0,5).map((e:any)=><div className="event" key={e.id}><div className="time">{e.start?.dateTime?new Date(e.start.dateTime).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}):"All day"}</div><div><b>{e.summary}</b><span>{e.location || (e.start?.date || "Google Calendar")}</span></div></div>)) : events.map(e=><div className="event" key={e[0]}><div className="time">{e[0]}</div><div><b>{e[1]}</b><span>{e[2]}</span></div></div>)}
          <button className="cta" onClick={()=>{setSeconds(25*60);setRunning(false);setFocus(true)}}>Start focus session</button>
          <button className="secondary" style={{width:"100%",marginTop:8}} onClick={connectGoogle}>{live?"Google connected":"Connect Google"}</button>
        </aside>
      </div>
      <div style={{textAlign:"center",fontSize:10,color:"#9aa3aa",paddingTop:24}}>LIFE · {live ? "live Google data" : "interactive product demo · sample data only"}</div>
    </div>

    {selected&&<div className="drawer"><button className="close" onClick={()=>setSelected(null)}>×</button><div className="label">{selected.sourceType}</div><h2>{selected.title}</h2><p>{selected.summary}</p><div className="sourcebox"><b>{selected.source}</b><br/><br/>Priority: {selected.priority}<br/>Due: {selected.due}<br/><br/><b>Next action</b><br/>{selected.nextAction || selected.reason || "Review and decide the next step."}<br/><br/><b>Why LIFE flagged this</b><br/>{selected.reason || "Connected information from your sources."}{selected.evidence?.length ? <><br/><br/><b>Evidence</b>{selected.evidence.map((e:any,i:number)=><div key={i} style={{marginTop:6}}>{e.provider} · {e.title}</div>)}</> : null}{selected.related_people?.length ? <><br/><br/><b>Related people</b>{selected.related_people.map((p:any)=><div key={p.id} style={{marginTop:6}}>{p.name || p.email}{p.email && p.name ? ` · ${p.email}` : ""}</div>)}</> : null}{selected.related_projects?.length ? <><br/><br/><b>Related projects</b>{selected.related_projects.map((p:any)=><div key={p.id} style={{marginTop:6}}>{p.name}</div>)}</> : null}</div><div style={{display:"grid",gap:8,marginTop:14}}><button className="cta" onClick={()=>confirmItem(selected.id)}>Confirm</button><button className="secondary" onClick={()=>dismissItem(selected.id)}>Dismiss</button><div style={{borderTop:"1px solid #edf0f2",paddingTop:12,marginTop:4}}><div className="muted" style={{marginBottom:7}}>Correct classification</div><input className="search" style={{width:"100%"}} value={editTitle} onChange={e=>setEditTitle(e.target.value)} placeholder="Correct title (optional)" /><select className="search" style={{width:"100%",marginTop:7}} value={editCategory} onChange={e=>setEditCategory(e.target.value)}><option value="">Keep category</option><option value="financial">Financial</option><option value="work">Work</option><option value="personal">Personal</option><option value="legal">Legal</option><option value="family">Family</option><option value="travel">Travel</option><option value="other">Other</option></select><button className="secondary" style={{marginTop:7,width:"100%"}} onClick={()=>correctItem(selected.id)}>Save correction</button></div></div></div>}

    {settingsOpen&&<div className="drawer"><button className="close" onClick={()=>setSettingsOpen(false)}>×</button><div className="label">Account</div><h2>Settings</h2><p>Control your Google connection and your LIFE data.</p><div className="sourcebox" style={{marginBottom:12}}><b>Google</b><br/>{googleConnected?"Connected":"Not connected"}</div><div className="sourcebox" style={{marginBottom:12}}><b>Microsoft</b><br/>{microsoftConnected?"Connected":"Not connected"}</div><button className="secondary" style={{width:"100%"}} onClick={exportData}>Export my data</button><button className="secondary" style={{width:"100%",marginTop:8}} onClick={logout}>Sign out</button><button className="secondary" style={{width:"100%",marginTop:8}} onClick={revokeAccess}>Revoke Google access</button><button className="secondary" style={{width:"100%",marginTop:8}} onClick={deleteAccount}>Delete LIFE account</button></div>}

    {focus&&<div className="focus"><div className="focusbox"><div className="eyebrow">FOCUS MODE</div><h2>One thing.</h2><div className="muted">Use this screen to work on the next important item.</div><div className="timer">{timerLabel}</div><div style={{display:"flex",gap:8,justifyContent:"center"}}><button className="secondary" onClick={()=>setRunning(x=>!x)}>{running?"Pause":"Start"}</button><button className="secondary" onClick={()=>{setRunning(false);setSeconds(25*60)}}>Reset</button><button className="secondary" onClick={()=>setFocus(false)}>Exit</button></div></div></div>}
    {notice&&<div className="notice">{notice}</div>}
  </main>;
}
