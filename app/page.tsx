"use client";

import { useState } from "react";

const items = [
  { title: "Today", text: "Your important tasks, deadlines and commitments in one place." },
  { title: "Inbox", text: "Connect Gmail later to extract actionable obligations automatically." },
  { title: "Calendar", text: "Your day, meetings and upcoming commitments." },
];

export default function LifePage() {
  const [done, setDone] = useState<string[]>([]);
  const toggle = (id: string) => setDone((x) => x.includes(id) ? x.filter((v) => v !== id) : [...x, id]);

  return (
    <main className="life">
      <style>{`
        *{box-sizing:border-box} body{margin:0;background:#f6f7f9}
        .life{min-height:100vh;color:#17202a;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,system-ui,sans-serif}
        .shell{width:min(100% - 32px,760px);margin:auto;padding:22px 0 40px}
        header{display:flex;justify-content:space-between;align-items:center;padding:8px 0 30px}
        .brand{font-size:24px;font-weight:750;letter-spacing:-.7px}.badge{font-size:12px;padding:7px 10px;border-radius:999px;background:#e9eef5;color:#536170}
        .hero{padding:30px 0 24px}.eyebrow{color:#6a7684;font-size:14px;font-weight:650}
        h1{font-size:clamp(42px,11vw,72px);line-height:.98;letter-spacing:-3px;margin:12px 0 18px}
        .sub{font-size:18px;line-height:1.5;color:#687481;max-width:600px}
        .today{margin-top:26px;background:#fff;border:1px solid #e3e7ec;border-radius:24px;padding:22px;box-shadow:0 8px 30px rgba(30,45,60,.06)}
        .today h2{margin:0 0 5px;font-size:21px}.date{color:#7b8792;font-size:14px}
        .task{display:flex;gap:13px;align-items:flex-start;padding:17px 0;border-bottom:1px solid #edf0f3}.task:last-child{border-bottom:0}
        .check{width:25px;height:25px;flex:0 0 25px;border-radius:50%;border:1.5px solid #b8c1ca;background:white;cursor:pointer;display:grid;place-items:center}
        .check.done{background:#17202a;color:white;border-color:#17202a}.task-title{font-weight:650;margin-bottom:4px}.task-text{color:#74808b;font-size:14px;line-height:1.4}
        .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}.card{background:#fff;border:1px solid #e3e7ec;border-radius:18px;padding:18px}
        .icon{font-size:20px;margin-bottom:12px}.card b{display:block;margin-bottom:6px}.card span{color:#77828d;font-size:13px;line-height:1.4}
        footer{text-align:center;color:#9aa3ac;font-size:12px;padding:30px 0 5px}
        @media(max-width:600px){.shell{width:min(100% - 24px,760px);padding-top:14px}.cards{grid-template-columns:1fr}.hero{padding-top:22px}h1{letter-spacing:-2px}.today{border-radius:20px;padding:18px}}
      `}</style>
      <div className="shell">
        <header><div className="brand">LIFE</div><div className="badge">Private · Personal OS</div></header>
        <section className="hero"><div className="eyebrow">GOOD MORNING</div><h1>Your life.<br/>Under control.</h1><div className="sub">LIFE turns your email, calendar and documents into a short list of things that actually need your attention.</div></section>
        <section className="today"><h2>Today</h2><div className="date">Your personal command center</div>
          {items.map((item)=>{const isDone=done.includes(item.title);return <div className="task" key={item.title}><button className={`check ${isDone?"done":""}`} onClick={()=>toggle(item.title)} aria-label={isDone?"Mark active":"Mark done"}>{isDone?"✓":""}</button><div><div className="task-title">{item.title}</div><div className="task-text">{item.text}</div></div></div>})}
        </section>
        <section className="cards">
          <div className="card"><div className="icon">✉</div><b>Gmail</b><span>OAuth connection is planned for T1a.</span></div>
          <div className="card"><div className="icon">◷</div><b>Calendar</b><span>Google Calendar follows the Gmail integration.</span></div>
          <div className="card"><div className="icon">🔒</div><b>Privacy first</b><span>Read-only permissions, revocable access and no training by default.</span></div>
        </section>
        <footer>LIFE · T1a · isolated application surface</footer>
      </div>
    </main>
  );
}
