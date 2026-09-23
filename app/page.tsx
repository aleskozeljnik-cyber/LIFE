"use client";

import { useEffect, useMemo, useState } from "react";

type Section = "Today" | "Inbox" | "Calendar" | "Projects" | "Notes";
type Task = {
  id: string;
  title: string;
  detail: string;
  section: Section;
  priority: "high" | "normal";
  due?: string;
  project?: string;
};

const seed: Task[] = [
  { id: "1", title: "Review today's commitments", detail: "3 items need attention", section: "Today", priority: "high", due: "Today" },
  { id: "2", title: "Follow up on important email", detail: "Action suggested from inbox", section: "Inbox", priority: "high", due: "Today" },
  { id: "3", title: "Prepare for next meeting", detail: "Tomorrow · 09:00", section: "Calendar", priority: "normal", due: "Tomorrow" },
  { id: "4", title: "Energy project review", detail: "Open project · next action needed", section: "Projects", priority: "high", project: "Work" },
  { id: "5", title: "Ideas & things to remember", detail: "Personal notes", section: "Notes", priority: "normal" },
];

const events = [
  { time: "09:00", title: "Daily planning", meta: "Today · Personal" },
  { time: "11:30", title: "Focus block", meta: "Today · 90 min" },
  { time: "15:00", title: "Review & follow-ups", meta: "Today · Personal" },
  { time: "17:30", title: "Family time", meta: "Today · Personal" },
];

const nav: Section[] = ["Today", "Inbox", "Calendar", "Projects", "Notes"];

