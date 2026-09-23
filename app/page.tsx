"use client";

import { useEffect, useMemo, useState } from "react";

type Task = { id: string; title: string; detail: string; section: "Today" | "Inbox" | "Calendar"; priority?: "high" | "normal" };

const seed: Task[] = [
  { id: "t1", title: "Review today's commitments", detail: "3 items need attention", section: "Today", priority: "high" },
  { id: "t2", title: "Follow up on important email", detail: "Inbox item · action suggested", section: "Inbox", priority: "high" },
  { id: "t3", title: "Prepare for next meeting", detail: "Calendar · tomorrow 09:00", section: "Calendar" },
];

const events = [
  { time: "09:00", title: "Daily planning", meta: "Today · Personal" },
  { time: "11:30", title: "Focus block", meta: "Today · 90 min" },
  { time: "15:00", title: "Review & follow-ups", meta: "Today · Personal" },
];

export default function LifePage() {
  const [tab, setTab] = useState<"Today" | "Inbox" | "Calendar">("Today");
  const [tasks, setTasks] = useState<Task[]>(seed);
  const [done, setDone] = useState<string[]>([]);
  const [newTask, setNewTask] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("life-state-v1");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed.tasks)) setTasks(parsed.tasks);
        if (Array.isArray(parsed.done)) setDone(parsed.done);
      }
    } catch {}
  }, []);

  useEffect(() => {
    localStorage.setItem("life-state-v1", JSON.stringify({ tasks, done }));
  }, [tasks, done]);

  const visible = useMemo(() => tasks.filter((t) => t.section === tab), [tasks, tab]);
  const openCount = tasks.filter((t) => !done.includes(t.id)).length;

  function toggle(id: string) {
    setDone((x) => x.includes(id) ? x.filter((v) => v !== id) : [...x, id]);
  }

  function addTask() {
    const title = newTask.trim();
    if (!title) return;
    setTasks((x) => [{ id: crypto.randomUUID(), title, detail: "Added to LIFE", section: tab, priority: "normal" }, ...x]);
    setNewTask("");
    setNotice("Added to LIFE");
    setTimeout(() => setNotice(""), 1800);
  }

  function connect(name: string) {
    setNotice(name + " connection is prepared for the next integration step.");
    setTimeout(() => setNotice(""), 2600);
  }

  return (
    <main className="life">
      <style>{\`
        *{box-sizing:border-box}html{background:#f4f6f8}body{margin:0}
        .life{min-height:100vh;color:#17202a;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,system-ui,sans-serif}
        .shell{width:min(1180px,calc(100% - 32px));margin:auto;padding:22px 0 44px}
        header{display:flex;justify-content:space-between;align-items:center;padding:5px 0 24px}
        .brand{font-size:24px;font-weight:800;letter-spacing:-.8px}.badge{font-size:12px;padding:7px 11px;border-radius:999px;background:#e8edf2;color:#52606d}
        .hero{padding:28px 0 22px}.eyebrow{color:#71808e;font-size:12px;font-weight:750;letter-spacing:.12em}
        h1{font-size:clamp(40px,7vw,68px);line-height:.98;letter-spacing:-3px;margin:10px 0 16px}.sub{font-size:17px;line-height:1.55;color:#697784;max-width:680px}
        .layout{display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:start}
        .panel{background:#fff;border:1px solid #e1e6eb;border-radius:22px;box-shadow:0 8px 28px rgba(30,45,60,.055)}
        .main{padding:20px}.tabs{display:flex;gap:6px;margin-bottom:14px}
        .tab{border:0;background:transparent;padding:10px 13px;border-radius:10px;color:#687682;font-weight:700;cursor:pointer}.tab.active{background:#17202a;color:#fff}
        .summary{display:flex;justify-content:space-between;align-items:center;padding:7px 2px 15px}.summary h2{margin:0;font-size:20px}.count{font-size:12px;color:#7b8792}
        .task{display:flex;gap:13px;align-items:flex-start;padding:16px 4px;border-top:1px solid #edf0f3}.check{width:25px;height:25px;flex:0 0 25px;border-radius:50%;border:1.5px solid #b7c1ca;background:white;cursor:pointer;display:grid;place-items:center}.check.done{background:#17202a;color:#fff;border-color:#17202a}
        .taskTitle{font-weight:700;margin-bottom:4px}.taskTitle.strike{text-decoration:line-through;color:#87929c}.detail{font-size:13px;color:#7a8691;line-height:1.45}.high{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:#8a5960;font-weight:800;margin-left:8px}
        .composer{display:flex;gap:8px;margin-top:14px}.composer input{min-width:0;flex:1;border:1px solid #d9e0e6;border-radius:11px;padding:12px 13px;font:inherit;outline:none}.composer button,.connect{border:1px solid #17202a;background:#17202a;color:#fff;border-radius:11px;padding:11px 14px;font-weight:750;cursor:pointer}
        .side{padding:18px}.side h3{margin:2px 0 14px;font-size:16px}.metric{padding:14px 0;border-top:1px solid #edf0f3}.metric:first-of-type{border-top:0}.metric b{display:block;font-size:23px}.metric span{font-size:12px;color:#7b8792}
        .integration{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:13px 0;border-top:1px solid #edf0f3}.integration:first-of-type{border-top:0}.integration b{font-size:14px}.integration span{display:block;font-size:11px;color:#7b8792;margin-top:3px}.connect{padding:8px 10px;font-size:11px}
        .calendar{padding:2px 4px}.event{display:flex;gap:15px;padding:15px 0;border-top:1px solid #edf0f3}.time{width:48px;color:#788590;font-size:12px;font-weight:700}.event b{font-size:14px}.event span{display:block;color:#7b8792;font-size:12px;margin-top:4px}
        .notice{position:fixed;right:18px;bottom:18px;background:#17202a;color:#fff;border-radius:12px;padding:12px 15px;font-size:13px;box-shadow:0 10px 30px rgba(0,0,0,.15)}
        footer{text-align:center;color:#9aa3ac;font-size:11px;padding:28px 0 0}
        @media(max-width:800px){.layout{grid-template-columns:1fr}.side{order:2}}@media(max-width:600px){.shell{width:calc(100% - 24px);padding-top:14px}header{padding-bottom:15px}.hero{padding-top:22px}h1{letter-spacing:-2px}.panel{border-radius:18px}.main{padding:15px}.composer{display:grid;grid-template-columns:1fr auto}}
      \`}</style>

      <div className="shell">
        <header><div className="brand">LIFE</div><div className="badge">Private · Personal OS</div></header>
        <section className="hero">
          <div className="eyebrow">GOOD MORNING</div>
          <h1>Your life.<br/>Under control.</h1>
          <div className="sub">LIFE turns your email, calendar and documents into a short list of things that actually need your attention.</div>
        </section>
        <div className="layout">
          <section className="panel main">
            <div className="tabs">
              {(["Today","Inbox","Calendar"] as const).map((x) => <button key={x} className={"tab " + (tab===x ? "active" : "")} onClick={()=>setTab(x)}>{x}</button>)}
            </div>
            {tab === "Calendar" ? (
              <div className="calendar">
                <div className="summary"><h2>Today</h2><span className="count">{events.length} events</span></div>
                {events.map((e)=><div className="event" key={e.time}><div className="time">{e.time}</div><div><b>{e.title}</b><span>{e.meta}</span></div></div>)}
              </div>
            ) : (
              <>
                <div className="summary"><h2>{tab}</h2><span className="count">{visible.filter(x=>!done.includes(x.id)).length} open</span></div>
                {visible.length === 0 && <div className="detail" style={{padding:"18px 4px"}}>Nothing here yet.</div>}
                {visible.map((item) => {
                  const isDone = done.includes(item.id);
                  return <div className="task" key={item.id}>
                    <button className={"check " + (isDone ? "done" : "")} onClick={()=>toggle(item.id)} aria-label={isDone ? "Mark active" : "Mark done"}>{isDone ? "✓" : ""}</button>
                    <div><div className={"taskTitle " + (isDone ? "strike" : "")}>{item.title}{item.priority==="high" && !isDone && <span className="high">Important</span>}</div><div className="detail">{item.detail}</div></div>
                  </div>;
                })}
                <div className="composer"><input value={newTask} onChange={e=>setNewTask(e.target.value)} onKeyDown={e=>{if(e.key==="Enter")addTask()}} placeholder={"Add to " + tab.toLowerCase() + "…"} /><button onClick={addTask}>Add</button></div>
              </>
            )}
          </section>
          <aside className="panel side">
            <h3>At a glance</h3>
            <div className="metric"><b>{openCount}</b><span>open items</span></div>
            <div className="metric"><b>{done.length}</b><span>completed</span></div>
            <div className="metric"><b>1</b><span>day in focus</span></div>
            <h3 style={{marginTop:22}}>Connections</h3>
            <div className="integration"><div><b>Gmail</b><span>Read-only · planned</span></div><button className="connect" onClick={()=>connect("Gmail")}>Connect</button></div>
            <div className="integration"><div><b>Calendar</b><span>Read-only · planned</span></div><button className="connect" onClick={()=>connect("Calendar")}>Connect</button></div>
            <div className="integration"><div><b>Documents</b><span>Local-first surface</span></div><button className="connect" onClick={()=>connect("Documents")}>Open</button></div>
          </aside>
        </div>
        <footer>LIFE · standalone application · local state only · no EIE dependency</footer>
      </div>
      {notice && <div className="notice">{notice}</div>}
    </main>
  );
}