export default function LifePage() {
  const [section, setSection] = useState<Section>("Today");
  const [tasks, setTasks] = useState<Task[]>(seed);
  const [done, setDone] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [newItem, setNewItem] = useState("");
  const [notice, setNotice] = useState("");
  const [focus, setFocus] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("life-state-v2");
      if (saved) {
        const p = JSON.parse(saved);
        if (Array.isArray(p.tasks)) setTasks(p.tasks);
        if (Array.isArray(p.done)) setDone(p.done);
      }
    } catch {}
  }, []);

  useEffect(() => {
    localStorage.setItem("life-state-v2", JSON.stringify({ tasks, done }));
  }, [tasks, done]);

  const open = tasks.filter(t => !done.includes(t.id));
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return tasks.filter(t => t.section === section && (!q || (t.title + " " + t.detail).toLowerCase().includes(q)));
  }, [tasks, section, query]);

  const notify = (message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 2200);
  };

  const toggle = (id: string) => setDone(x => x.includes(id) ? x.filter(v => v !== id) : [...x, id]);

  const add = () => {
    const title = newItem.trim();
    if (!title) return;
    setTasks(x => [{ id: crypto.randomUUID(), title, detail: "Added to LIFE", section, priority: "normal", due: section === "Today" ? "Today" : undefined }, ...x]);
    setNewItem("");
    notify("Added to LIFE");
  };

  const removeDone = () => {
    const ids = new Set(done);
    setTasks(x => x.filter(t => !ids.has(t.id)));
    setDone([]);
    notify("Completed items cleared");
  };

  return (
    <main className="life">
      <style>{`
        *{box-sizing:border-box}html,body{margin:0;background:#f5f7f9;color:#15202b}
        button,input{font:inherit}.life{min-height:100vh;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,system-ui,sans-serif}
        .shell{width:min(1240px,calc(100% - 28px));margin:auto;padding:18px 0 34px}
        .top{height:52px;display:flex;align-items:center;justify-content:space-between}.brand{font-size:24px;font-weight:850;letter-spacing:-1px}
        .topRight{display:flex;align-items:center;gap:8px}.pill{font-size:11px;font-weight:750;padding:7px 10px;border-radius:99px;background:#e9eef2;color:#5d6a75}
        .iconBtn{border:1px solid #dce2e7;background:#fff;border-radius:10px;padding:8px 10px;cursor:pointer}
        .hero{padding:42px 0 30px}.eyebrow{font-size:11px;letter-spacing:.14em;font-weight:800;color:#7b8791}
        h1{font-size:clamp(42px,6vw,72px);line-height:.94;letter-spacing:-4px;margin:9px 0 16px}.lead{max-width:720px;font-size:17px;line-height:1.55;color:#687681}
        .grid{display:grid;grid-template-columns:190px minmax(0,1fr) 270px;gap:14px;align-items:start}.card{background:#fff;border:1px solid #e1e6eb;border-radius:20px;box-shadow:0 8px 30px rgba(28,43,58,.05)}
        .nav{padding:9px}.nav button{width:100%;border:0;background:transparent;text-align:left;padding:11px 12px;border-radius:11px;color:#697681;font-weight:720;cursor:pointer}.nav button.active{background:#15202b;color:#fff}
        .nav .sep{height:1px;background:#edf0f3;margin:8px 5px}.small{font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:#9aa4ad;padding:9px 12px 5px;font-weight:800}
        .main{padding:18px}.mainHead{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:14px}.mainHead h2{margin:0;font-size:20px}.count{font-size:12px;color:#84909a}
        .tools{display:flex;gap:7px}.search{width:150px;border:1px solid #dce2e7;border-radius:10px;padding:9px 10px;outline:none;background:#fafbfc}.secondary{border:1px solid #dce2e7;background:#fff;border-radius:10px;padding:9px 11px;font-weight:700;cursor:pointer}
        .task{display:flex;gap:12px;padding:15px 4px;border-top:1px solid #edf0f3}.check{width:25px;height:25px;flex:0 0 25px;border:1.5px solid #b9c3cb;border-radius:50%;background:#fff;cursor:pointer;display:grid;place-items:center}.check.done{background:#15202b;color:#fff;border-color:#15202b}
        .title{font-weight:750;font-size:14px}.strike{text-decoration:line-through;color:#8a959e}.detail{font-size:12px;color:#7b8791;margin-top:4px;line-height:1.4}.tag{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:#8b5b62;font-weight:850;margin-left:8px}
        .composer{display:flex;gap:7px;margin-top:12px}.composer input{flex:1;min-width:0;border:1px solid #dce2e7;border-radius:10px;padding:11px 12px;outline:none}.primary{border:0;background:#15202b;color:#fff;border-radius:10px;padding:10px 14px;font-weight:750;cursor:pointer}
        .empty{padding:28px 5px;color:#87929c;font-size:13px}.calendar{padding:2px 4px}.event{display:flex;gap:16px;padding:15px 0;border-top:1px solid #edf0f3}.time{width:48px;font-size:12px;color:#77838e;font-weight:800}.event b{font-size:14px}.event span{display:block;color:#7c8791;font-size:12px;margin-top:4px}
        .side{padding:17px}.side h3{margin:1px 0 13px;font-size:15px}.metric{border-top:1px solid #edf0f3;padding:13px 0}.metric:first-of-type{border-top:0}.metric b{display:block;font-size:23px}.metric span{font-size:11px;color:#818c96}
        .connection{border-top:1px solid #edf0f3;padding:12px 0;display:flex;justify-content:space-between;gap:8px;align-items:center}.connection b{font-size:13px}.connection span{display:block;font-size:10px;color:#84909a;margin-top:3px}.connect{border:1px solid #dce2e7;background:#fff;border-radius:9px;padding:7px 9px;font-size:10px;font-weight:800;cursor:pointer}
        .focus{position:fixed;inset:0;background:#f5f7f9;z-index:5;display:grid;place-items:center}.focusBox{text-align:center;width:min(620px,calc(100% - 32px))}.focusBox h2{font-size:64px;letter-spacing:-4px;margin:0 0 12px}.focusBox p{color:#7b8791}.timer{font-size:82px;font-weight:800;letter-spacing:-5px;margin:30px 0}.notice{position:fixed;right:18px;bottom:18px;background:#15202b;color:#fff;padding:11px 14px;border-radius:11px;font-size:12px;box-shadow:0 12px 35px rgba(0,0,0,.18);z-index:10}
        footer{text-align:center;color:#9aa4ad;font-size:10px;padding:25px 0 0}
        @media(max-width:980px){.grid{grid-template-columns:150px minmax(0,1fr)}.side{grid-column:2}.search{width:130px}}@media(max-width:650px){.shell{width:calc(100% - 20px)}.hero{padding:30px 0 22px}h1{letter-spacing:-2.5px}.grid{grid-template-columns:1fr}.nav{display:flex;gap:4px;overflow:auto}.nav button{white-space:nowrap;width:auto}.nav .sep,.small{display:none}.side{grid-column:auto}.mainHead{align-items:flex-start;flex-direction:column}.tools{width:100%}.search{flex:1}.focusBox h2{font-size:46px}.timer{font-size:62px}}
      `}</style>

      <div className="shell">
        <header className="top"><div className="brand">LIFE</div><div className="topRight"><button className="iconBtn" onClick={()=>setFocus(true)}>Focus</button><span className="pill">Private · Personal OS</span></div></header>

        <section className="hero"><div className="eyebrow">GOOD MORNING</div><h1>Your life.<br/>Under control.</h1><div className="lead">One place for what needs your attention — commitments, inbox, calendar, projects and notes.</div></section>

        <div className="grid">
          <nav className="card nav">
            <div className="small">Workspace</div>
            {nav.map(n=><button key={n} className={section===n?"active":""} onClick={()=>setSection(n)}>{n}</button>)}
            <div className="sep"/>
            <button onClick={()=>notify("Automation center coming next")}>Automations</button>
            <button onClick={()=>notify("Settings saved locally")}>Settings</button>
          </nav>

          <section className="card main">
            <div className="mainHead"><div><h2>{section}</h2><div className="count">{section==="Calendar" ? events.length+" events" : visible.filter(t=>!done.includes(t.id)).length+" open"}</div></div><div className="tools"><input className="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search…" />{done.length>0&&<button className="secondary" onClick={removeDone}>Clear done</button>}</div></div>

            {section==="Calendar" ? <div className="calendar">{events.map(e=><div className="event" key={e.time}><div className="time">{e.time}</div><div><b>{e.title}</b><span>{e.meta}</span></div></div>)}</div> :
              visible.length===0 ? <div className="empty">Nothing here yet. Add your first item below.</div> :
              <>{visible.map(t=>{const isDone=done.includes(t.id);return <div className="task" key={t.id}><button className={"check "+(isDone?"done":"")} onClick={()=>toggle(t.id)}>{isDone?"✓":""}</button><div><div className={"title "+(isDone?"strike":"")}>{t.title}{t.priority==="high"&&!isDone&&<span className="tag">Important</span>}</div><div className="detail">{t.detail}{t.due&&" · "+t.due}</div></div></div>})}
              <div className="composer"><input value={newItem} onChange={e=>setNewItem(e.target.value)} onKeyDown={e=>e.key==="Enter"&&add()} placeholder={"Add to "+section.toLowerCase()+"…"} /><button className="primary" onClick={add}>Add</button></div></>}
          </section>

          <aside className="card side">
            <h3>At a glance</h3>
            <div className="metric"><b>{open.length}</b><span>open items</span></div>
            <div className="metric"><b>{done.length}</b><span>completed</span></div>
            <div className="metric"><b>{events.length}</b><span>today's events</span></div>
            <h3 style={{marginTop:20}}>Connections</h3>
            <div className="connection"><div><b>Gmail</b><span>Read-only integration</span></div><button className="connect" onClick={()=>notify("Gmail integration requires connection setup")}>Connect</button></div>
            <div className="connection"><div><b>Calendar</b><span>Read-only integration</span></div><button className="connect" onClick={()=>notify("Calendar integration requires connection setup")}>Connect</button></div>
            <div className="connection"><div><b>Documents</b><span>Local-first</span></div><button className="connect" onClick={()=>setSection("Notes")}>Open</button></div>
          </aside>
        </div>
        <footer>LIFE · standalone · local-first · no EIE dependency</footer>
      </div>

      {focus&&<div className="focus"><div className="focusBox"><div className="eyebrow">FOCUS MODE</div><h2>One thing.</h2><p>Remove distractions and work on the next important item.</p><div className="timer">25:00</div><button className="primary" onClick={()=>setFocus(false)}>Exit focus</button></div></div>}
      {notice&&<div className="notice">{notice}</div>}
    </main>
  );
}
